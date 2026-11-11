"""
Brownian Motion Baseline Drift and Slant Simulator for Engine D.
Implements continuous Markov mean-reverting spring model for natural baseline perturbation.
"""
import random
from typing import Tuple

class BrownianDriftSimulator:
    """Simulates biological human hand baseline drift, hesitation, and micro-slant."""

    def __init__(
        self,
        baseline_jitter_px: float = 1.8,
        char_spacing_noise_px: float = 1.2,
        spring_constant: float = 0.25
    ):
        self.baseline_jitter = baseline_jitter_px
        self.char_spacing_noise = char_spacing_noise_px
        self.k = spring_constant
        self.current_dy = 0.0

    def get_perturbation(self, char: str, is_end_of_word: bool = False) -> Tuple[float, float]:
        """
        Returns (dx, dy) coordinate adjustments for character.
        dy uses a mean-reverting spring model so the line naturally rises and dips
        without ever running off the ruled notebook line.
        """
        # Brownian noise step
        step_noise = random.gauss(0, self.baseline_jitter * 0.5)
        # Mean reverting restoration force back to nominal baseline (0.0)
        restoration = -self.k * self.current_dy
        self.current_dy = self.current_dy + step_noise + restoration
        # Cap maximum vertical deviation to prevent drifting into adjacent line
        self.current_dy = max(-3.0, min(3.0, self.current_dy))

        dx = random.gauss(0, self.char_spacing_noise * 0.4)
        if is_end_of_word:
            dx += random.uniform(2.0, 5.0)  # Human word-separation rhythm

        return dx, self.current_dy

    def reset_line(self):
        """Resets baseline state at the start of a new line."""
        self.current_dy = random.uniform(-0.5, 0.5)
