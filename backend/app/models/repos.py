"""
Pydantic models for the repo finder agent system.
"""
from pydantic import BaseModel, Field
from typing import Optional


class RepoFinderRequest(BaseModel):
    """User preferences for finding repositories to contribute to."""
    query: str = Field(..., description="Free-form user query describing what they want")


class RepoResult(BaseModel):
    """A single repository result from the finder."""
    full_name: str
    description: Optional[str] = None
    html_url: str
    stargazers_count: int = 0
    forks_count: int = 0
    language: Optional[str] = None
    topics: list[str] = []
    open_issues_count: int = 0
    updated_at: str = ""
    has_good_first_issues: bool = False
    good_first_issue_count: int = 0
    relevance_score: float = 0.0
    relevance_reasons: list[str] = []


class RepoFinderResponse(BaseModel):
    """Response from the repo finder agent."""
    repositories: list[RepoResult] = []
    total_found: int = 0
    search_strategies_used: list[str] = []
    execution_time: float = 0.0
