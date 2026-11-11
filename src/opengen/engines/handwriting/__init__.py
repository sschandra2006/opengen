"""
Engine D: Pure Realistic Handwriting Generation Engine.
Direct-to-notebook printing and synthetic handwriting synthesis.
"""
from opengen.engines.handwriting.engine import HandwritingEngine
from opengen.engines.handwriting.ruler import RULED_PRESETS
from opengen.engines.handwriting.glyph_bank import GlyphVariantBank
from opengen.engines.handwriting.drift import BrownianDriftSimulator
from opengen.engines.handwriting.physics import PenPhysicsSimulator

__all__ = [
    "HandwritingEngine",
    "RULED_PRESETS",
    "GlyphVariantBank",
    "BrownianDriftSimulator",
    "PenPhysicsSimulator",
]
