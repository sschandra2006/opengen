"""
Domain models for presentation generation (Engine B).
Represents deck outlines, slides, cards, native Excel-backed charts, and themes.
"""
from typing import List, Optional, Literal, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class SemanticComponentType(str, Enum):
    STAT_CARD_GRID = "stat_card_grid"
    ROADMAP_TIMELINE = "roadmap_timeline"
    BENTO_BOX_GRID = "bento_box_grid"
    COMPARISON_MATRIX = "comparison_matrix"
    QUADRANT_MATRIX_2X2 = "quadrant_matrix_2x2"
    EDITORIAL_TESTIMONIAL = "editorial_testimonial"

class BentoCardSpec(BaseModel):
    title: str
    value: Optional[str] = None
    description: str = ""
    trend_badge: Optional[str] = None
    col_span: int = Field(default=4, description="Spans 3, 4, 6, 8, or 12 in a 12-column grid")
    accent_color: Optional[str] = None
    icon_name: Optional[str] = None

class MetricCard(BaseModel):
    label: str
    value: str
    change_indicator: Optional[str] = None

class ChartSpec(BaseModel):
    chart_type: Literal["bar", "column", "line", "pie"] = "column"
    title: str
    categories: List[str] = Field(default_factory=list)
    series_name: str = "Series 1"
    values: List[float] = Field(default_factory=list)

class SlideCard(BaseModel):
    card_index: int = 1
    title: Optional[str] = None
    body_bullets: List[str] = Field(default_factory=list)
    icon_name: Optional[str] = None
    metric: Optional[MetricCard] = None

class SlideSpec(BaseModel):
    slide_number: int
    layout_type: Literal[
        "title_hero",
        "section_header",
        "single_column",
        "two_column",
        "three_column",
        "four_metrics",
        "split_chart",
        "bento_grid",
        "stat_card_grid",
        "roadmap_timeline",
        "comparison_matrix",
        "quadrant_matrix_2x2",
        "editorial_testimonial"
    ] = "three_column"
    title: str
    subtitle: Optional[str] = None
    cards: List[SlideCard] = Field(default_factory=list)
    bento_cards: List[BentoCardSpec] = Field(default_factory=list)
    narrative_stage: Optional[str] = None  # "hook", "pain", "solution", "product", "moat", "traction", "ask"
    chart: Optional[ChartSpec] = None
    speaker_notes: Optional[str] = None

class PresentationThemeSpec(BaseModel):
    name: str = "modern_corporate"
    primary_color: str = "#0F172A"       # Dark slate
    accent_color: str = "#2563EB"        # Blue
    background_color: str = "#FFFFFF"    # Crisp White
    card_background: str = "#F8FAFC"     # Soft light grey
    text_color: str = "#1E293B"          # Dark grey
    font_header: str = "Calibri"
    font_body: str = "Calibri"

class PresentationDeckSpec(BaseModel):
    topic: str
    theme_name: str = "modern_corporate"
    aspect_ratio: str = "16:9"
    slides: List[SlideSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

