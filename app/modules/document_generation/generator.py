"""
Document Generation Coordinator for Module 5 & 6.
Dispatches to DOCX Populator or PDF Reconstructor based on template type.
"""
import logging
from pathlib import Path
from typing import Optional

from app.models.mapping import MappingReport
from app.models.template_profile import TemplateProfile
from app.modules.document_generation.docx_populator import DocxPopulator
from app.modules.document_generation.pdf_reconstructor import PdfReconstructor

logger = logging.getLogger(__name__)

class DocumentGenerator:
    """Coordinates generation of high-quality editable Word documents."""

    @classmethod
    def generate(
        cls,
        template_path: str,
        output_docx_path: str,
        mapping_report: MappingReport,
        template_profile: TemplateProfile,
        instruction: Optional[str] = None
    ) -> str:
        ext = Path(template_path).suffix.lower()
        if ext == ".docx":
            logger.info("Using original DOCX template preservation pipeline")
            return DocxPopulator.populate(
                template_path=template_path,
                output_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile,
                instruction=instruction
            )
        elif ext == ".pdf":
            logger.info("Using PDF template reconstruction pipeline")
            return PdfReconstructor.reconstruct(
                pdf_path=template_path,
                output_docx_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile
            )
        else:
            raise ValueError(f"Unsupported template file extension: {ext}")
