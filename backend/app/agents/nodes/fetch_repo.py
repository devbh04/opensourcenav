"""
Node: Fetch Repository — clones the repo and collects files.
Supports session reuse (from /prepare-repo) and user-defined file selection.
"""
import logging
from app.services.github_service import clone_repo, collect_files, get_file_tree
from app.services.repo_session_store import get_session
from app.utils.helpers import extract_repo_name

logger = logging.getLogger(__name__)


def fetch_repo(state: dict) -> dict:
    """
    Clone the repository and collect all matching files.

    Strategy:
    1. If session_id is present → reuse the clone AND the pre-scanned file list
       from the session store (avoids re-scanning with different patterns).
    2. If selected_files is present → filter the full file list down to only
       the paths the user explicitly chose in the UI.
    3. If no session → fresh clone + collect with user-supplied patterns.
    4. If neither session nor selected_files → collect with default patterns.

    Reads from state: repo_url, session_id, selected_files, include_patterns, exclude_patterns
    Writes to state: repo_path, files, file_tree, repo_name
    """
    repo_url = state["repo_url"]
    session_id = state.get("session_id", "")
    selected_files = state.get("selected_files", [])
    include_patterns = state.get("include_patterns") or None
    exclude_patterns = state.get("exclude_patterns") or None

    # ── Try to reuse the session clone ───────────────────────────────────
    session = get_session(session_id) if session_id else None

    if session:
        logger.info(f"[fetch_repo] Reusing session clone for {session['repo_name']}")
        repo_path = session["repo_path"]
        repo_name = session["repo_name"]

        if selected_files:
            # The session already has ALL files scanned (no pattern filtering).
            # We just filter by the paths the user selected in the UI.
            selected_set = set(selected_files)
            all_session_files = session.get("all_files", [])

            files = [f for f in all_session_files if f["relative_path"] in selected_set]

            # Safety: if session files are somehow empty (old session format),
            # fall back to a fresh collect with a wildcard include + the user selection.
            if not files and selected_set:
                logger.warning("[fetch_repo] Session all_files empty — falling back to collect + filter")
                all_collected = collect_files(
                    repo_path,
                    include_patterns=["*"],
                    exclude_patterns=[".git/*", ".git/**"],
                )
                files = [f for f in all_collected if f["relative_path"] in selected_set]

            logger.info(
                f"[fetch_repo] User selected {len(files)}/{len(selected_files)} files "
                f"from session (total scanned: {len(all_session_files)})"
            )
        else:
            # No explicit selection: collect with user-supplied patterns (or defaults)
            files = collect_files(
                repo_path,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )
            logger.info(f"[fetch_repo] No file selection — using {len(files)} pattern-filtered files")

    else:
        # ── Fresh clone ───────────────────────────────────────────────────
        logger.info(f"[fetch_repo] No session — cloning {repo_url}")
        repo_name = extract_repo_name(repo_url)
        repo_path = clone_repo(repo_url)

        files = collect_files(
            repo_path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

        if selected_files:
            selected_set = set(selected_files)
            files = [f for f in files if f["relative_path"] in selected_set]
            logger.info(f"[fetch_repo] Filtered to {len(files)} user-selected files")

    file_tree = get_file_tree(repo_path)
    logger.info(f"[fetch_repo] Final: {len(files)} files to process, {len(file_tree)} top-level tree items")

    return {
        **state,
        "repo_path": repo_path,
        "repo_name": repo_name,
        "files": files,
        "file_tree": file_tree,
    }
