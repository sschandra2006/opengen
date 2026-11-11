"""
Visual Document Inspector for Module 7.
Inspects rendered PDF pages for overflow, blank pages, page count diffs,
margin violations, and broken tables using PyMuPDF.
"""
import logging
from typing import List, Dict, Any, Optional
import fitz

from app.models.validation_report import (
    FormattingValidationReport, PageVisualInspection, VisualIssue
)

logger = logging.getLogger(__name__)

class VisualInspector:
    """Performs geometric and visual layout inspection of rendered PDF documents."""

    @classmethod
    def inspect(cls, rendered_pdf_path: str, template_page_count: int = 1, iteration: int = 1) -> FormattingValidationReport:
        doc = fitz.open(rendered_pdf_path)
        gen_pages = len(doc)
        pages_inspection: List[PageVisualInspection] = []
        issues_summary: List[str] = []

        is_valid = True
        page_count_match = (gen_pages <= template_page_count or template_page_count == 0)

        if gen_pages > template_page_count and template_page_count > 0:
            msg = f"Unexpected page count increase: Template has {template_page_count} page(s), but generated output expanded to {gen_pages} page(s)."
            issues_summary.append(msg)
            is_valid = False

        for p_idx, page in enumerate(doc):
            page_num = p_idx + 1
            rect = page.rect
            page_text = page.get_text("text").strip()
            blocks = page.get_text("blocks")
            text_blocks = [b for b in blocks if len(b) > 4 and str(b[4]).strip()]
            images = page.get_images()
            drawings = page.get_drawings()

            page_issues: List[VisualIssue] = []

            # 1. Blank page detection
            is_blank = False
            if len(page_text) < 5 and len(images) == 0 and len(drawings) == 0:
                is_blank = True
                issue = VisualIssue(
                    issue_type="blank_page",
                    page_number=page_num,
                    severity="error",
                    description=f"Page {page_num} appears entirely blank.",
                    suggested_fix="Remove trailing page breaks or reduce paragraph spacing."
                )
                page_issues.append(issue)
                issues_summary.append(issue.description)
                is_valid = False

            # 2. Margin & Text Overflow Detection
            has_overflow = False
            # If text extends into the bottom 25 points or right 20 points
            if text_blocks:
                max_y1 = max(b[3] for b in text_blocks)
                max_x1 = max(b[2] for b in text_blocks)
                if max_y1 > (rect.height - 25) or max_x1 > (rect.width - 20):
                    has_overflow = True
                    issue = VisualIssue(
                        issue_type="overflow",
                        page_number=page_num,
                        severity="warning",
                        description=f"Text on Page {page_num} extends beyond margin boundary.",
                        suggested_fix="Downscale font sizes or reduce paragraph before/after spacing."
                    )
                    page_issues.append(issue)
                    issues_summary.append(issue.description)
                    is_valid = False

            # 3. Table Inspection
            has_broken_table = False
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for tab in tables.tables:
                        tab_bbox = tab.bbox
                        # Check horizontal clipping
                        if tab_bbox[2] > (rect.width - 20):
                            has_broken_table = True
                            issue = VisualIssue(
                                issue_type="broken_table",
                                page_number=page_num,
                                severity="error",
                                description=f"Table on Page {page_num} overflows past right page boundary.",
                                suggested_fix="Adjust column widths and reduce cell margins."
                            )
                            page_issues.append(issue)
                            issues_summary.append(issue.description)
                            is_valid = False
            except Exception:
                pass

            pages_inspection.append(PageVisualInspection(
                page_number=page_num,
                has_text_overflow=has_overflow,
                is_blank=is_blank,
                has_broken_table=has_broken_table,
                detected_elements={
                    "text_length": len(page_text),
                    "images_count": len(images),
                    "drawings_count": len(drawings)
                },
                issues=page_issues
            ))

        doc.close()

        status = "passed" if is_valid else ("warning" if any(i.severity == "warning" for p in pages_inspection for i in p.issues) else "failed")

        return FormattingValidationReport(
            is_valid=is_valid,
            iteration=iteration,
            template_page_count=template_page_count,
            generated_page_count=gen_pages,
            page_count_match=page_count_match,
            pages=pages_inspection,
            total_issues=len(issues_summary),
            issues_summary=issues_summary,
            status=status
        )
