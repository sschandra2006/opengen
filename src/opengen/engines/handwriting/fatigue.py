"""
Multi-Page Fatigue & Biological Motor Drift for Engine 4 (Handwriting Studio).
Simulates physical wrist and arm fatigue over multi-page essays:
- Margin indents wander rightward as writing progresses
- Character spacing widens as writing speed increases
- Baseline slant tilts gradually by +/- 1.5 degrees
"""
import random
from typing import Tuple, Optional


class MultiPageFatigueSimulator:
    """Simulates progressive biological fatigue across multi-page handwritten documents."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def get_page_fatigue_parameters(
        self,
        page_index: int,
        base_margin_px: int,
        base_line_pitch_px: int
    ) -> Tuple[int, int, float, float]:
        """
        Calculates adjusted margin, line pitch, spacing multiplier, and slant angle
        based on page count:
        Returns: (effective_margin_px, effective_pitch_px, spacing_factor, slant_degrees)
        """
        if page_index == 0:
            return base_margin_px, base_line_pitch_px, 1.0, 8.0

        # Progressively wander margin indent rightward (1px to 4px per page)
        margin_wander = int(min(24, page_index * self.rng.uniform(2.0, 5.0)))
        effective_margin = base_margin_px + margin_wander

        # Compress line pitch slightly (writer cramps towards bottom lines)
        pitch_compression = int(min(6, page_index * self.rng.uniform(0.5, 1.5)))
        effective_pitch = max(20, base_line_pitch_px - pitch_compression)

        # Character spacing widens by 4% to 8% as hand tires
        spacing_factor = min(1.15, 1.0 + (page_index * 0.03) + self.rng.uniform(-0.01, 0.02))

        # Slant tilts slightly more forward
        slant_deg = 8.0 + min(4.0, page_index * self.rng.uniform(0.4, 0.9))

        return effective_margin, effective_pitch, spacing_factor, slant_deg
