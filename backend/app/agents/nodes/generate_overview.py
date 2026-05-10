"""
Node: Generate Overview — creates index.md, architecture.md, and getting-started.md
"""
import json
import logging
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


def generate_overview(state: dict) -> dict:
    """
    Generate the main overview documentation pages.

    Reads from state: repo_name, structure_analysis, code_analysis, files
    Writes to state: overview_docs (list of page dicts)
    """
    repo_name = state.get("repo_name", "unknown")
    structure = state.get("structure_analysis", {})
    code_analysis = state.get("code_analysis", [])
    files = state.get("files", [])

    logger.info(f"[generate_overview] Generating overview docs for {repo_name}")

    llm = get_llm(temperature=0.3)

    # Find README content if exists
    readme_content = ""
    for f in files:
        if f["relative_path"].lower() in ("readme.md", "readme.txt", "readme"):
            readme_content = f["content"][:6000]
            break

    # Build context for the LLM
    abstractions_summary = []
    for ca in code_analysis[:30]:
        for abs_item in ca.get("key_abstractions", []):
            if abs_item.get("importance") in ("high", "medium"):
                abstractions_summary.append({
                    "name": abs_item["name"],
                    "type": abs_item["type"],
                    "description": abs_item["description"],
                    "file": ca["file_path"],
                })

    context = {
        "repo_name": repo_name,
        "description": structure.get("description", ""),
        "primary_language": structure.get("primary_language", ""),
        "languages": structure.get("languages", []),
        "frameworks": structure.get("frameworks", []),
        "project_type": structure.get("project_type", ""),
        "architecture_pattern": structure.get("architecture_pattern", ""),
        "key_features": structure.get("key_features", []),
        "entry_points": structure.get("entry_points", []),
        "build_system": structure.get("build_system", ""),
        "total_files": structure.get("total_files", 0),
        "total_lines": structure.get("total_lines", 0),
        "top_directories": structure.get("top_directories", []),
        "config_files": structure.get("config_files", []),
    }

    pages = []

    # ── 1. index.md (Overview) ──────────────────────────────────────
    prompt_index = f"""Create a comprehensive overview documentation page for the project "{repo_name}".

Project context:
{json.dumps(context, indent=2)}

README content (if available):
{readme_content[:4000]}

Key abstractions found:
{json.dumps(abstractions_summary[:20], indent=2)}

Write the page in Markdown with this structure:
- Start with a frontmatter block:
  ---
  title: "{repo_name} Documentation"
  description: "Complete documentation for {repo_name}"
  order: 0
  category: "root"
  icon: "home"
  ---
- A brief, compelling introduction paragraph
- "What is {repo_name}?" section
- "Key Features" section (bullet list)
- "Tech Stack" section (table format)
- "Quick Links" section linking to other doc pages (use relative links like ./getting-started, ./architecture, ./api-reference)
- "Project Stats" section (files, lines, languages)

Make it professional and engaging, like Stripe or Vercel docs.
Return ONLY the markdown content."""

    try:
        resp = llm.invoke(prompt_index)
        pages.append({
            "slug": "index",
            "title": f"{repo_name} Documentation",
            "description": structure.get("description", f"Documentation for {repo_name}"),
            "category": "root",
            "content_md": resp.content.strip(),
            "order": 0,
            "icon": "home",
        })
    except Exception as e:
        logger.error(f"[generate_overview] index.md generation failed: {e}")
        pages.append({
            "slug": "index",
            "title": f"{repo_name} Documentation",
            "description": f"Documentation for {repo_name}",
            "category": "root",
            "content_md": f"# {repo_name}\n\n{structure.get('description', 'Documentation')}",
            "order": 0,
            "icon": "home",
        })

    # ── 2. architecture.md ──────────────────────────────────────────
    prompt_arch = f"""Create an architecture documentation page for "{repo_name}".

Project context:
{json.dumps(context, indent=2)}

Key abstractions and their relationships:
{json.dumps(abstractions_summary[:25], indent=2)}

Write the page in Markdown:
- Frontmatter with title "Architecture Overview", order 1, icon "layout"
- "System Architecture" section with a Mermaid diagram showing the high-level architecture
- "Directory Structure" section showing the project layout
- "Core Components" section describing the main modules/components
- "Data Flow" section with a Mermaid sequence or flowchart diagram showing how data moves through the system
- "Design Patterns" section listing patterns used

Use Mermaid diagrams in ```mermaid code blocks. Make the diagrams accurate based on the actual code analysis.
Return ONLY the markdown content."""

    try:
        resp = llm.invoke(prompt_arch)
        pages.append({
            "slug": "architecture",
            "title": "Architecture Overview",
            "description": f"System architecture and design of {repo_name}",
            "category": "root",
            "content_md": resp.content.strip(),
            "order": 1,
            "icon": "layout",
        })
    except Exception as e:
        logger.error(f"[generate_overview] architecture.md failed: {e}")

    # ── 3. getting-started.md ───────────────────────────────────────
    prompt_gs = f"""Create a "Getting Started" documentation page for "{repo_name}".

Project context:
{json.dumps(context, indent=2)}

README content:
{readme_content[:4000]}

Config files found: {context.get('config_files', [])}

Write the page in Markdown:
- Frontmatter with title "Getting Started", order 2, icon "rocket"
- "Prerequisites" section (what you need installed)
- "Installation" section with step-by-step commands
- "Configuration" section (env vars, config files)
- "Running the Project" section (dev server, build, etc.)
- "First Steps" section (what to do after setup)
- "Troubleshooting" section (common issues)

Base the instructions on the actual build system ({context.get('build_system', 'unknown')}) and config files found.
Return ONLY the markdown content."""

    try:
        resp = llm.invoke(prompt_gs)
        pages.append({
            "slug": "getting-started",
            "title": "Getting Started",
            "description": f"Installation and setup guide for {repo_name}",
            "category": "root",
            "content_md": resp.content.strip(),
            "order": 2,
            "icon": "rocket",
        })
    except Exception as e:
        logger.error(f"[generate_overview] getting-started.md failed: {e}")

    logger.info(f"[generate_overview] Generated {len(pages)} overview pages")

    return {**state, "overview_docs": pages}
