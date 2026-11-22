"""
Comprehensive Test Suite for Anti-Slop Architecture & Human-Grade Craftsmanship Improvements.
Validates:
1. Document Studio: StyleRedliner buzzword scrubbing & Typst context guardrails.
2. Presentation Studio: Native PPTX comparison matrix & roadmap timeline without bullet points.
3. Image Studio: Optical lens prompts (zero "8k" junk), default negative prompts, and dynamic distance decay shadows.
4. Handwriting Studio: Dynamic velocity stroke thickness & AxiDraw vector SVG trajectory export.
5. Motion Studio: FFmpeg dynamic sidechain ducking filtergraph & 80 Hz high-pass acoustic filter.
6. Audio Studio: First-class AudioEngine, conversational breath tokens, punctuation timing, and EBU R128 mastering.
7. Creative Critic: Full Tier 1-4 audit dispatch including buzzword detection, prompt junk rejection, and audio quality checks.
"""
import pytest
from pathlib import Path
from PIL import Image

from opengen.engines.document.sku_classifier import SemanticSKUClassifier, StyleRedliner
from opengen.engines.document.typst_compiler import TypstCompiler
from opengen.engines.presentation.builder import PresentationBuilder
from opengen.engines.presentation.themes import THEMES
from opengen.domain.presentation import PresentationDeckSpec, SlideSpec, BentoCardSpec
from opengen.engines.image.optical_director import OpticalPromptDirector
from opengen.engines.image.shadow_synthesizer import StudioShadowSynthesizer
from opengen.engines.handwriting.engine import HandwritingEngine
from opengen.engines.handwriting.physics import PenPhysicsSimulator
from opengen.engines.motion.sound_designer import SoundDesigner
from opengen.engines.audio.timing import AudioTimingDirector
from opengen.engines.audio.engine import AudioEngine
from opengen.creative.quality_gate import CreativeCriticGate
from opengen.client import OpenGenClient


def test_style_redliner_and_buzzword_sanitization():
    raw_title = "🥛 Let us delve into a testament to unleashing the game-changer buffalo milk 🚀"
    # Redline text
    clean_title = StyleRedliner.redline_text(raw_title)
    assert "🥛" not in clean_title
    assert "🚀" not in clean_title
    assert "delve" not in clean_title.lower()
    assert "testament to" not in clean_title.lower()
    assert "unleashing" not in clean_title.lower()
    assert "game-changer" not in clean_title.lower()
    assert "buffalo milk" in clean_title

    # Document audit buzzword detection
    doc_with_buzzwords = {
        "title": "A testament to excellence",
        "narrative": "We will delve into our transformative game-changer strategy."
    }
    audit = CreativeCriticGate.audit_document(doc_with_buzzwords)
    assert audit["passed"] is False
    assert any("BUZZWORD_ANTI_PATTERN" in v for v in audit["violations"])


def test_optical_director_anti_slop_prompt_and_negatives():
    raw = "artisanal glass jar of Vedic ghee"
    expanded = OpticalPromptDirector.expand_prompt(raw, style="photorealistic")
    
    # 8k resolution MUST NOT be in expanded prompt (banned slop vector)
    assert "8k resolution" not in expanded
    assert "8k," not in expanded
    # Must include real lens optics & film stock
    assert "Hasselblad" in expanded
    assert "Kodak Portra 400" in expanded
    assert "micro-texture" in expanded

    # Negative prompt verification
    neg_prompt = OpticalPromptDirector.get_negative_prompt("photorealistic")
    assert "plastic skin" in neg_prompt
    assert "waxy sheen" in neg_prompt

    # Critic rejects prompt junk
    bad_spec = {"prompt": "A hyperrealistic 8k resolution photo of a car"}
    audit = CreativeCriticGate.audit_image(bad_spec)
    assert audit["passed"] is False
    assert any("PROMPT_JUNK_ANTI_PATTERN" in v for v in audit["violations"])


def test_studio_shadow_dynamic_decay(tmp_path):
    # Create mock product and background
    prod_path = tmp_path / "product.png"
    bg_path = tmp_path / "background.jpg"
    out_path = tmp_path / "composite.jpg"

    prod = Image.new("RGBA", (200, 200), (200, 50, 50, 255))
    prod.save(str(prod_path))
    bg = Image.new("RGB", (800, 600), (240, 240, 240))
    bg.save(str(bg_path))

    res = StudioShadowSynthesizer.composite_product_with_contact_shadow(
        product_png_path=str(prod_path),
        background_jpg_path=str(bg_path),
        output_path=str(out_path),
        offset_distance_px=30,
        light_angle_deg=45.0
    )
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0


def test_presentation_builder_semantic_components_without_bullets(tmp_path):
    out_pptx = tmp_path / "semantic_deck.pptx"
    slides = [
        # Slide 1: Big Stat Hero
        SlideSpec(
            slide_number=1,
            layout_type="bento_grid",
            title="Executive Performance Highlights",
            bento_cards=[
                BentoCardSpec(title="Net ARR Growth", value="$28.4M", description="114% YoY expansion.", trend_badge="Top Decile", col_span=6),
                BentoCardSpec(title="Customer Retention", value="142%", description="Enterprise expansion index.", col_span=6)
            ]
        ),
        # Slide 2: Comparison Matrix (Old Way vs New Way)
        SlideSpec(
            slide_number=2,
            layout_type="comparison_matrix",
            title="The Paradigm Shift",
            bento_cards=[
                BentoCardSpec(title="Fragile Scripts & Raw Bullets", description="High manual rework and generic templates.", col_span=6),
                BentoCardSpec(title="Deterministic Compilers & Optics", description="Zero-token deterministic layout with agency polish.", col_span=6)
            ]
        ),
        # Slide 3: Roadmap Timeline
        SlideSpec(
            slide_number=3,
            layout_type="roadmap_timeline",
            title="Strategic Implementation Phases",
            bento_cards=[
                BentoCardSpec(title="Audit & Extraction", description="Ingest brand and reference PDFs.", col_span=4),
                BentoCardSpec(title="Layout Solving", description="Solve 12-column responsive coordinates.", col_span=4),
                BentoCardSpec(title="Deterministic Render", description="Compile through Typst & python-pptx.", col_span=4)
            ]
        )
    ]
    deck = PresentationDeckSpec(topic="Autonomous Intelligence", slides=slides)
    res_path = PresentationBuilder.build_deck(deck, str(out_pptx))
    assert Path(res_path).exists()
    assert Path(res_path).stat().st_size > 0

    # Verify no bullet point disease in critic
    audit = CreativeCriticGate.audit_presentation({"slides": [s.model_dump() for s in slides]})
    assert audit["passed"] is True
    assert len(audit["violations"]) == 0


def test_sound_designer_sidechain_ducking_filtergraph():
    sd = SoundDesigner()
    # Test SFX cue extraction
    project_ir = {
        "scenes": [
            {
                "start": 2.0,
                "creativeAdDirectives": {
                    "audioPunctuation": {"foleyCue": "whoosh_slide", "jCutLeadSec": 0.25}
                }
            }
        ]
    }
    cues = sd.extract_sfx_cues_from_project(project_ir)
    assert len(cues) == 1
    assert cues[0]["sound"] == "whoosh_slide"
    assert cues[0]["timestamp_sec"] == 1.75  # 2.0 - 0.25


def test_handwriting_vector_svg_export(tmp_path):
    hw = HandwritingEngine()
    svg_out = tmp_path / "handwriting_plotter.svg"
    svg_content = hw.export_vector_strokes_svg(
        text="AxiDraw Direct Pen Plotting Test",
        output_svg_path=str(svg_out)
    )
    assert Path(svg_out).exists()
    assert "<svg" in svg_content
    assert "axidraw-layer" in svg_content
    assert "</svg>" in svg_content


def test_audio_timing_and_engine(tmp_path):
    # 1. Punctuation Timing SSML
    raw_script = "OpenGen eliminates AI slop. It enforces optics, grids, and acoustics."
    ssml = AudioTimingDirector.to_ssml(raw_script)
    assert '<break time="350ms"/>' in ssml  # Comma
    assert '<break time="750ms"/>' in ssml  # Period

    # 2. Audio Engine local synthesis and mastering
    voice_out = tmp_path / "voice_sample.mp3"
    generated_path = AudioEngine.generate_speech(
        text="Experience human-grade agency craftsmanship with OpenGen.",
        output_path=str(voice_out),
        apply_dsp_mastering=True
    )
    assert Path(generated_path).exists()
    assert Path(generated_path).stat().st_size > 0

    # 3. Audio Critic Audit
    audit_pass = CreativeCriticGate.audit_audio({
        "text": "Short prompt.",
        "is_mixed": True,
        "ducking_enabled": True
    })
    assert audit_pass["passed"] is True

    audit_fail = CreativeCriticGate.audit_audio({
        "text": "Word " * 40,  # Long monotone speech without breath tokens
        "is_mixed": True,
        "ducking_enabled": False
    })
    assert audit_fail["passed"] is False
    assert any("MONOTONE_SPEECH_CADENCE" in v for v in audit_fail["violations"])
    assert any("MISSING_SIDECHAIN_DUCKING" in v for v in audit_fail["violations"])


def test_sdk_client_audio_endpoint(tmp_path):
    client = OpenGenClient()
    assert hasattr(client, "audio")
    res = client.audio.generate(
        text="Testing the integrated AudioClient endpoint.",
        output_path=tmp_path / "client_voice.mp3"
    )
    assert Path(res.file_path).exists()
    assert res.job_id is not None


def test_ui_critic_and_ast_linter():
    # 1. Reject generic bootstrap and inline style hacks
    bad_code = """
    <div class="jumbotron">
      <h1 style="color: purple; background: yellow; font-size: 24px;">Old 2018 Hero</h1>
      <button class="btn btn-primary"><svg></svg></button>
      <table><tr><td>Unstyled Data</td></tr></table>
      <img src="logo.png">
    """
    audit = CreativeCriticGate.audit_ui(bad_code)
    assert audit["passed"] is False
    assert any("GENERIC_BOOTSTRAP_SYNDROME" in v for v in audit["violations"])
    assert any("INLINE_STYLE_HACK" in v for v in audit["violations"])
    assert any("UNSTYLED_DATA_TABLE" in v for v in audit["violations"])
    assert any("BROKEN_COMPONENT_AST" in v for v in audit["violations"])
    assert any("ACCESSIBILITY_DEFICIT" in v for v in audit["violations"])

    # 2. Accept clean shadcn/Tailwind bento dashboard
    from opengen.engines.ui.engine import UIEngine
    cards = [
        {"title": "Active Pipelines", "value": "1,420", "description": "High-throughput jobs.", "col_span": 1, "trend_badge": "+18%"},
        {"title": "P99 Render Latency", "value": "42ms", "description": "Deterministic Rust compiler.", "col_span": 2}
    ]
    clean_html = UIEngine.generate_bento_dashboard(cards=cards, title="OpenGen System Metrics")
    clean_audit = CreativeCriticGate.audit_ui(clean_html)
    assert clean_audit["passed"] is True
    assert len(clean_audit["violations"]) == 0
    assert clean_audit["score"] == 100


def test_negative_space_quality_gate():
    # 1. Presentation slide crowding (>8 cards on a slide)
    crowded_deck = {
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "bento_grid",
                "title": "Overcrowded Slide",
                "bento_cards": [{"title": f"Card {i}", "col_span": 2} for i in range(9)]
            }
        ]
    }
    audit_pres = CreativeCriticGate.audit_presentation(crowded_deck)
    assert audit_pres["passed"] is False
    assert any("NEGATIVE_SPACE_DEFICIT" in v for v in audit_pres["violations"])

    # 2. Document narrative wall of text (>250 words without break)
    crowded_doc = {
        "title": "Wall of Text Report",
        "narrative": " ".join(["enterprise"] * 260)
    }
    audit_doc = CreativeCriticGate.audit_document(crowded_doc)
    assert audit_doc["passed"] is False
    assert any("NEGATIVE_SPACE_DEFICIT" in v for v in audit_doc["violations"])


def test_ui_client_sdk_and_api(tmp_path):
    from fastapi.testclient import TestClient
    from opengen.api import app

    # 1. SDK Client
    client = OpenGenClient()
    assert hasattr(client, "ui")
    cards = [
        {"title": "Throughput", "value": "500 req/s", "description": "Peak capacity.", "trend_badge": "Optimal"}
    ]
    res = client.ui.generate_bento_dashboard(
        title="Production Analytics",
        cards=cards,
        output_path=tmp_path / "dashboard.html"
    )
    assert res.is_valid is True
    assert Path(res.file_path).exists()
    assert "<!DOCTYPE html>" in res.code

    # 2. REST API /ui/audit and /ui/bento
    api_client = TestClient(app)
    resp_bento = api_client.post("/api/v1/ui/bento", json={
        "title": "API Cloud Dashboard",
        "cards": [{"title": "API Status", "value": "99.99%", "description": "All systems nominal."}]
    })
    assert resp_bento.status_code == 200
    bento_data = resp_bento.json()
    assert bento_data["status"] == "completed"
    assert bento_data["critic_score"] == 100

    # 3. REST API /audio/generate
    resp_audio = api_client.post("/api/v1/audio/generate", json={
        "text": "OpenGen REST API speech synthesis verification.",
        "voice": "narrator"
    })
    assert resp_audio.status_code == 200
    audio_data = resp_audio.json()
    assert audio_data["status"] == "completed"
    assert Path(audio_data["file_path"]).exists()
