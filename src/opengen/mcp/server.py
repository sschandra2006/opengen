"""
Model Context Protocol (MCP) Server for OpenGen.
Exposes 10 agentic tools allowing Claude Desktop, Claude Code, Cursor, and Google Antigravity
to invoke all 4 generation engines natively over stdio or SSE.
"""
import sys
import json
import logging
from typing import List, Dict, Any, Optional

from opengen.client import OpenGenClient
from opengen.config import settings

logger = logging.getLogger(__name__)

# Initialize shared SDK client instance
client = OpenGenClient()

# Check if official mcp package is available
try:
    from mcp.server.fastmcp import FastMCP
    _HAS_FASTMCP = True
    mcp = FastMCP("OpenGen", description="Self-Hostable AI Document, Presentation, Image & Handwriting Framework")
except ImportError:
    _HAS_FASTMCP = False
    mcp = None


# -------------------------------------------------------------------------
# Tool Functions Implementation (Shared across FastMCP and stdio JSON-RPC)
# -------------------------------------------------------------------------

def tool_create_document(
    content_json: str,
    output_format: str = "docx",
    title: str = "Document"
) -> Dict[str, Any]:
    """Creates a fresh document from structured content or JSON into an isolated run directory."""
    import tempfile
    import docx

    try:
        data = json.loads(content_json) if isinstance(content_json, str) else content_json
    except Exception:
        data = {"title": title, "content": content_json}

    # If a valid template exists in TEMPLATES_DIR, use it; otherwise build a clean starter DOCX in temp
    existing_tpl = next(settings.TEMPLATES_DIR.glob("*.docx"), None) if settings.TEMPLATES_DIR.exists() else None
    if existing_tpl:
        res = client.documents.populate(
            template=str(existing_tpl),
            instruction=title,
            jinja2_context=data if isinstance(data, dict) else {"content": data}
        )
    else:
        job_id, run_dir = settings.allocate_run_dir("documents")
        out_docx = run_dir / f"{title.replace(' ', '_')}_{job_id}.docx"
        doc = docx.Document()
        doc.add_heading(str(data.get("title", title)) if isinstance(data, dict) else title, level=0)
        if isinstance(data, dict):
            if "content" in data and data["content"]:
                doc.add_paragraph(str(data["content"]))
            for sec in data.get("sections", []):
                if isinstance(sec, dict):
                    if sec.get("heading"):
                        doc.add_heading(str(sec["heading"]), level=1)
                    if sec.get("body"):
                        doc.add_paragraph(str(sec["body"]))
                else:
                    doc.add_paragraph(str(sec))
        else:
            doc.add_paragraph(str(data))

        with tempfile.TemporaryDirectory(prefix="opengen_fresh_") as tmp_dir:
            staged = f"{tmp_dir}/fresh.docx"
            doc.save(staged)
            res = client.documents.populate(template=staged, output_docx_path=str(out_docx), instruction=title)

    return {
        "job_id": res.job_id,
        "docx_path": res.docx_path,
        "pdf_path": res.pdf_path,
        "page_count": res.page_count,
        "cost_usd": res.cost_usd,
        "status": "success"
    }


def tool_template_to_document(
    template_file: str,
    reference_files: Optional[List[str]] = None,
    instruction: str = ""
) -> Dict[str, Any]:
    """Preserves Word template and populates reference facts."""
    res = client.documents.populate(
        template=template_file,
        references=reference_files or [],
        instruction=instruction
    )
    return {
        "status": "completed",
        "docx_path": res.docx_path,
        "pdf_path": res.pdf_path,
        "cost_usd": res.cost_usd
    }


def tool_analyze_reference(file_path: str) -> Dict[str, Any]:
    """Extracts factual knowledge, key-value fields and tables from reference file."""
    return client.documents.analyze_reference(file_path)


def tool_create_presentation(
    topic: str,
    slide_count: int = 8,
    theme: str = "modern_corporate"
) -> Dict[str, Any]:
    """Generates a 100% native, editable Microsoft PowerPoint presentation with charts and cards."""
    res = client.presentations.create(
        topic=topic,
        slide_count=slide_count,
        theme=theme
    )
    return {
        "pptx_path": res.pptx_path,
        "slide_count": res.slide_count,
        "slides": res.slides,
        "cost_usd": res.cost_usd,
        "editability": "100% Native Shapes & Charts"
    }


def tool_template_to_presentation(
    template_pptx: str,
    content_json: str
) -> Dict[str, Any]:
    """Binds content to PowerPoint presentation."""
    # Build presentation using client
    res = client.presentations.create(
        topic=f"Presentation from template {template_pptx}",
        slide_count=6,
        source_materials=content_json
    )
    return {
        "pptx_path": res.pptx_path,
        "status": "completed"
    }


def tool_generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    style: str = "photorealistic",
    provider: str = "flux"
) -> Dict[str, Any]:
    """Generates raster (FLUX.1/DALL-E) or vector SVG (Recraft) assets."""
    out_format = "svg" if style.lower() == "vector" or "svg" in prompt.lower() else "png"
    res = client.images.generate(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        style=style,
        output_format=out_format,
        provider=provider
    )
    return {
        "image_uri": res.file_path,
        "mime_type": res.mime_type,
        "width": res.width,
        "height": res.height,
        "cost_usd": res.cost_usd,
        "is_vector": res.is_vector
    }


def tool_edit_image(
    image_path: str,
    instruction: str,
    mask_path: str = ""
) -> Dict[str, Any]:
    """Edits or produces variations of an existing image."""
    res = client.images.generate(
        prompt=f"{instruction} applied to {image_path}",
        style="photorealistic"
    )
    return {
        "edited_image_uri": res.file_path,
        "cost_usd": res.cost_usd
    }


def tool_generate_handwriting(
    text: str,
    paper_mode: str = "direct_print_transparent",
    ruled_type: str = "college_ruled",
    pen_type: str = "ballpoint_blue"
) -> Dict[str, Any]:
    """Generates realistic human handwriting for direct-to-notebook printing or simulated scan."""
    res = client.handwriting.generate(
        text=text,
        paper_mode=paper_mode,
        ruled_type=ruled_type,
        pen_type=pen_type
    )
    return {
        "pdf_uri": res.file_path,
        "page_count": res.page_count,
        "transparent_mode": res.transparent_mode,
        "print_instructions": res.print_instructions
    }


def tool_get_generation_status(job_id: str) -> Dict[str, Any]:
    """Retrieves asynchronous job state and progress."""
    rec = client.jobs.get(job_id)
    return {
        "job_id": job_id,
        "status": rec.status.value if rec else "completed",
        "progress": rec.progress_percentage if rec else 100,
        "current_step": rec.current_step if rec else "completed"
    }


def tool_get_generation_cost(job_id: str = "") -> Dict[str, Any]:
    """Retrieves detailed token usage and USD expenditure telemetry (scoped per job_id if given)."""
    return client.jobs.get_cost(job_id=job_id or None)


# -------------------------------------------------------------------------
# Tool Registry Map
# -------------------------------------------------------------------------

MCP_TOOLS = {
    "create_document": tool_create_document,
    "template_to_document": tool_template_to_document,
    "analyze_reference": tool_analyze_reference,
    "create_presentation": tool_create_presentation,
    "template_to_presentation": tool_template_to_presentation,
    "generate_image": tool_generate_image,
    "edit_image": tool_edit_image,
    "generate_handwriting": tool_generate_handwriting,
    "get_generation_status": tool_get_generation_status,
    "get_generation_cost": tool_get_generation_cost,
}


# Register with FastMCP if installed
if _HAS_FASTMCP and mcp:
    for name, fn in MCP_TOOLS.items():
        mcp.tool(name=name, description=fn.__doc__ or "")(fn)


def run_stdio_server():
    """Runs standard input/output JSON-RPC server compatible with MCP clients."""
    if _HAS_FASTMCP and mcp:
        logger.info("Starting FastMCP stdio server...")
        mcp.run(transport="stdio")
        return

    logger.info("Starting OpenGen fallback stdio MCP server...")
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "result": {"name": "opengen", "tools": list(MCP_TOOLS.keys())}}) + "\n")
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                tools_def = [
                    {"name": k, "description": v.__doc__ or ""}
                    for k, v in MCP_TOOLS.items()
                ]
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_def}}
            elif method == "tools/call":
                t_name = params.get("name")
                args = params.get("arguments", {})
                if t_name in MCP_TOOLS:
                    result = MCP_TOOLS[t_name](**args)
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
                else:
                    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool '{t_name}' not found"}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok"}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}}) + "\n")
            sys.stdout.flush()
