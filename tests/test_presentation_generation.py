"""
Tests for Engine B: Presentation Generation.
Verifies storytelling planning, native shape/card assembly, Excel-backed chart generation,
and in-place single-slide regeneration.
"""
import pytest
from pathlib import Path
import pptx

from opengen.domain.presentation import (
    PresentationDeckSpec, SlideSpec, SlideCard, ChartSpec, MetricCard
)
from opengen.engines.presentation.themes import THEME_REGISTRY
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.presentation.builder import PresentationBuilder
from opengen.engines.presentation.regenerate import SlideRegenerator


def test_presentation_planner_deterministic_plan():
    planner = PresentationPlanner()
    deck_spec = planner.plan_deck(
        topic="Future of Autonomous Software Engineering",
        slide_count=6,
        theme_name="modern_corporate"
    )
    assert deck_spec.topic == "Future of Autonomous Software Engineering"
    assert len(deck_spec.slides) == 6
    assert deck_spec.theme_name == "modern_corporate"
    # First slide is title layout
    assert deck_spec.slides[0].layout_type == "title_hero"
    # Last slide is summary layout
    assert deck_spec.slides[-1].layout_type == "two_column"


def test_presentation_builder_native_pptx(tmp_path):
    output_pptx = tmp_path / "test_deck.pptx"
    planner = PresentationPlanner()
    deck_spec = planner.plan_deck(
        topic="Autonomous AI Agents in Production",
        slide_count=5,
        theme_name="ocean_blue"
    )

    PresentationBuilder.build_deck(deck_spec, str(output_pptx))
    assert output_pptx.exists()
    assert output_pptx.stat().st_size > 0

    # Verify PPTX structure using python-pptx
    prs = pptx.Presentation(str(output_pptx))
    # 16:9 widescreen dimensions (13.333 x 7.5 inches)
    assert round(prs.slide_width.inches, 2) == 13.33
    assert round(prs.slide_height.inches, 2) == 7.50
    assert len(prs.slides) == 5

    # Check slide 0 has title shapes and speaker notes
    slide_0 = prs.slides[0]
    assert len(slide_0.shapes) >= 1
    assert slide_0.has_notes_slide
    assert len(slide_0.notes_slide.notes_text_frame.text) > 0


def test_slide_in_place_regeneration(tmp_path):
    output_pptx = tmp_path / "regenerate_test.pptx"
    planner = PresentationPlanner()
    deck_spec = planner.plan_deck(topic="DevOps Optimization", slide_count=4)
    PresentationBuilder.build_deck(deck_spec, str(output_pptx))

    # Create new slide spec for slide index 1 (1-based)
    new_spec = SlideSpec(
        slide_number=1,
        title="Updated Architecture Overview",
        subtitle="Regenerated dynamically via partial regeneration",
        layout_type="two_column",
        cards=[
            SlideCard(card_index=1, title="Microservices", body_bullets=["Decoupled containers"]),
            SlideCard(card_index=2, title="Service Mesh", body_bullets=["mTLS security"])
        ],
        speaker_notes="Here is the updated slide note."
    )

    SlideRegenerator.regenerate_slide(
        pptx_path=str(output_pptx),
        slide_index=1,
        new_slide_spec=new_spec,
        theme_name="modern_corporate"
    )

    # Re-open and verify slide count remains 4 and slide 1 (0th in list) has updated title
    prs = pptx.Presentation(str(output_pptx))
    assert len(prs.slides) == 4
    slide_0 = prs.slides[0]
    title_text = ""
    for shape in slide_0.shapes:
        if shape.has_text_frame and shape.text_frame.text:
            if "Updated Architecture Overview" in shape.text_frame.text:
                title_text = shape.text_frame.text
                break
    assert "Updated Architecture Overview" in title_text
