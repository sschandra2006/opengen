"""
Versioned REST API routes for OpenGen (/api/v1).
Exposes endpoints for documents, presentations, images, handwriting, and per-job artifacts.
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from opengen.config import settings
from opengen.client import OpenGenClient
from opengen.domain.brand import BrandKitSpec
from opengen.security.path_guard import PathGuard

router = APIRouter(prefix="/api/v1", tags=["OpenGen Core API"])
client = OpenGenClient()


# -------------------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------------------

class DocumentGenerateRequest(BaseModel):
    template_path: str
    reference_paths: List[str] = []
    instruction: Optional[str] = None
    use_jinja2: bool = False
    context: Optional[Dict[str, Any]] = None


class PresentationGenerateRequest(BaseModel):
    topic: str
    slide_count: int = 8
    theme: str = "modern_corporate"
    source_materials: Optional[str] = None


class ImageGenerateRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    style: str = "photorealistic"
    output_format: str = "png"
    provider: Optional[str] = None
    transparent_background: bool = False


class HandwritingGenerateRequest(BaseModel):
    text: str
    paper_mode: str = "direct_print_transparent"
    ruled_type: str = "college_ruled"
    pen_type: str = "ballpoint_blue"


class TypstDocumentRequest(BaseModel):
    title: str = "Executive Architecture Report"
    subtitle: str = "Strategic Blueprint & Operational Performance Overview"
    executive_summary: str = ""
    metrics: List[Dict[str, str]] = []
    financial_rows: List[Dict[str, str]] = []
    findings: List[Dict[str, str]] = []
    brand_id: Optional[str] = None


class CatalogDocumentRequest(BaseModel):
    title: str = "Artisan Product Catalog & Price Guide"
    products: List[Dict[str, Any]]
    brand_id: Optional[str] = None
    hero_ratio: float = 0.15


class BentoPresentationRequest(BaseModel):
    topic: str
    slide_count: int = 7
    brand_id: Optional[str] = None
    source_materials: Optional[str] = None


class RelightImageRequest(BaseModel):
    product_png_path: str
    background_jpg_path: str
    light_angle_deg: float = 45.0
    shadow_intensity: float = 0.65


class MotionAdGenerateRequest(BaseModel):
    brief: str
    source_footage_path: Optional[str] = None
    duration: float = 18.0
    aspect_ratio: str = "9:16"
    brand_id: Optional[str] = None
    voiceover_path: Optional[str] = None
    music_path: Optional[str] = None


class MotionTemplateRequest(BaseModel):
    template_id: str = "flash_sale"
    variables: Optional[Dict[str, Any]] = None
    brand_id: Optional[str] = None
    aspect_ratio: Optional[str] = None


class MotionAuditRequest(BaseModel):
    footage_path: str


class MotionReframeRequest(BaseModel):
    video_path: str
    focal_override_x: Optional[float] = None


class CreativeAuditRequest(BaseModel):
    engine: str
    payload: Dict[str, Any]


# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Health check endpoint reporting engine readiness and session telemetry."""
    return {
        "status": "online",
        "engines": {
            "document": "ready",
            "presentation": "ready",
            "image": "ready",
            "handwriting": "ready",
            "motion": "ready",
        },
        "telemetry": client.jobs.get_cost()
    }


@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and validates a template or reference file securely."""
    safe_name = Path(file.filename).name
    target_dir = settings.UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"upload_{os.urandom(4).hex()}_{safe_name}"

    PathGuard.validate_path(target_path, target_dir)

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": safe_name,
        "saved_path": str(target_path),
        "size_bytes": target_path.stat().st_size
    }


@router.post("/documents/generate")
def generate_document(req: DocumentGenerateRequest):
    """Generates a Word/PDF document inside an isolated run directory."""
    try:
        res = client.documents.populate(
            template=req.template_path,
            references=req.reference_paths,
            instruction=req.instruction,
            use_jinja2=req.use_jinja2,
            jinja2_context=req.context
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "docx_path": res.docx_path,
            "pdf_path": res.pdf_path,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.docx_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/typst")
def compile_typst_document(req: TypstDocumentRequest):
    """Compiles a Swiss Editorial document report (<50ms) using Typst."""
    try:
        data = {
            "title": req.title,
            "subtitle": req.subtitle,
            "executive_summary": req.executive_summary,
            "metrics": req.metrics,
            "financial_rows": req.financial_rows,
            "findings": req.findings,
        }
        res = client.documents.compile_typst(
            data=data,
            brand_id=req.brand_id
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "pdf_path": res.pdf_path,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.pdf_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/catalog")
def compile_catalog_document(req: CatalogDocumentRequest):
    """Compiles an 80/20 Swiss Editorial product catalog to PDF with Hero Bento Cards and dot-leader menus."""
    try:
        res = client.documents.compile_catalog_typst(
            products=req.products,
            title=req.title,
            brand_id=req.brand_id,
            hero_ratio=req.hero_ratio
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "pdf_path": res.pdf_path,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.pdf_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presentations/generate")
def generate_presentation(req: PresentationGenerateRequest):
    """Generates an editable 100% native Microsoft PowerPoint presentation."""
    try:
        res = client.presentations.create(
            topic=req.topic,
            slide_count=req.slide_count,
            theme=req.theme,
            source_materials=req.source_materials
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "pptx_path": res.pptx_path,
            "slide_count": res.slide_count,
            "slides": res.slides,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.pptx_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presentations/bento")
def generate_bento_presentation(req: BentoPresentationRequest):
    """Generates an elite 12-column Bento Grid pitch deck (PPTX + fluid HTML)."""
    try:
        res = client.presentations.generate_bento(
            topic=req.topic,
            slide_count=req.slide_count,
            brand_id=req.brand_id,
            source_materials=req.source_materials
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "pptx_path": res.pptx_path,
            "slide_count": res.slide_count,
            "slides": res.slides,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.pptx_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/generate")
def generate_image(req: ImageGenerateRequest):
    """Generates a raster (FLUX/DALL-E) or vector SVG (Recraft) asset."""
    try:
        res = client.images.generate(
            prompt=req.prompt,
            aspect_ratio=req.aspect_ratio,
            style=req.style,
            output_format=req.output_format,
            provider=req.provider,
            transparent_background=req.transparent_background
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "mime_type": res.mime_type,
            "width": res.width,
            "height": res.height,
            "is_vector": res.is_vector,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/relight")
def relight_image_product(req: RelightImageRequest):
    """Synthesizes dual-pass physical contact shadow & directional cast shadow beneath product plate."""
    try:
        res = client.images.relight_product(
            product_png_path=req.product_png_path,
            background_jpg_path=req.background_jpg_path,
            light_angle_deg=req.light_angle_deg,
            shadow_intensity=req.shadow_intensity
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/handwriting/generate")
def generate_handwriting(req: HandwritingGenerateRequest):
    """Generates realistic human handwriting for direct physical notebook printing or scan simulation."""
    try:
        res = client.handwriting.generate(
            text=req.text,
            paper_mode=req.paper_mode,
            ruled_type=req.ruled_type,
            pen_type=req.pen_type
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "page_count": res.page_count,
            "transparent_mode": res.transparent_mode,
            "print_instructions": res.print_instructions,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/motion/ad")
def generate_motion_ad(req: MotionAdGenerateRequest):
    """Generates a high-converting direct-response video ad (<30s)."""
    try:
        res = client.motion.create_ad(
            brief=req.brief,
            source_footage=req.source_footage_path,
            duration=req.duration,
            aspect_ratio=req.aspect_ratio,
            brand_id=req.brand_id,
            voiceover_path=req.voiceover_path,
            music_path=req.music_path,
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "duration": res.duration,
            "aspect_ratio": res.aspect_ratio,
            "critic_score": res.critic_score,
            "critic_violations": res.critic_violations,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/motion/audit")
def audit_motion_footage(req: MotionAuditRequest):
    """Audits video footage for high-saliency hooks and pacing dead-zones."""
    try:
        report = client.motion.audit(req.footage_path)
        return {"status": "completed", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/motion/reframe")
def reframe_motion_video(req: MotionReframeRequest):
    """Dynamically reframes landscape video to 9:16 vertical using LERP tracking."""
    try:
        out_path = client.motion.reframe(
            input_video_path=req.video_path,
            focal_override_x=req.focal_override_x
        )
        return {"status": "completed", "output_path": out_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/motion/templates")
def list_motion_templates():
    """Lists available pre-configured video ad archetypes."""
    return {"templates": client.motion.list_templates()}


@router.post("/motion/template")
def generate_motion_from_template(req: MotionTemplateRequest):
    """Hydrates and renders a pre-configured video ad archetype."""
    try:
        res = client.motion.create_from_template(
            template_id=req.template_id,
            variables=req.variables,
            brand_id=req.brand_id,
            aspect_ratio=req.aspect_ratio
        )
        return {
            "status": "completed",
            "job_id": res.job_id,
            "file_path": res.file_path,
            "duration": res.duration,
            "aspect_ratio": res.aspect_ratio,
            "critic_score": res.critic_score,
            "critic_violations": res.critic_violations,
            "download_url": f"/api/v1/artifacts/{res.job_id}/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/creative/audit")
def audit_creative_payload(req: CreativeAuditRequest):
    """Audits any generation payload across Engines 1 to 5 against the Anti-Mediocrity Doctrine."""
    try:
        report = client.critic.audit(engine=req.engine, payload=req.payload)
        return {"status": "completed", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieves persisted task status, artifacts, and isolated telemetry."""
    rec = client.jobs.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": rec.job_id,
        "engine": rec.engine,
        "status": rec.status.value,
        "progress": rec.progress_percentage,
        "current_step": rec.current_step,
        "artifacts": rec.artifacts,
        "telemetry": rec.telemetry or client.jobs.get_cost(job_id)
    }


@router.get("/artifacts/{job_id}/{filename}/dl")
def download_job_artifact(job_id: str, filename: str):
    """Securely downloads an artifact belonging to a specific generation job."""
    rec = client.jobs.get(job_id)
    if rec and rec.metadata.get("run_dir"):
        run_dir = Path(rec.metadata["run_dir"])
        candidate = run_dir / Path(filename).name
        if candidate.exists():
            PathGuard.validate_path(candidate, settings.OUTPUT_DIR)
            return FileResponse(path=str(candidate), filename=candidate.name)

    raise HTTPException(status_code=404, detail="Job artifact not found")


@router.get("/artifacts/{filename}/dl")
def download_artifact(filename: str):
    """Legacy flat download route securely searching under settings.OUTPUT_DIR."""
    safe_name = Path(filename).name
    direct = settings.OUTPUT_DIR / safe_name
    if direct.exists():
        PathGuard.validate_path(direct, settings.OUTPUT_DIR)
        return FileResponse(path=str(direct), filename=safe_name)

    # Also locate inside nested engine/job run directories safely
    if settings.OUTPUT_DIR.exists():
        matches = list(settings.OUTPUT_DIR.rglob(safe_name))
        if matches:
            target = matches[0]
            PathGuard.validate_path(target, settings.OUTPUT_DIR)
            return FileResponse(path=str(target), filename=safe_name)

    raise HTTPException(status_code=404, detail="Artifact not found")


# -------------------------------------------------------------------------
# Creative Intelligence Endpoints (Brand Kits, Typst, Bento, Relighting)
# -------------------------------------------------------------------------

@router.post("/brands")
def register_brand(brand: BrandKitSpec):
    """Registers or updates a Brand Kit specification."""
    saved = client.brand_kits.register(brand)
    return {"status": "success", "brand": saved.model_dump()}


@router.get("/brands")
def list_brands():
    """Lists all registered brand kits."""
    brands = client.brand_kits.list()
    return {"brands": [b.model_dump() for b in brands]}


@router.get("/brands/{brand_id}")
def get_brand(brand_id: str):
    """Retrieves a specific brand kit."""
    b = client.brand_kits.get(brand_id)
    if not b:
        raise HTTPException(status_code=404, detail="Brand kit not found")
    return {"brand": b.model_dump()}


@router.post("/documents/typst")
def generate_typst_document(req: TypstDocumentRequest):
    """Compiles a Swiss Editorial document report (<50ms) using Typst."""
    try:
        data = req.model_dump()
        res = client.documents.compile_typst(
            data=data,
            brand_id=req.brand_id
        )
        return {
            "status": "completed",
            "pdf_path": res.pdf_path,
            "cost_usd": res.cost_usd,
            "job_id": res.job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presentations/bento")
def generate_bento_presentation(req: BentoPresentationRequest):
    """Generates an elite 12-column Bento Grid deck (both native PPTX and fluid HTML5)."""
    try:
        res = client.presentations.generate_bento(
            topic=req.topic,
            slide_count=req.slide_count,
            brand_id=req.brand_id,
            source_materials=req.source_materials
        )
        return {
            "status": "completed",
            "pptx_path": res.pptx_path,
            "slide_count": res.slide_count,
            "slides": res.slides,
            "cost_usd": res.cost_usd,
            "job_id": res.job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/relight")
def relight_product(req: RelightImageRequest):
    """Synthesizes dual-pass physical contact shadow & directional cast shadow beneath product plate."""
    try:
        res = client.images.relight_product(
            product_png_path=req.product_png_path,
            background_jpg_path=req.background_jpg_path,
            light_angle_deg=req.light_angle_deg,
            shadow_intensity=req.shadow_intensity
        )
        return {
            "status": "completed",
            "image_path": res.file_path,
            "width": res.width,
            "height": res.height,
            "job_id": res.job_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
