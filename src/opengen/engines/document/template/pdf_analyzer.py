"""
Deep PDF Template Analyzer.
Extracts page geometry, typography, tables, headings, images/logos,
and placeholders from PDF templates. Uses PyMuPDF.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz

from opengen.domain.document import (
    TemplateProfile, Margins, FontProfile, TableProfile,
    TableCellProfile, PlaceholderProfile, ImageProfile, SectionProfile
)
from opengen.engines.document.template.docx_analyzer import PLACEHOLDER_REGEX

class PdfAnalyzer:
    """Performs deep structural and styling analysis of a PDF template."""

    @classmethod
    def analyze(cls, file_path: str, file_hash: str = "") -> TemplateProfile:
        doc = fitz.open(file_path)
        profile = TemplateProfile(
            file_type="pdf",
            file_hash=file_hash,
            original_filename=Path(file_path).name,
            total_pages_approx=len(doc)
        )

        if len(doc) == 0:
            return profile

        # 1. Analyze Page Dimensions & Margins
        cls._analyze_geometry(doc, profile)

        # 2. Extract Text Blocks, Typography, Headings, and Placeholders
        cls._analyze_content(doc, profile)

        # 3. Extract Tables using PyMuPDF table detection
        cls._analyze_tables(doc, profile)

        # 4. Extract Images & Logos
        cls._analyze_images(doc, profile)

        profile.structure_summary = (
            f"PDF Template: {profile.page_size} {profile.orientation}, "
            f"{len(doc)} page(s), {len(profile.tables)} table(s), "
            f"{len(profile.placeholders)} placeholder(s) detected."
        )

        doc.close()
        return profile

    @classmethod
    def _analyze_geometry(cls, doc: fitz.Document, profile: TemplateProfile):
        sections_data: List[SectionProfile] = []
        for i, page in enumerate(doc):
            rect = page.rect
            width_in = round(rect.width / 72.0, 2)
            height_in = round(rect.height / 72.0, 2)
            orientation = "landscape" if width_in > height_in else "portrait"

            page_size = "Custom"
            if abs(width_in - 8.27) < 0.2 and abs(height_in - 11.69) < 0.2:
                page_size = "A4"
            elif abs(width_in - 8.5) < 0.2 and abs(height_in - 11.0) < 0.2:
                page_size = "Letter"

            # Estimate margins from text blocks bounding box
            blocks = page.get_text("blocks")
            text_blocks = [b for b in blocks if len(b) > 4 and str(b[4]).strip()]
            if text_blocks:
                x0 = min(b[0] for b in text_blocks)
                y0 = min(b[1] for b in text_blocks)
                x1 = max(b[2] for b in text_blocks)
                y1 = max(b[3] for b in text_blocks)
                top_m = round(y0 / 72.0, 2)
                bottom_m = round((rect.height - y1) / 72.0, 2)
                left_m = round(x0 / 72.0, 2)
                right_m = round((rect.width - x1) / 72.0, 2)
                margins = Margins(
                    top=max(0.4, min(top_m, 2.0)),
                    bottom=max(0.4, min(bottom_m, 2.0)),
                    left=max(0.4, min(left_m, 2.0)),
                    right=max(0.4, min(right_m, 2.0))
                )
            else:
                margins = Margins(top=1.0, bottom=1.0, left=1.0, right=1.0)

            sec_prof = SectionProfile(
                section_index=i,
                page_size=page_size,
                page_width_inches=width_in,
                page_height_inches=height_in,
                orientation=orientation,
                margins=margins
            )
            sections_data.append(sec_prof)

        if sections_data:
            profile.sections = sections_data
            profile.margins = sections_data[0].margins
            profile.page_size = sections_data[0].page_size
            profile.orientation = sections_data[0].orientation

    @classmethod
    def _analyze_content(cls, doc: fitz.Document, profile: TemplateProfile):
        headings = []
        placeholders: List[PlaceholderProfile] = []

        for p_idx, page in enumerate(doc):
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])

            for b in blocks:
                if b.get("type") == 0:  # Text Block
                    for line in b.get("lines", []):
                        full_line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()

                        # Placeholder check
                        for match in PLACEHOLDER_REGEX.finditer(full_line_text):
                            raw_ph = match.group(0)
                            clean_field = re.sub(r'[\{\}\<\>\[\]\s]', '', raw_ph).lower()
                            placeholders.append(PlaceholderProfile(
                                raw_key=raw_ph,
                                field_name=clean_field,
                                context=full_line_text[:120],
                                location_type="body",
                                paragraph_index=p_idx
                            ))

                        # Headings check
                        for span in line.get("spans", []):
                            size = span.get("size", 10.0)
                            flags = span.get("flags", 0)
                            font_name = span.get("font", "").lower()
                            span_text = span.get("text", "").strip()

                            if (size >= 13.0 or "bold" in font_name or flags & 2) and len(span_text) > 3:
                                headings.append({
                                    "text": span_text,
                                    "size": size,
                                    "page": p_idx + 1
                                })

        profile.headings = headings
        profile.placeholders.extend(placeholders)

    @classmethod
    def _analyze_tables(cls, doc: fitz.Document, profile: TemplateProfile):
        table_profiles: List[TableProfile] = []
        table_idx = 0

        for p_idx, page in enumerate(doc):
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for tab in tabs.tables:
                        table_idx += 1
                        grid = tab.extract()
                        if grid and len(grid) > 0:
                            num_rows = len(grid)
                            num_cols = len(grid[0])
                            col_widths = []
                            if hasattr(tab, "col_widths") and tab.col_widths:
                                col_widths = [round(w / 72.0, 2) for w in tab.col_widths]
                            else:
                                col_widths = [round(tab.bbox[2] - tab.bbox[0]) / (num_cols * 72.0)] * num_cols

                            table_profiles.append(TableProfile(
                                table_index=table_idx,
                                num_rows=num_rows,
                                num_cols=num_cols,
                                column_widths_inches=col_widths,
                                has_header=True
                            ))
            except Exception:
                pass

        profile.tables = table_profiles

    @classmethod
    def _analyze_images(cls, doc: fitz.Document, profile: TemplateProfile):
        images: List[ImageProfile] = []
        img_idx = 0
        for p_idx, page in enumerate(doc):
            for img in page.get_images():
                img_idx += 1
                images.append(ImageProfile(
                    image_index=img_idx,
                    filename=f"pdf_img_{img_idx}.png",
                    is_header_or_logo=(img_idx == 1 and p_idx == 0)
                ))
        profile.images = images
