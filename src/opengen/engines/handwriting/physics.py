"""
Pen Physics & Ink Dynamics Simulator for Engine D.
Simulates ink velocity, downstroke pressure dynamics, and realistic ink opacity.
"""
import random
from typing import Tuple

PEN_PALETTES = {
    "ballpoint_blue": (28, 59, 114),    # Hex #1C3B72
    "ballpoint_black": (26, 30, 36),    # Deep dark slate black
    "gel_pen_black": (15, 23, 42),      # Crisp saturated gel black
    "pencil": (58, 58, 58)              # Graphite grey
}

class PenPhysicsSimulator:
    """Calculates dynamic ink color and opacity based on simulated pen pressure."""

    @classmethod
    def get_ink_color(cls, pen_type: str = "ballpoint_blue", is_downstroke: bool = False) -> Tuple[int, int, int, int]:
        base_rgb = PEN_PALETTES.get(pen_type, PEN_PALETTES["ballpoint_blue"])

        if pen_type == "ballpoint_blue":
            # Heavier pressure and darker opacity on vertical downstrokes
            if is_downstroke:
                alpha = random.randint(245, 255)
            else:
                alpha = random.randint(210, 240)
            return (*base_rgb, alpha)

        elif pen_type == "pencil":
            # Graphite has lower saturation and softer opacity
            alpha = random.randint(180, 220)
            return (*base_rgb, alpha)

        else:
            # Gel pen
            alpha = random.randint(240, 255)
            return (*base_rgb, alpha)
