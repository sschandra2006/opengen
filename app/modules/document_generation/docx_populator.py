"""
DOCX Template Populator for Module 5.
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

from app.models.mapping import MappingReport, FieldMapping
from app.models.template_profile import TemplateProfile
from app.modules.document_generation.table_builder import TableBuilder

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
        # 1. Guarantee source document preservation
        shutil.copy2(template_path, output_path)

        doc = docx.Document(output_path)

        # Build replacement dictionaries:
        # raw_key -> replacement_value AND normalized_field -> replacement_value
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
            # Check cell placeholders
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        cls._replace_placeholders_in_paragraph(p, replacements)

            # Check if this table has table mappings
            for t_map in mapping_report.table_mappings:
                if t_map.template_table_index == t_idx + 1 and t_map.rows_data:
                    cls._populate_table_rows(table, t_map.rows_data)

            # Enforce cantSplit and tblHeader
            TableBuilder.apply_advanced_properties(table)

        # 4. Replace in Headers and Footers
        for section in doc.sections:
            for hp in section.header.paragraphs:
                cls._replace_placeholders_in_paragraph(hp, replacements)
            for fp in section.footer.paragraphs:
                cls._replace_placeholders_in_paragraph(fp, replacements)

        # 5. Non-placeholder insertion fallback
        if not template_profile.placeholders and mapping_report.mappings:
            cls._insert_non_placeholder_content(doc, mapping_report)

        doc.save(output_path)
        logger.info(f"DOCX template populated successfully: {output_path}")
        return output_path

    @classmethod
    def _replace_placeholders_in_paragraph(cls, paragraph: docx.text.paragraph.Paragraph, replacements: Dict[str, str]):
        """
        Replaces placeholders across XML runs preserving character formatting.
        Handles both single-run and multi-run split placeholders.
        """
        p_text = paragraph.text
        if not p_text:
            return

        # Check if any replacement target exists in the paragraph text
        needed_replacements = {k: v for k, v in replacements.items() if k in p_text}
        if not needed_replacements:
            return

        # Attempt simple single-run replacement first
        for key, val in needed_replacements.items():
            for run in paragraph.runs:
                if key in run.text:
                    run.text = run.text.replace(key, val)

        # Re-check paragraph text: if key still present, it spans multiple runs
        p_text = paragraph.text
        for key, val in needed_replacements.items():
            if key in p_text:
                cls._replace_multi_run_placeholder(paragraph, key, val)
                p_text = paragraph.text

    @classmethod
    def _replace_multi_run_placeholder(cls, paragraph: docx.text.paragraph.Paragraph, target: str, replacement: str):
        """
        Consolidates runs when a placeholder is split across multiple runs,
        preserving the font, size, bold, italic, and color of the leading run.
        """
        full_text = "".join(r.text for r in paragraph.runs)
        if target not in full_text:
            return

        start_idx = full_text.find(target)
        end_idx = start_idx + len(target)

        current_pos = 0
        target_runs_indices = []

        for r_idx, run in enumerate(paragraph.runs):
            run_len = len(run.text)
            run_end = current_pos + run_len

            if run_end > start_idx and current_pos < end_idx:
                target_runs_indices.append(r_idx)

            current_pos = run_end

        if not target_runs_indices:
            return

        # First run gets the replaced text segment
        first_r_idx = target_runs_indices[0]
        first_run = paragraph.runs[first_r_idx]

        # Consolidate all targeted runs
        combined_text = "".join(paragraph.runs[i].text for i in target_runs_indices)
        replaced_text = combined_text.replace(target, replacement, 1)

        first_run.text = replaced_text

        # Clear remaining runs in the match
        for r_idx in target_runs_indices[1:]:
            paragraph.runs[r_idx].text = ""

    @classmethod
    def _populate_table_rows(cls, table, rows_data: List[List[str]]):
        """Appends or updates table rows based on extracted table data."""
        if not rows_data:
            return

        num_existing_rows = len(table.rows)
        # Assume row 0 is header; if template only had 1 sample data row, replace it
        start_row_idx = 1 if num_existing_rows > 1 else num_existing_rows
        target_cols = len(table.columns)

        for data_row in rows_data:
            new_row = table.add_row()
            for c_idx in range(min(len(data_row), target_cols)):
                new_row.cells[c_idx].text = str(data_row[c_idx])

    @classmethod
    def _insert_non_placeholder_content(cls, doc: docx.Document, mapping_report: MappingReport):
        """
        When templates do not contain explicit placeholders:
        Inserts verified information blocks into relevant sections preserving typography.
        """
        # Append a clean summary table or section at the end of the document
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        run = p.add_run("Extracted Information Summary")
        run.bold = True
        run.font.size = Pt(12)

        table = doc.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Field"
        table.rows[0].cells[1].text = "Verified Value"
        table.rows[0].cells[0].paragraphs[0].runs[0].bold = True
        table.rows[0].cells[1].paragraphs[0].runs[0].bold = True

        for k, m in mapping_report.mappings.items():
            row = table.add_row()
            row.cells[0].text = k.replace("_", " ").title()
            row.cells[1].text = str(m.mapped_value)

        TableBuilder.apply_advanced_properties(table)
