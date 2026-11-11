"""
Deep DOCX Analyzer.
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

from app.models.template_profile import (
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
            # Dimensions
            width_in = section.page_width.inches if section.page_width else 8.27
            height_in = section.page_height.inches if section.page_height else 11.69
            orientation = "landscape" if width_in > height_in else "portrait"
            
            # Determine standard page name
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

            # Headers and Footers
            headers_text = [p.text.strip() for p in section.header.paragraphs if p.text.strip()]
            footers_text = [p.text.strip() for p in section.footer.paragraphs if p.text.strip()]

            # Page numbers in footer
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
            first_sec = sections_data[0]
            profile.page_size = first_sec.page_size
            profile.orientation = first_sec.orientation
            profile.margins = first_sec.margins
            profile.headers = first_sec.headers
            profile.footers = first_sec.footers

    @classmethod
    def _analyze_styles(cls, doc: docx.Document, profile: TemplateProfile):
        styles_map: Dict[str, FontProfile] = {}
        for s in doc.styles:
            if s.type == docx.enum.style.WD_STYLE_TYPE.PARAGRAPH:
                font = s.font
                fp = FontProfile(
                    name=font.name or "Calibri",
                    size_pt=font.size.pt if font.size else 11.0,
                    bold=font.bold if font.bold is not None else False,
                    italic=font.italic if font.italic is not None else False,
                    color_rgb=str(font.color.rgb) if (font.color and font.color.rgb) else "000000"
                )
                styles_map[s.name] = fp
        profile.styles = styles_map

    @classmethod
    def _analyze_paragraphs(cls, doc: docx.Document, profile: TemplateProfile):
        for p_idx, p in enumerate(doc.paragraphs):
            text = p.text
            if not text:
                continue

            # Heading detection
            style_name = p.style.name.lower() if p.style else ""
            if "heading" in style_name or "title" in style_name:
                profile.headings.append({
                    "text": text.strip(),
                    "style": p.style.name,
                    "paragraph_index": p_idx
                })

            # Check for placeholders
            cls._find_placeholders_in_text(text, profile, location_type="body", paragraph_index=p_idx, paragraph=p)

    @classmethod
    def _find_placeholders_in_text(cls, text: str, profile: TemplateProfile,
                                  location_type: str, paragraph_index: Optional[int] = None,
                                  paragraph: Optional[docx.text.paragraph.Paragraph] = None,
                                  table_index: Optional[int] = None,
                                  row_index: Optional[int] = None, col_index: Optional[int] = None):
        matches = PLACEHOLDER_REGEX.findall(text)
        for match_tuple in matches:
            raw_match = next((m for m in match_tuple if m), "")
            if not raw_match:
                continue
            
            # Clean raw match to get normalized field_name
            cleaned = raw_match.strip("{<[]}> ").strip()
            # Normalize whitespace/special chars to snake_case
            field_name = re.sub(r'[\s\-]+', '_', cleaned).lower()

            # Attempt to extract run font profile
            font_prof = None
            if paragraph and paragraph.runs:
                first_run = paragraph.runs[0]
                font_prof = FontProfile(
                    name=first_run.font.name or "Calibri",
                    size_pt=first_run.font.size.pt if first_run.font.size else 11.0,
                    bold=first_run.font.bold or False,
                    italic=first_run.font.italic or False,
                    color_rgb=str(first_run.font.color.rgb) if (first_run.font.color and first_run.font.color.rgb) else "000000"
                )

            # Avoid duplicates if exactly the same raw key already recorded in this location
            existing = any(
                p.raw_key == raw_match and p.paragraph_index == paragraph_index and p.table_index == table_index
                for p in profile.placeholders
            )
            if not existing:
                profile.placeholders.append(
                    PlaceholderProfile(
                        raw_key=raw_match,
                        field_name=field_name,
                        context=text[:150],
                        location_type=location_type,
                        paragraph_index=paragraph_index,
                        table_index=table_index,
                        row_index=row_index,
                        col_index=col_index,
                        run_font=font_prof
                    )
                )

    @classmethod
    def _analyze_tables(cls, doc: docx.Document, profile: TemplateProfile):
        for t_idx, table in enumerate(doc.tables):
            num_rows = len(table.rows)
            num_cols = len(table.columns) if num_rows > 0 else 0
            
            # Extract column widths
            col_widths = []
            if num_rows > 0 and len(table.rows[0].cells) > 0:
                for c in table.rows[0].cells:
                    col_widths.append(round(c.width.inches, 2) if c.width else 1.5)

            cells_profile: List[TableCellProfile] = []
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    
                    # Search placeholders in table cells
                    cls._find_placeholders_in_text(
                        cell_text, profile, location_type="table_cell",
                        table_index=t_idx, row_index=r_idx, col_index=c_idx
                    )

                    cells_profile.append(TableCellProfile(
                        row_idx=r_idx,
                        col_idx=c_idx,
                        text=cell_text,
                        width_inches=round(cell.width.inches, 2) if cell.width else None
                    ))

            # Detect repeated header
            repeat_header = False
            if num_rows > 0:
                trPr = table.rows[0]._tr.get_or_add_trPr()
                repeat_header = trPr.find(qn('w:tblHeader')) is not None

            table_prof = TableProfile(
                table_index=t_idx,
                num_rows=num_rows,
                num_cols=num_cols,
                column_widths_inches=col_widths,
                has_header=(num_rows > 1),
                repeat_header=repeat_header,
                cells=cells_profile
            )
            profile.tables.append(table_prof)

    @classmethod
    def _analyze_images(cls, doc: docx.Document, profile: TemplateProfile):
        # Scan inline drawings
        img_idx = 0
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                img_idx += 1
                profile.images.append(ImageProfile(
                    image_index=img_idx,
                    filename=Path(rel.target_ref).name,
                    is_header_or_logo=(img_idx == 1), # Likely first image is logo
                    location="header_or_body"
                ))
