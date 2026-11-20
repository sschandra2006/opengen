"""
Tests for Model Context Protocol (MCP) Server.
Verifies tool registration, signature contracts, and execution across all 10 tools.
"""
import pytest
from pathlib import Path
from opengen.mcp.server import (
    MCP_TOOLS,
    tool_create_presentation,
    tool_generate_handwriting,
    tool_generate_image,
    tool_get_generation_cost,
    tool_get_generation_status,
)


def test_mcp_tools_registration():
    expected_tools = [
        "create_document",
        "template_to_document",
        "analyze_reference",
        "create_presentation",
        "template_to_presentation",
        "generate_image",
        "edit_image",
        "generate_handwriting",
        "get_generation_status",
        "get_generation_cost",
        "register_brand_kit",
        "compile_typst_document",
        "generate_bento_presentation",
        "relight_product_image",
        "generate_motion_ad",
        "audit_ad_timeline",
        "reframe_video",
        "compile_catalog_typst",
        "creative_critic_audit",
        "jumpcut_video",
        "create_bento_mosaic",
        "isolate_product_image",
        "vectorize_image_to_svg",
        "export_nle_edl",
        "export_nle_fcpxml",
        "generate_marp_presentation"
    ]
    assert len(MCP_TOOLS) >= 19
    for t in expected_tools:
        assert t in MCP_TOOLS
        assert callable(MCP_TOOLS[t])


def test_mcp_tool_create_presentation():
    res = tool_create_presentation(topic="MCP Agent Architecture", slide_count=4)
    assert "pptx_path" in res
    assert Path(res["pptx_path"]).exists()
    assert res["slide_count"] == 4
    assert res["editability"] == "100% Native Shapes & Charts"


def test_mcp_tool_generate_handwriting():
    res = tool_generate_handwriting(
        text="Homework Assignment: MCP Tool Execution Test.",
        paper_mode="direct_print_transparent"
    )
    assert "pdf_uri" in res
    assert Path(res["pdf_uri"]).exists()
    assert res["page_count"] == 1
    assert res["transparent_mode"] is True


def test_mcp_tool_generate_image():
    res = tool_generate_image(
        prompt="Vector icon of a database",
        style="vector"
    )
    assert "image_uri" in res
    assert Path(res["image_uri"]).exists()
    assert res["is_vector"] is True


def test_mcp_tool_telemetry_and_status():
    cost = tool_get_generation_cost()
    assert "total_cost_usd" in cost

    status = tool_get_generation_status("job_test_123")
    assert status["job_id"] == "job_test_123"
    assert status["status"] == "completed"


def test_mcp_tool_compile_catalog_and_critic():
    import json
    from opengen.mcp.server import tool_compile_catalog_typst, tool_creative_critic_audit

    products = [
        {"name": "Organic Pure Milk", "price": "$4.50", "category": "Dairy", "is_hero": True},
        {"name": "Artisan Butter", "price": "$6.00", "category": "Dairy", "is_hero": False}
    ]
    res_cat = tool_compile_catalog_typst(products_json=json.dumps(products), title="Farm Fresh")
    assert res_cat["status"] == "completed"
    assert Path(res_cat["pdf_path"]).exists()

    critic_res = tool_creative_critic_audit(
        engine="document",
        payload_json=json.dumps({"text": "Pure fresh organic milk"})
    )
    assert critic_res["status"] == "completed"
    assert "report" in critic_res
    assert critic_res["report"]["passed"] is True
