"""
Miscellaneous helpers used across the backend.
"""
import re
import hashlib


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max_len with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def content_hash(content: str) -> str:
    """SHA-256 hash of content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def extract_repo_name(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    url = url.strip().rstrip("/").replace(".git", "")
    match = re.search(r"github\.com/([^/]+/[^/]+)", url)
    if match:
        return match.group(1)
    # Might already be owner/repo
    if re.match(r"^[^/]+/[^/]+$", url):
        return url
    raise ValueError(f"Cannot extract repo name from: {url}")


def count_lines(content: str) -> int:
    """Count non-empty lines in content."""
    return sum(1 for line in content.split("\n") if line.strip())


def estimate_tokens(text: str) -> int:
    """Rough token estimation (~4 chars per token)."""
    return len(text) // 4
