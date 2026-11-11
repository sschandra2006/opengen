"""
Native Microsoft PowerPoint (.pptx) Builder for Engine B.
Constructs genuine PowerPoint shapes, text boxes, and cards based on solved geometry.
Guarantees 100% native editability (no image flattening).
"""
import logging
from typing import Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from opengen.domain.presentation import (
    PresentationDeckSpec, SlideSpec, PresentationThemeSpec
)
from opengen.engines.presentation.themes import THEMES
from opengen.engines.presentation.layout_solver import CoordinateLayoutSolver
from opengen.engines.presentation.charts import NativeChartBuilder

logger = logging.getLogger(__name__)

def _hex_to_rgb(hex_str: str) -> RGBColor:
    hex_clean = hex_str.lstrip('#')
    return RGBColor(*(int(hex_clean[i:i+2], 16) for i in (0, 2, 4)))

class PresentationBuilder:
    """Builds native widescreen 16:9 PowerPoint presentations."""

    @classmethod
    def build_deck(
        cls,
        deck_spec: PresentationDeckSpec,
        output_pptx_path: str,
        template_pptx_path: Optional[str] = None
    ) -> str:
        prs = Presentation(template_pptx_path) if template_pptx_path else Presentation()

        # Enforce 16:9 Widescreen dimensions
        prs.slide_width = Inches(CoordinateLayoutSolver.SLIDE_WIDTH_IN)
        prs.slide_height = Inches(CoordinateLayoutSolver.SLIDE_HEIGHT_IN)

        theme = THEMES.get(deck_spec.theme_name, THEMES["modern_corporate"])
        blank_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]

        for slide_spec in deck_spec.slides:
            slide = prs.slides.add_slide(blank_layout)
            cls._apply_slide_background(slide, theme)
            cls._build_slide_content(slide, slide_spec, theme)

            # Speaker Notes
            if slide_spec.speaker_notes:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = slide_spec.speaker_notes

        prs.save(output_pptx_path)
        logger.info(f"Native editable presentation saved to: {output_pptx_path}")
        return output_pptx_path

    @classmethod
    def _apply_slide_background(cls, slide, theme: PresentationThemeSpec):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = _hex_to_rgb(theme.background_color)

    @classmethod
    def _build_slide_content(cls, slide, spec: SlideSpec, theme: PresentationThemeSpec):
        title_geo = CoordinateLayoutSolver.get_title_geometry()

        # 1. Slide Title & Subtitle
        title_box = slide.shapes.add_textbox(
            Inches(title_geo.x_in), Inches(title_geo.y_in),
            Inches(title_geo.w_in), Inches(title_geo.h_in)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = spec.title
        p_title.font.size = Pt(title_geo.recommended_font_pt)
        p_title.font.bold = True
        p_title.font.name = theme.font_header
        p_title.font.color.rgb = _hex_to_rgb(theme.primary_color)

        if spec.subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = spec.subtitle
            p_sub.font.size = Pt(14)
            p_sub.font.name = theme.font_body
            p_sub.font.color.rgb = _hex_to_rgb(theme.text_color)

        # 2. Body Cards Geometry
        card_texts = ["\n".join(c.body_bullets) for c in spec.cards]
        geometries = CoordinateLayoutSolver.solve_cards_geometry(
            spec.layout_type, len(spec.cards), card_texts
        )

        for idx, card in enumerate(spec.cards):
            if idx >= len(geometries):
                break
            geo = geometries[idx]

            # Native Rounded Rectangle Card Shape
            shape = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(geo.x_in), Inches(geo.y_in),
                Inches(geo.w_in), Inches(geo.h_in)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = _hex_to_rgb(theme.card_background)
            shape.line.color.rgb = _hex_to_rgb("#CBD5E1")
            shape.line.width = Pt(1)

            ctf = shape.text_frame
            ctf.word_wrap = True
            ctf.margin_top = Inches(0.2)
            ctf.margin_left = Inches(0.2)
            ctf.margin_right = Inches(0.2)
            ctf.margin_bottom = Inches(0.2)

            # Card Title
            if card.title:
                cp = ctf.paragraphs[0]
                cp.text = card.title
                cp.font.size = Pt(geo.recommended_font_pt + 2)
                cp.font.bold = True
                cp.font.name = theme.font_header
                cp.font.color.rgb = _hex_to_rgb(theme.accent_color)

            # Metric Display
            if card.metric:
                mp = ctf.add_paragraph() if card.title else ctf.paragraphs[0]
                mp.text = card.metric.value
                mp.font.size = Pt(36)
                mp.font.bold = True
                mp.font.color.rgb = _hex_to_rgb(theme.accent_color)

                lp = ctf.add_paragraph()
                lp.text = card.metric.label
                lp.font.size = Pt(13)
                lp.font.color.rgb = _hex_to_rgb(theme.text_color)

            # Body Bullets
            for b_idx, bullet in enumerate(card.body_bullets):
                bp = ctf.add_paragraph() if (card.title or card.metric or b_idx > 0) else ctf.paragraphs[0]
                bp.text = f"•  {bullet}"
                bp.font.size = Pt(geo.recommended_font_pt)
                bp.font.name = theme.font_body
                bp.font.color.rgb = _hex_to_rgb(theme.text_color)

        # 3. Native Chart
        if spec.chart:
            # Chart coordinates on right side for split_chart or bottom
            chart_geo = geometries[-1] if spec.layout_type == "split_chart" and len(geometries) > 1 else None
            x = chart_geo.x_in if chart_geo else 6.0
            y = chart_geo.y_in if chart_geo else 2.1
            w = chart_geo.w_in if chart_geo else 6.5
            h = chart_geo.h_in if chart_geo else 4.5

            NativeChartBuilder.add_chart(
                slide=slide,
                chart_spec=spec.chart,
                x_in=x, y_in=y, w_in=w, h_in=h,
                theme=theme
            )
