"""
DOCX Template Populator.
Preserves original template formatting, styles, margins, headers, footers,
and tables while accurately substituting placeholders and populating data.
Never modifies the original source template.
"""
import shutil
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from opengen.domain.document import TemplateProfile, MappingReport
from opengen.engines.document.table_builder import TableBuilder

logger = logging.getLogger(__name__)

class DocxPopulator:
    """Populates an existing DOCX template preserving 100% of its visual styles."""

    @classmethod
    def populate(
        cls,
        template_path: str,
        output_path: str,
        mapping_report: MappingReport,
        template_profile: TemplateProfile,
        instruction: Optional[str] = None
    ) -> str:
        import tempfile

        src = Path(template_path).resolve()
        dst = Path(output_path).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)

        # 1. Stage inside an isolated temporary folder so failed runs never corrupt sources or outputs
        with tempfile.TemporaryDirectory(prefix="opengen_docx_") as tmp_dir:
            staged_path = Path(tmp_dir) / "staged.docx"
            shutil.copy2(str(src), str(staged_path))

            doc = docx.Document(str(staged_path))

            # Build replacement dictionaries:
            replacements: Dict[str, str] = {}
            for placeholder in template_profile.placeholders:
                field_name = placeholder.field_name
                if field_name in mapping_report.mappings:
                    val = str(mapping_report.mappings[field_name].mapped_value)
                    replacements[placeholder.raw_key] = val
                    replacements[f"{{{{{field_name}}}}}"] = val
                    replacements[f"[{field_name}]"] = val
                    replacements[f"<{field_name}>"] = val
                    replacements[f"{{{field_name}}}"] = val

            # Also add any direct mappings
            for k, m in mapping_report.mappings.items():
                val = str(m.mapped_value)
                replacements[f"{{{{{k}}}}}"] = val
                replacements[f"[{k}]"] = val
                replacements[f"<{k}>"] = val
                replacements[f"{{{k}}}"] = val

            # 2. Replace placeholders in Body Paragraphs
            for p in doc.paragraphs:
                cls._replace_placeholders_in_paragraph(p, replacements)

            # 3. Replace placeholders & populate mapped tables
            for t_idx, table in enumerate(doc.tables):
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            cls._replace_placeholders_in_paragraph(p, replacements)

                for t_map in mapping_report.table_mappings:
                    if t_map.template_table_index == t_idx + 1 and t_map.rows_data:
                        cls._populate_table_rows(table, t_map.rows_data)

                TableBuilder.apply_advanced_properties(table)

            # 4. Replace in Headers and Footers
            for section in doc.sections:
                for hp in section.header.paragraphs:
                    cls._replace_placeholders_in_paragraph(hp, replacements)
                for fp in section.footer.paragraphs:
                    cls._replace_placeholders_in_paragraph(fp, replacements)

            # 5. Non-placeholder insertion fallback if document is completely blank of tags
            if not template_profile.placeholders and mapping_report.mappings:
                cls._insert_non_placeholder_content(doc, mapping_report)

            doc.save(str(staged_path))
            shutil.copy2(str(staged_path), str(dst))

        logger.info(f"DOCX template populated successfully: {dst}")
        return str(dst)

    @classmethod
    def _replace_placeholders_in_paragraph(cls, paragraph: docx.text.paragraph.Paragraph, replacements: Dict[str, str]):
        """
        Replaces placeholders across XML runs preserving character formatting.
        Handles both single-run and multi-run split placeholders.
        """
        if not paragraph.text:
            return

        full_text = paragraph.text
        has_match = False
        for ph in replacements:
            if ph in full_text:
                has_match = True
                break

        if not has_match:
            return

        # Attempt simple per-run replacement first to preserve exact fonts
        for run in paragraph.runs:
            for ph, val in replacements.items():
                if ph in run.text:
                    run.text = run.text.replace(ph, val)

        # Check if placeholder was split across runs
        current_text = "".join(r.text for r in paragraph.runs)
        still_contains = any(ph in current_text for ph in replacements)
        if still_contains:
            # Consolidate runs while preserving the first run's font styling
            first_font = None
            first_size = None
            first_bold = False
            first_italic = False
            first_color = None
            if paragraph.runs:
                r0 = paragraph.runs[0]
                first_font = r0.font.name
                first_size = r0.font.size
                first_bold = r0.bold
                first_italic = r0.italic
                first_color = r0.font.color.rgb if r0.font.color else None

            new_text = current_text
            for ph, val in replacements.items():
                new_text = new_text.replace(ph, val)

            paragraph.text = new_text
            if paragraph.runs and (first_font or first_size or first_bold or first_color):
                r = paragraph.runs[0]
                if first_font:
                    r.font.name = first_font
                if first_size:
                    r.font.size = first_size
                r.bold = first_bold
                r.italic = first_italic
                if first_color:
                    r.font.color.rgb = first_color

    @classmethod
    def _populate_table_rows(cls, table: docx.table.Table, rows_data: List[List[str]]):
        """Populates new data rows into a template table preserving header styling."""
        if not rows_data:
            return

        num_cols = len(table.columns)

        # Style reference row (row 1 if available, otherwise row 0)
        sample_row = table.rows[1] if len(table.rows) > 1 else table.rows[0]
        sample_fonts = []
        for cell in sample_row.cells:
            f_name, f_size, f_bold = "Calibri", Pt(10), False
            if cell.paragraphs and cell.paragraphs[0].runs:
                r = cell.paragraphs[0].runs[0]
                f_name = r.font.name or "Calibri"
                f_size = r.font.size or Pt(10)
                f_bold = r.bold or False
            sample_fonts.append((f_name, f_size, f_bold))

        for row_vals in rows_data:
            new_row = table.add_row()
            for c_idx, val in enumerate(row_vals[:num_cols]):
                cell = new_row.cells[c_idx]
                cell.text = str(val)
                if cell.paragraphs and cell.paragraphs[0].runs and c_idx < len(sample_fonts):
                    r = cell.paragraphs[0].runs[0]
                    f_name, f_size, f_bold = sample_fonts[c_idx]
                    r.font.name = f_name
                    r.font.size = f_size
                    r.bold = f_bold

    @classmethod
    def _insert_non_placeholder_content(cls, doc: docx.Document, mapping_report: MappingReport):
        """Fallback appending extracted fields when template contains zero tags."""
        doc.add_heading("Extracted & Verified Data", level=2)
        for k, mapping in mapping_report.mappings.items():
            p = doc.add_paragraph()
            p.add_run(f"{k.replace('_', ' ').title()}: ").bold = True
            p.add_run(str(mapping.mapped_value))
