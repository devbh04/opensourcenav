"""
Node: Generate Components — creates per-module/component documentation pages.
"""
import json
import logging
from app.services.llm_service import get_llm
from app.utils.helpers import slugify

logger = logging.getLogger(__name__)


def generate_components(state: dict) -> dict:
    """
    Generate individual documentation pages for key components/modules.

    Reads from state: code_analysis, structure_analysis, files, repo_name
    Writes to state: component_docs (list of page dicts)
    """
    code_analysis = state.get("code_analysis", [])
    structure = state.get("structure_analysis", {})
    files = state.get("files", [])
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[generate_components] Creating component docs")

    llm = get_llm(temperature=0.3)

    # Group files by top-level directory / module
    modules = {}
    for ca in code_analysis:
        fp = ca.get("file_path", "")
        parts = fp.split("/")
        if len(parts) > 1:
            module_name = parts[0]
        else:
            module_name = "root"

        if module_name not in modules:
            modules[module_name] = {
                "name": module_name,
                "files": [],
                "abstractions": [],
            }
        modules[module_name]["files"].append(ca)
        for abs_item in ca.get("key_abstractions", []):
            modules[module_name]["abstractions"].append({
                **abs_item,
                "source_file": fp,
            })

    # Filter to modules with meaningful content
    significant_modules = {
        name: mod for name, mod in modules.items()
        if len(mod["abstractions"]) >= 1 or len(mod["files"]) >= 2
    }

    # Limit to 12 most important modules
    sorted_modules = sorted(
        significant_modules.items(),
        key=lambda x: len(x[1]["abstractions"]),
        reverse=True,
    )[:12]

    pages = []
    for idx, (module_name, module_data) in enumerate(sorted_modules):
        # Get actual file contents for this module
        module_files_content = {}
        for f in files:
            if f["relative_path"].startswith(module_name + "/") or (
                module_name == "root" and "/" not in f["relative_path"]
            ):
                module_files_content[f["relative_path"]] = f["content"][:3000]

        prompt = f"""Create a detailed documentation page for the "{module_name}" module/component in "{repo_name}".

Module files:
{json.dumps([fa["file_path"] for fa in module_data["files"]], indent=2)}

Key abstractions in this module:
{json.dumps(module_data["abstractions"][:15], indent=2)}

Source code samples (first 3000 chars each):
{json.dumps(dict(list(module_files_content.items())[:5]), indent=2)[:8000]}

Write the documentation page in Markdown:
- Frontmatter with title, description, order: {idx + 10}, category: "components", icon: "cube"
- "Overview" — what this module does and its role in the project
- "Key Classes / Functions" — document each major abstraction with:
  - Purpose
  - Parameters/arguments (in a table if applicable)
  - Return values
  - Usage example with code block
- "Configuration" — any config this module uses
- "Relationships" — how this module interacts with other parts of the codebase (use a Mermaid diagram if helpful)
- "Source Files" — table listing the source files in this module

Code examples should use the actual code from the repository. Use appropriate syntax highlighting.
Return ONLY the markdown content."""

        try:
            resp = llm.invoke(prompt)
            slug = slugify(module_name)
            pages.append({
                "slug": f"components/{slug}",
                "title": module_name.replace("_", " ").replace("-", " ").title(),
                "description": f"Documentation for the {module_name} module",
                "category": "components",
                "content_md": resp.content.strip(),
                "order": idx + 10,
                "icon": "cube",
            })
        except Exception as e:
            logger.warning(f"[generate_components] Failed for {module_name}: {e}")

    logger.info(f"[generate_components] Generated {len(pages)} component pages")

    return {**state, "component_docs": pages}
