"""
Versioned REST API routes for OpenGen (/api/v1).
Exposes endpoints for documents, presentations, images, handwriting, and job telemetry.
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from opengen.config import settings
from opengen.client import OpenGenClient
from opengen.security.path_guard import PathGuard
from opengen.telemetry.cost_tracker import cost_tracker

router = APIRouter(prefix="/api/v1", tags=["OpenGen Core API"])
client = OpenGenClient()


# -------------------------------------------------------------------------
# Request / Response Schemas
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


# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Health check endpoint reporting engine readiness and telemetry."""
    return {
        "status": "online",
        "engines": {
            "document": "ready",
            "presentation": "ready",
            "image": "ready",
            "handwriting": "ready",
        },
        "telemetry": cost_tracker.get_aggregate_cost()
    }


@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and validates a template or reference file securely."""
    safe_name = Path(file.filename).name
    target_dir = settings.UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"upload_{os.urandom(4).hex()}_{safe_name}"

    # Path traversal validation
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
    """Submits or executes a Word/PDF document generation request."""
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
            "docx_path": res.docx_path,
            "pdf_path": res.pdf_path,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{Path(res.docx_path).name}/dl"
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
            "pptx_path": res.pptx_path,
            "slide_count": res.slide_count,
            "slides": res.slides,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{Path(res.pptx_path).name}/dl"
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
            "file_path": res.file_path,
            "mime_type": res.mime_type,
            "width": res.width,
            "height": res.height,
            "is_vector": res.is_vector,
            "cost_usd": res.cost_usd,
            "download_url": f"/api/v1/artifacts/{Path(res.file_path).name}/dl"
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
            "file_path": res.file_path,
            "page_count": res.page_count,
            "transparent_mode": res.transparent_mode,
            "print_instructions": res.print_instructions,
            "download_url": f"/api/v1/artifacts/{Path(res.file_path).name}/dl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieves asynchronous task status and progress."""
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
        "telemetry": cost_tracker.get_aggregate_cost()
    }


@router.get("/artifacts/{filename}/dl")
def download_artifact(filename: str):
    """Securely downloads generated DOCX, PPTX, PDF, or image files."""
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    PathGuard.validate_path(file_path, settings.OUTPUT_DIR)
    return FileResponse(path=str(file_path), filename=filename)
