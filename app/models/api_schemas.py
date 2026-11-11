"""
API Schemas for FastAPI web server endpoints.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GenerateDocumentRequest(BaseModel):
    template_file_id: str
    reference_file_ids: List[str]
    additional_text: Optional[str] = None
    instruction: Optional[str] = None
    output_format: str = "docx" # "docx" or "pdf" or "both"
    user_clarifications: Optional[Dict[str, Any]] = None

class DocumentJobStatus(BaseModel):
    job_id: str
    status: str # "queued", "analysing_template", "reading_references", "extracting_info", "mapping_info", "generating_docx", "checking_formatting", "completed", "failed", "pending_clarification"
    progress_percentage: int
    current_step: str
    template_profile: Optional[Dict[str, Any]] = None
    extracted_data: Optional[List[Dict[str, Any]]] = None
    mapping_report: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    token_usage: Optional[Dict[str, Any]] = None
    docx_download_url: Optional[str] = None
    pdf_download_url: Optional[str] = None
    error_message: Optional[str] = None
    clarifications_needed: Optional[List[str]] = None

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_size: int
    sha256_hash: str
    is_duplicate: bool = False
