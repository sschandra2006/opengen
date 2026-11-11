"""
PyMuPDF Fast Document & Table Extractor.
Extracts structured text, tables, and headings with page numbers and confidence tracking.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
import fitz

from opengen.domain.document import ExtractedTable
from opengen.engines.document.reference.ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)

class PyMuPDFExtractor:
    """Fast local extractor using PyMuPDF with OCR fallback."""

    @classmethod
    def extract_document(cls, file_path: str) -> Dict[str, Any]:
        doc = fitz.open(file_path)
        pages_content = []
        tables: List[ExtractedTable] = []
        headings = []
        full_text_parts = []
        ocr_used = False
        filename = Path(file_path).name

        table_idx = 0
        for p_idx, page in enumerate(doc):
            page_num = p_idx + 1
            page_text = page.get_text("text").strip()
            page_conf = 0.98

            # If page has almost no selectable text, attempt OCR
            if len(page_text) < 30:
                ocr_text, ocr_conf = OCRExtractor.extract_page_ocr(page)
                if ocr_text:
                    page_text = ocr_text
                    page_conf = ocr_conf
                    ocr_used = True

            full_text_parts.append(f"--- PAGE {page_num} ---\n{page_text}")

            # Extract tables
            try:
                found_tabs = page.find_tables()
                if found_tabs and found_tabs.tables:
                    for tab in found_tabs.tables:
                        table_idx += 1
                        grid = tab.extract()
                        if grid and len(grid) > 0:
                            header_row = [str(c or "").strip() for c in grid[0]]
                            data_rows = [
                                [str(c or "").strip() for c in row]
                                for row in grid[1:]
                            ]
                            tables.append(ExtractedTable(
                                table_index=table_idx,
                                source=filename,
                                page=page_num,
                                headers=header_row,
                                rows=data_rows,
                                confidence=0.95
                            ))
            except Exception as e:
                logger.debug(f"Table extraction error on page {page_num}: {e}")

            # Extract Headings (larger fonts)
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("size", 10) >= 13.0 or "bold" in span.get("font", "").lower():
                                span_text = span.get("text", "").strip()
                                if span_text and len(span_text) < 100:
                                    headings.append({
                                        "text": span_text,
                                        "page": page_num,
                                        "size": span.get("size")
                                    })

            pages_content.append({
                "page": page_num,
                "text": page_text,
                "confidence": page_conf
            })

        total_pages = len(doc)
        doc.close()

        return {
            "pages": pages_content,
            "tables": tables,
            "headings": headings,
            "full_text": "\n\n".join(full_text_parts),
            "ocr_used": ocr_used,
            "total_pages": total_pages
        }
