"""
Node: Generate Guides — creates deep-dive guide pages on key topics.
"""
import json
import logging
from app.services.llm_service import get_llm
from app.utils.json_extract import extract_json
from app.utils.helpers import slugify

logger = logging.getLogger(__name__)


def generate_guides(state: dict) -> dict:
    """
    Generate guide pages that explain key concepts and workflows in depth.

    Reads from state: structure_analysis, code_analysis, files, repo_name
    Writes to state: guide_docs (list of page dicts)
    """
    structure = state.get("structure_analysis", {})
    code_analysis = state.get("code_analysis", [])
    files = state.get("files", [])
    repo_name = state.get("repo_name", "unknown")

    logger.info(f"[generate_guides] Creating guide pages for {repo_name}")

    llm = get_llm(temperature=0.3)

    # Collect all abstractions and patterns
    all_abstractions = []
    all_patterns = []
    for ca in code_analysis:
        for abs_item in ca.get("key_abstractions", []):
            all_abstractions.append({**abs_item, "file": ca["file_path"]})
        all_patterns.extend(ca.get("patterns", []))

    unique_patterns = list(set(all_patterns))

    # Ask LLM to determine what guides to write
    plan_prompt = f"""Given this repository analysis, determine 3-5 guide topics that would be most helpful for developers.

Repository: {repo_name}
Type: {structure.get('project_type', 'unknown')}
Frameworks: {structure.get('frameworks', [])}
Key features: {structure.get('key_features', [])}
Patterns found: {unique_patterns}
Abstraction count: {len(all_abstractions)}

Return a JSON array of guide topics:
[
  {{
    "title": "Guide title",
    "slug": "guide-slug",
    "description": "What this guide covers",
    "relevant_files": ["paths of relevant source files"]
  }}
]

Focus on practical, actionable guides like:
- How the core workflow works
- How to extend/customize the project
- How authentication/data flow works
- How to deploy

Return ONLY valid JSON, no markdown fences."""

    try:
        resp = llm.invoke(plan_prompt)
        guide_topics = extract_json(resp.content)
        if guide_topics is None:
            raise ValueError("No valid JSON found")
    except Exception as e:
        logger.warning(f"[generate_guides] Guide planning failed: {e}")
        guide_topics = [
            {
                "title": "Core Concepts",
                "slug": "core-concepts",
                "description": f"Key concepts and patterns in {repo_name}",
                "relevant_files": [],
            }
        ]

    # Generate each guide
    pages = []
    for idx, topic in enumerate(guide_topics[:5]):
        # Get content of relevant files
        relevant_content = {}
        for f in files:
            if f["relative_path"] in topic.get("relevant_files", []):
                relevant_content[f["relative_path"]] = f["content"][:4000]

        # Get relevant code analysis
        relevant_analysis = [
            ca for ca in code_analysis
            if ca["file_path"] in topic.get("relevant_files", [])
        ]

        guide_prompt = f"""Write a comprehensive guide page for "{topic['title']}" in the "{repo_name}" project.

Guide description: {topic['description']}

Project context:
- Type: {structure.get('project_type', 'unknown')}
- Main language: {structure.get('primary_language', 'unknown')}
- Frameworks: {structure.get('frameworks', [])}

Relevant code analysis:
{json.dumps(relevant_analysis[:10], indent=2)[:5000]}

Relevant source code:
{json.dumps(relevant_content, indent=2)[:6000]}

Write the guide in Markdown:
- Frontmatter with title, description, order: {idx + 30}, category: "guides", icon: "book"
- Start with a brief "Overview" explaining what this guide covers and why it matters
- Use step-by-step sections with clear headings
- Include actual code examples from the repository (use code blocks with language)
- Include Mermaid diagrams where helpful (flowcharts, sequence diagrams)
- Add "Key Takeaways" at the end
- Add a "Related" section linking to other pages

Make it tutorial-like: explain concepts, show code, explain the code.
Return ONLY the markdown content."""

        try:
            resp = llm.invoke(guide_prompt)
            pages.append({
                "slug": f"guides/{slugify(topic.get('slug', topic['title']))}",
                "title": topic["title"],
                "description": topic.get("description", ""),
                "category": "guides",
                "content_md": resp.content.strip(),
                "order": idx + 30,
                "icon": "book",
            })
        except Exception as e:
            logger.warning(f"[generate_guides] Guide '{topic['title']}' failed: {e}")

    logger.info(f"[generate_guides] Generated {len(pages)} guide pages")

    return {**state, "guide_docs": pages}
