"""
Domain models for asynchronous jobs, execution status, and generation telemetry.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    ANALYSING_TEMPLATE = "analysing_template"
    READING_REFERENCES = "reading_references"
    EXTRACTING_INFO = "extracting_info"
    MAPPING_INFO = "mapping_info"
    GENERATING = "generating"
    CHECKING_FORMATTING = "checking_formatting"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING_CLARIFICATION = "pending_clarification"

class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class JobRecord(BaseModel):
    job_id: str
    engine: str  # "document", "presentation", "image", "handwriting"
    status: JobStatus = JobStatus.QUEUED
    current_step: str = "queued"
    progress_percentage: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifacts: Dict[str, str] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    clarifications_needed: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.job_id
