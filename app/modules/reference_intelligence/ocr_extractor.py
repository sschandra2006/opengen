"""
OCR Fallback Extractor for Scanned Reference Documents.
Utilizes RapidOCR and PyMuPDF pixmaps to extract text from image-only pages.
"""
import logging
from typing import List, Dict, Any, Tuple
import fitz

logger = logging.getLogger(__name__)

class OCRExtractor:
    """Extracts text from scanned PDF pages using local OCR."""

    _ocr_engine = None

    @classmethod
    def get_engine(cls):
        if cls._ocr_engine is None:
            try:
                from rapidocr import RapidOCR
                cls._ocr_engine = RapidOCR()
            except Exception:
                try:
                    from rapidocr_onnxruntime import RapidOCR
                    cls._ocr_engine = RapidOCR()
                except Exception as e:
                    logger.warning(f"RapidOCR not available: {e}")
        return cls._ocr_engine

    @classmethod
    def extract_page_ocr(cls, page: fitz.Page) -> Tuple[str, float]:
        """
        Renders a PDF page to pixmap and runs OCR.
        Returns (extracted_text, confidence)
        """
        try:
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            engine = cls.get_engine()
            if engine:
                res = engine(img_bytes)
                # Handle RapidOCROutput object (newer rapidocr)
                if hasattr(res, "txts") and res.txts:
                    lines = [str(t).strip() for t in res.txts if t]
                    scores = res.scores if hasattr(res, "scores") and res.scores else []
                    avg_conf = sum(scores) / len(scores) if scores else 0.90
                    return "\n".join(lines), round(float(avg_conf), 2)
                # Handle legacy tuple (result, elapse)
                elif isinstance(res, tuple) and res[0]:
                    lines = [item[1] for item in res[0] if item and len(item) > 1]
                    confidences = [item[2] for item in res[0] if item and len(item) > 2]
                    avg_conf = sum(confidences) / len(confidences) if confidences else 0.85
                    return "\n".join(lines), round(float(avg_conf), 2)
        except Exception as e:
            logger.warning(f"OCR failed for page {page.number}: {e}")

        return "", 0.0
