"""
GitHub service — repo cloning, file fetching, and API interactions.
"""
import os
import re
import shutil
import logging
import tempfile
import fnmatch
from pathlib import Path

import httpx
from git import Repo as GitRepo

from app.config import (
    GITHUB_TOKEN,
    CLONE_BASE_DIR,
    MAX_FILE_SIZE_BYTES,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_EXCLUDE_PATTERNS,
)

logger = logging.getLogger(__name__)


def parse_github_url(url: str) -> dict:
    """
    Parse a GitHub URL into owner and repo components.
    Handles: https://github.com/owner/repo, github.com/owner/repo, owner/repo
    """
    url = url.strip().rstrip("/").replace(".git", "")
    patterns = [
        r"(?:https?://)?github\.com/([^/]+)/([^/]+)",
        r"^([^/]+)/([^/]+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return {"owner": match.group(1), "repo": match.group(2)}
    raise ValueError(f"Invalid GitHub URL: {url}")


def clone_repo(repo_url: str) -> str:
    """
    Clone a GitHub repository to a local directory.

    Returns:
        Path to the cloned repository directory.
    """
    parsed = parse_github_url(repo_url)
    repo_name = f"{parsed['owner']}__{parsed['repo']}"
    clone_dir = os.path.join(CLONE_BASE_DIR, repo_name)

    # Remove existing clone
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    os.makedirs(CLONE_BASE_DIR, exist_ok=True)

    # Build clone URL with token for private repos
    clone_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}.git"
    if GITHUB_TOKEN:
        clone_url = f"https://{GITHUB_TOKEN}@github.com/{parsed['owner']}/{parsed['repo']}.git"

    logger.info(f"Cloning {parsed['owner']}/{parsed['repo']} → {clone_dir}")
    GitRepo.clone_from(clone_url, clone_dir, depth=1)
    logger.info(f"Clone complete: {clone_dir}")

    return clone_dir


def collect_files(
    repo_path: str,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    max_file_size: int | None = None,
) -> list[dict]:
    """
    Walk the cloned repo and collect file paths + contents.

    Returns:
        List of dicts: {path, relative_path, content, size, language}
    """
    include = include_patterns or DEFAULT_INCLUDE_PATTERNS
    exclude = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
    max_size = max_file_size or MAX_FILE_SIZE_BYTES

    files = []
    repo_root = Path(repo_path)

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue

        rel_path = str(path.relative_to(repo_root))

        # Check exclusions
        if _matches_any(rel_path, exclude):
            continue

        # Check inclusions
        if not _matches_any(rel_path, include) and not _matches_any(path.name, include):
            continue

        # Size check
        try:
            size = path.stat().st_size
            if size > max_size or size == 0:
                continue
        except OSError:
            continue

        # Read content
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        language = _detect_language(path.suffix)

        files.append({
            "path": str(path),
            "relative_path": rel_path,
            "content": content,
            "size": size,
            "language": language,
            "extension": path.suffix,
        })

    logger.info(f"Collected {len(files)} files from {repo_path}")
    return files


def get_file_tree(repo_path: str) -> list[dict]:
    """
    Generate a directory tree structure for the repo.

    Returns list of dicts: {name, path, type, children}
    The `path` field is the relative path from the repo root.
    """
    repo_root = Path(repo_path)
    tree = []

    SKIP_DIRS = {"node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build", ".next", ".tox", "egg-info"}

    for item in sorted(repo_root.iterdir()):
        if item.name.startswith("."):
            continue
        if item.name in SKIP_DIRS:
            continue

        rel = str(item.relative_to(repo_root))
        node = {"name": item.name, "path": rel, "type": "dir" if item.is_dir() else "file"}
        if item.is_dir():
            node["children"] = _build_tree(item, repo_root, SKIP_DIRS)
        tree.append(node)

    return tree


def _build_tree(path: Path, repo_root: Path, skip_dirs: set[str]) -> list[dict]:
    """Recursively build directory tree with NO depth limit."""
    children = []
    try:
        items = sorted(path.iterdir())
    except PermissionError:
        return []

    for item in items:
        if item.name.startswith("."):
            continue
        if item.name in skip_dirs:
            continue

        rel = str(item.relative_to(repo_root))
        node = {"name": item.name, "path": rel, "type": "dir" if item.is_dir() else "file"}
        if item.is_dir():
            node["children"] = _build_tree(item, repo_root, skip_dirs)
        children.append(node)

    return children


def _matches_any(path: str, patterns: list[str]) -> bool:
    """Check if a path matches any of the glob patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def _detect_language(suffix: str) -> str:
    """Map file extension to language name."""
    mapping = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "jsx", ".tsx": "tsx", ".java": "java",
        ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
        ".h": "c", ".rb": "ruby", ".php": "php", ".swift": "swift",
        ".kt": "kotlin", ".md": "markdown", ".yaml": "yaml",
        ".yml": "yaml", ".json": "json", ".toml": "toml",
        ".html": "html", ".css": "css", ".sh": "bash",
        ".sql": "sql", ".txt": "text",
    }
    return mapping.get(suffix.lower(), "text")


# ── GitHub API Helpers ───────────────────────────────────────────────

async def search_github_repos(
    query: str,
    sort: str = "stars",
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
) -> list[dict]:
    """Search GitHub repositories via REST API."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page,
        "page": page,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])


async def get_repo_info(owner: str, repo: str) -> dict:
    """Get repository metadata from GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def get_repo_issues(
    owner: str,
    repo: str,
    labels: str = "",
    state: str = "open",
    per_page: int = 30,
) -> list[dict]:
    """Get issues for a repository."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    params = {"state": state, "per_page": per_page}
    if labels:
        params["labels"] = labels

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


def cleanup_clone(repo_path: str) -> None:
    """Remove a cloned repository directory."""
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        logger.info(f"Cleaned up clone: {repo_path}")
