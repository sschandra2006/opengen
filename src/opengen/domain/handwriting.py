"""
Domain models for realistic handwriting synthesis (Engine D).
"""
from typing import Optional, Tuple, Literal
from pathlib import Path
from pydantic import BaseModel, Field

class RuledPaperSpecs(BaseModel):
    name: str = "college_ruled"
    line_pitch_mm: float = 7.1      # 7.1 mm for standard College Ruled notebook paper
    left_margin_mm: float = 31.75   # 1.25 inches
    top_margin_mm: float = 25.4     # 1.0 inch
    dpi: int = 300

    @property
    def line_pitch_px(self) -> int:
        return int((self.line_pitch_mm / 25.4) * self.dpi)

    @property
    def left_margin_px(self) -> int:
        return int((self.left_margin_mm / 25.4) * self.dpi)

class HandwritingProfile(BaseModel):
    pen_type: Literal["ballpoint_blue", "ballpoint_black", "gel_pen_black", "pencil"] = "ballpoint_blue"
    pen_color: Tuple[int, int, int] = (28, 59, 114)   # Blue ink hex #1C3B72
    baseline_jitter_px: float = 1.8
    char_spacing_noise_px: float = 1.2
    line_slant_deg: float = 0.8
    transparent_mode: bool = True     # True for printing ink directly onto real physical lined paper
    inject_mistakes: bool = False
