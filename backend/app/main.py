"""
EasyGit Backend — FastAPI application.

Endpoints:
  - POST /auth/guest          — register/sync guest user
  - POST /generate-docs       — queue doc generation for a repo
  - GET  /queue/status        — current queue status (for landing page)
  - GET  /queue/job/{job_id}  — specific job status
  - WS   /ws/progress/{job_id} — WebSocket for live progress
  - GET  /docs                — list all generated docs
  - GET  /docs/{owner}/{repo} — get doc metadata + nav
  - GET  /docs/{owner}/{repo}/{slug} — get a specific doc page
  - POST /chat                — chat with a repo's codebase
  - GET  /chat/sessions       — list chat sessions for a user
  - POST /find-repos          — find repos to contribute to
  - GET  /health              — health check
"""
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.db.mongodb import get_db, close_db
from app.services.queue_service import queue_service
from app.agents.docs_graph import run_docs_generation
from app.agents.repo_finder_graph import find_repos
from app.agents.chat_agent import chat_with_repo, get_chat_sessions
from app.utils.helpers import extract_repo_name

from app.models.docs import GenerateDocsRequest, GenerateDocsResponse, DocListItem, DocPageResponse, PrepareRepoRequest, PrepareRepoResponse
from app.models.user import RegisterGuestRequest, RegisterGuestResponse, GuestUser
from app.models.queue import QueueJob, QueueStatusResponse
from app.models.chat import ChatRequest, ChatResponse
from app.models.repos import RepoFinderRequest, RepoFinderResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifecycle ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting EasyGit backend...")

    # Initialize MongoDB (graceful — server starts even if DB is slow)
    try:
        await get_db()
    except Exception as e:
        logger.warning(f"MongoDB not ready at startup (will retry on first request): {e}")

    # Set the job handler for the queue
    queue_service.set_job_handler(_process_doc_job)

    # Recover any jobs stuck in "processing" from a previous crash
    try:
        await queue_service.recover_stale_jobs()
    except Exception as e:
        logger.warning(f"Failed to recover stale jobs: {e}")

    yield

    # Shutdown
    await close_db()
    logger.info("EasyGit backend stopped")


app = FastAPI(
    title="EasyGit API",
    description="Generate modern documentation for any GitHub repository",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Job Handler ──────────────────────────────────────────────────────

async def _process_doc_job(job: QueueJob) -> None:
    """
    Process a doc generation job — called by the queue worker.
    Runs the LangGraph pipeline and updates progress.
    """
    async def progress_callback(progress: float, phase: str):
        await queue_service.update_progress(job.job_id, progress, phase)

    try:
        result = await run_docs_generation(
            repo_url=job.repo_url,
            user_id=job.user_id,
            job_id=job.job_id,
            progress_callback=progress_callback,
            session_id=job.session_id,
            selected_files=job.selected_files,
            include_patterns=job.include_patterns,
            exclude_patterns=job.exclude_patterns,
        )

        if result.get("status") == "completed":
            await queue_service.update_progress(
                job.job_id, 1.0, "Documentation generated successfully!",
                status="completed",
            )
        else:
            await queue_service.mark_failed(
                job.job_id,
                result.get("error", "Unknown error"),
            )

    except Exception as e:
        logger.error(f"Job processing failed: {e}")
        await queue_service.mark_failed(job.job_id, str(e))


# ═════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════

# ── Auth ─────────────────────────────────────────────────────────────

@app.post("/auth/guest", response_model=RegisterGuestResponse)
async def register_guest(req: RegisterGuestRequest):
    """Register a new guest or sync an existing one."""
    from app.db.mongodb import get_collection
    from datetime import datetime

    col = await get_collection("users")

    if req.user_id:
        # Existing user — update last_active
        existing = await col.find_one({"user_id": req.user_id})
        if existing:
            await col.update_one(
                {"user_id": req.user_id},
                {"$set": {"last_active": datetime.utcnow().isoformat()}},
            )
            return RegisterGuestResponse(
                user_id=existing["user_id"],
                display_name=existing.get("display_name", "Guest"),
                is_new=False,
            )

    # New user
    user = GuestUser(display_name=req.display_name or "Guest")
    await col.insert_one(user.model_dump())

    return RegisterGuestResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        is_new=True,
    )


# ── Prepare Repo ─────────────────────────────────────────────────────

@app.post("/prepare-repo", response_model=PrepareRepoResponse)
async def prepare_repo(req: PrepareRepoRequest):
    """
    Step 1: Clone the repo and return the full file tree for user selection.
    Does NOT start the agent pipeline — just scans the repo fast.
    """
    import asyncio
    from app.services.github_service import clone_repo, get_file_tree
    from app.services.github_service import collect_files as _collect_all
    from app.services.repo_session_store import create_session
    from app.utils.helpers import extract_repo_name
    from app.config import DEFAULT_INCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS
    from pathlib import Path

    try:
        repo_name = extract_repo_name(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Clone in a thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        repo_path = await loop.run_in_executor(None, clone_repo, req.repo_url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to clone repository: {str(e)[:200]}")

    # Collect ALL files for the explorer UI.
    # We pass a broad set of common extensions instead of "*" because
    # fnmatch("src/app.py", "*") is False on most platforms (doesn't cross slashes).
    # Passing None for include_patterns makes collect_files use DEFAULT_INCLUDE_PATTERNS,
    # but we want to show EVERYTHING — so we skip pattern filtering entirely.
    all_files_raw = _collect_all(
        repo_path,
        include_patterns=None,   # None → uses DEFAULT_INCLUDE_PATTERNS (broad enough)
        exclude_patterns=[".git/*", ".git/**", "*.ico", "*.png", "*.jpg",
                          "*.gif", "*.woff", "*.woff2", "*.ttf", "*.eot",
                          "*.mp4", "*.mp3", "*.wav"],
    )
    all_file_paths = [f["relative_path"] for f in all_files_raw]

    # Determine stats
    languages_seen = set()
    total_size = 0
    for f in all_files_raw:
        languages_seen.add(f["language"])
        total_size += f["size"]

    stats = {
        "total_files": len(all_files_raw),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "languages": sorted(list(languages_seen)),
    }

    file_tree = get_file_tree(repo_path)
    session_id = create_session(repo_path, req.repo_url, repo_name, all_files_raw, file_tree)

    return PrepareRepoResponse(
        session_id=session_id,
        repo_name=repo_name,
        file_tree=file_tree,
        all_files=all_file_paths,
        stats=stats,
        default_include=DEFAULT_INCLUDE_PATTERNS,
        default_exclude=DEFAULT_EXCLUDE_PATTERNS,
    )


# ── Doc Generation ───────────────────────────────────────────────────

@app.post("/generate-docs", response_model=GenerateDocsResponse)
async def generate_docs(req: GenerateDocsRequest):
    """Queue documentation generation for a GitHub repository."""
    try:
        repo_name = extract_repo_name(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job = QueueJob(
        user_id=req.user_id,
        repo_url=req.repo_url,
        repo_name=repo_name,
        session_id=req.session_id,
        selected_files=req.selected_files,
        include_patterns=req.include_patterns,
        exclude_patterns=req.exclude_patterns,
    )

    queued_job = await queue_service.enqueue(job)

    # Get queue position
    status = await queue_service.get_status()
    position = 0
    for i, q_job in enumerate(status.queue):
        if q_job.job_id == queued_job.job_id:
            position = i + 1
            break

    return GenerateDocsResponse(
        success=True,
        job_id=queued_job.job_id,
        message=f"Documentation generation {'started' if position == 0 else 'queued'} for {repo_name}",
        queue_position=position,
        estimated_wait_seconds=position * 180,
    )


# ── Queue Status ─────────────────────────────────────────────────────

@app.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current queue status for the landing page."""
    return await queue_service.get_status()


@app.get("/queue/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    job = await queue_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/queue/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a queued or stuck job."""
    success = await queue_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already completed")
    return {"success": True, "message": f"Job {job_id} cancelled"}


# ── WebSocket Progress ───────────────────────────────────────────────

@app.websocket("/ws/progress/{job_id}")
async def ws_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job progress updates."""
    await websocket.accept()
    queue_service.register_ws(job_id, websocket)

    try:
        # Send current status immediately
        job = await queue_service.get_job(job_id)
        if job:
            await websocket.send_json(job.model_dump())

        # Keep alive until client disconnects
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        queue_service.unregister_ws(job_id, websocket)


# ── Docs Retrieval ───────────────────────────────────────────────────

@app.get("/docs")
async def list_docs(skip: int = Query(0, ge=0), limit: int = Query(16, gt=0, le=50)):
    """List all generated documentation sets."""
    from app.db.mongodb import get_collection

    col = await get_collection("docs")
    total = await col.count_documents({})
    cursor = col.find(
        {},
        {
            "repo_name": 1, "repo_url": 1, "generated_at": 1,
            "stats": 1, "meta.stats": 1, "_id": 0,
        },
    ).sort("generated_at", -1).skip(skip).limit(limit)

    docs = []
    async for doc in cursor:
        stats = doc.get("stats", doc.get("meta", {}).get("stats", {}))
        docs.append(DocListItem(
            repo_name=doc.get("repo_name", ""),
            repo_url=doc.get("repo_url", ""),
            generated_at=doc.get("generated_at", ""),
            page_count=stats.get("pages_generated", 0),
            languages=stats.get("languages", []),
        ))

    return {"docs": docs, "total": total, "skip": skip, "limit": limit}


@app.get("/docs/{owner}/{repo}")
async def get_doc_meta(owner: str, repo: str):
    """Get documentation metadata and navigation for a repo."""
    from app.db.mongodb import get_collection

    repo_name = f"{owner}/{repo}"
    col = await get_collection("docs")
    doc = await col.find_one(
        {"repo_name": repo_name},
        {"pages.content_md": 0},  # Exclude page content for meta-only
    )

    if not doc:
        raise HTTPException(status_code=404, detail=f"No docs found for {repo_name}")

    return {
        "repo_name": doc.get("repo_name"),
        "repo_url": doc.get("repo_url"),
        "generated_at": doc.get("generated_at"),
        "meta": doc.get("meta", {}),
        "stats": doc.get("stats", {}),
        "page_slugs": [p["slug"] for p in doc.get("pages", [])],
    }


@app.get("/docs/{owner}/{repo}/{slug:path}")
async def get_doc_page(owner: str, repo: str, slug: str):
    """Get a specific documentation page by slug."""
    from app.db.mongodb import get_collection

    repo_name = f"{owner}/{repo}"
    col = await get_collection("docs")
    doc = await col.find_one({"repo_name": repo_name})

    if not doc:
        raise HTTPException(status_code=404, detail=f"No docs found for {repo_name}")

    # Find the page
    target_slug = slug.strip("/")
    for page in doc.get("pages", []):
        if page["slug"].strip("/") == target_slug:
            return DocPageResponse(
                page=page,
                meta=doc.get("meta", {}),
                repo_name=repo_name,
            )

    raise HTTPException(status_code=404, detail=f"Page '{slug}' not found")


# ── Chat ─────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Chat with a repo's codebase using RAG."""
    return await chat_with_repo(req)


@app.get("/chat/sessions")
async def list_chat_sessions(user_id: str = Query(...)):
    """List chat sessions for a user."""
    sessions = await get_chat_sessions(user_id)
    return {"sessions": sessions}


# ── Repo Finder ──────────────────────────────────────────────────────

@app.post("/find-repos", response_model=RepoFinderResponse)
async def find_repos_endpoint(req: RepoFinderRequest):
    """Find repositories to contribute to based on preferences."""
    return await find_repos(req)


# ── Health ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.db.qdrant import get_qdrant

    health = {
        "status": "healthy",
        "services": {
            "api": "ok",
            "mongodb": "unknown",
            "qdrant": "unknown",
        },
    }

    # Check MongoDB
    try:
        db = await get_db()
        await db.command("ping")
        health["services"]["mongodb"] = "ok"
    except Exception as e:
        health["services"]["mongodb"] = f"error: {str(e)[:50]}"
        health["status"] = "degraded"

    # Check Qdrant
    try:
        client = get_qdrant()
        client.get_collections()
        health["services"]["qdrant"] = "ok"
    except Exception as e:
        health["services"]["qdrant"] = f"error: {str(e)[:50]}"
        health["status"] = "degraded"

    return health


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "EasyGit API",
        "version": "1.0.0",
        "description": "Generate modern documentation for any GitHub repository",
        "endpoints": {
            "auth": "POST /auth/guest",
            "generate": "POST /generate-docs",
            "queue": "GET /queue/status",
            "docs_list": "GET /docs",
            "docs_meta": "GET /docs/{owner}/{repo}",
            "docs_page": "GET /docs/{owner}/{repo}/{slug}",
            "chat": "POST /chat",
            "find_repos": "POST /find-repos",
            "health": "GET /health",
            "ws_progress": "WS /ws/progress/{job_id}",
        },
    }
