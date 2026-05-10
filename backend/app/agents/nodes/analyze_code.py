"""
Node: Analyze Code — deep per-file analysis to identify abstractions,
patterns, key functions, and how modules relate to each other.
"""
import json
import logging
from app.services.llm_service import get_llm
from app.utils.json_extract import extract_json

logger = logging.getLogger(__name__)


def analyze_code(state: dict) -> dict:
    """
    Perform deep code analysis across files to identify key abstractions,
    patterns, and module relationships for documentation.

    Reads from state: files, repo_name
    Writes to state: code_analysis (list of analysis results)
    """
    files = state["files"]
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[analyze_code] Analyzing code in {len(files)} files")

    llm = get_llm(temperature=0.1)

    # Filter to code files only (skip config, assets, etc.)
    code_files = [
        f for f in files
        if f.get("language") not in ("text", "markdown", "json", "yaml", "toml")
        and f.get("size", 0) > 100
    ]

    # If too many files, prioritize by size and importance
    if len(code_files) > 50:
        # Score files by likely importance
        def importance_score(f):
            score = 0
            rp = f["relative_path"].lower()
            # Main/index files are important
            if any(kw in rp for kw in ("main", "index", "app", "server", "api", "routes")):
                score += 10
            # Root-level files are more important
            if "/" not in f["relative_path"]:
                score += 5
            # Larger files likely have more logic
            score += min(f.get("size", 0) / 1000, 10)
            # src/ directory files
            if rp.startswith("src/"):
                score += 3
            return score

        code_files.sort(key=importance_score, reverse=True)
        code_files = code_files[:50]

    # Build a consolidated view for the LLM
    files_summary = []
    for f in code_files:
        content_preview = f["content"][:4000]  # Limit per file
        files_summary.append({
            "path": f["relative_path"],
            "language": f["language"],
            "size": f["size"],
            "content_preview": content_preview,
        })

    # Process in batches to stay within token limits
    batch_size = 10
    all_analysis = []

    for i in range(0, len(files_summary), batch_size):
        batch = files_summary[i : i + batch_size]
        batch_text = ""
        for fs in batch:
            batch_text += f"\n--- FILE: {fs['path']} ({fs['language']}) ---\n"
            batch_text += fs["content_preview"]
            batch_text += "\n"

        prompt = f"""Analyze these source code files from the repository "{repo_name}".

For each file, identify:
1. What the file does (purpose)
2. Key classes, functions, or exports
3. Dependencies and imports
4. Design patterns used
5. Important code snippets that should appear in documentation

{batch_text}

Return a JSON array where each element represents a file:
[
  {{
    "file_path": "path/to/file",
    "purpose": "What this file does in 1-2 sentences",
    "key_abstractions": [
      {{
        "name": "ClassName or functionName",
        "type": "class | function | component | middleware | hook | service | model | route | util",
        "description": "What it does",
        "importance": "high | medium | low"
      }}
    ],
    "imports_from": ["list of internal modules this file imports"],
    "exports": ["list of exported names"],
    "patterns": ["list of design patterns, e.g. singleton, factory, observer"],
    "doc_worthy_snippets": [
      {{
        "code": "actual code snippet (max 15 lines)",
        "explanation": "why this snippet is important for docs"
      }}
    ]
  }}
]

Return ONLY valid JSON, no markdown fences."""

        try:
            response = llm.invoke(prompt)
            batch_analysis = extract_json(response.content)
            if batch_analysis is None:
                raise ValueError("No valid JSON found")
            if isinstance(batch_analysis, list):
                all_analysis.extend(batch_analysis)
            else:
                all_analysis.append(batch_analysis)
        except Exception as e:
            logger.warning(f"[analyze_code] Batch {i // batch_size + 1} failed: {e}")
            # Fallback: basic analysis without LLM
            for fs in batch:
                all_analysis.append({
                    "file_path": fs["path"],
                    "purpose": f"Source file ({fs['language']})",
                    "key_abstractions": [],
                    "imports_from": [],
                    "exports": [],
                    "patterns": [],
                    "doc_worthy_snippets": [],
                })

    logger.info(f"[analyze_code] Analyzed {len(all_analysis)} files")

    return {**state, "code_analysis": all_analysis}
