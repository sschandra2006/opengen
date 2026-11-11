"""
Deep PDF Analyzer.
Extracts page geometry, typography, tables, headings, images/logos,
and placeholders from PDF templates. Uses PyMuPDF with Docling/OCR fallbacks.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF

from app.models.template_profile import (
    TemplateProfile, Margins, FontProfile, TableProfile,
    TableCellProfile, PlaceholderProfile, ImageProfile, SectionProfile
)
from app.modules.template_intelligence.docx_analyzer import PLACEHOLDER_REGEX

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
            first_sec = sections_data[0]
            profile.page_size = first_sec.page_size
            profile.orientation = first_sec.orientation
            profile.margins = first_sec.margins

    @classmethod
    def _analyze_content(cls, doc: fitz.Document, profile: TemplateProfile):
        font_sizes = []
        for p_idx, page in enumerate(doc):
            text_page = page.get_text("dict")
            blocks = text_page.get("blocks", [])

            for b_idx, block in enumerate(blocks):
                if block.get("type") == 0:  # Text block
                    block_text_list = []
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            line_text += span_text
                            size = span.get("size", 11.0)
                            font_sizes.append(size)
                            font_name = span.get("font", "Calibri")
                            flags = span.get("flags", 0)
                            color_val = span.get("color", 0)
                            color_hex = f"{color_val:06x}" if isinstance(color_val, int) else "000000"

                            # Record style
                            if font_name not in profile.styles:
                                profile.styles[font_name] = FontProfile(
                                    name=font_name,
                                    size_pt=round(size, 1),
                                    bold=bool(flags & 2 or "bold" in font_name.lower()),
                                    italic=bool(flags & 1 or "italic" in font_name.lower()),
                                    color_rgb=color_hex
                                )

                        block_text_list.append(line_text)

                    full_block_text = " ".join(block_text_list).strip()
                    if not full_block_text:
                        continue

                    # Check for Headings: larger font or bold
                    first_span = None
                    if block.get("lines") and block["lines"][0].get("spans"):
                        first_span = block["lines"][0]["spans"][0]

                    if first_span and (first_span.get("size", 11) >= 13.0 or "bold" in first_span.get("font", "").lower()):
                        profile.headings.append({
                            "text": full_block_text[:100],
                            "page": p_idx + 1,
                            "size_pt": first_span.get("size", 11),
                            "font": first_span.get("font", "Calibri")
                        })

                    # Search placeholders in block text
                    cls._find_placeholders(full_block_text, profile, page_num=p_idx + 1)

    @classmethod
    def _find_placeholders(cls, text: str, profile: TemplateProfile, page_num: int):
        matches = PLACEHOLDER_REGEX.findall(text)
        for match_tuple in matches:
            raw_match = next((m for m in match_tuple if m), "")
            if not raw_match:
                continue

            cleaned = raw_match.strip("{<[]}> ").strip()
            field_name = re.sub(r'[\s\-]+', '_', cleaned).lower()

            existing = any(
                p.raw_key == raw_match and p.field_name == field_name
                for p in profile.placeholders
            )
            if not existing:
                profile.placeholders.append(
                    PlaceholderProfile(
                        raw_key=raw_match,
                        field_name=field_name,
                        context=text[:150],
                        location_type="pdf_page",
                        paragraph_index=page_num
                    )
                )

    @classmethod
    def _analyze_tables(cls, doc: fitz.Document, profile: TemplateProfile):
        t_global_idx = 0
        for p_idx, page in enumerate(doc):
            try:
                tables = page.find_tables()
                if not tables or not tables.tables:
                    continue

                for tab in tables.tables:
                    t_global_idx += 1
                    extracted = tab.extract()
                    if not extracted:
                        continue

                    num_rows = len(extracted)
                    num_cols = len(extracted[0]) if num_rows > 0 else 0
                    cells: List[TableCellProfile] = []

                    for r_idx, row in enumerate(extracted):
                        for c_idx, val in enumerate(row):
                            cell_text = (val or "").strip()
                            cells.append(TableCellProfile(
                                row_idx=r_idx,
                                col_idx=c_idx,
                                text=cell_text
                            ))
                            # Check placeholders in cell
                            cls._find_placeholders(cell_text, profile, page_num=p_idx + 1)

                    profile.tables.append(TableProfile(
                        table_index=t_global_idx,
                        num_rows=num_rows,
                        num_cols=num_cols,
                        has_header=num_rows > 1,
                        cells=cells
                    ))
            except Exception:
                pass

    @classmethod
    def _analyze_images(cls, doc: fitz.Document, profile: TemplateProfile):
        img_idx = 0
        for p_idx, page in enumerate(doc):
            image_list = page.get_images(full=True)
            for img in image_list:
                img_idx += 1
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_ext = base_image.get("ext", "png")
                w = base_image.get("width", 100)
                h = base_image.get("height", 100)

                profile.images.append(ImageProfile(
                    image_index=img_idx,
                    filename=f"image_{img_idx}.{image_ext}",
                    width_inches=round(w / 150.0, 2),
                    height_inches=round(h / 150.0, 2),
                    is_header_or_logo=(img_idx == 1 and p_idx == 0) # Top image on first page is likely logo
                ))
