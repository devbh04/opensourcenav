import os
import re
import math
import base64
import requests
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils.cache import cache
from app.utils.config import GITHUB_TOKEN

# Headers for GitHub API
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
} if GITHUB_TOKEN else {
    "Accept": "application/vnd.github+json"
}

def search_repositories_custom_query(query, min_stars=100, per_page=100, max_results=200):
    """Enhanced search with pagination support and better error handling"""
    try:
        all_repos = []
        page = 1
        
        while len(all_repos) < max_results and page <= 3:  # Limit to 3 pages to manage rate limits
            # Build URL with pagination
            if "stars:" in query:
                url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}&page={page}"
            else:
                url = f"https://api.github.com/search/repositories?q={query}+stars:>={min_stars}&sort=stars&order=desc&per_page={per_page}&page={page}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 403:
                print(f"Rate limit exceeded. Waiting...")
                break
            elif response.status_code != 200:
                print(f"GitHub API error: {response.status_code}")
                break
            
            page_data = response.json()
            items = page_data.get("items", [])
            
            if not items:
                print(f"No more results on page {page}")
                break
                
            all_repos.extend(items)
            page += 1
            
            # If we got less than per_page results, this is the last page
            if len(items) < per_page:
                break
        
        return all_repos[:max_results]
        
    except Exception as e:
        print(f"Error in search_repositories_custom_query: {e}")
        return []

def search_repositories_with_text_match(query, min_stars=100, per_page=50):
    """Search with text match metadata for better relevance scoring"""
    try:
        # Use text-match media type for enhanced results
        text_match_headers = {
            **headers,
            "Accept": "application/vnd.github.text-match+json"
        }
        
        if "stars:" in query:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
        else:
            url = f"https://api.github.com/search/repositories?q={query}+stars:>={min_stars}&sort=stars&order=desc&per_page={per_page}"
        
        response = requests.get(url, headers=text_match_headers, timeout=10)
        
        if response.status_code == 200:
            repos = response.json().get("items", [])
            
            # Calculate enhanced scores based on text matches
            for repo in repos:
                text_matches = repo.get('text_matches', [])
                repo['enhanced_score'] = calculate_text_match_score(text_matches)
            
            # Sort by enhanced score
            repos.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)
            return repos
        else:
            print(f"Text match search failed: {response.status_code}")
            return search_repositories_custom_query(query, min_stars, per_page)
            
    except Exception as e:
        print(f"Error in text match search: {e}")
        return search_repositories_custom_query(query, min_stars, per_page)

def calculate_text_match_score(text_matches):
    """Calculate relevance score based on text match metadata"""
    if not text_matches:
        return 0
    
    score = 0
    for match in text_matches:
        property_name = match.get('property', '')
        matches = match.get('matches', [])
        
        # Weight different properties differently
        property_weights = {
            'name': 10,        # Repository name matches are most important
            'description': 7,   # Description matches are very important
            'readme': 5,       # README matches are moderately important
            'topics': 8        # Topic matches are very important
        }
        
        weight = property_weights.get(property_name, 3)
        score += len(matches) * weight
    
    return score

def get_repo_readme(repo_full_name):
    """Get repository README content with caching"""
    cached_readme = cache.get("readme", repo_full_name)
    if cached_readme is not None:
        return cached_readme
    
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        cache.set("readme", repo_full_name, content)
        return content
    
    cache.set("readme", repo_full_name, "")
    return ""

def get_good_first_issues(repo_full_name, per_page=5):
    """Get good first issues for a repository with caching"""
    cached_issues = cache.get("good_first_issues", repo_full_name)
    if cached_issues is not None:
        return cached_issues
    
    url = f"https://api.github.com/repos/{repo_full_name}/issues?labels=good%20first%20issue&state=open&per_page={per_page}"
    res = requests.get(url, headers=headers, timeout=10)
    
    if res.status_code == 200:
        issues = res.json()
        cache.set("good_first_issues", repo_full_name, issues)
        return issues
    
    cache.set("good_first_issues", repo_full_name, [])
    return []

def repo_has_required_tech(repo_full_name, tech_stack):
    """Enhanced repository technology validation with broader detection and caching"""
    try:
        # Create cache key that includes tech stack
        tech_key = "_".join(sorted([tech.lower() for tech in tech_stack]))
        cache_key = f"{repo_full_name}_{tech_key}"

        # Check cache first
        cached_result = cache.get("tech_verification", cache_key)
        if cached_result is not None:
            return cached_result

        contents_url = f"https://api.github.com/repos/{repo_full_name}/contents"
        res = requests.get(contents_url, headers=headers, timeout=10)

        if res.status_code != 200:
            cache.set("tech_verification", cache_key, False)
            return False

        files = res.json()
        filenames = [file["name"].lower() for file in files]

        # Enhanced Python detection
        if any(tech.lower() in ["python", "py"] for tech in tech_stack):
            python_indicators = [
                "requirements.txt", "setup.py", "pyproject.toml", 
                "pipfile", "environment.yml", "conda.yml"
            ]
            if any(indicator in filenames for indicator in python_indicators):
                cache.set("tech_verification", cache_key, True)
                return True
            
            # Check for .py files in root
            if any(f.endswith('.py') for f in filenames):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced JavaScript/TypeScript/React detection
        js_techs = ["react", "javascript", "typescript", "js", "ts", "node", "nodejs", "next", "vue", "angular"]
        if any(tech.lower() in js_techs for tech in tech_stack):
            js_indicators = ["package.json", "yarn.lock", "package-lock.json", "tsconfig.json"]
            
            if any(indicator in filenames for indicator in js_indicators):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced Java detection
        if any(tech.lower() == "java" for tech in tech_stack):
            java_indicators = [
                "pom.xml", "build.gradle", "gradle.build", "build.xml",
                "maven.xml", "settings.gradle"
            ]
            if any(indicator in filenames for indicator in java_indicators):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced C++ detection
        if any(tech.lower() in ["c++", "cpp", "c"] for tech in tech_stack):
            cpp_indicators = [
                "makefile", "cmake", "cmakelist.txt", "configure.ac",
                "configure.in", "build.sh"
            ]
            if any(indicator in filenames for indicator in cpp_indicators):
                cache.set("tech_verification", cache_key, True)
                return True
            # Check for C++ source files
            if any(f.endswith(('.cpp', '.cc', '.cxx', '.h', '.hpp')) for f in filenames):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced Go detection
        if any(tech.lower() == "go" for tech in tech_stack):
            go_indicators = ["go.mod", "go.sum", "glide.yaml", "dep.toml"]
            if any(indicator in filenames for indicator in go_indicators):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced Rust detection
        if any(tech.lower() == "rust" for tech in tech_stack):
            if "cargo.toml" in filenames:
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced PHP detection
        if any(tech.lower() == "php" for tech in tech_stack):
            php_indicators = ["composer.json", "composer.lock"]
            if any(indicator in filenames for indicator in php_indicators):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced Ruby detection
        if any(tech.lower() == "ruby" for tech in tech_stack):
            ruby_indicators = ["gemfile", "gemfile.lock", "rakefile"]
            if any(indicator in filenames for indicator in ruby_indicators):
                cache.set("tech_verification", cache_key, True)
                return True

        # Enhanced C# detection
        if any(tech.lower() in ["c#", "csharp", "dotnet"] for tech in tech_stack):
            csharp_indicators = [
                ".csproj", ".sln", "packages.config", "project.json",
                "global.json", "nuget.config"
            ]
            if any(any(indicator in f for indicator in csharp_indicators) for f in filenames):
                cache.set("tech_verification", cache_key, True)
                return True

        # Fallback: check if any tech stack item appears in file extensions or names
        for tech in tech_stack:
            tech_lower = tech.lower()
            if any(tech_lower in f for f in filenames):
                cache.set("tech_verification", cache_key, True)
                return True

        cache.set("tech_verification", cache_key, False)
        return False

    except Exception as e:
        print(f"Error in repo_has_required_tech for {repo_full_name}: {e}")
        cache.set("tech_verification", cache_key, False)  # Cache failed attempts too
        return False  # Conservative approach: if we can't verify, don't include

def get_repo_topics(repo_full_name):
    """Get repository topics with caching"""
    try:
        # Check cache first
        cached_topics = cache.get("topics", repo_full_name)
        if cached_topics is not None:
            return cached_topics

        # Fetch from GitHub API
        url = f"https://api.github.com/repos/{repo_full_name}/topics"
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            topics = response.json().get("names", [])
            # Cache the result
            cache.set("topics", repo_full_name, topics)
            return topics
        
        cache.set("topics", repo_full_name, [])
        return []
    except Exception as e:
        print(f"Error getting topics for {repo_full_name}: {e}")
        return []

def analyze_repo_activity(repo_full_name):
    """Analyze repository activity level with caching"""
    cached_activity = cache.get("activity", repo_full_name)
    if cached_activity is not None:
        return cached_activity
    
    url = f"https://api.github.com/repos/{repo_full_name}"
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        repo_data = response.json()
        activity = {
            'last_updated': repo_data.get('updated_at'),
            'open_issues_count': repo_data.get('open_issues_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'stars': repo_data.get('stargazers_count', 0),
            'language': repo_data.get('language'),
            'description': repo_data.get('description', '')
        }
        cache.set("activity", repo_full_name, activity)
        return activity
    
    return None

def calculate_repo_quality_score(repo_data):
    """Calculate a comprehensive quality score for a repository"""
    try:
        score = 0
        
        # Basic metrics
        stars = repo_data.get('stargazers_count', 0)
        forks = repo_data.get('forks_count', 0)
        issues = repo_data.get('open_issues_count', 0)
        size = repo_data.get('size', 0)
        
        # Star score (logarithmic to prevent huge repos from dominating)
        if stars > 0:
            score += min(math.log10(stars) * 15, 50)  # Cap at 50 points
        
        # Fork score (indicates usefulness)
        if forks > 0:
            score += min(math.log10(forks) * 10, 30)  # Cap at 30 points
        
        # Issues score (indicates activity, but too many might indicate problems)
        if issues > 0:
            if issues <= 50:
                score += min(issues * 0.2, 10)  # Reasonable issue count
            else:
                score -= (issues - 50) * 0.1  # Penalty for too many issues
        
        # Size score (substantial projects)
        if 1000 <= size <= 50000:  # Sweet spot for project size
            score += 10
        elif size > 50000:
            score += 5  # Large projects get some credit but might be complex
        
        # Recency bonus
        try:
            updated_at = repo_data.get('updated_at', '')
            if updated_at:
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days
                if days_since_update <= 30:
                    score += 15  # Very recent update
                elif days_since_update <= 90:
                    score += 10  # Recent update
                elif days_since_update <= 365:
                    score += 5   # Updated within a year
        except:
            pass
        
        # Description bonus (well-documented projects)
        description = repo_data.get('description', '')
        if description and len(description.strip()) > 20:
            score += 5
        
        # Language bonus (having a primary language)
        if repo_data.get('language'):
            score += 5
        
        # Archive/disabled penalty
        if repo_data.get('archived', False):
            score -= 50
        if repo_data.get('disabled', False):
            score -= 50
        
        # Fork penalty (prefer original projects)
        if repo_data.get('fork', False):
            score -= 10
        
        return max(score, 0)  # Ensure non-negative score
        
    except Exception as e:
        print(f"Error calculating quality score: {e}")
        return 0

def get_enhanced_repo_data(repo_full_name):
    """Get comprehensive repository data including quality metrics"""
    try:
        # Check cache first
        cached_data = cache.get("enhanced_repo", repo_full_name)
        if cached_data is not None:
            return cached_data
        
        # Get basic repo data
        url = f"https://api.github.com/repos/{repo_full_name}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
            
        repo_data = response.json()
        
        # Add quality score
        repo_data['quality_score'] = calculate_repo_quality_score(repo_data)
        
        # Add topics
        repo_data['topics'] = get_repo_topics(repo_full_name)
        
        # Add contributor count (if available)
        try:
            contributors_url = f"https://api.github.com/repos/{repo_full_name}/contributors?per_page=1"
            contrib_response = requests.get(contributors_url, headers=headers, timeout=5)
            if contrib_response.status_code == 200:
                repo_data['contributor_count'] = len(contrib_response.json())
        except:
            repo_data['contributor_count'] = 0
        
        # Cache the enhanced data
        cache.set("enhanced_repo", repo_full_name, repo_data)
        return repo_data
        
    except Exception as e:
        print(f"Error getting enhanced repo data for {repo_full_name}: {e}")
        return None

def build_advanced_queries(tech_stack: List[str], domain: str, min_stars_val: int, min_forks_val: int, min_open_issues_val: int, contribution: str) -> List[str]:
    """Build multiple sophisticated GitHub search queries for better repository discovery"""
    queries = []
    
    # Base technology terms
    tech_terms = " ".join(tech_stack) if tech_stack else ""
    primary_language = tech_stack[0] if tech_stack else ""
    
    # Domain-specific topics
    domain_topics: Dict[str, List[str]] = {
        "Web Development": ["web", "javascript", "frontend", "backend", "fullstack"],
        "Mobile Development": ["mobile", "android", "ios", "react-native", "flutter"],
        "AI/ML": ["machine-learning", "artificial-intelligence", "deep-learning", "neural-network"],
        "Data Science": ["data", "analytics", "visualization", "jupyter", "pandas"],
        "DevOps": ["devops", "docker", "kubernetes", "ci-cd", "deployment"],
        "Game Development": ["game", "unity", "gamedev", "2d", "3d"],
        "Cybersecurity": ["security", "cryptography", "penetration-testing", "vulnerability"],
        "IoT": ["iot", "arduino", "raspberry-pi", "embedded", "sensor"],
        "Blockchain": ["blockchain", "cryptocurrency", "smart-contracts", "web3"],
        "Scientific Computing": ["scientific", "research", "mathematics", "simulation"],
    }
    
    # Contribution-specific filters
    contribution_filters = {
        "Documentation": "topic:documentation OR good-first-issues:>0",
        "Bug Fixes": "help-wanted-issues:>0 OR good-first-issues:>0", 
        "Features": "help-wanted-issues:>0",
        "Testing": "topic:testing OR topic:unit-testing",
        "Design": "topic:design OR topic:ui OR topic:ux"
    }
    
    # Quality and activity filters
    base_quality = "archived:false mirror:false"
    recent_activity = "pushed:>2023-01-01"
    good_quality = f"stars:>={max(min_stars_val, 5)} forks:>={max(min_forks_val, 1)}"
    
    # Query 1: High-quality recent projects with exact language match
    if primary_language:
        query1_parts = [
            f"language:{primary_language}",
            base_quality,
            recent_activity,
            good_quality,
            "size:>1000"
        ]
        if tech_terms:
            query1_parts.append(f'"{tech_terms}" in:description')
        
        # Add domain topics if specified
        if domain != "Any" and domain in domain_topics:
            topic_filters = " OR ".join([f"topic:{topic}" for topic in domain_topics[domain][:2]])
            query1_parts.append(f"({topic_filters})")
            
        queries.append(" ".join(query1_parts))

    # Query 2: Topic-based search with broader language support
    if domain != "Any" and domain in domain_topics:
        for topic in domain_topics[domain][:2]:
            query2_parts = [
                f"topic:{topic}",
                base_quality,
                f"stars:>={max(min_stars_val//2, 10)}"
            ]
            if primary_language:
                query2_parts.append(f"language:{primary_language}")
            queries.append(" ".join(query2_parts))

    # Query 3: README content search for comprehensive matching
    if tech_terms:
        query3_parts = [
            f"{tech_terms} in:readme",
            base_quality,
            f"stars:>={max(min_stars_val//3, 2)}",
            "fork:false"
        ]
        if primary_language:
            query3_parts.append(f"language:{primary_language}")
            
        queries.append(" ".join(query3_parts))

    # Query 4: Contribution-specific search
    if contribution and contribution != "Any" and contribution in contribution_filters:
        query4_parts = [
            contribution_filters[contribution],
            base_quality,
            recent_activity
        ]
        if primary_language:
            query4_parts.append(f"language:{primary_language}")
        if tech_terms:
            query4_parts.append(f'"{tech_terms}" in:description')
            
        queries.append(" ".join(query4_parts))

    # Fallback query if no specific queries were built
    if not queries:
        fallback_parts = ["stars:>10", base_quality, recent_activity]
        if primary_language:
            fallback_parts.append(f"language:{primary_language}")
        queries.append(" ".join(fallback_parts))

    return queries[:5]  # Limit to 5 queries to respect rate limits

# GitHub Issue Analysis for Git Helper integration
class GitHubService:
    """Service for GitHub API operations with enhanced error handling"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = headers

    def parse_github_url(self, url: str) -> dict:
        """Extract owner and repo from GitHub URL"""
        pattern = r"github\.com\/([^\/]+)\/([^\/]+)"
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")
        
        return {
            "owner": match.group(1),
            "repo": match.group(2).replace(".git", "")  # Remove .git if present
        }

    async def get_issues(self, repo_url: str, options: dict) -> dict:
        """Fetch issues for a repository with proper pagination"""
        try:
            parsed = self.parse_github_url(repo_url)
            owner, repo = parsed["owner"], parsed["repo"]
            
            # Check cache first
            cache_key = f"{owner}_{repo}_{options.get('difficulty', 'all')}"
            cached_issues = cache.get("repo_issues", cache_key)
            if cached_issues is not None:
                return cached_issues
            
            difficulty = options.get("difficulty", "all")
            max_issues = 1000 if difficulty == "all" else 200
            
            all_issues = []
            page = 1
            per_page = 100
            
            while len(all_issues) < max_issues:
                url = f"{self.base_url}/repos/{owner}/{repo}/issues"
                params = {
                    "state": options.get("state", "open"),
                    "per_page": per_page,
                    "page": page
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code != 200:
                        break
                    
                    issues = response.json()
                    if not issues:
                        break
                    
                    all_issues.extend(issues)
                    page += 1
                    
                    if len(issues) < per_page:
                        break
            
            # Filter by difficulty if specified
            if difficulty != "all":
                all_issues = self._filter_issues_by_difficulty(all_issues, difficulty)
            
            result = {
                "issues": all_issues[:max_issues],
                "totalCount": len(all_issues),
                "repository": {"owner": owner, "repo": repo, "fullName": f"{owner}/{repo}"},
                "difficulty": difficulty
            }
            
            # Cache the result
            cache.set("repo_issues", cache_key, result)
            return result
            
        except Exception as e:
            print(f"Error fetching issues: {e}")
            return {"issues": [], "totalCount": 0, "error": str(e)}

    def _filter_issues_by_difficulty(self, issues: List[dict], difficulty: str) -> List[dict]:
        """Filter issues based on difficulty labels"""
        difficulty_labels = {
            "beginner": ["good first issue", "beginner", "first-timers-only", "help wanted"],
            "easy": ["easy", "simple", "low-hanging-fruit"],
            "medium": ["enhancement", "feature", "improvement", "medium"],
            "hard": ["bug", "hard", "advanced", "complex", "expert"]
        }
        
        target_labels = difficulty_labels.get(difficulty, [])
        if not target_labels:
            return issues
        
        filtered_issues = []
        for issue in issues:
            issue_labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
            if any(target_label in " ".join(issue_labels) for target_label in target_labels):
                filtered_issues.append(issue)
        
        return filtered_issues

    async def get_repository_info(self, repo_url: str) -> dict:
        """Get repository information"""
        try:
            parsed = self.parse_github_url(repo_url)
            owner, repo = parsed["owner"], parsed["repo"]
            
            # Check cache first
            cache_key = f"{owner}_{repo}"
            cached_info = cache.get("repo_info", cache_key)
            if cached_info is not None:
                return cached_info
            
            url = f"{self.base_url}/repos/{owner}/{repo}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    repo_data = response.json()
                    result = {
                        "name": repo_data["name"],
                        "fullName": repo_data["full_name"],
                        "description": repo_data.get("description"),
                        "stars": repo_data["stargazers_count"],
                        "forks": repo_data["forks_count"],
                        "language": repo_data.get("language"),
                        "openIssues": repo_data["open_issues_count"],
                        "url": repo_data["html_url"]
                    }
                    
                    # Cache the result
                    cache.set("repo_info", cache_key, result)
                    return result
                else:
                    return {"error": f"Repository not found: {response.status_code}"}
                    
        except Exception as e:
            print(f"Error fetching repository info: {e}")
            return {"error": str(e)}

# Initialize global service
github_service = GitHubService()
