"""
Node: Generate Diagrams — creates Mermaid chart definitions for the docs.
"""
import json
import logging
from app.services.llm_service import get_llm
from app.utils.json_extract import extract_json

logger = logging.getLogger(__name__)


def generate_diagrams(state: dict) -> dict:
    """
    Generate Mermaid diagram definitions.

    Reads: structure_analysis, code_analysis, repo_name
    Writes: diagrams (list of diagram defs)
    """
    structure = state.get("structure_analysis", {})
    code_analysis = state.get("code_analysis", [])
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[generate_diagrams] Creating diagrams for {repo_name}")

    llm = get_llm(model="gemini-3.1-pro-preview", temperature=0.2)

    modules = {}
    for ca in code_analysis:
        fp = ca["file_path"]
        module = fp.split("/")[0] if "/" in fp else "root"
        if module not in modules:
            modules[module] = {"files": [], "imports": []}
        modules[module]["files"].append(fp)
        modules[module]["imports"].extend(ca.get("imports_from", []))

    prompt = f"""Create 4 Mermaid diagrams for "{repo_name}" docs.

Type: {structure.get('project_type', 'unknown')}
Frameworks: {structure.get('frameworks', [])}
Modules: {json.dumps(list(modules.keys()))}

Return JSON array:
[{{"title":"...","type":"flowchart","description":"...","mermaid_code":"graph TD\\n A-->B"}}]

Use valid Mermaid. Quote labels with special chars. Max 12 nodes.
Return ONLY valid JSON."""

    try:
        resp = llm.invoke(prompt)
        diagrams = extract_json(resp.content)
        if diagrams is None:
            raise ValueError("No valid JSON found")
    except Exception as e:
        logger.warning(f"[generate_diagrams] Failed: {e}")
        diagrams = [{"title": "Architecture", "type": "flowchart",
                      "description": f"{repo_name} architecture",
                      "mermaid_code": f"graph TD\n  A[\"{repo_name}\"]-->B[\"Core\"]"}]

    logger.info(f"[generate_diagrams] Generated {len(diagrams)} diagrams")
    return {**state, "diagrams": diagrams}
