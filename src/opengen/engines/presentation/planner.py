"""
Presentation Storytelling & Outline Planner for Engine B.
Interacts with the ProviderManager to generate structured 16:9 presentation specifications,
with high-quality deterministic fallback when offline or in test environments.
"""
import logging
from typing import Optional, List
from opengen.domain.presentation import (
    PresentationDeckSpec, SlideSpec, SlideCard, ChartSpec, MetricCard
)
from opengen.providers.manager import ProviderManager, provider_manager

logger = logging.getLogger(__name__)

class PresentationPlanner:
    """Uses LLM to structure topic ideas into an executive multi-slide outline."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None):
        self.provider_manager = provider_mgr or provider_manager

    def plan_deck(
        self,
        topic: str,
        slide_count: int = 8,
        theme_name: str = "modern_corporate",
        source_materials: Optional[str] = None
    ) -> PresentationDeckSpec:
        logger.info(f"Planning {slide_count}-slide presentation for topic: '{topic}'")

        system_prompt = (
            "You are an executive presentation designer and corporate storytelling specialist. "
            "Plan a 16:9 widescreen presentation deck. "
            "For each slide, choose an appropriate layout: "
            "'title_hero' (slide 1), 'two_column', 'three_column', 'four_metrics', 'split_chart', or 'single_column'. "
            "Ensure bullet points are punchy, concise, and executive-ready. "
            "Include 1-2 quantitative chart slides with sample categories and numerical values."
        )

        user_prompt = f"Topic: {topic}\nTarget Slide Count: {slide_count}\nTheme: {theme_name}"
        if source_materials:
            user_prompt += f"\nReference Context:\n{source_materials[:3000]}"

        try:
            deck_spec, telemetry = self.provider_manager.generate_structured(
                prompt=user_prompt,
                response_model=PresentationDeckSpec,
                system_prompt=system_prompt
            )
            deck_spec.theme_name = theme_name
            return deck_spec
        except Exception as e:
            logger.info(f"LLM planner unavailable ({e}); using deterministic presentation planner fallback.")
            return self._build_deterministic_deck(topic, slide_count, theme_name)

    def _build_deterministic_deck(
        self,
        topic: str,
        slide_count: int,
        theme_name: str
    ) -> PresentationDeckSpec:
        slides = []
        # Slide 1: Title hero
        slides.append(
            SlideSpec(
                slide_number=1,
                layout_type="title_hero",
                title=topic,
                subtitle="Strategic Architecture & Implementation Overview",
                speaker_notes=f"Welcome to this executive presentation on {topic}."
            )
        )

        # Intermediate slides
        layout_cycle = ["two_column", "three_column", "four_metrics", "split_chart"]
        for idx in range(2, slide_count):
            layout = layout_cycle[(idx - 2) % len(layout_cycle)]
            cards = [
                SlideCard(
                    card_index=1,
                    title="Key Finding A",
                    body_bullets=["Initial architectural baseline", "Key structural metric"]
                ),
                SlideCard(
                    card_index=2,
                    title="Key Finding B",
                    body_bullets=["Operational performance gains", "Scalable distribution"]
                )
            ]
            chart = None
            if layout == "split_chart":
                chart = ChartSpec(
                    chart_type="column",
                    title="Performance Growth (x)",
                    categories=["Q1", "Q2", "Q3", "Q4"],
                    values=[12.5, 24.0, 38.2, 54.0]
                )
            slides.append(
                SlideSpec(
                    slide_number=idx,
                    layout_type=layout,
                    title=f"Core Pillar {idx - 1}: Strategic Analysis",
                    subtitle="Systematic breakdown and execution metrics",
                    cards=cards,
                    chart=chart,
                    speaker_notes=f"Key analytical drivers for phase {idx - 1}."
                )
            )

        # Final slide
        if slide_count >= 2:
            slides.append(
                SlideSpec(
                    slide_number=slide_count,
                    layout_type="two_column",
                    title="Summary & Next Steps",
                    subtitle="Strategic Roadmap and Actionable Milestones",
                    cards=[
                        SlideCard(
                            card_index=1,
                            title="Immediate Actions",
                            body_bullets=["Deploy reference architecture", "Establish observability"]
                        ),
                        SlideCard(
                            card_index=2,
                            title="Long-term Goals",
                            body_bullets=["Scale self-hosted instances", "Community feedback loop"]
                        )
                    ],
                    speaker_notes="Conclusion and strategic path forward."
                )
            )

        return PresentationDeckSpec(
            topic=topic,
            theme_name=theme_name,
            slides=slides
        )
