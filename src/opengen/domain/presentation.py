"""
Domain models for presentation generation (Engine B).
Represents deck outlines, slides, cards, native Excel-backed charts, and themes.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

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
        "split_chart"
    ] = "three_column"
    title: str
    subtitle: Optional[str] = None
    cards: List[SlideCard] = Field(default_factory=list)
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
