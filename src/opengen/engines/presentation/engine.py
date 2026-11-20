"""
Unified Presentation Generation Engine (Engine B Coordinator).
Coordinates storytelling planning, geometry layout solving, native shape assembly,
and slide-level regeneration.
"""
import logging
from typing import Optional, Tuple
from pathlib import Path
from opengen.domain.presentation import PresentationDeckSpec, SlideSpec
from opengen.domain.brand import BrandKitSpec
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.presentation.builder import PresentationBuilder
from opengen.engines.presentation.regenerate import SlideRegenerator
from opengen.engines.presentation.bento_compiler import BentoSlideCompiler
from opengen.engines.presentation.marp_compiler import MarpSlideCompiler

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

    def generate_bento_presentation(
        self,
        topic: str,
        output_pptx_path: str,
        output_html_path: Optional[str] = None,
        slide_count: int = 7,
        theme_name: str = "modern_corporate",
        brand: Optional[BrandKitSpec] = None,
        source_materials: Optional[str] = None
    ) -> Tuple[PresentationDeckSpec, str, str]:
        """
        Plans and compiles an elite Bento Grid presentation following Sequoia/YC narrative arcs.
        Produces both native editable PPTX and responsive fluid HTML5 presentation.
        """
        deck_spec = self.planner.plan_deck(
            topic=topic,
            slide_count=slide_count,
            theme_name=brand.brandId if brand else theme_name,
            source_materials=source_materials,
            use_bento=True
        )

        # 1. Build Native PowerPoint
        PresentationBuilder.build_deck(
            deck_spec=deck_spec,
            output_pptx_path=output_pptx_path
        )

        # 2. Build Gamma-style Bento HTML
        html_path = output_html_path or str(Path(output_pptx_path).with_suffix(".html"))
        BentoSlideCompiler.compile_deck_to_html_file(
            deck=deck_spec,
            output_html_path=html_path,
            brand=brand
        )

        return deck_spec, output_pptx_path, html_path

    def compile_marp_presentation(
        self,
        topic: str,
        output_md_path: str,
        slide_count: int = 7,
        brand: Optional[BrandKitSpec] = None,
        source_materials: Optional[str] = None
    ) -> Tuple[PresentationDeckSpec, str]:
        """Plans and compiles a standard Marp/Slidev Markdown presentation."""
        deck_spec = self.planner.plan_deck(
            topic=topic,
            slide_count=slide_count,
            theme_name=brand.brandId if brand else "modern_corporate",
            source_materials=source_materials,
            use_bento=True
        )
        MarpSlideCompiler.compile_deck_to_markdown(
            deck=deck_spec,
            output_md_path=output_md_path,
            brand=brand
        )
        return deck_spec, output_md_path

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
