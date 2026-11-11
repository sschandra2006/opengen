"""
FastAPI web routes and endpoints for Document Generation Engine.
"""
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.models.api_schemas import (
    UploadResponse, GenerateDocumentRequest, DocumentJobStatus
)
from app.modules.input_manager.validator import validator
from app.modules.memory_cache.storage import storage
from app.modules.pipeline import DocumentGenerationPipeline

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api")

@api_router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Uploads and validates a template or reference file."""
    try:
        content = await file.read()
        res = validator.process_and_store(content, file.filename)
        return res
    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/generate", response_model=DocumentJobStatus)
async def start_generation(req: GenerateDocumentRequest, background_tasks: BackgroundTasks):
    """Initiates a document generation job."""
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    storage.save_job(job_id, status="queued", current_step="queued", progress=0, data={})

    pipeline = DocumentGenerationPipeline()

    def task():
        pipeline.run(
            job_id=job_id,
            template_file_id=req.template_file_id,
            reference_file_ids=req.reference_file_ids,
            additional_text=req.additional_text,
            instruction=req.instruction,
            output_format=req.output_format,
            user_clarifications=req.user_clarifications
        )

    background_tasks.add_task(task)

    return DocumentJobStatus(
        job_id=job_id,
        status="queued",
        progress_percentage=0,
        current_step="queued"
    )

@api_router.get("/status/{job_id}", response_model=DocumentJobStatus)
async def get_job_status(job_id: str):
    """Polls real-time generation progress and retrieves artifacts."""
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = job.get("data", {})
    return DocumentJobStatus(
        job_id=job_id,
        status=job["status"],
        progress_percentage=job["progress_percentage"],
        current_step=job["current_step"],
        template_profile=data.get("template_profile"),
        extracted_data=data.get("extracted_data"),
        mapping_report=data.get("mapping_report"),
        validation_report=data.get("validation_report"),
        token_usage=data.get("token_usage"),
        docx_download_url=data.get("docx_download_url"),
        pdf_download_url=data.get("pdf_download_url"),
        error_message=data.get("error"),
        clarifications_needed=data.get("clarifications_needed")
    )

@api_router.post("/resolve/{job_id}", response_model=DocumentJobStatus)
async def resolve_clarifications(job_id: str, clarifications: dict, background_tasks: BackgroundTasks):
    """Resumes generation after the user resolves missing or conflicting fields."""
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pipeline = DocumentGenerationPipeline()
    # Find original file IDs from job data
    data = job.get("data", {})
    t_profile = data.get("template_profile", {})
    template_hash = t_profile.get("file_hash")
    templ_file = storage.get_file_by_hash(template_hash) if template_hash else None
    template_file_id = templ_file["file_id"] if templ_file else None

    # Retrieve reference file IDs
    ref_file_ids = []
    for d in data.get("extracted_data", []):
        f_hash = d.get("file_hash")
        if f_hash:
            f = storage.get_file_by_hash(f_hash)
            if f:
                ref_file_ids.append(f["file_id"])

    def task():
        pipeline.run(
            job_id=job_id,
            template_file_id=template_file_id,
            reference_file_ids=ref_file_ids,
            user_clarifications=clarifications
        )

    background_tasks.add_task(task)
    return DocumentJobStatus(
        job_id=job_id,
        status="resumed",
        progress_percentage=55,
        current_step="resumed"
    )

@api_router.get("/download/{job_id}/{fmt}")
async def download_file(job_id: str, fmt: str):
    """Downloads the final editable DOCX or rendered PDF."""
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = job.get("data", {})
    if fmt == "docx":
        path = data.get("docx_path")
        if path and Path(path).exists():
            return FileResponse(path, filename=Path(path).name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif fmt == "pdf":
        path = data.get("pdf_path")
        if path and Path(path).exists():
            return FileResponse(path, filename=Path(path).name, media_type="application/pdf")

    raise HTTPException(status_code=404, detail="Requested file not ready or not found")
