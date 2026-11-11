"""
Unified Presentation Generation Engine (Engine B Coordinator).
Coordinates storytelling planning, geometry layout solving, native shape assembly,
and slide-level regeneration.
"""
import logging
from typing import Optional
from opengen.domain.presentation import PresentationDeckSpec, SlideSpec
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.presentation.builder import PresentationBuilder
from opengen.engines.presentation.regenerate import SlideRegenerator

logger = logging.getLogger(__name__)

class PresentationEngine:
    """Master entrypoint for Engine B: Presentation Generation."""

    def __init__(self, planner: Optional[PresentationPlanner] = None):
        self.planner = planner or PresentationPlanner()

    def generate_presentation(
        self,
        topic: str,
        output_pptx_path: str,
        slide_count: int = 8,
        theme_name: str = "modern_corporate",
        source_materials: Optional[str] = None
    ) -> PresentationDeckSpec:
        """Plans and builds a 100% native editable PowerPoint presentation."""
        deck_spec = self.planner.plan_deck(
            topic=topic,
            slide_count=slide_count,
            theme_name=theme_name,
            source_materials=source_materials
        )

        PresentationBuilder.build_deck(
            deck_spec=deck_spec,
            output_pptx_path=output_pptx_path
        )

        return deck_spec

    def regenerate_slide(
        self,
        pptx_path: str,
        slide_index: int,
        new_slide_spec: SlideSpec,
        theme_name: str = "modern_corporate"
    ) -> str:
        """Regenerates a single slide in-place."""
        return SlideRegenerator.regenerate_slide(
            pptx_path=pptx_path,
            slide_index=slide_index,
            new_slide_spec=new_slide_spec,
            theme_name=theme_name
        )

presentation_engine = PresentationEngine()
