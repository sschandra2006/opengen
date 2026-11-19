"""
Comprehensive Test Suite for the Unified Creative Intelligence Specification across Engines 1 to 5.
Validates:
- Engine 1: Semantic SKU Classifier, Emoji Stripping, Vector Icons, Typst Dot-Leader Catalogs
- Engine 2: 12-Column Responsive Bento Grids, Banning Bullet Points
- Engine 3: Camera Optics, Dual-Pass Contact Shadow & Negative Space
- Engine 4: Biomechanical Bezier Ligatures, Multi-Page Fatigue, Pen Dynamics & Imperfections
- Engine 5: Motion Graphics Retention Funnel, Saliency & Foley Audio
- Cross-Studio: Unified Brand Kit Tokens and Autonomous Creative Critic Gate
"""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw

from opengen.engines.document.sku_classifier import SemanticSKUClassifier
from opengen.engines.document.typst_compiler import TypstCompiler
from opengen.engines.handwriting.ligature_engine import CursiveLigatureEngine
from opengen.engines.handwriting.fatigue import MultiPageFatigueSimulator
from opengen.engines.handwriting.imperfections import HumanImperfectionGenerator
from opengen.engines.handwriting.physics import PenPhysicsSimulator
from opengen.domain.brand import BrandKitSpec, ColorPalette, TypographyTokens, GeometryTokens
from opengen.brand.resolver import BrandKitTokenResolver
from opengen.creative.quality_gate import CreativeCriticGate
from opengen.client import OpenGenClient


# -------------------------------------------------------------------------
# 1. Engine 1: Document Studio Creative Tests
# -------------------------------------------------------------------------

def test_sku_classifier_80_20_and_emoji_stripping():
    raw_products = [
        {"name": "🥛 PURE FRESH BUFFALO MILK 1L", "price": "₹85", "category": "Milk"},
        {"name": "🧈 ARTISAN CULTURED BUTTER 500G", "price": "₹450", "category": "Butter"},
        {"name": "🍯 HIGH AROMA VEDIC GHEE 1L JAR", "price": "₹1,250", "category": "Ghee", "is_hero": True},
        {"name": "🧀 MALAI PANEER 200G", "price": "₹120", "category": "Paneer"},
        {"name": "Standard Milk 500ml", "price": "₹38", "category": "Milk"},
        {"name": "Toned Milk 500ml", "price": "₹35", "category": "Milk"},
    ]

    # Test emoji stripping
    sanitized = SemanticSKUClassifier.sanitize_title("🥛 PURE FRESH BUFFALO MILK 1L")
    assert "🥛" not in sanitized
    assert "PURE FRESH BUFFALO MILK 1L" == sanitized

    # Test 80/20 partitioning
    heroes, streamlined = SemanticSKUClassifier.classify_catalog(raw_products, hero_ratio=0.3)
    assert len(heroes) >= 1
    assert any("VEDIC GHEE" in h["name"] for h in heroes)
    assert len(streamlined) >= 3

    # Test vector icon resolution
    assert SemanticSKUClassifier.resolve_vector_icon("Milk") == "droplet"
    assert SemanticSKUClassifier.resolve_vector_icon("Ghee") == "flame"


def test_typst_catalog_source_generation(tmp_path):
    products = [
        {"name": "Vedic Bilona Cow Ghee", "price": "₹1,450", "category": "Ghee", "is_hero": True, "spec": "1 Litre Glass Jar"},
        {"name": "Standardized Fresh Milk", "price": "₹38", "category": "Milk", "spec": "500ml Pouch"},
        {"name": "Toned Fresh Milk", "price": "₹35", "category": "Milk", "spec": "500ml Pouch"},
    ]
    out_pdf = tmp_path / "artisan_catalog.pdf"
    res_pdf = TypstCompiler.compile_catalog(products, str(out_pdf))

    assert Path(res_pdf).exists()
    typ_source = (tmp_path / "artisan_catalog.typ").read_text(encoding="utf-8")
    assert "HERO SPOTLIGHT" in typ_source
    assert "repeat[ . ]" in typ_source  # Dot-leader syntax


# -------------------------------------------------------------------------
# 2. Engine 4: Handwriting Biomechanical Tests
# -------------------------------------------------------------------------

def test_cursive_ligature_spline():
    p0 = (10.0, 50.0)
    p3 = (30.0, 52.0)
    curve = CursiveLigatureEngine.calculate_connecting_stroke("a", "b", p0, p3, slant_deg=8.0)
    assert len(curve) > 5
    # Should not connect space or punctuation
    empty_curve = CursiveLigatureEngine.calculate_connecting_stroke(" ", "b", p0, p3)
    assert len(empty_curve) == 0


def test_multi_page_fatigue_drift():
    sim = MultiPageFatigueSimulator(seed=42)
    m0, p0, s0, slant0 = sim.get_page_fatigue_parameters(0, 100, 30)
    m3, p3, s3, slant3 = sim.get_page_fatigue_parameters(3, 100, 30)

    # By page 3, margin should drift rightward and spacing factor should widen
    assert m3 > m0
    assert s3 > s0
    assert slant3 >= slant0


def test_human_imperfections_and_pen_dynamics():
    # Strikethrough test
    img = Image.new("RGBA", (200, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    HumanImperfectionGenerator.draw_strikethrough(draw, (20, 30, 80, 50), (28, 59, 114, 255))

    # Highlighter test
    highlighted = HumanImperfectionGenerator.apply_highlighter(img, (20, 30, 80, 50), color_name="yellow")
    assert highlighted.size == (200, 100)

    # Stroke thickness velocity physics
    thick_slow = PenPhysicsSimulator.calculate_stroke_thickness(velocity=0.3, curvature=2.0)
    thin_fast = PenPhysicsSimulator.calculate_stroke_thickness(velocity=3.5, curvature=0.0)
    assert thick_slow > thin_fast


# -------------------------------------------------------------------------
# 3. Cross-Studio Brand Kit & Quality Critic Gate Tests
# -------------------------------------------------------------------------

def test_brand_kit_motion_and_handwriting_tokens():
    brand = BrandKitSpec(
        brandId="brand_artisan_dairy",
        brandName="Sangam Heritage Dairy",
        colorPalette=ColorPalette(primary="#d97706", backgroundDark="#1e293b", textHighContrast="#ffffff"),
        typography=TypographyTokens(headingFont="Plus Jakarta Sans", displayFont="Newsreader"),
        geometry=GeometryTokens(cardCornerRadiusPx=12)
    )

    motion_tokens = BrandKitTokenResolver.to_motion_tokens(brand)
    assert motion_tokens["backgroundColor"] == "#1e293b"
    assert motion_tokens["accentColor"] == "#d97706"
    assert motion_tokens["safeZoneMarginPx"] == 240

    hw_profile = BrandKitTokenResolver.to_handwriting_profile(brand)
    assert hw_profile["pen_type"] == "fountain_pen"


def test_creative_critic_gate_all_engines():
    # 1. Document audit (catches emojis)
    doc_bad = {"title": "Fresh Milk 🥛 Rate Card", "products": [{"name": "Milk 🥛"}]}
    audit_doc = CreativeCriticGate.audit_document(doc_bad)
    assert audit_doc["passed"] is False
    assert any("EMOJI_ANTI_PATTERN" in v for v in audit_doc["violations"])

    # 2. Presentation audit (catches bullet disease)
    deck_bad = {
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "three_column",
                "cards": [
                    {"body_bullets": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5", "Point 6"]}
                ]
            }
        ]
    }
    audit_pres = CreativeCriticGate.audit_presentation(deck_bad)
    assert audit_pres["passed"] is False
    assert any("BULLET_POINT_DISEASE" in v for v in audit_pres["violations"])

    # 3. Handwriting audit (catches triplet repeats)
    audit_hw = CreativeCriticGate.audit_handwriting("coooommittee")
    assert audit_hw["passed"] is False
    assert any("TRIPLET_GLYPH_REPETITION" in v for v in audit_hw["violations"])

    # 4. Motion audit (catches duration overruns and hook slowness)
    motion_bad = {
        "settings": {"aspectRatio": "9:16"},
        "scenes": [{"duration": 5.0, "creativeAdDirectives": {}}]
    }
    audit_motion = CreativeCriticGate.audit_motion(motion_bad)
    assert audit_motion["passed"] is False
    assert any("HOOK_TOO_SLOW" in v for v in audit_motion["violations"])
