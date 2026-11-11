"""
Slide-Level Single Slide Regeneration for Engine B.
Allows modifying or regenerating a single slide in-place in < 1.5s
without modifying surrounding slides.
"""
import logging
from typing import Optional
from pptx import Presentation
from pptx.util import Inches

from opengen.domain.presentation import SlideSpec, PresentationThemeSpec
from opengen.engines.presentation.themes import THEMES
from opengen.engines.presentation.builder import PresentationBuilder

logger = logging.getLogger(__name__)

class SlideRegenerator:
    """Modifies a targeted slide in-place inside an existing PPTX presentation."""

    @classmethod
    def regenerate_slide(
        cls,
        pptx_path: str,
        slide_index: int,
        new_slide_spec: SlideSpec,
        theme_name: str = "modern_corporate",
        output_path: Optional[str] = None
    ) -> str:
        out = output_path or pptx_path
        prs = Presentation(pptx_path)

        if slide_index <= 0 or slide_index > len(prs.slides):
            raise ValueError(f"Slide index {slide_index} out of range (1 to {len(prs.slides)}).")

        target_slide = prs.slides[slide_index - 1]
        theme = THEMES.get(theme_name, THEMES["modern_corporate"])

        # Remove all existing shapes on this slide
        sp_ids = [sp.shape_id for sp in target_slide.shapes]
        for sp_id in sp_ids:
            for sp in list(target_slide.shapes):
                if sp.shape_id == sp_id:
                    el = sp.element
                    el.getparent().remove(el)

        # Rebuild slide content in-place
        PresentationBuilder._apply_slide_background(target_slide, theme)
        PresentationBuilder._build_slide_content(target_slide, new_slide_spec, theme)

        prs.save(out)
        logger.info(f"Regenerated slide {slide_index} in {out}")
        return out
