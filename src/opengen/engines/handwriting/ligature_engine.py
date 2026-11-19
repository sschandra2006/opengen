"""
Continuous Cursive Ligatures and Bezier Spline Joining for Engine 4 (Handwriting Studio).
Connects consecutive handwriting glyphs with smooth mathematical cubic Bezier curves,
eliminating the "floating disconnected letter" font syndrome.
"""
from typing import List, Tuple, Optional
import numpy as np


class CursiveLigatureEngine:
    """Calculates continuous cubic Bezier ligatures between character glyph boundaries."""

    @staticmethod
    def compute_cubic_bezier(
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        num_points: int = 16
    ) -> List[Tuple[float, float]]:
        """
        Calculates cubic Bezier curve points:
        B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 P3,  t in [0, 1]
        """
        t = np.linspace(0.0, 1.0, num_points)
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        return list(zip(x, y))

    @classmethod
    def calculate_connecting_stroke(
        cls,
        char_prev: str,
        char_next: str,
        exit_pos: Tuple[float, float],
        entry_pos: Tuple[float, float],
        slant_deg: float = 8.0
    ) -> List[Tuple[float, float]]:
        """
        Calculates a natural connecting stroke from the exit baseline of char_prev
        to the entry point of char_next, taking handwriting slant into account.
        """
        # If space or punctuation, no connecting ligature
        if char_prev in " .,;:!?'\"\n\t" or char_next in " .,;:!?'\"\n\t":
            return []

        x0, y0 = exit_pos
        x3, y3 = entry_pos

        dx = x3 - x0
        dy = y3 - y0

        # Control points creating a slight natural upward dipping curve
        rad = np.radians(slant_deg)
        slant_offset = np.tan(rad) * abs(dy)

        p1 = (x0 + dx * 0.35 + slant_offset * 0.2, y0 + dy * 0.15 + 2.0)
        p2 = (x0 + dx * 0.70 + slant_offset * 0.5, y3 - dy * 0.10 + 1.0)

        return cls.compute_cubic_bezier((x0, y0), p1, p2, (x3, y3), num_points=12)
