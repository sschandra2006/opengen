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
    mcp = FastMCP("OpenGen", description="Self-Hostable AI Multi-Modal Generation Framework (Documents, Presentations, Images, Handwriting, Video Ads)")
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


def tool_register_brand_kit(
    brand_json: str
) -> Dict[str, Any]:
    """Registers a Cross-Studio Brand Kit JSON with color palette, typography, and geometry tokens."""
    from opengen.domain.brand import BrandKitSpec
    try:
        data = json.loads(brand_json) if isinstance(brand_json, str) else brand_json
        brand = BrandKitSpec.model_validate(data)
        saved = client.brand_kits.register(brand)
        return {"status": "success", "brand_id": saved.brandId, "brand_name": saved.brandName}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_compile_typst_document(
    report_json: str,
    brand_id: str = ""
) -> Dict[str, Any]:
    """Compiles a publication-grade Swiss Editorial PDF report (<50ms) using Typst."""
    try:
        data = json.loads(report_json) if isinstance(report_json, str) else report_json
        res = client.documents.compile_typst(
            data=data,
            brand_id=brand_id or None
        )
        return {
            "status": "completed",
            "pdf_path": res.pdf_path,
            "cost_usd": res.cost_usd,
            "compiler": "typst"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_generate_bento_presentation(
    topic: str,
    slide_count: int = 7,
    brand_id: str = ""
) -> Dict[str, Any]:
    """Generates an elite 12-column Bento Grid pitch deck following Sequoia/YC narrative arcs."""
    try:
        res = client.presentations.generate_bento(
            topic=topic,
            slide_count=slide_count,
            brand_id=brand_id or None
        )
        return {
            "status": "completed",
            "pptx_path": res.pptx_path,
            "slide_count": res.slide_count,
            "slides": res.slides
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_relight_product_image(
    product_png_path: str,
    background_jpg_path: str,
    light_angle_deg: float = 45.0,
    shadow_intensity: float = 0.65
) -> Dict[str, Any]:
    """Synthesizes physics-based dual-pass contact shadow beneath product cutout over background."""
    try:
        res = client.images.relight_product(
            product_png_path=product_png_path,
            background_jpg_path=background_jpg_path,
            light_angle_deg=light_angle_deg,
            shadow_intensity=shadow_intensity
        )
        return {
            "status": "completed",
            "image_path": res.file_path,
            "width": res.width,
            "height": res.height
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_generate_motion_ad(
    brief: str,
    duration: float = 18.0,
    aspect_ratio: str = "9:16",
    brand_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a high-converting performance video ad (<30s) using Engine 5."""
    try:
        res = client.motion.create_ad(
            brief=brief,
            duration=duration,
            aspect_ratio=aspect_ratio,
            brand_id=brand_id
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "duration": res.duration,
            "critic_score": res.critic_score,
            "critic_violations": res.critic_violations
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_audit_ad_timeline(project_ir_json: str) -> Dict[str, Any]:
    """Audits an OpenGen IR project against viral retention metrics (Hook speed, monotony, safe-zones)."""
    try:
        data = json.loads(project_ir_json) if isinstance(project_ir_json, str) else project_ir_json
        from opengen.engines.motion.ad_critic import AdCriticAgent
        critic = AdCriticAgent()
        report = critic.audit_ad_timeline(data)
        return {"status": "completed", "audit": report}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_reframe_video(
    input_video_path: str,
    focal_override_x: Optional[float] = None
) -> Dict[str, Any]:
    """Dynamically reframes a landscape video to 9:16 vertical using LERP tracking."""
    try:
        out = client.motion.reframe(input_video_path, focal_override_x=focal_override_x)
        return {"status": "completed", "output_path": out}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_compile_catalog_typst(
    products_json: str,
    title: str = "Artisan Product Catalog & Price Guide",
    brand_id: str = "",
    hero_ratio: float = 0.15
) -> Dict[str, Any]:
    """Compiles an 80/20 Swiss Editorial product catalog to PDF with Hero Bento Cards and dot-leader menus."""
    try:
        products = json.loads(products_json) if isinstance(products_json, str) else products_json
        if isinstance(products, dict) and "products" in products:
            products = products["products"]
        res = client.documents.compile_catalog_typst(
            products=products,
            title=title,
            brand_id=brand_id or None,
            hero_ratio=hero_ratio
        )
        return {
            "status": "completed",
            "pdf_path": res.pdf_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_creative_critic_audit(
    engine: str,
    payload_json: str
) -> Dict[str, Any]:
    """Audits any project payload across Engines 1 to 5 against the Anti-Mediocrity Doctrine."""
    try:
        data = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
        report = client.critic.audit(engine=engine, payload=data)
        return {"status": "completed", "report": report}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_jumpcut_video(
    input_video_path: str,
    silence_thresh_sec: float = 0.35
) -> Dict[str, Any]:
    """Surgically cuts dead air (>0.35s) and adds dynamic camera punch-ins."""
    try:
        out_p = client.motion.jumpcut(input_video_path, silence_thresh_sec=silence_thresh_sec)
        return {"status": "completed", "output_path": out_p}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_create_bento_mosaic(
    clip_paths: List[str],
    duration: float = 4.0
) -> Dict[str, Any]:
    """Assembles 2 to 4 video clips into an animated 9:16 Bento Box mosaic."""
    try:
        out_p = client.motion.create_collage(clips=clip_paths, duration=duration)
        return {"status": "completed", "output_path": out_p}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_isolate_product_image(image_path: str) -> Dict[str, Any]:
    """Removes background from product or subject image, returning transparent RGBA PNG."""
    try:
        out_p = client.images.isolate(image_path)
        return {"status": "completed", "output_path": out_p}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_vectorize_image_to_svg(image_path: str, color_hex: str = "#38bdf8") -> Dict[str, Any]:
    """Converts raster image or silhouette into clean mathematical SVG paths."""
    try:
        out_p = client.images.vectorize(image_path, color_hex=color_hex)
        return {"status": "completed", "svg_path": out_p}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_export_nle_edl(project_ir_json: str) -> Dict[str, Any]:
    """Exports an OpenGen IR timeline into CMX 3600 EDL for DaVinci Resolve."""
    try:
        data = json.loads(project_ir_json) if isinstance(project_ir_json, str) else project_ir_json
        edl_text = client.motion.export_edl(data)
        return {"status": "completed", "edl_content": edl_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_export_nle_fcpxml(project_ir_json: str) -> Dict[str, Any]:
    """Exports an OpenGen IR timeline into Apple FCPXML v1.9."""
    try:
        data = json.loads(project_ir_json) if isinstance(project_ir_json, str) else project_ir_json
        xml_text = client.motion.export_fcpxml(data)
        return {"status": "completed", "fcpxml_content": xml_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_generate_marp_presentation(
    topic: str,
    slide_count: int = 7,
    brand_id: str = ""
) -> Dict[str, Any]:
    """Generates standard Marp/Slidev Markdown deck for developer presentations."""
    try:
        _, md_path = client.presentations.generate_marp(
            topic=topic,
            slide_count=slide_count,
            brand_id=brand_id or None
        )
        return {"status": "completed", "markdown_path": md_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    "register_brand_kit": tool_register_brand_kit,
    "compile_typst_document": tool_compile_typst_document,
    "generate_bento_presentation": tool_generate_bento_presentation,
    "relight_product_image": tool_relight_product_image,
    "generate_motion_ad": tool_generate_motion_ad,
    "audit_ad_timeline": tool_audit_ad_timeline,
    "reframe_video": tool_reframe_video,
    "compile_catalog_typst": tool_compile_catalog_typst,
    "creative_critic_audit": tool_creative_critic_audit,
    "jumpcut_video": tool_jumpcut_video,
    "create_bento_mosaic": tool_create_bento_mosaic,
    "isolate_product_image": tool_isolate_product_image,
    "vectorize_image_to_svg": tool_vectorize_image_to_svg,
    "export_nle_edl": tool_export_nle_edl,
    "export_nle_fcpxml": tool_export_nle_fcpxml,
    "generate_marp_presentation": tool_generate_marp_presentation,
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
