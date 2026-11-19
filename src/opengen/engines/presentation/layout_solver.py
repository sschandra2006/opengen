"""
Coordinate Geometry Layout Solver for 16:9 Presentations.
Calculates exact spatial coordinates (X, Y, Width, Height) in inches
and implements dynamic font-scaling guards to prevent text overflow.
"""
from dataclasses import dataclass
from typing import List, Tuple
from opengen.domain.presentation import SlideSpec

@dataclass
class BoxGeometry:
    x_in: float
    y_in: float
    w_in: float
    h_in: float
    recommended_font_pt: float = 14.0

class CoordinateLayoutSolver:
    """Solves element geometry on a standard 16:9 widescreen canvas (13.333" x 7.5")."""

    SLIDE_WIDTH_IN: float = 13.333
    SLIDE_HEIGHT_IN: float = 7.500
    MARGIN_LEFT_IN: float = 0.8
    MARGIN_TOP_IN: float = 0.8
    AVAILABLE_WIDTH_IN: float = 11.733  # 13.333 - 1.6
    AVAILABLE_HEIGHT_IN: float = 5.2    # Content area below title

    @classmethod
    def get_title_geometry(cls) -> BoxGeometry:
        return BoxGeometry(
            x_in=cls.MARGIN_LEFT_IN,
            y_in=cls.MARGIN_TOP_IN,
            w_in=cls.AVAILABLE_WIDTH_IN,
            h_in=1.1,
            recommended_font_pt=28.0
        )

    @classmethod
    def solve_cards_geometry(cls, layout_type: str, card_count: int, texts: List[str] = None) -> List[BoxGeometry]:
        """
        Solves X, Y, Width, Height for cards according to layout type.
        """
        y_start = 2.1
        texts = texts or [""] * card_count
        boxes: List[BoxGeometry] = []

        if layout_type == "title_hero":
            boxes.append(BoxGeometry(
                x_in=cls.MARGIN_LEFT_IN,
                y_in=2.4,
                w_in=cls.AVAILABLE_WIDTH_IN,
                h_in=3.0,
                recommended_font_pt=20.0
            ))

        elif layout_type == "single_column":
            boxes.append(BoxGeometry(
                x_in=cls.MARGIN_LEFT_IN,
                y_in=y_start,
                w_in=cls.AVAILABLE_WIDTH_IN,
                h_in=cls.AVAILABLE_HEIGHT_IN - 0.5,
                recommended_font_pt=16.0
            ))

        elif layout_type == "two_column":
            gap = 0.5
            w_card = (cls.AVAILABLE_WIDTH_IN - gap) / 2.0
            h_card = cls.AVAILABLE_HEIGHT_IN - 0.6
            for i in range(2):
                x = cls.MARGIN_LEFT_IN + i * (w_card + gap)
                f_size = cls._calculate_font_scaling(texts[i] if i < len(texts) else "", w_card, h_card, base_pt=15.0)
                boxes.append(BoxGeometry(x_in=x, y_in=y_start, w_in=w_card, h_in=h_card, recommended_font_pt=f_size))

        elif layout_type == "three_column":
            gap = 0.4
            w_card = (cls.AVAILABLE_WIDTH_IN - (2 * gap)) / 3.0
            h_card = cls.AVAILABLE_HEIGHT_IN - 0.7
            for i in range(3):
                x = cls.MARGIN_LEFT_IN + i * (w_card + gap)
                f_size = cls._calculate_font_scaling(texts[i] if i < len(texts) else "", w_card, h_card, base_pt=14.0)
                boxes.append(BoxGeometry(x_in=x, y_in=y_start, w_in=w_card, h_in=h_card, recommended_font_pt=f_size))

        elif layout_type == "four_metrics":
            gap = 0.3
            w_card = (cls.AVAILABLE_WIDTH_IN - (3 * gap)) / 4.0
            h_card = cls.AVAILABLE_HEIGHT_IN - 1.2
            for i in range(4):
                x = cls.MARGIN_LEFT_IN + i * (w_card + gap)
                boxes.append(BoxGeometry(x_in=x, y_in=y_start + 0.3, w_in=w_card, h_in=h_card, recommended_font_pt=13.0))

        elif layout_type == "split_chart":
            # Left card (40% width), right chart (60% width)
            w_card = 4.5
            w_chart = cls.AVAILABLE_WIDTH_IN - w_card - 0.5
            h = cls.AVAILABLE_HEIGHT_IN - 0.6
            boxes.append(BoxGeometry(x_in=cls.MARGIN_LEFT_IN, y_in=y_start, w_in=w_card, h_in=h, recommended_font_pt=14.0))
            boxes.append(BoxGeometry(x_in=cls.MARGIN_LEFT_IN + w_card + 0.5, y_in=y_start, w_in=w_chart, h_in=h, recommended_font_pt=12.0))

        elif layout_type in ["bento_grid", "stat_card_grid", "comparison_matrix", "roadmap_timeline"]:
            # 12-column responsive grid layout
            if card_count == 2:
                spans = [6, 6]
            elif card_count == 3:
                spans = [4, 4, 4]
            elif card_count == 4:
                spans = [3, 3, 3, 3]
            else:
                spans = [12 // max(1, card_count)] * card_count
            return cls.solve_12col_bento_geometry(spans, y_start=y_start, h_card=cls.AVAILABLE_HEIGHT_IN - 0.7)

        else:
            # Fallback to single card
            boxes.append(BoxGeometry(x_in=cls.MARGIN_LEFT_IN, y_in=y_start, w_in=cls.AVAILABLE_WIDTH_IN, h_in=4.2))

        return boxes

    @classmethod
    def solve_12col_bento_geometry(
        cls,
        col_spans: List[int],
        y_start: float = 2.1,
        h_card: float = 4.5,
        gap: float = 0.35
    ) -> List[BoxGeometry]:
        """
        Solves exact X, Y, Width, Height for cards according to a 12-column grid.
        Total available width is divided into 12 proportional columns.
        """
        total_gaps = 11 * gap
        col_unit = (cls.AVAILABLE_WIDTH_IN - total_gaps) / 12.0
        boxes = []
        cur_x = cls.MARGIN_LEFT_IN

        for span in col_spans:
            w = (span * col_unit) + ((span - 1) * gap)
            boxes.append(BoxGeometry(
                x_in=cur_x,
                y_in=y_start,
                w_in=w,
                h_in=h_card,
                recommended_font_pt=14.0 if span >= 4 else 12.0
            ))
            cur_x += w + gap

        return boxes

    @classmethod
    def _calculate_font_scaling(cls, text: str, width_in: float, height_in: float, base_pt: float = 14.0) -> float:
        """Dynamically reduces font size if total characters exceed container bounds."""
        if not text:
            return base_pt
        char_count = len(text)
        # Approximate capacity in characters at base font size
        max_chars = int((width_in * 12) * (height_in * 3.5))
        if char_count > max_chars * 1.4:
            return max(10.0, base_pt - 4.0)
        elif char_count > max_chars:
            return max(11.0, base_pt - 2.0)
        return base_pt
