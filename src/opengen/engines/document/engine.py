"""
Unified Document Generation Engine (Engine A Coordinator).
Coordinates template preservation, PDF reconstruction, Jinja2 rendering, and visual healing loops.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from opengen.domain.document import (
    TemplateProfile, MappingReport, FormattingValidationReport
)
from opengen.engines.document.docx_populator import DocxPopulator
from opengen.engines.document.pdf_reconstructor import PdfReconstructor
from opengen.engines.document.template.docxtpl_engine import DocxTplEngine
from opengen.engines.document.validation.auto_corrector import AutoCorrector

logger = logging.getLogger(__name__)

class DocumentEngine:
    """Master entrypoint for Engine A: Document Generation."""

    @classmethod
    def generate_document(
        cls,
        template_path: str,
        output_docx_path: str,
        mapping_report: MappingReport,
        template_profile: TemplateProfile,
        instruction: Optional[str] = None,
        use_jinja2: bool = False,
        jinja2_context: Optional[Dict[str, Any]] = None
    ) -> str:
        ext = Path(template_path).suffix.lower()

        if use_jinja2 and ext == ".docx" and jinja2_context:
            logger.info("Executing Jinja2 dynamic template rendering (docxtpl)")
            return DocxTplEngine.render_template(
                template_path=template_path,
                output_path=output_docx_path,
                context=jinja2_context
            )
        elif ext == ".docx":
            logger.info("Executing DOCX template preservation pipeline")
            return DocxPopulator.populate(
                template_path=template_path,
                output_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile,
                instruction=instruction
            )
        elif ext == ".pdf":
            logger.info("Executing PDF template reconstruction pipeline")
            return PdfReconstructor.reconstruct(
                pdf_path=template_path,
                output_docx_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile
            )
        else:
            raise ValueError(f"Unsupported template format: '{ext}'. Must be .docx or .pdf")

    @classmethod
    def validate_and_heal(
        cls,
        docx_path: str,
        output_pdf_path: str,
        expected_page_count: int = 1,
        max_iterations: int = 3
    ) -> Tuple[FormattingValidationReport, str]:
        """Runs the 3-loop visual layout healing engine."""
        return AutoCorrector.run_correction_loop(
            docx_path=docx_path,
            pdf_path=output_pdf_path,
            template_page_count=expected_page_count,
            max_iterations=max_iterations
        )
