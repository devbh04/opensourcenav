"""
Node: Search Repos — parallel GitHub search with multiple strategies.
"""
import logging
import asyncio
from app.services.github_service import search_github_repos

logger = logging.getLogger(__name__)


async def search_by_language(tech: list[str], min_stars: int) -> list[dict]:
    """Search repos by primary language."""
    results = []
    for lang in tech[:3]:
        query = f"language:{lang} stars:>={min_stars}"
        repos = await search_github_repos(query, per_page=30)
        results.extend(repos)
    return results


async def search_by_topic(tech: list[str], domain: str, min_stars: int) -> list[dict]:
    """Search repos by topic/domain."""
    results = []
    for t in tech[:3]:
        query = f"topic:{t.lower()}"
        if domain:
            query += f" topic:{domain.lower()}"
        query += f" stars:>={min_stars}"
        repos = await search_github_repos(query, per_page=30)
        results.extend(repos)
    return results


async def search_trending(tech: list[str], min_stars: int) -> list[dict]:
    """Search recently active repos."""
    results = []
    for lang in tech[:2]:
        query = f"language:{lang} stars:>={min_stars} pushed:>2026-04-01"
        repos = await search_github_repos(query, sort="updated", per_page=20)
        results.extend(repos)
    return results


async def search_good_first_issues(tech: list[str]) -> list[dict]:
    """Search repos with good-first-issue labels."""
    results = []
    for lang in tech[:2]:
        query = f"language:{lang} good-first-issues:>3 stars:>=50"
        repos = await search_github_repos(query, per_page=20)
        results.extend(repos)
    return results


async def parallel_repo_search(
    tech: list[str],
    domain: str = "",
    min_stars: int = 100,
) -> tuple[list[dict], list[str]]:
    """
    Run all search strategies in parallel and deduplicate.

    Returns: (deduplicated_repos, strategies_used)
    """
    strategies_used = []

    tasks = [
        search_by_language(tech, min_stars),
        search_by_topic(tech, domain, min_stars),
        search_trending(tech, min_stars),
        search_good_first_issues(tech),
    ]
    strategy_names = [
        "Language Search",
        "Topic/Domain Search",
        "Trending Repos",
        "Good First Issues",
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_repos = []
    seen_ids = set()

    for repos, name in zip(results, strategy_names):
        if isinstance(repos, Exception):
            logger.warning(f"[search_repos] {name} failed: {repos}")
            continue
        strategies_used.append(name)
        for repo in repos:
            rid = repo.get("id")
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                all_repos.append(repo)

    logger.info(f"[search_repos] Found {len(all_repos)} unique repos from {len(strategies_used)} strategies")
    return all_repos, strategies_used
