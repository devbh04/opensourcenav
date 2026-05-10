"""
DocsGen Agent Graph — LangGraph StateGraph with parallel fan-out/fan-in.

Flow:
  fetch_repo → [analyze_structure, analyze_code, embed_repo] (parallel)
             → [generate_overview, generate_components, generate_guides, generate_api_ref, generate_diagrams] (parallel)
             → store_docs
"""
import logging
import asyncio
import time
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from app.agents.nodes.fetch_repo import fetch_repo
from app.agents.nodes.analyze_structure import analyze_structure
from app.agents.nodes.analyze_code import analyze_code
from app.agents.nodes.embed_repo import embed_repo
from app.agents.nodes.generate_overview import generate_overview
from app.agents.nodes.generate_components import generate_components
from app.agents.nodes.generate_guides import generate_guides
from app.agents.nodes.generate_api_ref import generate_api_ref
from app.agents.nodes.generate_diagrams import generate_diagrams
from app.agents.nodes.store_docs import store_docs

logger = logging.getLogger(__name__)


# ── State Schema ─────────────────────────────────────────────────────

class DocsGenState(TypedDict, total=False):
    # Input
    repo_url: str
    user_id: str
    job_id: str
    session_id: str
    selected_files: list
    include_patterns: list
    exclude_patterns: list

    # After fetch
    repo_path: str
    repo_name: str
    files: list
    file_tree: list

    # After parallel analysis
    structure_analysis: dict
    code_analysis: list
    qdrant_collection: str
    chunks_count: int

    # After parallel doc generation
    overview_docs: list
    component_docs: list
    guide_docs: list
    api_ref_doc: dict
    diagrams: list

    # Final
    mongo_doc_id: str
    status: str
    progress: float
    error: Optional[str]


# ── Parallel Execution Wrappers ──────────────────────────────────────

def parallel_analysis(state: dict) -> dict:
    """
    Run analysis phase: embed_repo runs in a background thread while
    LLM analysis (structure + code) runs sequentially to avoid rate limits.
    """
    import concurrent.futures

    logger.info("[parallel_analysis] Starting analysis phase")

    results = {}

    # Start embedding in background (uses Embedding API, separate quota)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_embed = executor.submit(embed_repo, state)

        # Run LLM analysis sequentially to avoid 429s
        try:
            structure_result = analyze_structure(state)
            results["structure_analysis"] = structure_result.get("structure_analysis", {})
        except Exception as e:
            logger.error(f"[parallel_analysis] analyze_structure failed: {e}")
            results["structure_analysis"] = {}

        try:
            code_result = analyze_code(state)
            results["code_analysis"] = code_result.get("code_analysis", [])
        except Exception as e:
            logger.error(f"[parallel_analysis] analyze_code failed: {e}")
            results["code_analysis"] = []

        # Wait for embedding to finish
        try:
            embed_result = future_embed.result(timeout=300)
            results["qdrant_collection"] = embed_result.get("qdrant_collection", "")
            results["chunks_count"] = embed_result.get("chunks_count", 0)
        except Exception as e:
            logger.error(f"[parallel_analysis] embed_repo failed: {e}")
            results["qdrant_collection"] = ""
            results["chunks_count"] = 0

    logger.info("[parallel_analysis] Analysis phase complete")
    return {**state, **results}


def parallel_doc_generation(state: dict) -> dict:
    """
    Run doc generation nodes with limited concurrency (max 2 at a time)
    to avoid Vertex AI rate limits.
    """
    import concurrent.futures

    logger.info("[parallel_doc_generation] Starting doc generation")

    results = {}

    # Batch 1: overview + diagrams (lighter tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_overview = executor.submit(generate_overview, state)
        future_diagrams = executor.submit(generate_diagrams, state)

        try:
            r = future_overview.result(timeout=300)
            results["overview_docs"] = r.get("overview_docs", [])
        except Exception as e:
            logger.error(f"[parallel_doc_generation] overview failed: {e}")
            results["overview_docs"] = []

        try:
            r = future_diagrams.result(timeout=300)
            results["diagrams"] = r.get("diagrams", [])
        except Exception as e:
            logger.error(f"[parallel_doc_generation] diagrams failed: {e}")
            results["diagrams"] = []

    # Batch 2: components + api_ref
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_components = executor.submit(generate_components, state)
        future_api = executor.submit(generate_api_ref, state)

        try:
            r = future_components.result(timeout=300)
            results["component_docs"] = r.get("component_docs", [])
        except Exception as e:
            logger.error(f"[parallel_doc_generation] components failed: {e}")
            results["component_docs"] = []

        try:
            r = future_api.result(timeout=300)
            results["api_ref_doc"] = r.get("api_ref_doc", {})
        except Exception as e:
            logger.error(f"[parallel_doc_generation] api_ref failed: {e}")
            results["api_ref_doc"] = {}

    # Batch 3: guides (heaviest — makes multiple LLM calls)
    try:
        r = generate_guides(state)
        results["guide_docs"] = r.get("guide_docs", [])
    except Exception as e:
        logger.error(f"[parallel_doc_generation] guides failed: {e}")
        results["guide_docs"] = []

    logger.info("[parallel_doc_generation] Doc generation phase complete")
    return {**state, **results}


# ── Build the LangGraph ─────────────────────────────────────────────

def build_docs_graph() -> StateGraph:
    """Build and compile the DocsGen LangGraph."""

    graph = StateGraph(DocsGenState)

    # Add nodes
    graph.add_node("fetch_repo", fetch_repo)
    graph.add_node("parallel_analysis", parallel_analysis)
    graph.add_node("parallel_doc_generation", parallel_doc_generation)
    graph.add_node("store_docs", store_docs)

    # Define edges: linear pipeline with parallel internals
    graph.add_edge(START, "fetch_repo")
    graph.add_edge("fetch_repo", "parallel_analysis")
    graph.add_edge("parallel_analysis", "parallel_doc_generation")
    graph.add_edge("parallel_doc_generation", "store_docs")
    graph.add_edge("store_docs", END)

    return graph.compile()


# ── Convenience Runner ───────────────────────────────────────────────

async def run_docs_generation(
    repo_url: str,
    user_id: str,
    job_id: str,
    progress_callback=None,
    session_id: str = "",
    selected_files: list = [],
    include_patterns: list = [],
    exclude_patterns: list = [],
) -> dict:
    """
    Run the full docs generation pipeline.

    Args:
        repo_url: GitHub repository URL
        user_id: Guest user ID
        job_id: Queue job ID
        progress_callback: async fn(progress, phase) for status updates

    Returns:
        Final state dict with all generated content
    """
    start_time = time.time()

    async def update_progress(progress: float, phase: str):
        if progress_callback:
            await progress_callback(progress, phase)

    await update_progress(0.05, "Cloning repository...")

    initial_state = {
        "repo_url": repo_url,
        "user_id": user_id,
        "job_id": job_id,
        "session_id": session_id,
        "selected_files": selected_files,
        "include_patterns": include_patterns,
        "exclude_patterns": exclude_patterns,
        "status": "processing",
        "progress": 0.0,
    }

    compiled_graph = build_docs_graph()

    # Run the graph
    # LangGraph's invoke is sync for sync nodes, we run in executor
    loop = asyncio.get_event_loop()

    await update_progress(0.1, "Fetching repository files...")

    try:
        # Run the compiled graph using the async API
        final_state = await compiled_graph.ainvoke(initial_state)

        elapsed = time.time() - start_time
        final_state["status"] = "completed"
        final_state["progress"] = 1.0

        await update_progress(1.0, f"Complete! Generated docs in {elapsed:.1f}s")

        logger.info(f"Docs generation complete for {repo_url} in {elapsed:.1f}s")
        return final_state

    except Exception as e:
        logger.error(f"Docs generation failed: {e}")
        await update_progress(0.0, f"Failed: {str(e)[:100]}")
        return {
            **initial_state,
            "status": "failed",
            "error": str(e),
        }
