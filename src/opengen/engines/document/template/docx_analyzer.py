"""
Deep DOCX Template Analyzer.
Extracts page geometry, typography, margins, paragraph styles, tables,
headers/footers, embedded images, and placeholders from DOCX templates.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

from opengen.domain.document import (
    TemplateProfile, Margins, FontProfile, TableProfile,
    TableCellProfile, PlaceholderProfile, ImageProfile, SectionProfile
)

# Regex to detect templating placeholders
PLACEHOLDER_REGEX = re.compile(
    r'(\{\{[a-zA-Z0-9_.\s\-]+\}\})|'       # Jinja style: {{name}}
    r'(\<[a-zA-Z0-9_.\s\-]{2,50}\>)|'      # Tag style: <Student Name>
    r'(\[[a-zA-Z0-9_.\s\-]{2,50}\])|'      # Bracket style: [Student Name]
    r'(\{[a-zA-Z0-9_]{3,40}\})'            # Single brace style: {student_name}
)

class DocxAnalyzer:
    """Performs deep structural and styling analysis of a DOCX document."""

    @classmethod
    def analyze(cls, file_path: str, file_hash: str = "") -> TemplateProfile:
        doc = docx.Document(file_path)
        profile = TemplateProfile(
            file_type="docx",
            file_hash=file_hash,
            original_filename=Path(file_path).name
        )

        # 1. Analyze sections (Page geometry, margins, headers, footers)
        cls._analyze_sections(doc, profile)

        # 2. Extract Styles
        cls._analyze_styles(doc, profile)

        # 3. Analyze Body Paragraphs & Headings & Placeholders
        cls._analyze_paragraphs(doc, profile)

        # 4. Analyze Tables
        cls._analyze_tables(doc, profile)

        # 5. Analyze Embedded Images
        cls._analyze_images(doc, profile)

        # 6. Overall structure summary
        profile.structure_summary = (
            f"DOCX Template: {profile.page_size} {profile.orientation}, "
            f"{len(profile.sections)} section(s), {len(profile.tables)} table(s), "
            f"{len(profile.placeholders)} placeholder(s) detected."
        )

        return profile

    @classmethod
    def _analyze_sections(cls, doc: docx.Document, profile: TemplateProfile):
        sections_data: List[SectionProfile] = []
        for i, section in enumerate(doc.sections):
            width_in = section.page_width.inches if section.page_width else 8.27
            height_in = section.page_height.inches if section.page_height else 11.69
            orientation = "landscape" if width_in > height_in else "portrait"

            page_size = "Custom"
            if abs(width_in - 8.27) < 0.2 and abs(height_in - 11.69) < 0.2:
                page_size = "A4"
            elif abs(width_in - 8.5) < 0.2 and abs(height_in - 11.0) < 0.2:
                page_size = "Letter"
            elif abs(width_in - 8.5) < 0.2 and abs(height_in - 14.0) < 0.2:
                page_size = "Legal"

            margins = Margins(
                top=round(section.top_margin.inches, 2) if section.top_margin else 1.0,
                bottom=round(section.bottom_margin.inches, 2) if section.bottom_margin else 1.0,
                left=round(section.left_margin.inches, 2) if section.left_margin else 1.0,
                right=round(section.right_margin.inches, 2) if section.right_margin else 1.0,
            )

            headers_text = [p.text.strip() for p in section.header.paragraphs if p.text.strip()]
            footers_text = [p.text.strip() for p in section.footer.paragraphs if p.text.strip()]
            has_pg = any("PAGE" in p._p.xml for p in section.footer.paragraphs)

            sec_prof = SectionProfile(
                section_index=i,
                page_size=page_size,
                page_width_inches=round(width_in, 2),
                page_height_inches=round(height_in, 2),
                orientation=orientation,
                margins=margins,
                headers=headers_text,
                footers=footers_text,
                has_page_numbers=has_pg
            )
            sections_data.append(sec_prof)

        if sections_data:
            profile.sections = sections_data
            profile.margins = sections_data[0].margins
            profile.page_size = sections_data[0].page_size
            profile.orientation = sections_data[0].orientation
            profile.headers = sections_data[0].headers
            profile.footers = sections_data[0].footers

    @classmethod
    def _analyze_styles(cls, doc: docx.Document, profile: TemplateProfile):
        styles_map: Dict[str, FontProfile] = {}
        for s in doc.styles:
            if s.type == docx.enum.style.WD_STYLE_TYPE.PARAGRAPH and hasattr(s, "font"):
                try:
                    f = s.font
                    fp = FontProfile(
                        name=f.name or "Calibri",
                        size_pt=f.size.pt if f.size else 11.0,
                        bold=f.bold or False,
                        italic=f.italic or False,
                        color_rgb=str(f.color.rgb) if f.color and f.color.rgb else "000000"
                    )
                    styles_map[s.name] = fp
                except Exception:
                    pass
        profile.styles = styles_map

    @classmethod
    def _analyze_paragraphs(cls, doc: docx.Document, profile: TemplateProfile):
        headings = []
        placeholders: List[PlaceholderProfile] = []

        for p_idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if not text:
                continue

            if p.style and p.style.name.startswith("Heading"):
                headings.append({
                    "level": p.style.name,
                    "text": text,
                    "index": p_idx
                })

            for match in PLACEHOLDER_REGEX.finditer(text):
                raw_ph = match.group(0)
                clean_field = re.sub(r'[\{\}\<\>\[\]\s]', '', raw_ph).lower()
                placeholders.append(PlaceholderProfile(
                    raw_key=raw_ph,
                    field_name=clean_field,
                    context=text[:150],
                    location_type="body",
                    paragraph_index=p_idx
                ))

        profile.headings = headings
        profile.placeholders.extend(placeholders)

    @classmethod
    def _analyze_tables(cls, doc: docx.Document, profile: TemplateProfile):
        table_profiles: List[TableProfile] = []

        for t_idx, table in enumerate(doc.tables):
            num_rows = len(table.rows)
            num_cols = len(table.columns) if num_rows > 0 else 0
            if num_rows == 0 or num_cols == 0:
                continue

            widths = []
            for col in table.columns:
                try:
                    widths.append(round(col.width.inches, 2))
                except Exception:
                    widths.append(1.5)

            has_hdr = False
            r0 = table.rows[0]
            if any("tblHeader" in r0._tr.xml for r in table.rows[:1]):
                has_hdr = True
            elif all(any(run.bold for p in cell.paragraphs for run in p.runs) for cell in r0.cells):
                has_hdr = True

            cells_prof: List[TableCellProfile] = []
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    for match in PLACEHOLDER_REGEX.finditer(cell_text):
                        raw_ph = match.group(0)
                        clean_field = re.sub(r'[\{\}\<\>\[\]\s]', '', raw_ph).lower()
                        profile.placeholders.append(PlaceholderProfile(
                            raw_key=raw_ph,
                            field_name=clean_field,
                            context=cell_text[:100],
                            location_type="table_cell",
                            table_index=t_idx + 1,
                            row_index=r_idx,
                            col_index=c_idx
                        ))

                    cells_prof.append(TableCellProfile(
                        row_idx=r_idx,
                        col_idx=c_idx,
                        text=cell_text[:50]
                    ))

            table_profiles.append(TableProfile(
                table_index=t_idx + 1,
                num_rows=num_rows,
                num_cols=num_cols,
                column_widths_inches=widths,
                has_header=has_hdr,
                cells=cells_prof
            ))

        profile.tables = table_profiles

    @classmethod
    def _analyze_images(cls, doc: docx.Document, profile: TemplateProfile):
        images: List[ImageProfile] = []
        img_idx = 0
        try:
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    img_idx += 1
                    images.append(ImageProfile(
                        image_index=img_idx,
                        filename=Path(rel.target_ref).name,
                        is_header_or_logo=(img_idx == 1)
                    ))
        except Exception:
            pass
        profile.images = images
