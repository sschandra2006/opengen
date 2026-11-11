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
    ]
    assert len(MCP_TOOLS) == 10
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
