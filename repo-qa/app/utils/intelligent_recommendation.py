"""
Enhanced Intelligent Repository Recommendation System
This module provides personalized repository recommendations based on comprehensive user profiling
and advanced GitHub API analysis.
"""

import asyncio
import time
import math
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from app.utils.cache import cache
from app.utils.config import GITHUB_TOKEN

# Enhanced headers with more specific accept types
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
} if GITHUB_TOKEN else {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

class UserProfile:
    """Enhanced user profile for personalized recommendations"""
    
    def __init__(self, preferences: Dict[str, Any]):
        # Core preferences
        self.tech_stack = preferences.get('selected_tech', [])
        self.primary_language = preferences.get('primary_language', '')
        self.experience_level = preferences.get('experience_level', 'intermediate')  # beginner, intermediate, expert
        
        # Repository preferences
        self.min_stars = preferences.get('min_stars', 100)
        self.max_stars = preferences.get('max_stars', None)
        self.min_forks = preferences.get('min_forks', 10)
        self.activity_preference = preferences.get('activity_preference', 'active')  # active, stable, any
        self.license_preference = preferences.get('license_preferences', [])  # mit, apache-2.0, gpl-3.0, etc.
        
        # Contribution preferences
        self.contribution_types = preferences.get('contribution_types', [])
        self.issue_complexity = preferences.get('issue_complexity', 'medium')
        
        # Learning preferences
        self.learning_style = preferences.get('learning_style', 'hands_on')  # hands_on, documentation, examples
        
        # User context
        self.github_username = preferences.get('github_username', '')
        self.current_skill_areas = preferences.get('current_skills', [])
        self.wanted_skill_areas = preferences.get('wanted_skills', [])
        
    def get_search_weight_factors(self) -> Dict[str, float]:
        """Get weight factors for different aspects based on user profile"""
        weights = {
            'stars': 1.0,
            'forks': 0.7,
            'issues': 0.5,
            'activity': 1.2 if self.activity_preference == 'active' else 0.8,
            'documentation': 1.5 if self.learning_style == 'documentation' else 1.0,
            'examples': 1.3 if self.learning_style == 'examples' else 1.0,
            'beginner_friendly': 1.8 if self.experience_level == 'beginner' else 0.9,
            'complexity': 0.8 if self.experience_level == 'beginner' else 1.2,
            'established': 1.3,
            'trending': 1.2
        }
        return weights

class IntelligentRepositorySearch:
    """Advanced repository search with multiple strategies and deep analysis"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    async def get_personalized_recommendations(self, user_profile: UserProfile, limit: int = 100) -> List[Dict[str, Any]]:
        """Get personalized repository recommendations using multiple strategies"""
        print(f"[INFO] Getting personalized recommendations for user profile...")
        
        # Strategy 1: User's GitHub activity analysis (if username provided)
        user_activity_repos = []
        if user_profile.github_username:
            user_activity_repos = await self._analyze_user_github_activity(user_profile.github_username)
        
        # Strategy 2: Smart technology-based search
        tech_based_repos = await self._smart_technology_search(user_profile)
        
        # Strategy 3: Trending repositories in user's areas
        trending_repos = await self._get_trending_repositories(user_profile)
        
        # Strategy 4: Learning path recommendations
        learning_repos = await self._get_learning_path_repos(user_profile)
        
        # Combine and deduplicate
        all_repos = self._combine_and_deduplicate([
            user_activity_repos,
            tech_based_repos,
            trending_repos,
            learning_repos
        ])
        
        print(f"[INFO] Found {len(all_repos)} unique repositories before analysis")
        
        # Deep analysis and scoring
        analyzed_repos = await self._deep_analyze_repositories(all_repos, user_profile)
        
        # Sort by personalized score
        analyzed_repos.sort(key=lambda x: x.get('personalized_score', 0), reverse=True)
        
        print(f"[INFO] Returning {min(len(analyzed_repos), limit)} repositories after analysis")
        
        return analyzed_repos[:limit]
    
    async def _analyze_user_github_activity(self, username: str) -> List[Dict[str, Any]]:
        """Analyze user's GitHub activity to find similar repositories"""
        print(f"[INFO] Analyzing GitHub activity for user: {username}")
        
        try:
            # Get user's starred repositories
            starred_repos = await self._get_user_starred_repos(username)
            
            # Get user's repositories
            user_repos = await self._get_user_repositories(username)
            
            # Get user's following activity
            following_activity = await self._get_user_following_activity(username)
            
            # Analyze patterns and find similar repositories
            similar_repos = await self._find_similar_repositories(starred_repos, user_repos)
            
            return similar_repos[:50]  # Return top 50 from user activity analysis
            
        except Exception as e:
            print(f"[WARNING] Could not analyze user activity: {e}")
            return []
    
    async def _get_user_starred_repos(self, username: str) -> List[Dict[str, Any]]:
        """Get user's starred repositories"""
        cache_key = f"user_starred_{username}"
        cached = cache.get("user_activity", cache_key)
        if cached:
            return cached
        
        try:
            url = f"https://api.github.com/users/{username}/starred"
            response = self.session.get(url, params={"per_page": 100})
            
            if response.status_code == 200:
                starred = response.json()
                cache.set("user_activity", cache_key, starred)
                return starred
        except Exception as e:
            print(f"[WARNING] Error getting starred repos: {e}")
        
        return []
    
    async def _get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get user's own repositories"""
        cache_key = f"user_repos_{username}"
        cached = cache.get("user_activity", cache_key)
        if cached:
            return cached
        
        try:
            url = f"https://api.github.com/users/{username}/repos"
            response = self.session.get(url, params={"per_page": 100, "sort": "updated"})
            
            if response.status_code == 200:
                repos = response.json()
                cache.set("user_activity", cache_key, repos)
                return repos
        except Exception as e:
            print(f"[WARNING] Error getting user repos: {e}")
        
        return []
    
    async def _get_user_following_activity(self, username: str) -> List[Dict[str, Any]]:
        """Get activity from users that this user follows"""
        try:
            # Get following list
            url = f"https://api.github.com/users/{username}/following"
            response = self.session.get(url, params={"per_page": 20})
            
            if response.status_code == 200:
                following = response.json()
                
                # Get recent activity from a few key people they follow
                activity_repos = []
                for user in following[:5]:  # Limit to avoid too many API calls
                    user_repos = await self._get_user_repositories(user['login'])
                    activity_repos.extend(user_repos[:5])  # Top 5 repos from each followed user
                
                return activity_repos
        except Exception as e:
            print(f"[WARNING] Error getting following activity: {e}")
        
        return []
    
    async def _smart_technology_search(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Smart search based on technology stack with context awareness"""
        print(f"[INFO] Performing smart technology search...")
        
        search_queries = []
        
        # Primary language focused search
        if user_profile.primary_language:
            primary_query = self._build_primary_language_query(user_profile)
            search_queries.append(primary_query)
        
        # Multi-tech stack search
        if len(user_profile.tech_stack) > 1:
            combo_query = self._build_tech_combination_query(user_profile)
            search_queries.append(combo_query)
        
        # Execute searches
        all_repos = []
        for query in search_queries[:3]:  # Limit queries to avoid rate limits
            try:
                print(f"[INFO] Executing query: {query[:100]}...")
                repos = await self._execute_search_query(query, per_page=100)  # Increased from 50
                all_repos.extend(repos)
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"[WARNING] Query failed: {e}")
                continue
        
        return self._deduplicate_repos(all_repos)
    
    def _build_primary_language_query(self, user_profile: UserProfile) -> str:
        """Build a sophisticated query for the primary language"""
        query_parts = [f"language:{user_profile.primary_language}"]
        
        # Add experience level filters
        if user_profile.experience_level == 'beginner':
            query_parts.extend([
                "good-first-issues:>3"
            ])
        elif user_profile.experience_level == 'expert':
            query_parts.extend([
                "forks:>50"
            ])
        
        # Add activity filters
        if user_profile.activity_preference == 'active':
            recent_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            query_parts.append(f"pushed:>{recent_date}")
        
        # Add stars filter based on experience
        min_stars = user_profile.min_stars
        if user_profile.experience_level == 'beginner':
            min_stars = max(min_stars, 200)  # Beginners get more established repos
        
        query_parts.append(f"stars:>={min_stars}")
        
        return " ".join(query_parts)
    
    def _build_tech_combination_query(self, user_profile: UserProfile) -> str:
        """Build query for technology combinations"""
        # Create combinations of technologies
        tech_combinations = []
        primary = user_profile.primary_language or user_profile.tech_stack[0]
        
        for tech in user_profile.tech_stack:
            if tech != primary:
                combo = f"language:{primary} topic:{tech.lower()}"
                tech_combinations.append(combo)
        
        if tech_combinations:
            query = f"({' OR '.join(tech_combinations)}) stars:>={user_profile.min_stars}"
            
            # Add context
            if user_profile.activity_preference == 'active':
                query += " pushed:>2024-01-01"
                
            return query
        
        return f"language:{primary} stars:>={user_profile.min_stars}"
    
    def _build_domain_tech_query(self, user_profile: UserProfile, domain: str) -> str:
        """Build domain-specific technology queries"""
        domain_keywords = {
            'web_development': ['web', 'frontend', 'backend', 'fullstack', 'api', 'server'],
            'mobile_development': ['mobile', 'ios', 'android', 'react-native', 'flutter', 'app'],
            'data_science': ['data', 'analytics', 'machine-learning', 'ai', 'ml', 'statistics'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci-cd', 'deployment', 'infrastructure'],
            'game_development': ['game', 'gamedev', 'unity', 'unreal', 'graphics', '3d'],
            'blockchain': ['blockchain', 'cryptocurrency', 'web3', 'smart-contracts', 'defi'],
            'cybersecurity': ['security', 'cryptography', 'penetration-testing', 'vulnerability'],
            'iot': ['iot', 'arduino', 'raspberry-pi', 'embedded', 'sensors'],
            'fintech': ['fintech', 'finance', 'trading', 'payments', 'banking'],
            'healthtech': ['health', 'medical', 'healthcare', 'telemedicine', 'biotech']
        }
        
        keywords = domain_keywords.get(domain.lower().replace(' ', '_'), [domain.lower()])
        topic_queries = [f"topic:{keyword}" for keyword in keywords[:3]]
        
        query = f"({' OR '.join(topic_queries)})"
        
        if user_profile.primary_language:
            query += f" language:{user_profile.primary_language}"
        
        query += f" stars:>={user_profile.min_stars}"
        
        return query
    
    async def _goal_oriented_search(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Search based on user's specific goals"""
        print(f"[INFO] Performing goal-oriented search...")
        
        goal_queries = []
        
        for goal in user_profile.project_goals:
            if goal == 'learning':
                query = self._build_learning_query(user_profile)
            elif goal == 'contributing':
                query = self._build_contributing_query(user_profile)
            elif goal == 'building':
                query = self._build_building_query(user_profile)
            elif goal == 'research':
                query = self._build_research_query(user_profile)
            else:
                continue
            
            goal_queries.append(query)
        
        # Execute goal-based searches
        all_repos = []
        for query in goal_queries:
            try:
                repos = await self._execute_search_query(query, per_page=100)  # Increased to get more repos
                all_repos.extend(repos)
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"[WARNING] Goal query failed: {e}")
                continue
        
        return self._deduplicate_repos(all_repos)
    
    def _build_learning_query(self, user_profile: UserProfile) -> str:
        """Build query for learning-focused repositories"""
        query_parts = []
        
        if user_profile.primary_language:
            query_parts.append(f"language:{user_profile.primary_language}")
        
        # Learning-specific filters
        query_parts.extend([
            "stars:>=100",  # Well-regarded learning resources
            "size:<30000"   # Not too complex for learning
        ])
        
        return " ".join(query_parts)
    
    def _build_contributing_query(self, user_profile: UserProfile) -> str:
        """Build query for contribution-focused repositories"""
        query_parts = [
            "help-wanted-issues:>2"
        ]
        
        if user_profile.primary_language:
            query_parts.append(f"language:{user_profile.primary_language}")
        
        # Contribution-friendly filters
        query_parts.extend([
            f"stars:>={user_profile.min_stars}",
            "archived:false"
        ])
        
        # Add recent activity
        recent_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        query_parts.append(f"pushed:>{recent_date}")
        
        return " ".join(query_parts)
    
    def _build_building_query(self, user_profile: UserProfile) -> str:
        """Build query for building/development focused repositories"""
        query_parts = []
        
        if user_profile.primary_language:
            query_parts.append(f"language:{user_profile.primary_language}")
        
        # Building-focused filters
        query_parts.extend([
            f"stars:>={user_profile.min_stars}",
            "forks:>20",  # Proven utility
            "archived:false"
        ])
        
        # Add recent activity
        recent_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        query_parts.append(f"pushed:>{recent_date}")
        
        return " ".join(query_parts)
    
    def _build_research_query(self, user_profile: UserProfile) -> str:
        """Build query for research-oriented repositories"""
        query_parts = []
        
        if user_profile.primary_language:
            query_parts.append(f"language:{user_profile.primary_language}")
        
        # Research-specific filters
        query_parts.extend([
            "stars:>=50",
            "archived:false"
        ])
        
        return " ".join(query_parts)
    
    async def _get_trending_repositories(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Get trending repositories in user's technology areas"""
        print(f"[INFO] Getting trending repositories...")
        
        # GitHub doesn't have a direct trending API, so we simulate with recent popular repos
        trending_query = self._build_trending_query(user_profile)
        
        try:
            repos = await self._execute_search_query(trending_query, per_page=100)  # Increased to get more repos
            return repos
        except Exception as e:
            print(f"[WARNING] Trending search failed: {e}")
            return []
    
    def _build_trending_query(self, user_profile: UserProfile) -> str:
        """Build query for trending repositories"""
        # Recent repositories with good activity
        recent_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        query_parts = [
            f"pushed:>{recent_date}",
            "stars:>50",  # Good activity indicator
            "archived:false"
        ]
        
        if user_profile.primary_language:
            query_parts.append(f"language:{user_profile.primary_language}")
        
        return " ".join(query_parts)
    
    async def _get_learning_path_repos(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Get repositories that form a learning path for the user"""
        print(f"[INFO] Building learning path repositories...")
        
        learning_repos = []
        
        # Based on current skills vs wanted skills
        skill_gap_repos = await self._find_skill_gap_repos(user_profile)
        learning_repos.extend(skill_gap_repos)
        
        # Progressive difficulty repos
        progressive_repos = await self._find_progressive_difficulty_repos(user_profile)
        learning_repos.extend(progressive_repos)
        
        return self._deduplicate_repos(learning_repos)
    
    async def _find_skill_gap_repos(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Find repositories that help bridge skill gaps"""
        gap_repos = []
        
        for wanted_skill in user_profile.wanted_skill_areas[:3]:  # Limit to 3 skills
            if wanted_skill not in user_profile.current_skill_areas:
                # This is a skill gap - find learning resources
                query = f"stars:>=100 archived:false"
                
                if user_profile.primary_language:
                    query += f" language:{user_profile.primary_language}"
                
                try:
                    repos = await self._execute_search_query(query, per_page=5)
                    gap_repos.extend(repos)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[WARNING] Skill gap search failed for {wanted_skill}: {e}")
                    continue
        
        return gap_repos
    
    async def _find_progressive_difficulty_repos(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Find repositories with progressive difficulty for learning"""
        if user_profile.experience_level == 'expert':
            return []  # Experts don't need progressive learning
        
        # Simple progressive search
        progressive_repos = []
        
        query = f"stars:>=100 archived:false"
        
        if user_profile.primary_language:
            query += f" language:{user_profile.primary_language}"
        
        try:
            repos = await self._execute_search_query(query, per_page=5)
            for repo in repos:
                repo['learning_level'] = user_profile.experience_level
            progressive_repos.extend(repos)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[WARNING] Progressive difficulty search failed: {e}")
        
        return progressive_repos
    
    async def _execute_search_query(self, query: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Execute a GitHub search query with caching and rate limiting protection"""
        cache_key = f"search_{hash(query)}_{per_page}"
        cached = cache.get("search_results", cache_key)
        if cached:
            return cached
        
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                repos = response.json().get("items", [])
                cache.set("search_results", cache_key, repos)
                return repos
            elif response.status_code == 403:
                print("[WARNING] Rate limit hit, using cached results only")
                return []
            elif response.status_code == 422:
                print(f"[WARNING] Invalid search query: {query[:100]}...")
                return []
            else:
                print(f"[WARNING] Search failed with status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Search query execution failed: {e}")
            return []
    
    def _combine_and_deduplicate(self, repo_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine multiple repository lists and remove duplicates"""
        seen_ids = set()
        combined = []
        
        for repo_list in repo_lists:
            for repo in repo_list:
                repo_id = repo.get('id')
                if repo_id and repo_id not in seen_ids:
                    seen_ids.add(repo_id)
                    combined.append(repo)
        
        return combined
    
    def _deduplicate_repos(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate repositories"""
        seen_ids = set()
        unique_repos = []
        
        for repo in repos:
            repo_id = repo.get('id')
            if repo_id and repo_id not in seen_ids:
                seen_ids.add(repo_id)
                unique_repos.append(repo)
        
        return unique_repos
    
    async def _find_similar_repositories(self, starred_repos: List[Dict], user_repos: List[Dict]) -> List[Dict[str, Any]]:
        """Find repositories similar to user's starred and own repositories"""
        similar_repos = []
        
        # Analyze user's technology preferences from their activity
        tech_preferences = self._analyze_tech_preferences(starred_repos + user_repos)
        
        # Find repositories with similar technology stacks
        for tech in tech_preferences[:3]:  # Top 3 technologies
            query = f"language:{tech} stars:>=100 forks:>=20"
            try:
                repos = await self._execute_search_query(query, per_page=15)
                similar_repos.extend(repos)
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"[WARNING] Similar repo search failed for {tech}: {e}")
                continue
        
        return similar_repos
    
    def _analyze_tech_preferences(self, repos: List[Dict]) -> List[str]:
        """Analyze technology preferences from repository list"""
        tech_count = {}
        
        for repo in repos:
            language = repo.get('language')
            if language:
                tech_count[language] = tech_count.get(language, 0) + 1
            
            # Also count topics as technologies
            for topic in repo.get('topics', []):
                if topic in ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'cpp', 'c++']:
                    tech_count[topic] = tech_count.get(topic, 0) + 0.5
        
        # Sort by frequency
        sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
        return [tech for tech, count in sorted_tech]
    
    async def _check_good_first_issues(self, repo_name: str) -> Dict[str, Any]:
        """Get the number of open issues in the repository"""
        cache_key = f"open_issues_{repo_name}"
        cached = cache.get("open_issues", cache_key)
        if cached:
            print(f"[DEBUG] Using cached open issues data for {repo_name}: {cached}")
            return cached
        
        try:
            print(f"[DEBUG] Making API call to get open issues count for {repo_name}")
            
            # Get repository info which includes open issues count
            repo_url = f"https://api.github.com/repos/{repo_name}"
            response = self.session.get(repo_url, timeout=5)
            
            if response.status_code == 200:
                repo_data = response.json()
                open_issues_count = repo_data.get('open_issues_count', 0)
                
                print(f"[DEBUG] Found {open_issues_count} open issues in {repo_name}")
                
                result = {
                    'has_good_first_issues': open_issues_count > 0,
                    'good_first_issue_count': open_issues_count
                }
                
                print(f"[DEBUG] Final open issues result for {repo_name}: {result}")
                cache.set("open_issues", cache_key, result)
                return result
                
            elif response.status_code == 403:
                print(f"[WARNING] Rate limited while checking {repo_name}")
            else:
                print(f"[WARNING] API error {response.status_code} for {repo_name}")
                
        except Exception as e:
            print(f"[ERROR] Failed to get open issues count for {repo_name}: {e}")
        
        # Default values if check fails
        return {'has_good_first_issues': False, 'good_first_issue_count': 0}

    async def _deep_analyze_repositories(self, repos: List[Dict[str, Any]], user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Perform deep analysis on repositories and calculate personalized scores"""
        print(f"[INFO] Performing deep analysis on {len(repos)} repositories...")
        
        if len(repos) == 0:
            print("[WARNING] No repositories to analyze!")
            return []
        
        analyzed_repos = []
        weight_factors = user_profile.get_search_weight_factors()
        gfi_found_count = 0
        
        for i, repo in enumerate(repos[:150]):  # Increased from 50 to process more repositories
            try:
                if i % 20 == 0:
                    print(f"[INFO] Analyzed {i}/{min(len(repos), 150)} repositories...")
                
                # Use basic data but enhance with good first issues check
                enhanced_repo = repo.copy()
                
                # Check for good first issues specifically for every repository
                repo_name = repo.get('full_name')
                if repo_name:
                    print(f"[DEBUG] Checking good first issues for {repo_name}")
                    gfi_data = await self._check_good_first_issues(repo_name)
                    enhanced_repo.update(gfi_data)
                    
                    # Debug logging for good first issues
                    if gfi_data.get('has_good_first_issues'):
                        gfi_found_count += 1
                        print(f"[DEBUG] ✅ Found {gfi_data.get('good_first_issue_count', 0)} good first issues in {repo_name}")
                    else:
                        print(f"[DEBUG] ❌ No good first issues found in {repo_name}")
                    
                    await asyncio.sleep(0.15)  # Slightly longer delay to be respectful to API
                else:
                    # Set default values if no repo name
                    enhanced_repo['has_good_first_issues'] = False
                    enhanced_repo['good_first_issue_count'] = 0
                
                # Calculate personalized score
                personalized_score = self._calculate_personalized_score(enhanced_repo, user_profile, weight_factors)
                enhanced_repo['personalized_score'] = personalized_score
                
                # Add relevance explanation
                enhanced_repo['relevance_reasons'] = self._generate_relevance_explanation(enhanced_repo, user_profile)
                
                analyzed_repos.append(enhanced_repo)
                
            except Exception as e:
                print(f"[WARNING] Failed to analyze repo {repo.get('full_name', 'unknown')}: {e}")
                # Add with basic score
                repo['personalized_score'] = 50.0
                repo['relevance_reasons'] = ["Basic match"]
                repo['has_good_first_issues'] = False
                repo['good_first_issue_count'] = 0
                analyzed_repos.append(repo)
                continue
        
        print(f"[INFO] Analysis complete: {gfi_found_count} repositories have good first issues out of {len(analyzed_repos)} total")
        return analyzed_repos
    
    async def _enhance_repository_data(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance repository with additional data from GitHub API"""
        repo_name = repo.get('full_name')
        if not repo_name:
            return repo
        
        # Check cache first
        cache_key = f"enhanced_{repo_name}"
        cached = cache.get("enhanced_repos", cache_key)
        if cached:
            return {**repo, **cached}
        
        enhanced_data = {}
        
        try:
            # Get repository details
            repo_url = f"https://api.github.com/repos/{repo_name}"
            response = self.session.get(repo_url, timeout=5)
            
            if response.status_code == 200:
                repo_details = response.json()
                
                enhanced_data.update({
                    'has_wiki': repo_details.get('has_wiki', False),
                    'has_pages': repo_details.get('has_pages', False),
                    'license': repo_details.get('license', {}).get('key') if repo_details.get('license') else None,
                    'default_branch': repo_details.get('default_branch', 'main'),
                    'subscribers_count': repo_details.get('subscribers_count', 0),
                    'network_count': repo_details.get('network_count', 0),
                    'created_at': repo_details.get('created_at'),
                    'pushed_at': repo_details.get('pushed_at'),
                })
            
            # Get issues to check for good first issues
            issues_url = f"https://api.github.com/repos/{repo_name}/issues"
            issues_response = self.session.get(issues_url, params={
                "state": "open", 
                "labels": "good first issue,good-first-issue,beginner,help wanted",
                "per_page": 10
            }, timeout=5)
            
            if issues_response.status_code == 200:
                issues = issues_response.json()
                enhanced_data['recent_issues'] = len(issues)
                enhanced_data['has_good_first_issues'] = len(issues) > 0
                
                # Check for specific good first issue labels
                good_first_issue_count = 0
                for issue in issues:
                    labels = [label.get('name', '').lower() for label in issue.get('labels', [])]
                    if any(gfi_label in labels for gfi_label in ['good first issue', 'good-first-issue', 'beginner', 'good first issues']):
                        good_first_issue_count += 1
                
                enhanced_data['good_first_issue_count'] = good_first_issue_count
                enhanced_data['has_good_first_issues'] = good_first_issue_count > 0
            else:
                # Fallback: check if repo has help-wanted-issues from search
                enhanced_data['has_good_first_issues'] = repo.get('has_issues', False)
                enhanced_data['good_first_issue_count'] = 0
            
            # Cache the enhanced data
            cache.set("enhanced_repos", cache_key, enhanced_data)
            
        except Exception as e:
            print(f"[WARNING] Failed to enhance repo {repo_name}: {e}")
            # Set default values
            enhanced_data['has_good_first_issues'] = False
            enhanced_data['good_first_issue_count'] = 0
        
        return {**repo, **enhanced_data}
    
    def _calculate_personalized_score(self, repo: Dict[str, Any], user_profile: UserProfile, weight_factors: Dict[str, float]) -> float:
        """Calculate a personalized relevance score for the repository"""
        score = 0.0
        
        # Base popularity score (normalized)
        stars = repo.get('stargazers_count', 0)
        forks = repo.get('forks_count', 0)
        
        # Logarithmic scaling to prevent huge repos from dominating
        star_score = math.log10(max(stars, 1)) * 10 * weight_factors['stars']
        fork_score = math.log10(max(forks, 1)) * 5 * weight_factors['forks']
        
        score += star_score + fork_score
        
        # Activity score
        if repo.get('pushed_at'):
            try:
                last_push = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
                days_since_push = (datetime.now(last_push.tzinfo) - last_push).days
                
                if days_since_push <= 7:
                    activity_score = 20
                elif days_since_push <= 30:
                    activity_score = 15
                elif days_since_push <= 90:
                    activity_score = 10
                elif days_since_push <= 365:
                    activity_score = 5
                else:
                    activity_score = 0
                
                score += activity_score * weight_factors['activity']
            except:
                pass
        
        # Language match score
        repo_language = repo.get('language', '').lower()
        if repo_language == user_profile.primary_language.lower():
            score += 25
        elif repo_language in [tech.lower() for tech in user_profile.tech_stack]:
            score += 15
        
        # Topics match score
        repo_topics = [topic.lower() for topic in repo.get('topics', [])]
        user_interests = [tech.lower() for tech in user_profile.tech_stack]
        
        topic_matches = len(set(repo_topics) & set(user_interests))
        score += topic_matches * 10
        
        # Experience level appropriateness
        if user_profile.experience_level == 'beginner':
            if repo.get('has_good_first_issues'):
                score += 25 * weight_factors['beginner_friendly']
            
            gfi_count = repo.get('good_first_issue_count', 0)
            if gfi_count > 0:
                score += min(gfi_count * 5, 20) * weight_factors['beginner_friendly']  # Up to 20 extra points
            
            if 'tutorial' in repo_topics or 'learning' in repo_topics:
                score += 15 * weight_factors['beginner_friendly']
            # Penalize overly complex projects for beginners
            if stars > 50000:
                score -= 10
        
        elif user_profile.experience_level == 'expert':
            if stars > 5000:  # Established, serious projects
                score += 15 * weight_factors['complexity']
            if 'advanced' in repo_topics or 'performance' in repo_topics:
                score += 10 * weight_factors['complexity']
        
        # License preference
        repo_license = repo.get('license')
        if isinstance(repo_license, dict):
            repo_license = repo_license.get('key')
        
        if repo_license and repo_license in user_profile.license_preference:
            score += 10
        
        # Contribution friendliness
        if user_profile.contribution_types:  # Only if user specified contribution preferences
            if repo.get('has_good_first_issues'):
                score += 20
            
            gfi_count = repo.get('good_first_issue_count', 0)
            if gfi_count > 0:
                score += min(gfi_count * 3, 15)  # Up to 15 extra points for multiple good first issues
            
            if repo.get('recent_issues', 0) > 0:
                score += 10
            
            contributor_count = repo.get('contributor_count', 0)
            if 5 <= contributor_count <= 50:  # Sweet spot for contribution
                score += 15
        
        # Learning value (always considered for all users)
        if repo.get('has_wiki'):
            score += 10 * weight_factors['documentation']
        if repo.get('has_pages'):
            score += 8 * weight_factors['documentation']
        if any(term in repo.get('description', '').lower() for term in ['example', 'tutorial', 'demo', 'sample']):
            score += 12 * weight_factors['examples']
        
        # Repository size penalty for very large projects (to keep manageable)
        repo_size = repo.get('size', 0)
        if repo_size > 200000:  # Very large projects might be overwhelming
            score -= 5
        
        return max(score, 0)  # Ensure non-negative score
    
    def _generate_relevance_explanation(self, repo: Dict[str, Any], user_profile: UserProfile) -> List[str]:
        """Generate human-readable explanation of why this repo is relevant"""
        reasons = []
        
        # Language match
        repo_language = repo.get('language', '')
        if repo_language.lower() == user_profile.primary_language.lower():
            reasons.append(f"Uses your primary language: {repo_language}")
        elif repo_language.lower() in [tech.lower() for tech in user_profile.tech_stack]:
            reasons.append(f"Uses technology in your stack: {repo_language}")
        
        # Topic matches
        repo_topics = repo.get('topics', [])
        user_interests = [tech.lower() for tech in user_profile.tech_stack]
        
        matching_topics = list(set([topic.lower() for topic in repo_topics]) & set(user_interests))
        if matching_topics:
            reasons.append(f"Matches your tech stack: {', '.join(matching_topics[:3])}")
        
        # Experience level fit
        if user_profile.experience_level == 'beginner' and repo.get('has_good_first_issues'):
            gfi_count = repo.get('good_first_issue_count', 0)
            if gfi_count > 0:
                reasons.append(f"Has {gfi_count} good first issue{'s' if gfi_count != 1 else ''} for beginners")
            else:
                reasons.append("Has good first issues for beginners")
        
        # Contribution opportunities
        if user_profile.contribution_types and repo.get('has_good_first_issues'):
            gfi_count = repo.get('good_first_issue_count', 0)
            if gfi_count > 0:
                reasons.append(f"Great for contributions: {gfi_count} beginner-friendly issue{'s' if gfi_count != 1 else ''}")
            else:
                reasons.append("Good contribution opportunities available")
        
        # Learning value
        learning_indicators = []
        if repo.get('has_wiki'):
            learning_indicators.append("comprehensive documentation")
        if any(term in repo.get('description', '').lower() for term in ['tutorial', 'example', 'demo']):
            learning_indicators.append("educational content")
        if learning_indicators:
            reasons.append(f"Good for learning: {', '.join(learning_indicators)}")
        
        # Activity level
        if repo.get('pushed_at'):
            try:
                last_push = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
                days_since_push = (datetime.now(last_push.tzinfo) - last_push).days
                
                if days_since_push <= 30:
                    reasons.append("Recently active project")
            except:
                pass
        
        # Popularity appropriateness
        stars = repo.get('stargazers_count', 0)
        if stars >= 1000:
            reasons.append(f"Well-established project ({stars:,} stars)")
        elif stars >= 100:
            reasons.append("Growing project with community interest")
        
        # Default reason if nothing specific found
        if not reasons:
            reasons.append("Matches your technology preferences")
        
        return reasons[:4]  # Limit to 4 reasons for clarity

# Create global instance
intelligent_search = IntelligentRepositorySearch()
