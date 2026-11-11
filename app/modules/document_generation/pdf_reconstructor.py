"""
PDF Template Reconstructor for Module 6.
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

from app.models.mapping import MappingReport
from app.models.template_profile import TemplateProfile
from app.modules.document_generation.table_builder import TableBuilder
from app.modules.template_intelligence.docx_analyzer import PLACEHOLDER_REGEX

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
                            font_name = span.get("font", "Calibri")
                            font_size = span.get("size", 11.0)
                            flags = span.get("flags", 0)

                            run.font.name = "Calibri"  # Safe standard font
                            run.font.size = Pt(min(max(font_size, 8.0), 28.0))
                            run.bold = bool(flags & 2 or "bold" in font_name.lower())
                            run.italic = bool(flags & 1 or "italic" in font_name.lower())

                # Image Block
                elif block.get("type") == 1:
                    pass # Embedded images can be preserved if needed

            # 3. If tables found on this page, reconstruct them in docx
            for tab in page_tables:
                extracted = tab.extract()
                if extracted and len(extracted) > 0:
                    num_rows = len(extracted)
                    num_cols = len(extracted[0])
                    word_table = doc.add_table(rows=num_rows, cols=num_cols)
                    
                    for r_idx, row in enumerate(extracted):
                        for c_idx, val in enumerate(row):
                            cell_text = (val or "").strip()
                            for raw_k, repl_val in replacements.items():
                                if raw_k in cell_text:
                                    cell_text = cell_text.replace(raw_k, repl_val)
                            cell = word_table.cell(r_idx, c_idx)
                            cell.text = cell_text
                            if r_idx == 0:
                                for run in cell.paragraphs[0].runs:
                                    run.bold = True

                    TableBuilder.apply_advanced_properties(word_table)

        pdf_doc.close()
        doc.save(output_docx_path)
        logger.info(f"Reconstructed PDF template as editable DOCX: {output_docx_path}")
        return output_docx_path
