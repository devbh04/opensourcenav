"""
Node: Store Docs — assembles all generated pages and stores in MongoDB.
"""
import logging
from datetime import datetime
from app.db.mongodb import get_collection
from app.utils.helpers import slugify

logger = logging.getLogger(__name__)


async def store_docs(state: dict) -> dict:
    """
    Assemble all generated doc pages, build navigation, and store in MongoDB.

    Reads: overview_docs, component_docs, guide_docs, api_ref_doc, diagrams,
           structure_analysis, repo_name, repo_url, user_id, qdrant_collection
    Writes: mongo_doc_id
    """
    repo_name = state.get("repo_name", "unknown")
    repo_url = state.get("repo_url", "")
    user_id = state.get("user_id", "")
    structure = state.get("structure_analysis", {})
    qdrant_collection = state.get("qdrant_collection", "")

    logger.info(f"[store_docs] Assembling docs for {repo_name}")

    # Collect all pages
    all_pages = []
    all_pages.extend(state.get("overview_docs", []))
    all_pages.extend(state.get("component_docs", []))
    all_pages.extend(state.get("guide_docs", []))

    api_ref = state.get("api_ref_doc")
    if api_ref:
        all_pages.append(api_ref)

    # Add diagrams page
    diagrams = state.get("diagrams", [])
    if diagrams:
        md_lines = [
            "---",
            'title: "Diagrams"',
            f'description: "Visual diagrams for {repo_name}"',
            "order: 6",
            'category: "root"',
            'icon: "chart"',
            "---",
            "",
            "# Diagrams",
            "",
            f"> Visual representations of {repo_name}'s architecture and data flow.",
            "",
        ]
        for d in diagrams:
            md_lines.append(f"## {d.get('title', 'Diagram')}")
            md_lines.append("")
            md_lines.append(d.get("description", ""))
            md_lines.append("")
            md_lines.append("```mermaid")
            md_lines.append(d.get("mermaid_code", "graph TD\n  A-->B"))
            md_lines.append("```")
            md_lines.append("")

        all_pages.append({
            "slug": "diagrams",
            "title": "Diagrams",
            "description": f"Visual diagrams for {repo_name}",
            "category": "root",
            "content_md": "\n".join(md_lines),
            "order": 6,
            "icon": "chart",
        })

    # Sort pages by order
    all_pages.sort(key=lambda p: p.get("order", 99))

    # Build navigation tree
    nav_root = []
    nav_components = []
    nav_guides = []

    for page in all_pages:
        nav_item = {
            "title": page["title"],
            "slug": page["slug"],
            "icon": page.get("icon", ""),
        }
        cat = page.get("category", "root")
        if cat == "components":
            nav_components.append(nav_item)
        elif cat == "guides":
            nav_guides.append(nav_item)
        else:
            nav_root.append(nav_item)

    navigation = list(nav_root)
    if nav_components:
        navigation.append({
            "title": "Components",
            "slug": "components",
            "icon": "cube",
            "children": nav_components,
        })
    if nav_guides:
        navigation.append({
            "title": "Guides",
            "slug": "guides",
            "icon": "book",
            "children": nav_guides,
        })

    # Build the document
    doc = {
        "repo_url": repo_url,
        "repo_name": repo_name,
        "generated_by": user_id,
        "generated_at": datetime.utcnow().isoformat(),
        "meta": {
            "repo_name": repo_name,
            "repo_url": repo_url,
            "generated_at": datetime.utcnow().isoformat(),
            "navigation": navigation,
            "stats": {
                "total_files_analyzed": structure.get("total_files", 0),
                "total_lines": structure.get("total_lines", 0),
                "languages": structure.get("languages", []),
                "abstractions_found": len(state.get("code_analysis", [])),
                "diagrams_generated": len(diagrams),
                "pages_generated": len(all_pages),
            },
        },
        "pages": all_pages,
        "stats": {
            "total_files_analyzed": structure.get("total_files", 0),
            "total_lines": structure.get("total_lines", 0),
            "languages": structure.get("languages", []),
            "abstractions_found": len(state.get("code_analysis", [])),
            "diagrams_generated": len(diagrams),
            "generation_time_seconds": 0,
        },
        "qdrant_collection": qdrant_collection,
    }

    # Upsert into MongoDB (replace if exists for same repo)
    col = await get_collection("docs")
    result = await col.replace_one(
        {"repo_name": repo_name},
        doc,
        upsert=True,
    )

    doc_id = str(result.upserted_id or "updated")
    logger.info(f"[store_docs] Stored {len(all_pages)} pages in MongoDB (id={doc_id})")

    return {**state, "mongo_doc_id": doc_id}
