"""
Smart code chunker — splits source files into meaningful chunks
for vector embedding, respecting function/class boundaries.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Target chunk size in characters (~500 tokens ≈ 2000 chars)
TARGET_CHUNK_SIZE = 2000
MAX_CHUNK_SIZE = 4000
MIN_CHUNK_SIZE = 200


def chunk_file(file_info: dict) -> list[dict]:
    """
    Split a single file into semantically meaningful chunks.

    Args:
        file_info: dict with keys: relative_path, content, language, extension

    Returns:
        List of chunk dicts with: content, file_path, chunk_index, start_line, end_line, language
    """
    content = file_info.get("content", "")
    rel_path = file_info.get("relative_path", "")
    language = file_info.get("language", "text")

    if not content.strip():
        return []

    lines = content.split("\n")

    # For small files, return as single chunk
    if len(content) <= TARGET_CHUNK_SIZE:
        return [{
            "content": content,
            "file_path": rel_path,
            "chunk_index": 0,
            "start_line": 1,
            "end_line": len(lines),
            "language": language,
        }]

    # Try boundary-aware chunking for code files
    if language in ("python", "javascript", "typescript", "jsx", "tsx", "java", "go", "rust", "cpp", "c", "ruby", "php", "kotlin", "swift"):
        chunks = _chunk_by_boundaries(lines, rel_path, language)
        if chunks:
            return chunks

    # Fall back to line-based chunking
    return _chunk_by_lines(lines, rel_path, language)


def _chunk_by_boundaries(lines: list[str], rel_path: str, language: str) -> list[dict]:
    """
    Split code at function/class boundaries.
    Returns empty list if no boundaries found (falls back to line-based).
    """
    boundary_pattern = _get_boundary_pattern(language)
    if not boundary_pattern:
        return []

    boundaries = []
    for i, line in enumerate(lines):
        if re.match(boundary_pattern, line):
            boundaries.append(i)

    if len(boundaries) < 2:
        return []

    # Add start and end boundaries
    if boundaries[0] != 0:
        boundaries.insert(0, 0)
    if boundaries[-1] != len(lines) - 1:
        boundaries.append(len(lines))

    chunks = []
    for idx in range(len(boundaries) - 1):
        start = boundaries[idx]
        end = boundaries[idx + 1]
        chunk_lines = lines[start:end]
        chunk_content = "\n".join(chunk_lines)

        # If chunk is too large, split further
        if len(chunk_content) > MAX_CHUNK_SIZE:
            sub_chunks = _chunk_by_lines(chunk_lines, rel_path, language, base_line=start)
            for sc in sub_chunks:
                sc["chunk_index"] = len(chunks)
                chunks.append(sc)
        elif len(chunk_content) >= MIN_CHUNK_SIZE:
            chunks.append({
                "content": chunk_content,
                "file_path": rel_path,
                "chunk_index": len(chunks),
                "start_line": start + 1,
                "end_line": end,
                "language": language,
            })

    return chunks


def _chunk_by_lines(
    lines: list[str],
    rel_path: str,
    language: str,
    base_line: int = 0,
) -> list[dict]:
    """Simple line-based chunking at ~TARGET_CHUNK_SIZE boundaries."""
    chunks = []
    current_lines = []
    current_size = 0
    start_line = base_line

    for i, line in enumerate(lines):
        current_lines.append(line)
        current_size += len(line) + 1  # +1 for newline

        if current_size >= TARGET_CHUNK_SIZE:
            chunk_content = "\n".join(current_lines)
            if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "content": chunk_content,
                    "file_path": rel_path,
                    "chunk_index": len(chunks),
                    "start_line": start_line + 1,
                    "end_line": base_line + i + 1,
                    "language": language,
                })
            current_lines = []
            current_size = 0
            start_line = base_line + i + 1

    # Remaining lines
    if current_lines:
        chunk_content = "\n".join(current_lines)
        if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
            chunks.append({
                "content": chunk_content,
                "file_path": rel_path,
                "chunk_index": len(chunks),
                "start_line": start_line + 1,
                "end_line": base_line + len(lines),
                "language": language,
            })

    return chunks


def _get_boundary_pattern(language: str) -> str | None:
    """Get regex pattern for function/class boundaries by language."""
    patterns = {
        "python": r"^(class\s|def\s|async\s+def\s)",
        "javascript": r"^(function\s|class\s|const\s+\w+\s*=\s*(async\s+)?\(|export\s+(default\s+)?function|export\s+(default\s+)?class)",
        "typescript": r"^(function\s|class\s|interface\s|type\s|const\s+\w+\s*=\s*(async\s+)?\(|export\s+(default\s+)?function|export\s+(default\s+)?class)",
        "jsx": r"^(function\s|class\s|const\s+\w+\s*=\s*(async\s+)?\(|export\s+(default\s+)?function)",
        "tsx": r"^(function\s|class\s|interface\s|const\s+\w+\s*=\s*(async\s+)?\(|export\s+(default\s+)?function)",
        "java": r"^(\s*(public|private|protected|static)\s+.*(class|interface|enum|void|int|String|boolean|List))",
        "go": r"^(func\s|type\s+\w+\s+(struct|interface))",
        "rust": r"^(fn\s|pub\s+fn\s|struct\s|pub\s+struct\s|impl\s|trait\s|pub\s+trait\s|enum\s|pub\s+enum\s|mod\s)",
        "cpp": r"^(class\s|struct\s|void\s|int\s|bool\s|auto\s|template\s|namespace\s)",
        "c": r"^(void\s|int\s|char\s|struct\s|typedef\s|static\s)",
        "ruby": r"^(class\s|module\s|def\s)",
        "php": r"^(class\s|function\s|public\s+function|private\s+function|protected\s+function)",
        "kotlin": r"^(fun\s|class\s|object\s|interface\s|data\s+class)",
        "swift": r"^(func\s|class\s|struct\s|enum\s|protocol\s|extension\s)",
    }
    return patterns.get(language)


def chunk_files(files: list[dict]) -> list[dict]:
    """Chunk all files and return a flat list of chunks."""
    all_chunks = []
    for f in files:
        chunks = chunk_file(f)
        all_chunks.extend(chunks)
    logger.info(f"Generated {len(all_chunks)} chunks from {len(files)} files")
    return all_chunks
