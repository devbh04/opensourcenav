"""
Node: Analyze Structure — detects tech stack, directory layout, and project metadata.
"""
import json
import logging
from collections import Counter
from app.services.llm_service import get_llm
from app.utils.json_extract import extract_json

logger = logging.getLogger(__name__)


def analyze_structure(state: dict) -> dict:
    """
    Analyze the repository structure: tech stack, frameworks, build system, etc.

    Reads from state: files, file_tree, repo_name
    Writes to state: structure_analysis
    """
    files = state["files"]
    file_tree = state["file_tree"]
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[analyze_structure] Analyzing {len(files)} files")

    # ── Static analysis ──────────────────────────────────────────────

    # Language distribution
    lang_counter = Counter(f["language"] for f in files if f.get("language"))
    languages = [lang for lang, _ in lang_counter.most_common(10)]
    primary_language = languages[0] if languages else "unknown"

    # File extension distribution
    ext_counter = Counter(f["extension"] for f in files if f.get("extension"))

    # Key config files detection
    config_files = []
    config_names = {
        "package.json", "requirements.txt", "setup.py", "pyproject.toml",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
        "Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".env", ".env.example", "tsconfig.json", "next.config.js", "next.config.ts",
        "vite.config.ts", "webpack.config.js", "jest.config.js",
        "README.md", "CONTRIBUTING.md", "LICENSE",
    }
    for f in files:
        if f["relative_path"].split("/")[-1] in config_names:
            config_files.append(f["relative_path"])

    # Directory structure
    top_dirs = [item["name"] for item in file_tree if item.get("type") == "dir"]

    # Total stats
    total_lines = sum(f["content"].count("\n") + 1 for f in files)
    total_size = sum(f["size"] for f in files)

    # ── LLM analysis for deeper insights ─────────────────────────────

    # Build a summary for the LLM
    file_list_summary = "\n".join(
        f"  {f['relative_path']} ({f['language']}, {f['size']}B)"
        for f in files[:80]  # Limit to avoid token explosion
    )

    config_contents = {}
    for f in files:
        fname = f["relative_path"].split("/")[-1]
        if fname in ("package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "README.md"):
            config_contents[f["relative_path"]] = f["content"][:3000]

    llm = get_llm(temperature=0.1)

    prompt = f"""Analyze this repository structure and provide a JSON response.

Repository: {repo_name}
Primary Language: {primary_language}
Languages: {', '.join(languages)}
Top directories: {', '.join(top_dirs)}
Total files: {len(files)}

File listing (first 80):
{file_list_summary}

Config file contents:
{json.dumps(config_contents, indent=2)[:5000]}

Return a JSON object with these fields:
{{
  "project_type": "web_app | cli_tool | library | api | mobile_app | ml_project | other",
  "frameworks": ["list of frameworks detected, e.g. React, FastAPI, Django"],
  "build_system": "npm | pip | cargo | gradle | maven | make | other",
  "testing_framework": "jest | pytest | go_test | junit | none_detected",
  "description": "1-2 sentence description of what this project does",
  "key_features": ["list of 3-5 main features/capabilities"],
  "architecture_pattern": "monolith | microservices | mvc | component_based | modular | other",
  "entry_points": ["list of main entry files, e.g. src/index.ts, main.py"]
}}

Return ONLY valid JSON, no markdown fences."""

    try:
        response = llm.invoke(prompt)
        llm_analysis = extract_json(response.content)
        if llm_analysis is None:
            raise ValueError("No valid JSON found in response")
    except Exception as e:
        logger.warning(f"[analyze_structure] LLM analysis failed: {e}")
        llm_analysis = {
            "project_type": "other",
            "frameworks": [],
            "build_system": "unknown",
            "testing_framework": "none_detected",
            "description": f"A {primary_language} project",
            "key_features": [],
            "architecture_pattern": "other",
            "entry_points": [],
        }

    structure_analysis = {
        "repo_name": repo_name,
        "primary_language": primary_language,
        "languages": languages,
        "language_distribution": dict(lang_counter),
        "extension_distribution": dict(ext_counter),
        "config_files": config_files,
        "top_directories": top_dirs,
        "total_files": len(files),
        "total_lines": total_lines,
        "total_size_bytes": total_size,
        **llm_analysis,
    }

    logger.info(f"[analyze_structure] Complete — {primary_language} {llm_analysis.get('project_type', 'project')}")

    return {**state, "structure_analysis": structure_analysis}
