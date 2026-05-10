"""
RepoFinder Agent — finds repos to contribute to based on user preferences.
Uses parallel search + LLM scoring.
"""
import json
import time
import logging
from app.services.llm_service import get_llm
from app.utils.json_extract import extract_json
from app.agents.nodes.search_repos import parallel_repo_search
from app.models.repos import RepoFinderRequest, RepoFinderResponse, RepoResult

logger = logging.getLogger(__name__)


async def find_repos(request: RepoFinderRequest) -> RepoFinderResponse:
    """
    Run the repo finder agent pipeline.

    1. Parallel GitHub searches
    2. LLM-based scoring and ranking
    3. Return sorted results
    """
    start_time = time.time()
    logger.info(f"[find_repos] Searching for repos: query={request.query}")

    llm = get_llm(model="gemini-3.1-pro-preview", temperature=0.1)

    # 1. Generate GitHub search queries
    query_prompt = f"""You are an expert GitHub search architect. The user wants to find repositories to explore or contribute to based on this natural language request:
"{request.query}"

Generate 3 to 5 distinct GitHub API search query strings (using qualifiers like language:python, stars:50..500, pushed:>2026-01-01, topic:agents, good-first-issues:>0, etc.) that would optimally find repositories matching this specific request. 
Also provide a short explanation for each strategy.

Return ONLY a valid JSON array of objects:
[{{"query": "language:typescript stars:>10 topic:react", "strategy": "Finds popular React repos"}}]"""

    try:
        resp = llm.invoke(query_prompt)
        queries_data = extract_json(resp.content)
        if not queries_data:
            raise ValueError("No valid JSON queries found")
    except Exception as e:
        logger.warning(f"[find_repos] Query generation failed: {e}")
        queries_data = [{"query": "stars:>100", "strategy": "Fallback generic search"}]

    strategies_used = [q.get("strategy", "Search") for q in queries_data]

    # 2. Parallel search execution
    from app.services.github_service import search_github_repos
    import asyncio

    tasks = [search_github_repos(q.get("query", "stars:>10"), per_page=15) for q in queries_data]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_repos = []
    seen_ids = set()

    for repos in results:
        if isinstance(repos, Exception):
            logger.warning(f"[find_repos] Search task failed: {repos}")
            continue
        for repo in repos:
            rid = repo.get("id")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                raw_repos.append(repo)

    if not raw_repos:
        return RepoFinderResponse(
            repositories=[],
            total_found=0,
            search_strategies_used=strategies_used,
            execution_time=time.time() - start_time,
        )

    # 3. LLM scoring
    repos_for_scoring = raw_repos[:40]
    repo_summaries = [
        {
            "idx": i,
            "name": r.get("full_name", ""),
            "description": (r.get("description") or "")[:150],
            "language": r.get("language", ""),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "topics": r.get("topics", [])[:5],
        }
        for i, r in enumerate(repos_for_scoring)
    ]

    score_prompt = f"""Evaluate these repositories based on the user's request: "{request.query}"

Repositories:
{json.dumps(repo_summaries, indent=2)[:8000]}

For each repo, determine how well it matches the user's intent. Return a JSON array:
[{{"idx": 0, "score": 0.95, "reasons": ["Perfect match for what the user requested", "Active"]}}]

Score from 0.0 to 1.0. Include all repos.
Return ONLY valid JSON."""

    scored_repos = []
    try:
        resp = llm.invoke(score_prompt)
        scores = extract_json(resp.content)
        if scores is None:
            raise ValueError("No valid JSON found")

        score_map = {s["idx"]: s for s in scores}

        for i, repo in enumerate(repos_for_scoring):
            score_data = score_map.get(i, {"score": 0.3, "reasons": []})
            scored_repos.append(RepoResult(
                full_name=repo.get("full_name", ""),
                description=repo.get("description"),
                html_url=repo.get("html_url", ""),
                stargazers_count=repo.get("stargazers_count", 0),
                forks_count=repo.get("forks_count", 0),
                language=repo.get("language"),
                topics=repo.get("topics", []),
                open_issues_count=repo.get("open_issues_count", 0),
                updated_at=repo.get("updated_at", ""),
                has_good_first_issues=repo.get("open_issues_count", 0) > 5,
                good_first_issue_count=0,
                relevance_score=score_data.get("score", 0.3),
                relevance_reasons=score_data.get("reasons", []),
            ))

    except Exception as e:
        logger.warning(f"[find_repos] LLM scoring failed: {e}")
        for repo in repos_for_scoring:
            scored_repos.append(RepoResult(
                full_name=repo.get("full_name", ""),
                description=repo.get("description"),
                html_url=repo.get("html_url", ""),
                stargazers_count=repo.get("stargazers_count", 0),
                forks_count=repo.get("forks_count", 0),
                language=repo.get("language"),
                topics=repo.get("topics", []),
                open_issues_count=repo.get("open_issues_count", 0),
                updated_at=repo.get("updated_at", ""),
                relevance_score=0.5,
                relevance_reasons=["Matches search criteria"],
            ))

    # Sort by relevance score
    scored_repos.sort(key=lambda r: r.relevance_score, reverse=True)

    return RepoFinderResponse(
        repositories=scored_repos,
        total_found=len(scored_repos),
        search_strategies_used=strategies_used,
        execution_time=time.time() - start_time,
    )
