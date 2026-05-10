"""
Repo Session Store — in-memory cache for cloned repos between prepare and generate steps.

A session is created when a user calls /prepare-repo and consumed when they
call /generate-docs. Sessions expire after 30 minutes.
"""
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SESSION_TTL_MINUTES = 30

_sessions: dict[str, dict] = {}


def create_session(
    repo_path: str,
    repo_url: str,
    repo_name: str,
    all_files: list[dict],
    file_tree: list[dict],
) -> str:
    """Create a new session and return its ID."""
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "repo_path": repo_path,
        "repo_url": repo_url,
        "repo_name": repo_name,
        "all_files": all_files,
        "file_tree": file_tree,
        "created_at": datetime.utcnow(),
    }
    logger.info(f"[repo_session] Created session {sid[:8]}... for {repo_name}")
    return sid


def get_session(sid: str) -> dict | None:
    """Retrieve a session by ID. Returns None if expired or not found."""
    session = _sessions.get(sid)
    if not session:
        return None

    age = datetime.utcnow() - session["created_at"]
    if age > timedelta(minutes=SESSION_TTL_MINUTES):
        logger.info(f"[repo_session] Session {sid[:8]}... expired — removing")
        del _sessions[sid]
        return None

    return session


def cleanup_expired() -> int:
    """Remove all expired sessions. Returns count of removed sessions."""
    now = datetime.utcnow()
    expired = [
        sid for sid, data in _sessions.items()
        if now - data["created_at"] > timedelta(minutes=SESSION_TTL_MINUTES)
    ]
    for sid in expired:
        del _sessions[sid]

    if expired:
        logger.info(f"[repo_session] Cleaned up {len(expired)} expired sessions")

    return len(expired)


def delete_session(sid: str) -> None:
    """Explicitly delete a session (e.g. after generate-docs consumes it)."""
    if sid in _sessions:
        del _sessions[sid]
        logger.info(f"[repo_session] Deleted session {sid[:8]}...")
