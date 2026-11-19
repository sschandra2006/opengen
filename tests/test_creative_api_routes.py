"""
Tests for Extended Creative Intelligence & Engine 5 REST API Endpoints.
Verifies /documents/typst, /documents/catalog, /presentations/bento,
/images/relight, /motion/templates, /motion/template, and /creative/audit.
"""
from fastapi.testclient import TestClient
from opengen.api import app
from pathlib import Path
import tempfile
from PIL import Image

client = TestClient(app)


def test_api_documents_typst():
    payload = {
        "title": "Quarterly Financial Overview",
        "subtitle": "Q3 Enterprise Performance",
        "executive_summary": "Net revenues increased by 42% quarter-over-quarter.",
        "metrics": [{"label": "EBITDA Margin", "value": "34.2%"}],
        "findings": [{"title": "Cloud Migration", "desc": "Reduced operational latency by 68%."}]
    }
    response = client.post("/api/v1/documents/typst", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "pdf_path" in data
    assert Path(data["pdf_path"]).exists()


def test_api_documents_catalog():
    payload = {
        "title": "Artisan Dairy Catalog",
        "products": [
            {"name": "A2 Gir Cow Milk", "price": "$4.50", "category": "Dairy", "is_hero": True},
            {"name": "Cultured Curd Butter", "price": "$7.00", "category": "Dairy", "is_hero": False}
        ]
    }
    response = client.post("/api/v1/documents/catalog", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "pdf_path" in data
    assert Path(data["pdf_path"]).exists()


def test_api_presentations_bento():
    payload = {
        "topic": "Sequoia AI Narrative Pitch",
        "slide_count": 4
    }
    response = client.post("/api/v1/presentations/bento", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "pptx_path" in data
    assert Path(data["pptx_path"]).exists()
    assert data["slide_count"] >= 4


def test_api_images_relight():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create dummy product and background images
        prod_path = Path(tmp_dir) / "product.png"
        bg_path = Path(tmp_dir) / "background.jpg"

        Image.new("RGBA", (200, 200), (200, 100, 50, 255)).save(prod_path)
        Image.new("RGB", (600, 600), (240, 240, 240)).save(bg_path)

        payload = {
            "product_png_path": str(prod_path),
            "background_jpg_path": str(bg_path),
            "light_angle_deg": 45.0,
            "shadow_intensity": 0.65
        }
        response = client.post("/api/v1/images/relight", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "file_path" in data
        assert Path(data["file_path"]).exists()


def test_api_motion_templates():
    # 1. List templates
    resp_list = client.get("/api/v1/motion/templates")
    assert resp_list.status_code == 200
    templates = resp_list.json()["templates"]
    assert len(templates) >= 3

    # 2. Render from template
    resp_gen = client.post("/api/v1/motion/template", json={
        "template_id": "flash_sale",
        "variables": {"hook_title": "EXCLUSIVE API TEST DROP"}
    })
    assert resp_gen.status_code == 200
    data = resp_gen.json()
    assert data["status"] == "completed"
    assert "file_path" in data
    assert Path(data["file_path"]).exists()
    assert data["duration"] > 0


def test_api_creative_audit():
    # Test valid document
    resp = client.post("/api/v1/creative/audit", json={
        "engine": "document",
        "payload": {"title": "Executive Summary", "content": "Clean Swiss layout without emojis"}
    })
    assert resp.status_code == 200
    report = resp.json()["report"]
    assert report["passed"] is True
    assert report["score"] == 100

    # Test emoji anti-pattern
    resp_bad = client.post("/api/v1/creative/audit", json={
        "engine": "document",
        "payload": {"title": "Bad Summary", "content": "Special promo 🔥🚀 don't miss out!"}
    })
    assert resp_bad.status_code == 200
    report_bad = resp_bad.json()["report"]
    assert report_bad["passed"] is False
    assert any("EMOJI_ANTI_PATTERN" in v for v in report_bad["violations"])
