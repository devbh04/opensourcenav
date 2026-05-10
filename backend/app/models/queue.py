"""
Pydantic models for the job queue system.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

# ── Status Enum (as string literals) ─────────────────────────────────
QUEUE_STATUS_QUEUED = "queued"
QUEUE_STATUS_PROCESSING = "processing"
QUEUE_STATUS_COMPLETED = "completed"
QUEUE_STATUS_FAILED = "failed"


class QueueJob(BaseModel):
    """A single job in the processing queue."""
    job_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str
    repo_url: str
    repo_name: str = ""
    status: str = QUEUE_STATUS_QUEUED
    progress: float = 0.0
    current_phase: str = "Queued"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration_seconds: int = 180
    error: Optional[str] = None
    result_doc_id: Optional[str] = None
    # File selection
    session_id: str = ""
    selected_files: list[str] = []
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []


class QueueStatusResponse(BaseModel):
    """Response for queue status queries."""
    current_job: Optional[QueueJob] = None
    queue: list[QueueJob] = []
    total_in_queue: int = 0


class JobProgressUpdate(BaseModel):
    """WebSocket message for live progress updates."""
    job_id: str
    status: str
    progress: float
    current_phase: str
    error: Optional[str] = None
