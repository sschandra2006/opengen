"""
Docling Reference Document Extractor (Optional Extension).
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from opengen.domain.document import ExtractedTable

logger = logging.getLogger(__name__)

class DoclingExtractor:
    """Uses Docling DocumentConverter for deep layout extraction when installed."""

    _converter = None

    @classmethod
    def get_converter(cls):
        if cls._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                cls._converter = DocumentConverter()
            except Exception as e:
                logger.debug(f"Docling not available: {e}")
        return cls._converter

    @classmethod
    def extract_document(cls, file_path: str) -> Optional[Dict[str, Any]]:
        converter = cls.get_converter()
        if not converter:
            return None

        filename = Path(file_path).name
        try:
            conv_result = converter.convert(file_path)
            doc = conv_result.document
            markdown_text = doc.export_to_markdown()

            tables: List[ExtractedTable] = []
            for t_idx, table in enumerate(doc.tables):
                df = table.export_to_dataframe()
                headers = [str(col) for col in df.columns]
                rows = [[str(val) for val in row] for row in df.values.tolist()]
                tables.append(ExtractedTable(
                    table_index=t_idx + 1,
                    source=filename,
                    page=1,
                    headers=headers,
                    rows=rows,
                    confidence=0.98,
                    raw_markdown=markdown_text[:500]
                ))

            return {
                "full_text": markdown_text,
                "tables": tables,
                "ocr_used": False,
                "total_pages": 1
            }
        except Exception as e:
            logger.warning(f"Docling extraction failed for {file_path}: {e}")
            return None
