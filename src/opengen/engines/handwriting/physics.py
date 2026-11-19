"""
Pen Physics & Ink Dynamics Simulator for Engine D.
Simulates ink velocity, downstroke pressure dynamics, and realistic ink opacity.
"""
import random
from typing import Optional, Tuple

PEN_PALETTES = {
    "ballpoint_blue": (28, 59, 114),    # Hex #1C3B72
    "ballpoint_black": (26, 30, 36),    # Deep dark slate black
    "gel_pen_black": (10, 14, 23),      # Crisp saturated gel black
    "fountain_pen": (26, 54, 93),       # Deep capillary ink blue #1A365D
    "pencil": (58, 58, 58)              # Graphite grey #3A3A3A
}


class PenPhysicsSimulator:
    """Calculates dynamic ink color, velocity-to-thickness dynamics, and ink pooling."""

    @classmethod
    def calculate_stroke_thickness(
        cls,
        velocity: float = 1.0,
        curvature: float = 0.0,
        pen_type: str = "ballpoint_blue",
        base_width: float = 2.0
    ) -> float:
        """
        Calculates physical stroke thickness based on pen velocity and inflection curvature:
        w(v) = w_min + (w_max - w_min) * exp(-k * v)
        Decelerations at sharp inflection points trigger natural ink pooling.
        """
        import numpy as np

        if pen_type == "fountain_pen":
            w_min, w_max, k = 1.0, 4.2, 0.9
        elif pen_type == "gel_pen_black":
            w_min, w_max, k = 1.6, 3.0, 0.5
        elif pen_type == "pencil":
            w_min, w_max, k = 1.2, 2.8, 0.4
        else:  # ballpoint_blue
            w_min, w_max, k = 1.2, 3.5, 0.7

        # Deceleration factor from curvature (high curvature = lower speed)
        effective_v = max(0.1, velocity / (1.0 + 2.0 * abs(curvature)))
        thickness = w_min + (w_max - w_min) * float(np.exp(-k * effective_v))
        return round(thickness, 2)

    @classmethod
    def get_ink_color(
        cls,
        pen_type: str = "ballpoint_blue",
        is_downstroke: bool = False,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, int, int]:
        r = rng or random
        base_rgb = PEN_PALETTES.get(pen_type, PEN_PALETTES["ballpoint_blue"])

        if pen_type == "ballpoint_blue":
            # Heavier pressure and darker opacity on vertical downstrokes
            alpha = r.randint(245, 255) if is_downstroke else r.randint(210, 240)
            return (*base_rgb, alpha)

        elif pen_type == "fountain_pen":
            # Wide dynamic shading range reflecting capillary action
            alpha = r.randint(235, 255) if is_downstroke else r.randint(160, 210)
            return (*base_rgb, alpha)

        elif pen_type == "pencil":
            alpha = r.randint(180, 220)
            return (*base_rgb, alpha)

        else:
            alpha = r.randint(240, 255)
            return (*base_rgb, alpha)
