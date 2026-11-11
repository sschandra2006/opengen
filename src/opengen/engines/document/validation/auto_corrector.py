"""
Auto-Correction Engine for Visual Document Validation.
Iteratively fixes overflow, table clipping, and page bloat up to 3 times.
"""
import logging
from typing import Tuple
import docx
from docx.shared import Pt

from opengen.domain.document import FormattingValidationReport
from opengen.engines.document.validation.renderer import DocumentRenderer
from opengen.engines.document.validation.inspector import VisualInspector
from opengen.engines.document.table_builder import TableBuilder

logger = logging.getLogger(__name__)

class AutoCorrector:
    """Executes automatic feedback-driven correction loops on generated Word documents."""

    @classmethod
    def run_correction_loop(
        cls,
        docx_path: str,
        pdf_path: str,
        template_page_count: int,
        max_iterations: int = 3
    ) -> Tuple[FormattingValidationReport, str]:
        # Initial render & inspection
        DocumentRenderer.convert_docx_to_pdf(docx_path, pdf_path)
        report = VisualInspector.inspect(pdf_path, template_page_count=template_page_count, iteration=1)

        if report.is_valid:
            logger.info("Visual validation passed on first iteration without corrections.")
            return report, pdf_path

        # Iterative auto-correction loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Auto-correction iteration {iteration}/{max_iterations} for {docx_path}")
            corrections = cls._apply_docx_corrections(docx_path, report, iteration)
            report.corrections_applied.extend(corrections)

            # Re-render
            DocumentRenderer.convert_docx_to_pdf(docx_path, pdf_path)
            # Re-inspect
            report = VisualInspector.inspect(pdf_path, template_page_count=template_page_count, iteration=iteration + 1)
            report.corrections_applied = corrections

            if report.is_valid:
                logger.info(f"Auto-correction succeeded at iteration {iteration}.")
                report.status = "auto_corrected"
                return report, pdf_path

        logger.warning(f"Auto-correction reached max iterations ({max_iterations}). Remaining issues documented in report.")
        return report, pdf_path

    @classmethod
    def _apply_docx_corrections(cls, docx_path: str, report: FormattingValidationReport, iteration: int) -> list:
        doc = docx.Document(docx_path)
        applied = []

        # Strategy 1: Tighten paragraph spacing
        for p in doc.paragraphs:
            if p.paragraph_format.space_after and p.paragraph_format.space_after > Pt(2):
                p.paragraph_format.space_after = Pt(2)
            if p.paragraph_format.space_before and p.paragraph_format.space_before > Pt(2):
                p.paragraph_format.space_before = Pt(0)
            if iteration >= 2 and p.paragraph_format.line_spacing and p.paragraph_format.line_spacing > 1.05:
                p.paragraph_format.line_spacing = 1.05

        applied.append("Reduced paragraph before/after spacing and tightened line spacing")

        # Strategy 2: Downscale fonts by 0.5pt on iteration 2 or 3
        if iteration >= 2:
            for p in doc.paragraphs:
                for run in p.runs:
                    if run.font.size and run.font.size.pt > 8.5:
                        run.font.size = Pt(max(8.0, run.font.size.pt - 0.5))
            applied.append("Downscaled body typography by 0.5pt to prevent overflow")

        # Strategy 3: Tighten table padding & cell margins
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    TableBuilder.set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(1)
                        p.paragraph_format.space_before = Pt(0)
                        for run in p.runs:
                            if run.font.size and run.font.size.pt > 8.0:
                                run.font.size = Pt(max(7.5, run.font.size.pt - 0.5))

        applied.append("Compacted table cell padding and cell typography")

        doc.save(docx_path)
        return applied
