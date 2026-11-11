"""
Information Extractor for Module 3: Reference Document Intelligence.
Extracts structured facts, tables, entities, and context from reference documents.
Retains source filename, page number, confidence, and contextual snippet for each item.
"""
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.models.extracted_info import (
    ExtractedInformation, ExtractedField, ExtractedTable
)
from app.modules.memory_cache.storage import storage
from app.modules.reference_intelligence.pymupdf_extractor import PyMuPDFExtractor
from app.modules.reference_intelligence.docling_extractor import DoclingExtractor
from app.modules.token_optimization.ai_router import AIRouter

logger = logging.getLogger(__name__)

# Common regex patterns for deterministic local extraction
REGEX_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone": re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "date": re.compile(r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
    "currency": re.compile(r'(?:[\$€£₹]|\bUSD|\bEUR|\bINR)\s*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?'),
    "key_value": re.compile(r'^([A-Za-z0-9\s/_-]{2,35}):\s*([^\r\n]+)$', re.MULTILINE)
}

class ReferenceIntelligenceEngine:
    """Orchestrates extraction of structured knowledge from reference documents."""

    def __init__(self, ai_router: Optional[AIRouter] = None):
        self.ai_router = ai_router or AIRouter()

    def process_reference(self, file_path: str, file_hash: str) -> ExtractedInformation:
        filename = Path(file_path).name

        # 1. Check persistent cache
        cached_data = storage.get_reference_extraction(file_hash)
        if cached_data:
            logger.info(f"Loaded extracted reference data for '{filename}' from cache (0 tokens)")
            return ExtractedInformation(**cached_data)

        disk_file = settings.EXTRACTED_DATA_DIR / f"{file_hash}.json"
        if disk_file.exists():
            try:
                with open(disk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    storage.save_reference_extraction(file_hash, filename, data)
                    return ExtractedInformation(**data)
            except Exception as e:
                logger.warning(f"Failed to read disk cache for reference: {e}")

        # 2. Extract raw document content and tables locally
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            parsed = PyMuPDFExtractor.extract_document(file_path)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            parsed = {
                "pages": [{"page": 1, "text": txt, "confidence": 1.0}],
                "tables": [],
                "headings": [],
                "full_text": txt,
                "ocr_used": False,
                "total_pages": 1
            }
        else:
            # Fallback for text/docs
            parsed = PyMuPDFExtractor.extract_document(file_path)

        fields: List[ExtractedField] = []
        raw_text = parsed.get("full_text", "")

        # 3. Deterministic Local Pattern Extraction (0 AI tokens)
        for page_data in parsed.get("pages", []):
            page_num = page_data["page"]
            text = page_data["text"]

            # Key-Value lines
            for match in REGEX_PATTERNS["key_value"].finditer(text):
                raw_k, raw_v = match.group(1).strip(), match.group(2).strip()
                field_key = re.sub(r'[\s/]+', '_', raw_k).lower()
                if raw_v and len(raw_v) < 250:
                    fields.append(ExtractedField(
                        field=field_key,
                        value=raw_v,
                        source=filename,
                        page=page_num,
                        confidence=0.98,
                        field_type="key_value",
                        context=f"{raw_k}: {raw_v}",
                        raw_snippet=match.group(0)
                    ))

            # Dates
            for match in REGEX_PATTERNS["date"].finditer(text):
                val = match.group(0).strip()
                fields.append(ExtractedField(
                    field="detected_date",
                    value=val,
                    source=filename,
                    page=page_num,
                    confidence=0.95,
                    field_type="date",
                    context=text[max(0, match.start() - 30): min(len(text), match.end() + 30)],
                    raw_snippet=val
                ))

            # Currency / Financial figures
            for match in REGEX_PATTERNS["currency"].finditer(text):
                val = match.group(0).strip()
                fields.append(ExtractedField(
                    field="financial_amount",
                    value=val,
                    source=filename,
                    page=page_num,
                    confidence=0.95,
                    field_type="currency",
                    context=text[max(0, match.start() - 30): min(len(text), match.end() + 30)],
                    raw_snippet=val
                ))

        # 4. Local AI Entity Extraction using Qwen3:8B for unstructured paragraphs if insufficient fields
        if len(fields) < 4 and len(raw_text) > 100:
            prompt = (
                f"Analyze this document excerpt from '{filename}' and extract key factual entities (names, titles, organizations, dates, amounts, qualifications, addresses, identifiers).\n"
                f"Excerpt:\n{raw_text[:2500]}\n\n"
                f"Return JSON strictly formatted as:\n"
                f'{{"entities": [{{"field": "standardized_snake_case_key", "value": "extracted exact value", "type": "person_name/org/date/metric/id", "confidence": 0.95}}]}}'
            )
            ai_res = self.ai_router.route_task("preliminary_extraction", prompt)
            entities = ai_res.get("entities", [])
            for ent in entities:
                f_name = ent.get("field", "").strip()
                f_val = ent.get("value")
                if f_name and f_val:
                    fields.append(ExtractedField(
                        field=f_name,
                        value=f_val,
                        source=filename,
                        page=1,
                        confidence=float(ent.get("confidence", 0.90)),
                        field_type=ent.get("type", "text"),
                        context=f"Extracted entity from {filename}"
                    ))

        # Deduplicate fields
        seen = set()
        deduped_fields = []
        for f in fields:
            key = (f.field, str(f.value).strip().lower())
            if key not in seen:
                seen.add(key)
                deduped_fields.append(f)

        extracted_info = ExtractedInformation(
            document_id=file_hash[:12],
            filename=filename,
            file_hash=file_hash,
            fields=deduped_fields,
            tables=parsed.get("tables", []),
            headings=parsed.get("headings", []),
            raw_text=raw_text,
            ocr_used=parsed.get("ocr_used", False),
            total_pages=parsed.get("total_pages", 1)
        )

        # 5. Save to Cache
        info_dict = extracted_info.model_dump()
        storage.save_reference_extraction(file_hash, filename, info_dict)
        try:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(info_dict, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist extracted data to disk: {e}")

        return extracted_info
