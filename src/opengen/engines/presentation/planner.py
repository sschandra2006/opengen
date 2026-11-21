"""
Presentation Storytelling & Outline Planner for Engine B.
Interacts with the ProviderManager to generate structured 16:9 presentation specifications,
with high-quality deterministic fallback when offline or in test environments.
"""
import logging
from typing import Optional, List
from opengen.domain.presentation import (
    PresentationDeckSpec, SlideSpec, SlideCard, ChartSpec, MetricCard,
    BentoCardSpec, SemanticComponentType
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
        source_materials: Optional[str] = None,
        use_bento: bool = False,
        subgraph_context: Optional[str] = None
    ) -> PresentationDeckSpec:
        logger.info(f"Planning {slide_count}-slide presentation for topic: '{topic}' (bento={use_bento})")

        if use_bento:
            system_prompt = (
                "You are an executive presentation designer following the Gamma.app and Sequoia Capital pitch narrative arcs. "
                "Plan a 16:9 widescreen presentation deck using fluid Bento Grids and Semantic Visual Components. "
                "STRICT DESIGN RULE: NEVER output raw bullet points. "
                "Map facts to: 'stat_card_grid' (metrics & giant KPIs), 'roadmap_timeline' (process & numbered milestones), "
                "'bento_box_grid' (asymmetric hero + secondary cards), or 'comparison_matrix' (Old Way vs New Way). "
                "Follow the persuasion arc: Hook, The Urgent Problem, The Inevitable Solution, Product in Action, Moat, Traction, The Ask."
            )
        else:
            system_prompt = (
                "You are an executive presentation designer and corporate storytelling specialist. "
                "Plan a 16:9 widescreen presentation deck. "
                "For each slide, choose an appropriate layout: "
                "'title_hero' (slide 1), 'two_column', 'three_column', 'four_metrics', 'split_chart', or 'single_column'. "
                "STRICT DESIGN RULE: Avoid lazy bullet lists. Structure takeaways into distinct concise semantic cards. "
                "Include 1-2 quantitative chart slides with sample categories and numerical values."
            )

        user_prompt = f"Topic: {topic}\nTarget Slide Count: {slide_count}\nTheme: {theme_name}"
        if subgraph_context:
            user_prompt += f"\nTargeted Knowledge Graph Context:\n{subgraph_context}"
        elif source_materials:
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
            if use_bento:
                return self._build_deterministic_bento_deck(topic, slide_count, theme_name)
            return self._build_deterministic_deck(topic, slide_count, theme_name)

    def _build_deterministic_bento_deck(
        self,
        topic: str,
        slide_count: int,
        theme_name: str
    ) -> PresentationDeckSpec:
        """Constructs an elite 7-stage Sequoia/YC narrative pitch deck with Bento components."""
        slides = []
        # Stage 1: The Hook / Cover
        slides.append(
            SlideSpec(
                slide_number=1,
                narrative_stage="hook",
                layout_type="title_hero",
                title=topic,
                subtitle="Next-Generation Enterprise Architecture & Exponential Scale",
                bento_cards=[
                    BentoCardSpec(title="Core Thesis", description="Autonomous creative intelligence replacing sterile AI templates.", col_span=12)
                ],
                speaker_notes=f"Welcome to the strategic unveiling of {topic}."
            )
        )

        # Stage 2: The Urgent Problem (Villain)
        if slide_count >= 2:
            slides.append(
                SlideSpec(
                    slide_number=2,
                    narrative_stage="pain",
                    layout_type="comparison_matrix",
                    title="The Legacy Friction",
                    subtitle="Current AI generators create plastic, low-value artifacts with zero brand cohesion.",
                    bento_cards=[
                        BentoCardSpec(title="The Naive Approach", description="Rigid bullet points, uncalibrated lighting, and broken document margins.", col_span=6, accent_color="#f43f5e"),
                        BentoCardSpec(title="The Strategic Cost", description="Loss of executive credibility, 80% manual rework, and brand dilution.", col_span=6, accent_color="#fb923c")
                    ]
                )
            )

        # Stage 3: The Inevitable Solution (Secret Weapon)
        if slide_count >= 3:
            slides.append(
                SlideSpec(
                    slide_number=3,
                    narrative_stage="solution",
                    layout_type="bento_grid",
                    title="The OpenGen Breakthrough",
                    subtitle="Creative Intelligence: Optical physics, Swiss editorial typography, and fluid Bento grids.",
                    bento_cards=[
                        BentoCardSpec(title="Algorithmic Auto-Layout", value="10x", description="Dynamic 12-column responsive layout engine guarantees zero text overflow.", col_span=8, trend_badge="+85% faster"),
                        BentoCardSpec(title="Studio Optics", value="100%", description="Dual-pass contact shadow & studio relighting.", col_span=4)
                    ]
                )
            )

        # Stage 4: Product in Action (Roadmap Timeline)
        if slide_count >= 4:
            slides.append(
                SlideSpec(
                    slide_number=4,
                    narrative_stage="product",
                    layout_type="roadmap_timeline",
                    title="Unified Multi-Studio Pipeline",
                    subtitle="End-to-end deterministic execution from brief to publication-grade artifact.",
                    bento_cards=[
                        BentoCardSpec(title="1. Brand DNA Ingestion", description="Shared 60-30-10 palette, geometry, and asset tokens.", col_span=4),
                        BentoCardSpec(title="2. Dynamic Compilation", description="Typst 20ms compile & native 16:9 widescreen PPTX shapes.", col_span=4),
                        BentoCardSpec(title="3. Physical Validation", description="PyMuPDF boundary inspection & contact shadow synthesis.", col_span=4)
                    ]
                )
            )

        # Stage 5: Unfair Advantage & Moat
        if slide_count >= 5:
            slides.append(
                SlideSpec(
                    slide_number=5,
                    narrative_stage="moat",
                    layout_type="comparison_matrix",
                    title="Defensible Technological Moat",
                    subtitle="Why proprietary constraint-based layout outpaces generic web-to-image exporters.",
                    bento_cards=[
                        BentoCardSpec(title="100% Native Editability", description="Every shape, card, and table remains fully editable in PowerPoint & Keynote.", col_span=6),
                        BentoCardSpec(title="Sub-50ms Typst Pipeline", description="Zero LibreOffice bloat. Standalone high-speed publication typesetting.", col_span=6)
                    ]
                )
            )

        # Stage 6: Traction Proof (Giant Stat Cards)
        if slide_count >= 6:
            slides.append(
                SlideSpec(
                    slide_number=6,
                    narrative_stage="traction",
                    layout_type="stat_card_grid",
                    title="Exponential Traction Proof",
                    subtitle="Rapid customer adoption and industry-leading performance benchmarks.",
                    bento_cards=[
                        BentoCardSpec(title="ARR Run-Rate", value="$14.2M", description="Annual recurring revenue across enterprise tiers.", trend_badge="▲ +112% YoY", col_span=4, accent_color="#38bdf8"),
                        BentoCardSpec(title="Net Retention", value="138%", description="Expansion across Fortune 500 design studios.", trend_badge="Top Decile SaaS", col_span=4, accent_color="#10b981"),
                        BentoCardSpec(title="Gross Margin", value="84.5%", description="Efficient 0-token deterministic local processing.", trend_badge="Benchmark: 72%", col_span=4, accent_color="#6366f1")
                    ]
                )
            )

        # Stage 7: The Ask / Next Horizon
        if slide_count >= 7:
            slides.append(
                SlideSpec(
                    slide_number=7,
                    narrative_stage="ask",
                    layout_type="bento_grid",
                    title="Capital Allocation & Milestones",
                    subtitle="Targeting global market leadership in autonomous creative intelligence.",
                    bento_cards=[
                        BentoCardSpec(title="Global Edge Nodes", description="Deploying sub-10ms inference and rendering edge points.", col_span=4),
                        BentoCardSpec(title="Enterprise SDK Expansion", description="Native bindings for Python, TypeScript, and MCP.", col_span=4),
                        BentoCardSpec(title="Next Round Target", value="$25M", description="Series A expansion capital.", col_span=4, accent_color="#38bdf8")
                    ]
                )
            )

        return PresentationDeckSpec(
            topic=topic,
            theme_name=theme_name,
            slides=slides
        )

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
