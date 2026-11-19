"""
Comprehensive Test Suite for OpenGen Creative Intelligence Blueprint.
Verifies Brand Kit Tokens, Typst High-Speed Typesetting, Gamma-Style Bento Slides,
Sequoia/YC Narrative Arcs, Optical Prompt Expansion, and Studio Shadow Relighting.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from opengen.domain.brand import BrandKitSpec, ColorPalette, TypographyTokens, GeometryTokens
from opengen.brand.store import BrandKitStore, brand_kit_store
from opengen.brand.resolver import BrandKitTokenResolver
from opengen.engines.document.typst_compiler import TypstCompiler
from opengen.engines.document.engine import DocumentEngine
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.presentation.layout_solver import CoordinateLayoutSolver
from opengen.engines.presentation.bento_compiler import BentoSlideCompiler
from opengen.engines.presentation.engine import PresentationEngine
from opengen.engines.image.optical_director import OpticalPromptDirector
from opengen.engines.image.shadow_synthesizer import StudioShadowSynthesizer
from opengen.client import OpenGenClient
from opengen.api.app import app
from opengen.mcp.server import (
    tool_register_brand_kit,
    tool_compile_typst_document,
    tool_generate_bento_presentation,
    tool_relight_product_image
)


# -------------------------------------------------------------------------
# 1. Brand Kit & Design Token Tests
# -------------------------------------------------------------------------

def test_brand_kit_registration_and_resolver(tmp_path):
    store = BrandKitStore(storage_dir=tmp_path / "brands")
    custom_brand = BrandKitSpec(
        brandId="brand_lumina_ai",
        brandName="Lumina AI",
        colorPalette=ColorPalette(
            primary="#06b6d4",
            secondary="#8b5cf6",
            backgroundDark="#020617",
            surfaceCard="#0f172a"
        ),
        typography=TypographyTokens(
            displayFont="Newsreader",
            headingFont="Plus Jakarta Sans",
            bodyFont="Inter"
        ),
        geometry=GeometryTokens(
            cardCornerRadiusPx=16
        )
    )

    store.save_brand(custom_brand)
    assert store.has_brand("brand_lumina_ai")
    retrieved = store.get_brand("brand_lumina_ai")
    assert retrieved is not None
    assert retrieved.brandName == "Lumina AI"

    # Test Typst variable emission
    typst_vars = BrandKitTokenResolver.to_typst_vars(custom_brand)
    assert 'rgb("#06b6d4")' in typst_vars
    assert 'card-radius = 16pt' in typst_vars

    # Test CSS custom properties
    css_vars = BrandKitTokenResolver.to_css_variables(custom_brand)
    assert "--brand-primary: #06b6d4;" in css_vars
    assert "--card-radius: 16px;" in css_vars

    # Test PPTX theme conversion
    pptx_theme = BrandKitTokenResolver.to_presentation_theme(custom_brand)
    assert pptx_theme.accent_color == "#06b6d4"
    assert pptx_theme.card_background == "#0f172a"

    # Test Optical prompt tokens
    opt_tokens = BrandKitTokenResolver.to_optical_prompt_tokens(custom_brand)
    assert "Lumina AI" in opt_tokens
    assert "#06b6d4" in opt_tokens


# -------------------------------------------------------------------------
# 2. Document Studio (Typst & Swiss Editorial) Tests
# -------------------------------------------------------------------------

def test_typst_document_compilation(tmp_path):
    data = {
        "title": "QuantumFlow Strategic Architecture",
        "subtitle": "Q4 Enterprise Blueprint & Cloud Infrastructure",
        "brand_name": "QuantumFlow AI",
        "executive_summary": "The migration to deterministic AI compilation achieved 30x latency reduction.",
        "metrics": [
            {"label": "ARR Run-Rate", "value": "$14.2M", "trend": "▲ +112% YoY"},
            {"label": "Net Retention", "value": "138%", "trend": "Top Decile"},
            {"label": "Gross Margin", "value": "84.5%", "trend": "Industry Benchmark: 72%"}
        ],
        "financial_rows": [
            {"segment": "Enterprise Tier", "q1": "$4.2M", "q2": "$6.8M", "delta": "+62%", "status": "Strong"},
            {"segment": "Mid-Market", "q1": "$2.1M", "q2": "$3.1M", "delta": "+45%", "status": "On Track"}
        ]
    }

    # Verify Typst markup generation
    typ_source = TypstCompiler.build_typst_source(data)
    assert "QuantumFlow Strategic Architecture" in typ_source
    assert "ARR RUN-RATE" in typ_source
    assert "$14.2M" in typ_source
    assert "Segment Financial Highlights" in typ_source

    # Compile report to PDF
    pdf_out = tmp_path / "executive_report.pdf"
    res_path = DocumentEngine.compile_typst(data, str(pdf_out))
    assert Path(res_path).exists()
    assert Path(res_path).stat().st_size > 1000

    # Verify with PyMuPDF
    import pymupdf
    with pymupdf.open(res_path) as doc:
        assert len(doc) >= 1
        page_text = doc[0].get_text()
        assert "QuantumFlow" in page_text or "Executive" in page_text


# -------------------------------------------------------------------------
# 3. Presentation Studio (Bento & Sequoia Narrative) Tests
# -------------------------------------------------------------------------

def test_presentation_bento_generation(tmp_path):
    client = OpenGenClient()
    pptx_out = tmp_path / "deck.pptx"
    html_out = tmp_path / "deck.html"

    res = client.presentations.generate_bento(
        topic="Autonomous AI Creative Intelligence Platform",
        slide_count=7,
        output_pptx_path=pptx_out,
        output_html_path=html_out
    )

    # 1. Native PowerPoint Artifact Check
    assert Path(res.pptx_path).exists()
    assert Path(res.pptx_path).stat().st_size > 10000
    assert res.slide_count >= 7

    # 2. Fluid Bento HTML Artifact Check
    assert html_out.exists()
    html_content = html_out.read_text(encoding="utf-8")
    assert "Autonomous AI Creative Intelligence Platform" in html_content
    assert "bento-grid" in html_content
    assert "bento-card" in html_content
    assert "col-8" in html_content or "col-6" in html_content or "col-4" in html_content

    # 3. Sequoia Narrative Stage Check
    stages = [s.get("narrative_stage") for s in res.slides]
    assert "hook" in stages
    assert "pain" in stages
    assert "solution" in stages
    assert "traction" in stages


def test_12col_layout_solver():
    # Test 3-column span [4, 4, 4]
    boxes = CoordinateLayoutSolver.solve_12col_bento_geometry([4, 4, 4])
    assert len(boxes) == 3
    # Check that cards are placed side by side with gap
    assert boxes[1].x_in > boxes[0].x_in + boxes[0].w_in
    assert boxes[2].x_in > boxes[1].x_in + boxes[1].w_in

    # Test asymmetric hero span [8, 4]
    boxes_asym = CoordinateLayoutSolver.solve_12col_bento_geometry([8, 4])
    assert len(boxes_asym) == 2
    assert boxes_asym[0].w_in > boxes_asym[1].w_in * 1.5


# -------------------------------------------------------------------------
# 4. Image Studio (Optical Director & Contact Shadow) Tests
# -------------------------------------------------------------------------

def test_optical_prompt_director():
    prompt = "sleek matte wireless headphones"
    expanded = OpticalPromptDirector.expand_prompt(
        raw_prompt=prompt,
        preset_type="product_macro",
        lighting_type="commercial_studio",
        reserve_negative_space=True
    )
    assert "Hasselblad H6D-100c" in expanded
    assert "HC 100mm f/2.2" in expanded
    assert "Profoto softbox" in expanded
    assert "60% clean negative space" in expanded
    assert "zero plastic sheen" in expanded


def test_studio_contact_shadow_synthesis(tmp_path):
    # 1. Create synthetic product cutout with alpha
    p_img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    draw = ImageDraw.Draw(p_img)
    draw.rounded_rectangle([80, 80, 320, 320], radius=30, fill=(40, 40, 45, 255))
    product_path = tmp_path / "product_cutout.png"
    p_img.save(product_path)

    # 2. Create synthetic lifestyle background
    bg_img = Image.new("RGB", (1024, 768), (240, 242, 245))
    bg_path = tmp_path / "background.jpg"
    bg_img.save(bg_path)

    # 3. Composite with dual-pass contact shadow
    out_composite = tmp_path / "final_composite.jpg"
    res_path = StudioShadowSynthesizer.composite_product_with_contact_shadow(
        product_png_path=str(product_path),
        background_jpg_path=str(bg_path),
        output_path=str(out_composite),
        light_angle_deg=45.0,
        shadow_intensity=0.7
    )

    assert Path(res_path).exists()
    assert Path(res_path).stat().st_size > 5000
    with Image.open(res_path) as im:
        assert im.size == (1024, 768)


# -------------------------------------------------------------------------
# 5. REST API & MCP Server Tool Tests
# -------------------------------------------------------------------------

def test_rest_api_creative_intelligence(tmp_path):
    api_client = TestClient(app)

    # 1. Brand Kit Registration
    brand_payload = {
        "brandId": "test_brand_alpha",
        "brandName": "Alpha Corp",
        "colorPalette": {
            "primary": "#38bdf8",
            "secondary": "#6366f1"
        }
    }
    r_brand = api_client.post("/api/v1/brands", json=brand_payload)
    assert r_brand.status_code == 200
    assert r_brand.json()["status"] == "success"

    # 2. Typst Document Route
    typst_payload = {
        "title": "Alpha Corp Executive Brief",
        "subtitle": "Performance & Architecture",
        "executive_summary": "System latency dropped under 30ms.",
        "metrics": [
            {"label": "Uptime", "value": "99.99%", "trend": "Rock Solid"}
        ],
        "brand_id": "test_brand_alpha"
    }
    r_doc = api_client.post("/api/v1/documents/typst", json=typst_payload)
    assert r_doc.status_code == 200
    assert r_doc.json()["status"] == "completed"
    assert Path(r_doc.json()["pdf_path"]).exists()

    # 3. Bento Presentation Route
    bento_payload = {
        "topic": "Alpha Cloud Transformation",
        "slide_count": 5,
        "brand_id": "test_brand_alpha"
    }
    r_pres = api_client.post("/api/v1/presentations/bento", json=bento_payload)
    assert r_pres.status_code == 200
    assert r_pres.json()["status"] == "completed"
    assert Path(r_pres.json()["pptx_path"]).exists()


def test_mcp_creative_tools(tmp_path):
    # 1. MCP Brand Kit Tool
    b_res = tool_register_brand_kit(json.dumps({
        "brandId": "brand_mcp_test",
        "brandName": "MCP Test Brand"
    }))
    assert b_res["status"] == "success"

    # 2. MCP Bento Presentation Tool
    p_res = tool_generate_bento_presentation(
        topic="Autonomous AI Research",
        slide_count=5,
        brand_id="brand_mcp_test"
    )
    assert p_res["status"] == "completed"
    assert Path(p_res["pptx_path"]).exists()
