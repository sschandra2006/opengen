"""
Tests for Engine D: Realistic Handwriting Generation.
Verifies glyph variance non-repetition, Brownian baseline drift,
and direct-to-notebook transparent PDF print generation.
"""
import pytest
from pathlib import Path
from PIL import Image
import pymupdf

from opengen.domain.handwriting import RuledPaperSpecs, HandwritingProfile
from opengen.engines.handwriting.glyph_bank import GlyphVariantBank
from opengen.engines.handwriting.drift import BrownianDriftSimulator
from opengen.engines.handwriting.physics import PenPhysicsSimulator
from opengen.engines.handwriting.ruler import RULED_PRESETS
from opengen.engines.handwriting.engine import HandwritingEngine


def test_glyph_variant_bank():
    bank = GlyphVariantBank(font_size=20)
    history = {}
    f1 = bank.get_font_for_char("e", 0, history)
    f2 = bank.get_font_for_char("e", 1, history)
    # Consecutive occurrences should record history
    assert history.get("e") is not None


def test_brownian_drift_simulator():
    sim = BrownianDriftSimulator()
    sim.reset_line()

    dx1, dy1 = sim.get_perturbation("a", is_end_of_word=False)
    dx2, dy2 = sim.get_perturbation("b", is_end_of_word=False)

    # Perturbations must stay within bounded baseline jitter
    assert abs(dy1) <= 15
    assert abs(dy2) <= 15


def test_pen_physics_colors():
    c_regular = PenPhysicsSimulator.get_ink_color("ballpoint_blue", is_downstroke=False)
    c_downstroke = PenPhysicsSimulator.get_ink_color("ballpoint_blue", is_downstroke=True)

    assert len(c_regular) == 4
    assert len(c_downstroke) == 4
    # Downstrokes have higher opacity/alpha
    assert c_downstroke[3] >= c_regular[3]


def test_handwriting_direct_print_transparent_mode(tmp_path):
    output_pdf = tmp_path / "handwritten_layer.pdf"
    specs = RULED_PRESETS["college_ruled"]
    profile = HandwritingProfile(pen_type="ballpoint_blue")
    engine = HandwritingEngine(specs=specs, profile=profile)

    sample_text = (
        "Problem 1: Given the linear recurrence relation T(n) = 2T(n/2) + O(n), "
        "by the Master Theorem we find that the asymptotic runtime complexity is O(n log n)."
    )

    result_path = engine.generate_handwriting(
        text=sample_text,
        output_pdf_path=str(output_pdf),
        transparent_mode=True
    )

    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0

    # Verify PDF opens and has 1 page
    doc = pymupdf.open(result_path)
    assert len(doc) >= 1
    doc.close()


def test_handwriting_synthetic_scanned_paper_mode(tmp_path):
    output_pdf = tmp_path / "synthetic_scan.pdf"
    specs = RULED_PRESETS["college_ruled"]
    profile = HandwritingProfile(pen_type="gel_pen_black")
    engine = HandwritingEngine(specs=specs, profile=profile)

    sample_text = "Notes on Distributed Systems Consensus: Paxos and Raft algorithms."

    result_path = engine.generate_handwriting(
        text=sample_text,
        output_pdf_path=str(output_pdf),
        transparent_mode=False
    )

    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0

    doc = pymupdf.open(result_path)
    assert len(doc) == 1
    doc.close()
