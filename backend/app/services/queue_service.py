"""
Queue service — manages a global FIFO job queue.

Rules:
  1. Only ONE job processes at a time (globally).
  2. If a user submits while their job is running, it queues behind.
  3. Landing page shows current job + queue positions + ETAs.
  4. State is persisted in MongoDB so it survives restarts.
  5. On startup, stale "processing" jobs are recovered (re-queued).
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, Awaitable

from app.db.mongodb import get_collection
from app.models.queue import (
    QueueJob,
    QueueStatusResponse,
    JobProgressUpdate,
    QUEUE_STATUS_QUEUED,
    QUEUE_STATUS_PROCESSING,
    QUEUE_STATUS_COMPLETED,
    QUEUE_STATUS_FAILED,
)

logger = logging.getLogger(__name__)


class QueueService:
    """Global job queue with single-worker processing."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._processing = False
        self._current_job: Optional[QueueJob] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._job_handler: Optional[Callable[..., Awaitable]] = None
        # WebSocket connections for progress updates
        self._ws_connections: dict[str, list] = {}  # job_id -> [websocket, ...]

    def set_job_handler(self, handler: Callable[..., Awaitable]) -> None:
        """Set the async function that processes jobs (called by main.py on startup)."""
        self._job_handler = handler

    async def recover_stale_jobs(self) -> None:
        """
        Recover jobs that were left as "processing" from a previous server crash.
        These are re-queued so the worker can pick them up again.
        """
        try:
            col = await get_collection("queue")
            result = await col.update_many(
                {"status": QUEUE_STATUS_PROCESSING},
                {"$set": {
                    "status": QUEUE_STATUS_QUEUED,
                    "progress": 0.0,
                    "current_phase": "Re-queued after server restart",
                    "error": None,
                }},
            )
            if result.modified_count > 0:
                logger.warning(
                    f"Recovered {result.modified_count} stale job(s) stuck in 'processing' state"
                )
                # Start the worker since we have jobs now
                self._start_worker()
        except Exception as e:
            logger.warning(f"Failed to recover stale jobs: {e}")

    async def enqueue(self, job: QueueJob) -> QueueJob:
        """
        Add a job to the queue. Starts processing if idle.

        Returns the job with queue position info.
        """
        col = await get_collection("queue")

        # Check if this repo is already being processed or queued
        existing = await col.find_one({
            "repo_url": job.repo_url,
            "status": {"$in": [QUEUE_STATUS_QUEUED, QUEUE_STATUS_PROCESSING]},
        })
        if existing:
            logger.info(f"Job for {job.repo_url} already in queue/processing")
            return QueueJob(**{k: v for k, v in existing.items() if k != "_id"})

        # Persist to MongoDB
        await col.insert_one(job.model_dump())
        logger.info(f"Job enqueued: {job.job_id} for {job.repo_url}")

        # Calculate queue position
        queued_count = await col.count_documents({"status": QUEUE_STATUS_QUEUED})
        job.estimated_duration_seconds = queued_count * 180  # rough estimate

        # Start worker if not running
        if not self._processing:
            self._start_worker()

        return job

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or stuck job — removes it from the queue."""
        col = await get_collection("queue")
        result = await col.update_one(
            {"job_id": job_id, "status": {"$in": [QUEUE_STATUS_QUEUED, QUEUE_STATUS_PROCESSING]}},
            {"$set": {
                "status": QUEUE_STATUS_FAILED,
                "error": "Cancelled by user",
                "completed_at": datetime.utcnow().isoformat(),
                "current_phase": "Cancelled",
            }},
        )
        if result.modified_count > 0:
            logger.info(f"Job {job_id} cancelled")
            return True
        return False

    async def get_status(self) -> QueueStatusResponse:
        """Get current queue status for the landing page."""
        col = await get_collection("queue")

        current = await col.find_one({"status": QUEUE_STATUS_PROCESSING})
        current_job = QueueJob(**{k: v for k, v in current.items() if k != "_id"}) if current else None

        queued_cursor = col.find({"status": QUEUE_STATUS_QUEUED}).sort("created_at", 1)
        queue = []
        async for doc in queued_cursor:
            queue.append(QueueJob(**{k: v for k, v in doc.items() if k != "_id"}))

        return QueueStatusResponse(
            current_job=current_job,
            queue=queue,
            total_in_queue=len(queue),
        )

    async def get_job(self, job_id: str) -> Optional[QueueJob]:
        """Get a specific job by ID."""
        col = await get_collection("queue")
        doc = await col.find_one({"job_id": job_id})
        if doc:
            return QueueJob(**{k: v for k, v in doc.items() if k != "_id"})
        return None

    async def get_recent_completed(self, limit: int = 10) -> list[QueueJob]:
        """Get recently completed jobs."""
        col = await get_collection("queue")
        cursor = col.find({"status": QUEUE_STATUS_COMPLETED}).sort("completed_at", -1).limit(limit)
        jobs = []
        async for doc in cursor:
            jobs.append(QueueJob(**{k: v for k, v in doc.items() if k != "_id"}))
        return jobs

    async def update_progress(
        self,
        job_id: str,
        progress: float,
        phase: str,
        status: str | None = None,
    ) -> None:
        """Update job progress — also pushes to WebSocket subscribers."""
        col = await get_collection("queue")

        update_data = {
            "progress": progress,
            "current_phase": phase,
        }
        if status:
            update_data["status"] = status
            if status == QUEUE_STATUS_COMPLETED:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            elif status == QUEUE_STATUS_FAILED:
                update_data["completed_at"] = datetime.utcnow().isoformat()

        await col.update_one({"job_id": job_id}, {"$set": update_data})

        # Push WebSocket update
        update = JobProgressUpdate(
            job_id=job_id,
            status=status or QUEUE_STATUS_PROCESSING,
            progress=progress,
            current_phase=phase,
        )
        await self._broadcast_progress(job_id, update)

    async def mark_failed(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        col = await get_collection("queue")
        await col.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": QUEUE_STATUS_FAILED,
                "error": error,
                "completed_at": datetime.utcnow().isoformat(),
                "current_phase": f"Failed: {error[:100]}",
            }},
        )
        update = JobProgressUpdate(
            job_id=job_id,
            status=QUEUE_STATUS_FAILED,
            progress=0.0,
            current_phase=f"Failed: {error[:100]}",
            error=error,
        )
        await self._broadcast_progress(job_id, update)

    # ── WebSocket Management ─────────────────────────────────────────

    def register_ws(self, job_id: str, ws) -> None:
        """Register a WebSocket connection for job updates."""
        if job_id not in self._ws_connections:
            self._ws_connections[job_id] = []
        self._ws_connections[job_id].append(ws)

    def unregister_ws(self, job_id: str, ws) -> None:
        """Unregister a WebSocket connection."""
        if job_id in self._ws_connections:
            self._ws_connections[job_id] = [
                w for w in self._ws_connections[job_id] if w is not ws
            ]

    async def _broadcast_progress(self, job_id: str, update: JobProgressUpdate) -> None:
        """Send progress update to all WebSocket subscribers."""
        if job_id not in self._ws_connections:
            return

        dead = []
        for ws in self._ws_connections[job_id]:
            try:
                await ws.send_json(update.model_dump())
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.unregister_ws(job_id, ws)

    # ── Worker Loop ──────────────────────────────────────────────────

    def _start_worker(self) -> None:
        """Start the background worker task."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Queue worker started")

    async def _worker_loop(self) -> None:
        """Process jobs one at a time from the queue."""
        while True:
            col = await get_collection("queue")

            # Find the next queued job (FIFO)
            next_doc = await col.find_one(
                {"status": QUEUE_STATUS_QUEUED},
                sort=[("created_at", 1)],
            )

            if not next_doc:
                self._processing = False
                logger.info("Queue empty, worker sleeping")
                break

            self._processing = True
            job = QueueJob(**{k: v for k, v in next_doc.items() if k != "_id"})
            self._current_job = job

            # Mark as processing
            await col.update_one(
                {"job_id": job.job_id},
                {"$set": {
                    "status": QUEUE_STATUS_PROCESSING,
                    "started_at": datetime.utcnow().isoformat(),
                    "current_phase": "Starting...",
                }},
            )

            logger.info(f"Processing job: {job.job_id} — {job.repo_url}")

            try:
                if self._job_handler:
                    await self._job_handler(job)
                else:
                    logger.error("No job handler set!")
                    await self.mark_failed(job.job_id, "No job handler configured")

            except Exception as e:
                logger.error(f"Job {job.job_id} failed: {e}")
                await self.mark_failed(job.job_id, str(e))

            self._current_job = None

        self._processing = False


# ── Singleton ────────────────────────────────────────────────────────
queue_service = QueueService()
