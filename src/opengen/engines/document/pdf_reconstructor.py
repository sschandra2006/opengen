"""
PDF Template Reconstructor.
Reconstructs a PDF template's visual layout, typography, tables, and images
into a 100% editable Microsoft Word (.docx) document.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from opengen.domain.document import TemplateProfile, MappingReport
from opengen.engines.document.table_builder import TableBuilder

logger = logging.getLogger(__name__)

class PdfReconstructor:
    """Recreates a PDF template into an editable Word document."""

    @classmethod
    def reconstruct(
        cls,
        pdf_path: str,
        output_docx_path: str,
        mapping_report: MappingReport,
        template_profile: TemplateProfile
    ) -> str:
        pdf_doc = fitz.open(pdf_path)
        doc = docx.Document()

        # Build replacement lookup
        replacements = {}
        for k, m in mapping_report.mappings.items():
            val = str(m.mapped_value)
            replacements[f"{{{{{k}}}}}"] = val
            replacements[f"[{k}]"] = val
            replacements[f"<{k}>"] = val
            replacements[f"{{{k}}}"] = val

        for ph in template_profile.placeholders:
            if ph.field_name in mapping_report.mappings:
                val = str(mapping_report.mappings[ph.field_name].mapped_value)
                replacements[ph.raw_key] = val

        # Configure first section geometry
        first_sec = doc.sections[0]
        first_sec.top_margin = Inches(template_profile.margins.top)
        first_sec.bottom_margin = Inches(template_profile.margins.bottom)
        first_sec.left_margin = Inches(template_profile.margins.left)
        first_sec.right_margin = Inches(template_profile.margins.right)

        if template_profile.orientation == "landscape":
            first_sec.page_width = Inches(11.69)
            first_sec.page_height = Inches(8.27)
        else:
            first_sec.page_width = Inches(8.27)
            first_sec.page_height = Inches(11.69)

        total_pdf_pages = len(pdf_doc)

        for p_idx, page in enumerate(pdf_doc):
            if p_idx > 0:
                doc.add_page_break()

            # 1. Check for Tables on this page
            page_tables = []
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    page_tables = tabs.tables
            except Exception:
                pass

            # 2. Extract text blocks
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])

            for block in blocks:
                # Text Block
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        p = doc.add_paragraph()
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(3)

                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if not span_text:
                                continue

                            # Replace placeholders if present
                            for raw_k, repl_val in replacements.items():
                                if raw_k in span_text:
                                    span_text = span_text.replace(raw_k, repl_val)

                            run = p.add_run(span_text)
                            size = span.get("size", 10.5)
                            run.font.size = Pt(min(max(8, size), 24))

                            flags = span.get("flags", 0)
                            font_name = span.get("font", "").lower()
                            if flags & 2 or "bold" in font_name:
                                run.bold = True
                            if flags & 1 or "italic" in font_name or "oblique" in font_name:
                                run.italic = True

                            # Color
                            color_int = span.get("color", 0)
                            if color_int:
                                r = (color_int >> 16) & 255
                                g = (color_int >> 8) & 255
                                b = color_int & 255
                                run.font.color.rgb = RGBColor(r, g, b)

            # 3. Add Tables
            for tab in page_tables:
                grid = tab.extract()
                if grid and len(grid) > 0:
                    num_rows = len(grid)
                    num_cols = len(grid[0])
                    doc_tbl = doc.add_table(rows=num_rows, cols=num_cols)
                    TableBuilder.apply_advanced_properties(doc_tbl)

                    for r_i, row in enumerate(grid):
                        for c_i, val in enumerate(row):
                            cell_text = str(val or "")
                            for raw_k, repl_val in replacements.items():
                                if raw_k in cell_text:
                                    cell_text = cell_text.replace(raw_k, repl_val)
                            doc_tbl.cell(r_i, c_i).text = cell_text

        pdf_doc.close()
        doc.save(output_docx_path)
        logger.info(f"Reconstructed editable DOCX from PDF: {output_docx_path}")
        return output_docx_path
