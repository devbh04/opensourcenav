"""
Node: Generate API Reference — auto-generates reference docs from code analysis.
"""
import json
import logging
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def generate_api_ref(state: dict) -> dict:
    """
    Generate API reference documentation from code analysis.

    Reads from state: code_analysis, structure_analysis, files, repo_name
    Writes to state: api_ref_doc (single page dict)
    """
    code_analysis = state.get("code_analysis", [])
    structure = state.get("structure_analysis", {})
    files = state.get("files", [])
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[generate_api_ref] Generating API reference for {repo_name}")

    llm = get_llm(temperature=0.1)

    # Collect all high-importance abstractions
    all_abstractions = []
    for ca in code_analysis:
        for abs_item in ca.get("key_abstractions", []):
            all_abstractions.append({
                **abs_item,
                "source_file": ca["file_path"],
            })

    # Get doc-worthy snippets
    all_snippets = []
    for ca in code_analysis:
        for snippet in ca.get("doc_worthy_snippets", []):
            all_snippets.append({
                **snippet,
                "source_file": ca["file_path"],
            })

    prompt = f"""Create a comprehensive API/Module Reference documentation page for "{repo_name}".

Project type: {structure.get('project_type', 'unknown')}
Primary language: {structure.get('primary_language', 'unknown')}
Frameworks: {structure.get('frameworks', [])}

All abstractions (classes, functions, components, etc.):
{json.dumps(all_abstractions[:40], indent=2)}

Key code snippets:
{json.dumps(all_snippets[:20], indent=2)[:6000]}

Write the API reference in Markdown:
- Frontmatter with title "API Reference", description, order: 5, category: "root", icon: "code"
- Group by type (Classes, Functions, Components, etc.)
- For each entry include:
  - Name (as heading)
  - Source file path
  - Description
  - Signature/parameters in a table (Name | Type | Description)
  - Return value
  - Code example
- Use proper code blocks with syntax highlighting

Format it like professional API documentation (think: Stripe API docs style).
Return ONLY the markdown content."""

    try:
        resp = llm.invoke(prompt)
        api_ref_doc = {
            "slug": "api-reference",
            "title": "API Reference",
            "description": f"Complete API and module reference for {repo_name}",
            "category": "root",
            "content_md": resp.content.strip(),
            "order": 5,
            "icon": "code",
        }
    except Exception as e:
        logger.error(f"[generate_api_ref] Failed: {e}")
        # Fallback: generate a basic reference from the analysis data
        md_lines = [
            "---",
            'title: "API Reference"',
            f'description: "API reference for {repo_name}"',
            "order: 5",
            'category: "root"',
            'icon: "code"',
            "---",
            "",
            "# API Reference",
            "",
        ]
        for abs_item in all_abstractions[:30]:
            md_lines.append(f"## `{abs_item['name']}` ({abs_item['type']})")
            md_lines.append(f"\n{abs_item.get('description', '')}")
            md_lines.append(f"\n**Source:** `{abs_item.get('source_file', '')}`\n")

        api_ref_doc = {
            "slug": "api-reference",
            "title": "API Reference",
            "description": f"API reference for {repo_name}",
            "category": "root",
            "content_md": "\n".join(md_lines),
            "order": 5,
            "icon": "code",
        }

    logger.info(f"[generate_api_ref] API reference generated")

    return {**state, "api_ref_doc": api_ref_doc}
