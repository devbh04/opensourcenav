"""
Pydantic models for the documentation generation system.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request Models ───────────────────────────────────────────────────

class PrepareRepoRequest(BaseModel):
    """Request to clone and scan a repo (step 1 of 2)."""
    repo_url: str = Field(..., description="GitHub repository URL")
    user_id: str = Field(..., description="Guest user ID from localStorage")


class PrepareRepoResponse(BaseModel):
    """Response after cloning and scanning (step 1 of 2)."""
    session_id: str
    repo_name: str
    file_tree: list = []
    all_files: list[str] = []
    stats: dict = {}
    default_include: list[str] = []
    default_exclude: list[str] = []


class GenerateDocsRequest(BaseModel):
    """Request to generate documentation for a repository."""
    repo_url: str = Field(..., description="GitHub repository URL")
    user_id: str = Field(..., description="Guest user ID from localStorage")
    session_id: str = Field("", description="Session ID from /prepare-repo (reuses clone)")
    selected_files: list[str] = Field([], description="Relative paths to include; empty = all")
    include_patterns: list[str] = Field([], description="Glob patterns to include")
    exclude_patterns: list[str] = Field([], description="Glob patterns to exclude")


# ── Document Page ────────────────────────────────────────────────────

class DocPage(BaseModel):
    """Single documentation page stored in MongoDB."""
    slug: str = Field(..., description="URL-friendly identifier, e.g. 'getting-started'")
    title: str
    description: str = ""
    category: str = "root"
    content_md: str = Field("", description="Markdown content of the page")
    order: int = 0
    icon: str = ""


class NavItem(BaseModel):
    """Navigation tree item for the sidebar."""
    title: str
    slug: str
    icon: str = ""
    children: list["NavItem"] = []


class DocMeta(BaseModel):
    """Metadata for the generated documentation set (_meta.json equivalent)."""
    repo_name: str
    repo_url: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    navigation: list[NavItem] = []
    stats: dict = {}


class DocStats(BaseModel):
    """Statistics about the documentation generation."""
    total_files_analyzed: int = 0
    total_lines: int = 0
    languages: list[str] = []
    abstractions_found: int = 0
    diagrams_generated: int = 0
    generation_time_seconds: float = 0.0


# ── Stored Document ──────────────────────────────────────────────────

class StoredDoc(BaseModel):
    """Full documentation record stored in MongoDB."""
    repo_url: str
    repo_name: str
    generated_by: str = ""
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    meta: DocMeta
    pages: list[DocPage] = []
    stats: DocStats = DocStats()
    qdrant_collection: str = ""


# ── Response Models ──────────────────────────────────────────────────

class GenerateDocsResponse(BaseModel):
    """Response after queueing a doc generation job."""
    success: bool
    job_id: str = ""
    message: str = ""
    queue_position: int = 0
    estimated_wait_seconds: int = 0


class DocListItem(BaseModel):
    """Summary of a generated doc set for listing."""
    repo_name: str
    repo_url: str
    generated_at: str
    page_count: int = 0
    languages: list[str] = []


class DocPageResponse(BaseModel):
    """Response for a single doc page request."""
    page: DocPage
    meta: DocMeta
    repo_name: str
