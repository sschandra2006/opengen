"""
Information Extractor for Reference Document Intelligence.
Extracts structured facts, tables, entities, and context from reference documents.
"""
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from opengen.domain.document import (
    ExtractedInformation, ExtractedField, ExtractedTable
)
from opengen.cache.disk_store import cache_manager
from opengen.engines.document.reference.pymupdf_extractor import PyMuPDFExtractor
from opengen.engines.document.reference.docling_extractor import DoclingExtractor
from opengen.providers.manager import ProviderManager, provider_manager

logger = logging.getLogger(__name__)

# Common regex patterns for deterministic local extraction
REGEX_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone": re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "date": re.compile(r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
    "currency": re.compile(r'(?:[\$€£₹]|\bUSD|\bEUR|\bINR)\s*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?'),
    "key_value": re.compile(r'^([A-Za-z0-9\s/_-]{2,35}):\s*([^\r\n]+)$', re.MULTILINE)
}

class ExtractedEntityItem(BaseModel):
    field: str
    value: str
    type: str = "text"
    confidence: float = 0.90

class ExtractedEntitiesResponse(BaseModel):
    entities: List[ExtractedEntityItem] = []

class ReferenceIntelligenceEngine:
    """Orchestrates extraction of structured knowledge from reference documents."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None):
        self.provider_manager = provider_mgr or provider_manager

    def process_reference(self, file_path: str, file_hash: str) -> ExtractedInformation:
        filename = Path(file_path).name

        # 1. Check persistent L2 cache
        cached_data = cache_manager.get_reference_extraction(file_hash)
        if cached_data:
            logger.info(f"Loaded extracted reference data for '{filename}' from L2 cache (0 tokens)")
            return ExtractedInformation.model_validate(cached_data)

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
            parsed = PyMuPDFExtractor.extract_document(file_path)

        fields: List[ExtractedField] = []
        raw_text = parsed.get("full_text", "")

        # 3. Deterministic Local Pattern Extraction (0 AI tokens)
        for page_data in parsed.get("pages", []):
            page_num = page_data["page"]
            text = page_data["text"]

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

        # 4. Fallback LLM Entity Extraction for unstructured paragraphs if insufficient fields
        if len(fields) < 4 and len(raw_text) > 100:
            prompt = (
                f"Analyze this document excerpt from '{filename}' and extract key factual entities (names, titles, organizations, dates, amounts, qualifications, addresses, identifiers).\n"
                f"Excerpt:\n{raw_text[:2500]}"
            )
            try:
                ai_res, _ = self.provider_manager.generate_structured(
                    prompt=prompt,
                    response_model=ExtractedEntitiesResponse
                )
                for ent in ai_res.entities:
                    f_name = ent.field.strip()
                    f_val = ent.value.strip()
                    if f_name and f_val:
                        fields.append(ExtractedField(
                            field=f_name,
                            value=f_val,
                            source=filename,
                            page=1,
                            confidence=ent.confidence,
                            field_type=ent.type,
                            context=f"Extracted entity from {filename}"
                        ))
            except Exception as e:
                logger.warning(f"Fallback LLM extraction skipped: {e}")

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

        # 5. Save to L2 Cache
        cache_manager.set_reference_extraction(file_hash, extracted_info.model_dump())
        return extracted_info


class ReferenceExtractor:
    """Convenience wrapper for extracting knowledge from reference documents."""

    @classmethod
    def extract_reference(cls, file_path: str, provider_mgr: Optional[ProviderManager] = None) -> ExtractedInformation:
        import hashlib
        path = Path(file_path)
        if not path.exists():
            return ExtractedInformation(
                document_id="empty",
                filename=path.name,
                file_hash="",
                raw_text=""
            )
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        engine = ReferenceIntelligenceEngine(provider_mgr=provider_mgr)
        return engine.process_reference(file_path=file_path, file_hash=file_hash)

