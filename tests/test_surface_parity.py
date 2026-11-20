"""
Unit and Integration Tests for Surface Parity across SDK, MCP Server, and REST API.
Verifies that all new ecosystem adapters are exposed uniformly across interfaces.
"""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from opengen.api.app import app
from opengen.client import OpenGenClient
from opengen.mcp.server import MCP_TOOLS, tool_export_nle_edl, tool_export_nle_fcpxml, tool_generate_marp_presentation


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def sample_ir():
    return {
        "schemaVersion": "1.1.0",
        "projectId": "parity_01",
        "title": "Surface Parity Ad",
        "settings": {"fps": 30, "duration": 10.0, "width": 1080, "height": 1920},
        "scenes": [
            {"id": "sc1", "name": "Hook", "start": 0.0, "duration": 2.0},
            {"id": "sc2", "name": "Payoff", "start": 2.0, "duration": 3.0}
        ]
    }


@pytest.fixture
def sample_test_image(tmp_path):
    p = tmp_path / "square.png"
    im = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([20, 20, 80, 80], fill=(255, 0, 0, 255))
    im.save(str(p))
    return str(p)


def test_mcp_server_new_tools_registration():
    expected_new_tools = [
        "jumpcut_video",
        "create_bento_mosaic",
        "isolate_product_image",
        "vectorize_image_to_svg",
        "export_nle_edl",
        "export_nle_fcpxml",
        "generate_marp_presentation"
    ]
    for tool_name in expected_new_tools:
        assert tool_name in MCP_TOOLS, f"Missing MCP tool: {tool_name}"


def test_mcp_tool_export_nle(sample_ir):
    res_edl = tool_export_nle_edl(sample_ir)
    assert res_edl["status"] == "completed"
    assert "001  AX" in res_edl["edl_content"]

    res_xml = tool_export_nle_fcpxml(sample_ir)
    assert res_xml["status"] == "completed"
    assert '<fcpxml version="1.9">' in res_xml["fcpxml_content"]


def test_mcp_tool_marp_presentation():
    res = tool_generate_marp_presentation(topic="MCP Integration Topic", slide_count=4)
    assert res["status"] == "completed"
    assert Path(res["markdown_path"]).exists()
    assert "marp: true" in Path(res["markdown_path"]).read_text(encoding="utf-8")


def test_rest_api_export_edl_and_fcpxml(api_client, sample_ir):
    # Test EDL endpoint
    resp_edl = api_client.post("/api/v1/motion/export/edl", json={"project_ir": sample_ir})
    assert resp_edl.status_code == 200
    assert "001  AX" in resp_edl.json()["edl_content"]

    # Test FCPXML endpoint
    resp_xml = api_client.post("/api/v1/motion/export/fcpxml", json={"project_ir": sample_ir})
    assert resp_xml.status_code == 200
    assert "<fcpxml" in resp_xml.json()["fcpxml_content"]


def test_rest_api_image_vectorize(api_client, sample_test_image):
    resp = api_client.post("/api/v1/images/vectorize", json={"image_path": sample_test_image, "color_hex": "#10b981"})
    assert resp.status_code == 200
    svg_p = resp.json()["svg_path"]
    assert Path(svg_p).exists()
    assert "<svg" in Path(svg_p).read_text(encoding="utf-8")


def test_rest_api_presentation_marp(api_client):
    resp = api_client.post("/api/v1/presentations/marp", json={"topic": "REST API Pitch", "slide_count": 3})
    assert resp.status_code == 200
    md_p = resp.json()["markdown_path"]
    assert Path(md_p).exists()
    assert "marp: true" in Path(md_p).read_text(encoding="utf-8")


def test_sdk_client_method_parity():
    client = OpenGenClient()
    assert hasattr(client.motion, "jumpcut")
    assert hasattr(client.motion, "create_collage")
    assert hasattr(client.motion, "export_edl")
    assert hasattr(client.motion, "export_fcpxml")
    assert hasattr(client.images, "isolate")
    assert hasattr(client.images, "vectorize")
    assert hasattr(client.presentations, "generate_marp")
    assert hasattr(client.documents, "compile_reference_catalog")
