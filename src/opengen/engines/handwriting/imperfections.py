"""
Authentic Human Imperfections and Strikethrough Generator for Engine 4 (Handwriting Studio).
Generates realistic crossed-out words, superscript correction annotations,
and organic fluorescent highlighter overlays.
"""
import random
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw


class HumanImperfectionGenerator:
    """Simulates organic human mistakes, crossings-out, and annotations."""

    HIGHLIGHTER_COLORS = {
        "yellow": (255, 240, 32, 110),
        "mint": (64, 255, 170, 95),
        "cyan": (50, 220, 255, 95),
        "peach": (255, 170, 120, 100)
    }

    @staticmethod
    def draw_strikethrough(
        draw: ImageDraw.ImageDraw,
        box: Tuple[float, float, float, float],
        ink_color: Tuple[int, int, int, int],
        rng: Optional[random.Random] = None
    ):
        """
        Draws an authentic, organic double horizontal pen strikethrough across a word box.
        (x1, y1, x2, y2).
        """
        r = rng or random.Random()
        x1, y1, x2, y2 = box
        mid_y = (y1 + y2) / 2.0

        # Stroke 1: slight upward tilt with organic jitter
        y_jitter1 = r.uniform(-1.5, 1.5)
        draw.line(
            [(x1 - 2, mid_y + y_jitter1), (x2 + 3, mid_y - 1.0 + y_jitter1)],
            fill=ink_color,
            width=2
        )

        # Stroke 2: crossing slightly beneath
        y_jitter2 = r.uniform(-1.0, 2.0)
        draw.line(
            [(x1, mid_y + 3.0 + y_jitter2), (x2 + 2, mid_y + 2.0 + y_jitter2)],
            fill=ink_color,
            width=2
        )

    @classmethod
    def apply_highlighter(
        cls,
        image: Image.Image,
        box: Tuple[float, float, float, float],
        color_name: str = "yellow"
    ) -> Image.Image:
        """
        Applies a realistic semi-transparent highlighter overlay with natural end-stroke pooling.
        """
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        col = cls.HIGHLIGHTER_COLORS.get(color_name, cls.HIGHLIGHTER_COLORS["yellow"])
        x1, y1, x2, y2 = box

        # Main highlight rectangle
        draw.rectangle([x1 - 3, y1 - 2, x2 + 4, y2 + 2], fill=col)

        # End-stroke pooling (darker alpha accumulation where marker lifted)
        pool_col = (col[0], col[1], col[2], min(255, col[3] + 40))
        draw.rectangle([x2, y1 - 2, x2 + 5, y2 + 2], fill=pool_col)

        return Image.alpha_composite(image.convert("RGBA"), overlay)
