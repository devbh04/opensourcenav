# main.py - Enhanced with Claude 4 Copilot-style capabilities, Intelligent Tutorial Generator, and Git Helper
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import traceback
import asyncio
import time
import os
import json
import re
import math
import httpx

from app.utils import github_loader, chunker, embedder, summarizer, qa
from app.utils.tutorial_generator import TutorialGenerator
from app.utils.enhanced_qa import handle_request, get_execution_history, get_code_analysis, initialize_enhanced_qa
from app.utils.github_utils_enhanced import (
    search_repositories_custom_query,
    repo_has_required_tech,
    get_repo_topics,
    analyze_repo_activity,
    calculate_repo_quality_score,
    build_advanced_queries,
    github_service
)
from app.utils.cache import cache
from app.utils.intelligent_recommendation import intelligent_search, UserProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import intelligent tutorial generation system (optional)
INTELLIGENT_TUTORIAL_AVAILABLE = False
try:
    from app.utils.flow_engine import create_shared_state
    from app.utils.nodes import (
        FetchRepo, IdentifyAbstractions, AnalyzeRelationships, 
        OrderChapters, WriteChapters, CombineTutorial
    )
    from app.utils.llm_integration import get_llm_stats
    INTELLIGENT_TUTORIAL_AVAILABLE = True
    logger.info("Intelligent tutorial generation system loaded successfully")
except ImportError as e:
    logger.warning(f"Intelligent tutorial generation system not available: {e}")
    # Create dummy function for get_llm_stats
    def get_llm_stats():
        return {"error": "LLM integration not available"}
import json
import faiss
import pickle

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class RepoRequest(BaseModel):
    repo_url: str

class TutorialRequest(BaseModel):
    repository_url: str
    custom_instructions: str = ""

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    context_chunks_used: int
    total_tokens_used: int
    context_strategy: str = "broad_exploration"
    intent_type: str = "general_info"
    context_quality: str = "standard"
    history_used: bool = False
    conversations_referenced: int = 0
    # Enhanced fields for coding tasks
    task_type: str = "question"
    tasks_completed: int = 0
    tasks_successful: int = 0
    files_modified: int = 0
    changes: List[Dict[str, Any]] = []
    validation_summary: Dict[str, int] = {}

class IntelligentTutorialRequest(BaseModel):
    repo_url: str = ""
    local_dir: str = ""
    project_name: str = ""
    output_dir: str = "tutorial_output"
    max_abstractions: int = 12
    min_abstractions: int = 5
    include_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.h", "*.md"]
    exclude_patterns: List[str] = ["node_modules/*", ".git/*", "__pycache__/*", "*.pyc", "dist/*", "build/*"]
    selected_files: List[str] = []  # Specific files to process (overrides patterns if provided)
    max_file_size: int = 100000
    # Frontend format support
    url: str = ""  # Alternative to repo_url for frontend compatibility
    includeFileTypes: str = ""  # Comma-separated quoted strings from frontend
    excludeFileTypes: str = ""  # Comma-separated quoted strings from frontend
    selectedFiles: List[str] = []  # Frontend format for selected files

class IntelligentTutorialResponse(BaseModel):
    success: bool
    message: str
    # Content fields for frontend
    tutorial_content: str = ""  # Full tutorial markdown content
    index_content: str = ""  # index.md content
    readme_content: str = ""  # README.md content
    quick_reference_content: str = ""  # Quick reference content
    chapters: List[Dict[str, Any]] = []  # Individual chapters with metadata
    abstractions: List[Dict[str, Any]] = []  # Identified abstractions
    relationships: List[str] = []  # Code relationships as strings
    metadata: Dict[str, Any] = {}  # Generation metadata
    # Legacy fields for compatibility
    output_directory: str = ""
    chapters_generated: int = 0
    abstractions_identified: int = 0
    relationships_found: int = 0
    execution_time: float = 0.0
    error: str = ""
    llm_stats: Dict[str, Any] = {}
    files_created: List[str] = []

class FrontendTutorialRequest(BaseModel):
    """Request model that matches frontend data structure"""
    url: str
    includeFileTypes: str  # Comma-separated quoted strings
    excludeFileTypes: str  # Comma-separated quoted strings
    selectedFiles: List[str] = []  # Specific files selected by user
    project_name: str = ""
    output_dir: str = "tutorial_output"
    max_abstractions: int = 12
    min_abstractions: int = 5
    max_file_size: int = 100000

# ===========================
# GIT HELPER MODELS
# ===========================

# Enhanced request models for intelligent recommendations
class EnhancedPreferencesRequest(BaseModel):
    # Core technology preferences
    selected_tech: List[str] = Field(..., description="Technologies you work with")
    primary_language: str = Field("", description="Your primary programming language")
    experience_level: str = Field("intermediate", description="beginner, intermediate, or expert")
    
    # Repository preferences
    min_stars: int = Field(100, description="Minimum star count")
    max_stars: Optional[int] = Field(None, description="Maximum star count")
    min_forks: int = Field(10, description="Minimum fork count")
    activity_preference: str = Field("active", description="active, stable, or any")
    license_preferences: List[str] = Field([], description="Preferred licenses")
    
    # Contribution preferences
    contribution_types: List[str] = Field([], description="Types of contributions you want to make")
    issue_complexity: str = Field("medium", description="low, medium, high")
    
    # Learning preferences
    learning_style: str = Field("hands_on", description="hands_on, documentation, examples")
    
    # User context (optional)
    github_username: str = Field("", description="Your GitHub username for personalized analysis")
    current_skills: List[str] = Field([], description="Skills you currently have")
    wanted_skills: List[str] = Field([], description="Skills you want to learn")

# Updated repository item model with enhanced information
class EnhancedRepoItem(BaseModel):
    id: int
    full_name: str
    description: Optional[str]
    html_url: str
    stargazers_count: int
    forks_count: int
    language: Optional[str]
    topics: List[str]
    created_at: str
    updated_at: str
    pushed_at: Optional[str]
    license: Optional[str]
    
    # Enhanced fields
    personalized_score: float = Field(0.0, description="Personalized relevance score")
    relevance_reasons: List[str] = Field([], description="Why this repo is relevant to you")
    learning_level: Optional[str] = Field(None, description="Difficulty level for learning")
    contributor_count: Optional[int] = Field(None, description="Number of contributors")
    has_good_first_issues: bool = Field(False, description="Has beginner-friendly issues")
    good_first_issue_count: int = Field(0, description="Number of good first issues")
    activity_score: float = Field(0.0, description="Recent activity score")
    
class EnhancedRepoRecommendationResponse(BaseModel):
    repositories: List[EnhancedRepoItem]
    total_found: int
    search_strategies_used: List[str]
    personalization_factors: Dict[str, Any]
    cache_info: Dict[str, Any]

# Legacy models (keep for backward compatibility)
class PreferencesRequest(BaseModel):
    """Git Helper: Repository recommendation preferences"""
    selected_tech: List[str] = Field(..., description="List of preferred languages/tech e.g. ['Python','React']")
    min_stars: int = Field(100, ge=0)
    min_forks: int = Field(0, ge=0)
    min_open_issues: int = Field(10, ge=0, description="Minimum number of open issues for repositories")
    domain_industry: str = Field("Any")
    project_complexity: str = Field("Any")  # Any | Beginner | Intermediate | Advanced
    contribution_type: str = Field("Any")   # Any | Documentation | Bug Fixes | Features | Testing | Design
    language_strict: bool = Field(False)
    per_page: int = Field(200, ge=1, le=1000)

class RepoItem(BaseModel):
    """Git Helper: Repository item in recommendations"""
    id: int
    full_name: str
    description: Optional[str]
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    language: Optional[str]
    updated_at: Optional[str]
    html_url: str
    topics: List[str] = []
    quality_score: Optional[float] = 0.0

class RecommendationResponse(BaseModel):
    """Git Helper: Repository recommendation response"""
    query: str
    broadened_query: Optional[str] = None
    total_found_before_filter: int
    total_recommended: int
    items: List[RepoItem]
    execution_time: float = 0.0
    cache_used: bool = False

class IssueRequest(BaseModel):
    """Git Helper: GitHub issue analysis request"""
    repoUrl: str
    state: Optional[str] = "open"
    perPage: Optional[int] = 100
    page: Optional[int] = 1
    difficulty: Optional[str] = "all"  # all | beginner | easy | medium | hard
    userQuery: Optional[str] = ""

class RepoInfoRequest(BaseModel):
    """Git Helper: Repository information request"""
    repoUrl: str

class Label(BaseModel):
    """Git Helper: GitHub issue label"""
    name: str
    color: str

class User(BaseModel):
    """Git Helper: GitHub user"""
    login: str

class Issue(BaseModel):
    """Git Helper: GitHub issue"""
    id: int
    title: str
    body: Optional[str]
    html_url: str
    state: str
    created_at: str
    user: User
    labels: List[Label]

class Repository(BaseModel):
    """Git Helper: Repository info for issues"""
    owner: str
    repo: str
    fullName: str

class IssuesResponse(BaseModel):
    """Git Helper: Issues analysis response"""
    issues: List[Issue]
    totalCount: int
    repository: Repository
    difficulty: str
    execution_time: float = 0.0

class RepositoryInfo(BaseModel):
    """Git Helper: Detailed repository information"""
    name: str
    fullName: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    openIssues: int
    url: str
    quality_score: Optional[float] = 0.0
    topics: List[str] = []

# ===========================
# Issue Resolution Models
# ===========================

class IssueResolutionRequest(BaseModel):
    """Request model for issue resolution system"""
    repo_url: str = Field(..., description="GitHub repository URL")
    issue_url: str = Field(..., description="GitHub issue URL")
    user_context: Optional[str] = Field("", description="Additional context about user's setup or preferences")
    include_related_issues: bool = Field(True, description="Include analysis of related issues")
    difficulty_preference: str = Field("detailed", description="brief, detailed, or comprehensive")

class IssueDetails(BaseModel):
    """GitHub issue details"""
    number: int
    title: str
    body: Optional[str]
    state: str
    labels: List[str]
    assignees: List[str]
    author: str
    created_at: str
    updated_at: str
    comments_count: int
    html_url: str

class ResolutionStep(BaseModel):
    """Individual step in issue resolution"""
    step_number: int
    title: str
    description: str
    commands: List[str] = Field([], description="Terminal commands to execute")
    code_changes: List[str] = Field([], description="Code modifications needed")
    files_to_check: List[str] = Field([], description="Files to examine or modify")
    estimated_time: str = Field("", description="Estimated time for this step")
    difficulty: str = Field("medium", description="easy, medium, hard")
    prerequisites: List[str] = Field([], description="What needs to be done before this step")

class RepositoryAnalysis(BaseModel):
    """Analysis of repository structure and context"""
    tech_stack: List[str]
    main_directories: List[str]
    key_files: List[str]
    testing_setup: str
    build_system: str
    documentation_quality: str
    contributor_guidelines: str

class IssueResolutionResponse(BaseModel):
    """Complete issue resolution guide"""
    issue_details: IssueDetails
    repository_analysis: RepositoryAnalysis
    resolution_summary: str
    resolution_steps: List[ResolutionStep]
    alternative_approaches: List[str] = Field([], description="Alternative ways to solve the issue")
    related_issues: List[str] = Field([], description="Links to related issues")
    helpful_resources: List[str] = Field([], description="Documentation, tutorials, or references")
    estimated_total_time: str
    difficulty_level: str
    skills_required: List[str]
    context_used: Dict[str, Any] = Field({}, description="Information about what repository context was used")
    execution_time: float = 0.0

# ===========================

def parse_file_patterns(pattern_string: str) -> List[str]:
    """Parse comma-separated quoted pattern strings from frontend"""
    import re
    try:
        # Remove extra whitespace and split by comma, then extract quoted strings
        patterns = re.findall(r'"([^"]*)"', pattern_string)
        return [pattern.strip() for pattern in patterns if pattern.strip()]
    except Exception as e:
        logger.warning(f"Error parsing file patterns: {e}")
        return []

def process_repo(repo_url: str) -> List[Dict]:
    """Helper to download, chunk, and embed a repository, then load data for QA."""
    # 1. Clear state and download repo
    qa.clear_chat_history()
    repo_path = github_loader.download_repo(repo_url)

    # 2. Chunk the files
    chunks = chunker.chunk_repo(repo_path)
    if not chunks:
        raise HTTPException(status_code=400, detail="No processable files found in repository")

    # 3. Create embeddings and save index/map
    embedder.embed_chunks(chunks)

    # 4. Dynamically reload the newly created index and doc_map into the qa module
    #    This ensures the Q&A system has the data from the *current* repo.
    print("[INFO] Reloading FAISS index and document map for the Q&A module...")
    qa.index = faiss.read_index("vector.index")
    with open("doc_map.pkl", "rb") as f:
        qa.doc_map = pickle.load(f)
    print("[SUCCESS] Q&A module is ready with the new repository data.")
    
    # 5. Initialize enhanced Q&A system with the new data
    initialize_enhanced_qa()
    print("[SUCCESS] Enhanced Q&A system initialized with repository data.")
    
    return chunks

# ===========================
# GIT HELPER UTILITY FUNCTIONS
# ===========================

def _complexity_match(stars: int, project_complexity: str) -> bool:
    """Check if repository complexity matches user preference"""
    if project_complexity == "Any":
        return True
    if project_complexity == "Beginner":
        return stars <= 500
    if project_complexity == "Intermediate":
        return 100 <= stars <= 2000
    if project_complexity == "Advanced":
        return stars > 1000
    return True

async def get_repository_recommendations(prefs: PreferencesRequest) -> RecommendationResponse:
    """Get repository recommendations based on user preferences"""
    start_time = time.time()
    
    if not prefs.selected_tech:
        raise HTTPException(status_code=400, detail="selected_tech must contain at least one technology")
    
    try:
        # Build multiple advanced search queries
        queries = build_advanced_queries(
            prefs.selected_tech,
            prefs.domain_industry,
            prefs.min_stars,
            prefs.min_forks,
            prefs.min_open_issues,
            prefs.contribution_type,
        )
        
        all_repos = []
        seen_ids = set()
        
        # Execute searches sequentially to respect rate limits
        for i, query in enumerate(queries):
            print(f"[INFO] Executing search query {i+1}/{len(queries)}: {query[:100]}...")
            
            try:
                repos = search_repositories_custom_query(
                    query, 
                    prefs.min_stars, 
                    per_page=min(prefs.per_page, 100),
                    max_results=200
                )
                
                for repo in repos:
                    if repo.get('id') not in seen_ids:
                        seen_ids.add(repo.get('id'))
                        all_repos.append(repo)
                
                # Add delay between queries to respect rate limits
                if i < len(queries) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"[WARNING] Query {i+1} failed: {e}")
                continue
        
        print(f"[INFO] Found {len(all_repos)} repositories before filtering")
        
        # Optimize filtering: limit repos to process and add early filtering
        max_repos_to_process = min(len(all_repos), 100)  # Limit to 100 repos for processing
        print(f"[INFO] Processing top {max_repos_to_process} repositories for detailed filtering")
        
        # Pre-filter by basic criteria before expensive operations
        pre_filtered_repos = []
        for repo in all_repos[:max_repos_to_process]:
            # Quick filters that don't require API calls
            if repo.get("stargazers_count", 0) < prefs.min_stars:
                continue
            if repo.get("forks_count", 0) < prefs.min_forks:
                continue
            if repo.get("open_issues_count", 0) < prefs.min_open_issues:
                continue
            if not _complexity_match(repo.get("stargazers_count", 0), prefs.project_complexity):
                continue
                
            pre_filtered_repos.append(repo)
        
        print(f"[INFO] {len(pre_filtered_repos)} repositories passed pre-filtering")
        
        # Enhanced filtering and scoring (now on smaller set)
        recommended = []
        processed_count = 0
        
        for repo in pre_filtered_repos[:50]:  # Further limit to top 50 for detailed processing
            try:
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"[INFO] Processed {processed_count}/{min(len(pre_filtered_repos), 50)} repositories...")
                
                # Strict language check (no API call needed)
                if prefs.language_strict and prefs.selected_tech:
                    primary_language = repo.get("language")
                    if primary_language not in prefs.selected_tech:
                        continue

                # Get topics (cached API call)
                topics = get_repo_topics(repo["full_name"]) or []
                
                # Contribution type post-filter via topics
                if prefs.contribution_type in ("Documentation", "Testing", "Design"):
                    need_topic_map = {
                        "Documentation": "documentation",
                        "Testing": "testing", 
                        "Design": "design",
                    }
                    need_topic = need_topic_map[prefs.contribution_type]
                    topics_lower = [t.lower() for t in topics]
                    if need_topic not in topics_lower:
                        continue

                # Enhanced tech verification (cached, but still expensive - do selectively)
                # Skip tech verification for now if we have many repos, rely on GitHub's search accuracy
                tech_verified = True
                if len(pre_filtered_repos) <= 20:  # Only do expensive verification for small sets
                    tech_verified = repo_has_required_tech(repo["full_name"], prefs.selected_tech)
                    if not tech_verified:
                        continue

                # Calculate quality score
                quality_score = calculate_repo_quality_score(repo)

                recommended.append(
                    RepoItem(
                        id=repo.get("id"),
                        full_name=repo.get("full_name"),
                        description=repo.get("description"),
                        stargazers_count=repo.get("stargazers_count", 0),
                        forks_count=repo.get("forks_count", 0),
                        open_issues_count=repo.get("open_issues_count", 0),
                        language=repo.get("language"),
                        updated_at=repo.get("updated_at"),
                        html_url=repo.get("html_url"),
                        topics=topics[:5] if topics else [],
                        quality_score=quality_score,
                    )
                )
                
            except Exception as e:
                print(f"[WARNING] Error processing repo {repo.get('full_name', 'unknown')}: {e}")
                continue

        # Sort by quality score
        recommended.sort(key=lambda x: x.quality_score, reverse=True)
        
        print(f"[INFO] {len(recommended)} repositories passed detailed filtering")
        
        # Fallback: if no recommendations, return top repositories with basic info (faster processing)
        if not recommended and pre_filtered_repos:
            print("[INFO] No repos passed strict filtering, providing fallback results")
            for repo in pre_filtered_repos[:15]:  # Limit fallback to 15 repos
                try:
                    # Get topics but skip expensive tech verification
                    topics = get_repo_topics(repo["full_name"]) or []
                    quality_score = calculate_repo_quality_score(repo)
                    
                    recommended.append(
                        RepoItem(
                            id=repo.get("id"),
                            full_name=repo.get("full_name"),
                            description=repo.get("description"),
                            stargazers_count=repo.get("stargazers_count", 0),
                            forks_count=repo.get("forks_count", 0),
                            open_issues_count=repo.get("open_issues_count", 0),
                            language=repo.get("language"),
                            updated_at=repo.get("updated_at"),
                            html_url=repo.get("html_url"),
                            topics=topics[:5] if topics else [],
                            quality_score=quality_score,
                        )
                    )
                except Exception as e:
                    print(f"[WARNING] Error in fallback processing: {e}")
                    continue

        execution_time = time.time() - start_time
        
        return RecommendationResponse(
            query=" | ".join(queries),
            total_found_before_filter=len(all_repos),
            total_recommended=len(recommended),
            items=recommended,
            execution_time=execution_time,
            cache_used=False  # Could be enhanced to track cache usage
        )
        
    except Exception as e:
        print(f"[ERROR] Repository recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.post("/generate-readme")
async def generate_readme(data: RepoRequest):
    """Generate README for a GitHub repository"""
    try:
        chunks = process_repo(data.repo_url)
        readme_content = summarizer.generate_readme(chunks)
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        return {"message": "README generated successfully", "readme": readme_content, "repository": data.repo_url}
    except Exception as e:
        print(f"[ERROR] /generate-readme failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate README: {str(e)}")

@app.post("/generate-tutorial", response_model=IntelligentTutorialResponse)
async def generate_tutorial(request: TutorialRequest):
    """Generate comprehensive tutorial using legacy method"""
    try:
        logger.info(f"Generating tutorial for repository: {request.repository_url}")
        
        # First process the repository to get chunks
        chunks = process_repo(request.repository_url)
        
        # Now create TutorialGenerator with chunks
        tg = TutorialGenerator(chunks)
        tutorial_data = tg.generate_tutorial()
        
        # Save the tutorial to TUTORIAL.md file
        if 'full_markdown' in tutorial_data:
            tutorial_content = tutorial_data['full_markdown']
            with open("TUTORIAL.md", "w", encoding="utf-8") as f:
                f.write(tutorial_content)
            logger.info("Tutorial saved to TUTORIAL.md")
        
        # Save tutorial data as JSON
        with open("tutorial_data.json", "w", encoding="utf-8") as f:
            json.dump(tutorial_data, f, indent=2)
        logger.info("Tutorial data saved to tutorial_data.json")
        
        # Count chapters in tutorial data
        chapters_count = 0
        if 'chapters_data' in tutorial_data:
            chapters_count = len(tutorial_data['chapters_data'])
        elif 'total_chapters' in tutorial_data:
            chapters_count = tutorial_data['total_chapters']
        
        return IntelligentTutorialResponse(
            success=True,
            message="Tutorial generated successfully using legacy method",
            chapters_generated=chapters_count,
            abstractions_identified=len(getattr(tg, 'abstractions', [])),
            relationships_found=len(getattr(tg, 'relationships', [])),
            execution_time=0.0,
            files_created=["TUTORIAL.md", "tutorial_data.json"]
        )
    except Exception as e:
        logger.error(f"Error generating tutorial: {str(e)}")
        logger.error(traceback.format_exc())
        return IntelligentTutorialResponse(
            success=False,
            message="Failed to generate tutorial",
            error=str(e)
        )

@app.post("/generate-intelligent-tutorial", response_model=IntelligentTutorialResponse)
async def generate_intelligent_tutorial(request: IntelligentTutorialRequest):
    """Generate comprehensive tutorial using the new intelligent system - returns content without saving files"""
    start_time = time.time()
    
    if not INTELLIGENT_TUTORIAL_AVAILABLE:
        return IntelligentTutorialResponse(
            success=False,
            message="Intelligent tutorial generation system is not available. Missing dependencies.",
            execution_time=time.time() - start_time,
            error="Required dependencies not installed (GitPython, etc.)"
        )
    
    try:
        logger.info(f"Starting intelligent tutorial generation (content-only mode)")
        
        # Handle both frontend and backend request formats
        repo_url = request.url or request.repo_url
        if not repo_url and not request.local_dir:
            raise ValueError("Either url/repo_url or local_dir must be provided")
        
        if repo_url == "a" or not repo_url:
            raise ValueError("Please provide a valid repository URL")
        
        # Parse frontend patterns if provided, otherwise use existing patterns
        if request.includeFileTypes or request.excludeFileTypes:
            include_patterns = parse_file_patterns(request.includeFileTypes) if request.includeFileTypes else request.include_patterns
            exclude_patterns = parse_file_patterns(request.excludeFileTypes) if request.excludeFileTypes else request.exclude_patterns
            selected_files = request.selectedFiles if request.selectedFiles else request.selected_files
        else:
            include_patterns = request.include_patterns
            exclude_patterns = request.exclude_patterns
            selected_files = request.selected_files
        
        logger.info(f"Request: repo_url={repo_url}, local_dir={request.local_dir}, project_name={request.project_name}")
        logger.info(f"Using {len(include_patterns)} include patterns and {len(exclude_patterns)} exclude patterns")
        if selected_files:
            logger.info(f"Processing {len(selected_files)} selected files")
        
        # Engage Q&A system if we have a repository URL (not local directory)
        if repo_url:
            logger.info("Engaging Q&A system for tutorial generation...")
            chunks = process_repo(repo_url)
            logger.info(f"Q&A system engaged with {len(chunks)} chunks from repository")
        
        # Auto-generate project name if not provided
        if not request.project_name:
            if repo_url:
                request.project_name = repo_url.split('/')[-1].replace('.git', '')
            else:
                request.project_name = os.path.basename(request.local_dir.rstrip('/'))
        
        # Create shared state
        shared_state = create_shared_state()
        
        # Initialize nodes (include CombineTutorial to generate content)
        nodes = {
            'fetch': FetchRepo(),
            'identify': IdentifyAbstractions(),
            'analyze': AnalyzeRelationships(),
            'order': OrderChapters(),
            'write': WriteChapters(),
            'combine': CombineTutorial()
        }
        
        # Execute the flow
        logger.info("Executing tutorial generation flow...")
        
        # Step 1: Fetch Repository with custom patterns
        fetch_input = {
            'repo_url': repo_url,
            'local_dir': request.local_dir,
            'include_patterns': include_patterns,
            'exclude_patterns': exclude_patterns,
            'selected_files': selected_files,
            'max_file_size': request.max_file_size
        }
        
        # Log the patterns being used for debugging
        logger.info(f"Include patterns: {include_patterns[:5]}..." if len(include_patterns) > 5 else f"Include patterns: {include_patterns}")
        logger.info(f"Exclude patterns: {exclude_patterns[:5]}..." if len(exclude_patterns) > 5 else f"Exclude patterns: {exclude_patterns}")
        
        # Update shared state with fetch input
        shared_state.update(fetch_input)
        fetch_result = nodes['fetch'].run(shared_state)
        
        if not fetch_result.success:
            raise ValueError(f"Repository fetch failed: {fetch_result.error}")
        
        if not shared_state.get('files'):
            raise ValueError("No files found in repository with the specified patterns")
        
        files_found = len(shared_state.get('files', []))
        logger.info(f"Successfully fetched {files_found} files from repository")
        
        # Step 2: Identify Abstractions
        identify_input = {
            'max_abstractions': request.max_abstractions,
            'min_abstractions': request.min_abstractions
        }
        shared_state.update(identify_input)
        identify_result = nodes['identify'].run(shared_state)
        
        if not identify_result.success:
            raise ValueError(f"Abstraction identification failed: {identify_result.error}")
        
        abstractions_found = len(shared_state.get('abstractions', []))
        if abstractions_found == 0:
            raise ValueError("No abstractions could be identified from the codebase")
        
        logger.info(f"Identified {abstractions_found} abstractions")
        
        # Step 3: Analyze Relationships
        analyze_result = nodes['analyze'].run(shared_state)
        
        if not analyze_result.success:
            raise ValueError(f"Relationship analysis failed: {analyze_result.error}")
        
        relationships_found = len(shared_state.get('relationships', []))
        logger.info(f"Analyzed {relationships_found} relationships")
        
        # Step 4: Order Chapters
        order_result = nodes['order'].run(shared_state)
        
        if not order_result.success:
            raise ValueError(f"Chapter ordering failed: {order_result.error}")
        
        if not shared_state.get('chapter_order'):
            raise ValueError("Failed to determine optimal chapter order")
        
        chapters_ordered = len(shared_state.get('chapter_order', []))
        logger.info(f"Ordered {chapters_ordered} chapters")
        
        # Step 5: Write Chapters
        write_result = nodes['write'].run(shared_state)
        
        if not write_result.success:
            raise ValueError(f"Chapter writing failed: {write_result.error}")
        
        if not shared_state.get('chapters'):
            raise ValueError("Failed to generate chapter content")
        
        chapters_written = len(shared_state.get('chapters', []))
        logger.info(f"Generated content for {chapters_written} chapters")
        
        # Step 6: Combine Tutorial (generate content without saving files)
        combine_input = {
            'project_name': request.project_name,
            'output_dir': "temp_output"  # Not used since we don't save files
        }
        shared_state.update(combine_input)
        combine_result = nodes['combine'].run(shared_state)
        
        if not combine_result.success:
            raise ValueError(f"Tutorial combination failed: {combine_result.error}")
        
        logger.info(f"Generated tutorial content for frontend")
        
        execution_time = time.time() - start_time
        
        # Get LLM statistics
        llm_stats = get_llm_stats()
        
        # Get content from shared state (generated by CombineTutorial node)
        tutorial_content = shared_state.get('tutorial_content', '')
        index_content = shared_state.get('index_content', '')
        readme_content = shared_state.get('readme_content', '')
        quick_reference_content = shared_state.get('quick_reference_content', '')
        
        # Extract content from CombineTutorial node
        tutorial_content = shared_state.get('tutorial_content', '')
        index_content = shared_state.get('index_content', '')
        readme_content = shared_state.get('readme_content', '')
        quick_reference_content = shared_state.get('quick_reference_content', '')
        
        # Handle relationships data structure
        relationships_data = shared_state.get('relationships', [])
        if isinstance(relationships_data, dict):
            relationships = [f"{key}: {value}" for key, value in relationships_data.items()]
        elif isinstance(relationships_data, list):
            relationships = relationships_data
        else:
            relationships = []
        
        # Collect results
        abstractions_count = len(shared_state.get('abstractions', []))
        relationships_count = len(relationships)
        chapters_count = len(shared_state.get('chapters', []))
        
        logger.info(f"✅ Tutorial generation completed successfully!")
        logger.info(f"📊 Results: {chapters_count} chapters, {abstractions_count} abstractions, {relationships_count} relationships")
        logger.info(f"⏱️ Execution time: {execution_time:.2f}s")
        logger.info(f"📄 Generated content: tutorial, index, readme, quick reference")
        
        return IntelligentTutorialResponse(
            success=True,
            message=f"Intelligent tutorial generated successfully for '{request.project_name}' with custom file patterns",
            tutorial_content=tutorial_content,
            index_content=index_content,
            readme_content=readme_content,
            quick_reference_content=quick_reference_content,
            chapters=shared_state.get('chapters', []),
            abstractions=shared_state.get('abstractions', []),
            relationships=relationships,
            metadata={
                "project_name": request.project_name,
                "files_processed": files_found,
                "chapters_generated": chapters_count,
                "abstractions_identified": abstractions_count,
                "relationships_found": relationships_count,
                "selected_files_used": len(selected_files) if selected_files else None,
                "include_patterns_used": len(include_patterns),
                "exclude_patterns_used": len(exclude_patterns)
            },
            # Legacy fields for compatibility
            output_directory="",  # Not applicable since we're not saving files
            chapters_generated=chapters_count,
            abstractions_identified=abstractions_count,
            relationships_found=relationships_count,
            execution_time=execution_time,
            llm_stats=llm_stats,
            files_created=[]  # No files created since we return content
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ Error in intelligent tutorial generation: {error_msg}")
        logger.error(traceback.format_exc())
        
        return IntelligentTutorialResponse(
            success=False,
            message="Failed to generate intelligent tutorial",
            execution_time=execution_time,
            error=error_msg,
            llm_stats=get_llm_stats()
        )

class FrontendTutorialResponse(BaseModel):
    """Response model for frontend tutorial generation with embedded content"""
    success: bool
    message: str
    tutorial_content: str = ""  # Full tutorial markdown content
    index_content: str = ""  # index.md content
    readme_content: str = ""  # README.md content
    quick_reference_content: str = ""  # Quick reference content
    chapters: List[Dict[str, Any]] = []  # Individual chapters with metadata
    abstractions: List[Dict[str, Any]] = []  # Identified abstractions
    relationships: List[str] = []  # Code relationships as strings
    metadata: Dict[str, Any] = {}  # Generation metadata
    execution_time: float = 0.0
    error: str = ""

@app.post("/generate-tutorial-frontend", response_model=FrontendTutorialResponse)
async def generate_tutorial_frontend(request: FrontendTutorialRequest):
    """Generate tutorial using frontend data format and return content directly"""
    start_time = time.time()
    
    try:
        logger.info(f"Frontend tutorial request received: url={request.url}")
        
        # Parse the frontend patterns
        include_patterns = parse_file_patterns(request.includeFileTypes)
        exclude_patterns = parse_file_patterns(request.excludeFileTypes)
        
        logger.info(f"Parsed {len(include_patterns)} include patterns and {len(exclude_patterns)} exclude patterns")
        
        # Validate URL
        if not request.url or request.url == "a":
            raise ValueError("Please provide a valid repository URL")
        
        # Auto-generate project name if not provided
        project_name = request.project_name
        if not project_name:
            project_name = request.url.split('/')[-1].replace('.git', '')
        
        # Convert to internal request format (but don't create files)
        internal_request = IntelligentTutorialRequest(
            repo_url=request.url,
            project_name=project_name,
            output_dir="temp_output",  # Use temp directory since we won't save files
            max_abstractions=request.max_abstractions,
            min_abstractions=request.min_abstractions,
            include_patterns=include_patterns if include_patterns else ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.h", "*.md"],
            exclude_patterns=exclude_patterns if exclude_patterns else ["node_modules/*", ".git/*", "__pycache__/*", "*.pyc", "dist/*", "build/*"],
            selected_files=request.selectedFiles or [],  # Use selectedFiles if provided
            max_file_size=request.max_file_size
        )
        
        logger.info(f"Frontend request converted successfully")
        if internal_request.selected_files:
            logger.info(f"Processing {len(internal_request.selected_files)} selected files")
        else:
            logger.info(f"Using pattern-based file discovery")
        logger.info(f"Include patterns: {internal_request.include_patterns[:3]}..." if len(internal_request.include_patterns) > 3 else f"Include patterns: {internal_request.include_patterns}")
        logger.info(f"Exclude patterns: {internal_request.exclude_patterns[:3]}..." if len(internal_request.exclude_patterns) > 3 else f"Exclude patterns: {internal_request.exclude_patterns}")
        
        # Engage Q&A system like other tutorial endpoints do
        logger.info("Engaging Q&A system for tutorial generation...")
        chunks = process_repo(request.url)
        logger.info(f"Q&A system engaged with {len(chunks)} chunks from repository")
        
        # Use CombineTutorial node for robust content generation
        tutorial_response = await generate_intelligent_tutorial(internal_request)
        
        execution_time = time.time() - start_time
        
        if tutorial_response.success:
            # Extract content from tutorial response
            tutorial_content = tutorial_response.tutorial_content or ""
            index_content = tutorial_response.index_content or ""
            readme_content = tutorial_response.readme_content or ""
            quick_reference_content = tutorial_response.quick_reference_content or ""
            chapters = tutorial_response.chapters
            abstractions = tutorial_response.abstractions
            relationships = tutorial_response.relationships
            
            return FrontendTutorialResponse(
                success=True,
                message=f"Tutorial generated successfully for '{project_name}'",
                tutorial_content=tutorial_content,
                index_content=index_content,
                readme_content=readme_content,
                quick_reference_content=quick_reference_content,
                chapters=chapters,
                abstractions=abstractions,
                relationships=relationships,
                metadata={
                    "project_name": project_name,
                    "files_processed": 0,  # Will be available in tutorial_response if needed
                    "chapters_generated": len(chapters),
                    "abstractions_identified": len(abstractions),
                    "relationships_found": len(relationships),
                    "selected_files_used": len(internal_request.selected_files) if internal_request.selected_files else None
                },
                execution_time=execution_time
            )
        else:
            return FrontendTutorialResponse(
                success=False,
                message="Failed to generate tutorial",
                error=tutorial_response.error or "Unknown error",
                execution_time=execution_time
            )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error processing frontend tutorial request: {str(e)}")
        logger.error(traceback.format_exc())
        return FrontendTutorialResponse(
            success=False,
            message="Failed to process frontend tutorial request",
            error=str(e),
            execution_time=execution_time
        )

@app.get("/mermaid-chart-demo")
async def get_mermaid_chart_demo():
    """Demonstrate different types of Mermaid charts available for tutorials"""
    try:
        from app.utils.mermaid_generator import MermaidChartGenerator
        
        generator = MermaidChartGenerator()
        
        # Example data for different chart types
        demo_charts = {}
        
        # Flowchart example
        flowchart_data = {
            'nodes': [
                {'id': 'A', 'label': 'Start', 'shape': 'rect', 'class': 'foundation'},
                {'id': 'B', 'label': 'Process Data', 'shape': 'rect', 'class': 'core'},
                {'id': 'C', 'label': 'Decision', 'shape': 'diamond', 'class': 'core'},
                {'id': 'D', 'label': 'Output', 'shape': 'rect', 'class': 'advanced'}
            ],
            'connections': [
                {'from': 'A', 'to': 'B', 'style': 'solid'},
                {'from': 'B', 'to': 'C', 'style': 'solid'},
                {'from': 'C', 'to': 'D', 'label': 'Yes', 'style': 'solid'}
            ],
            'direction': 'TD'
        }
        demo_charts['flowchart'] = generator.generate_chart('flowchart', flowchart_data, "Code Flow Process")
        
        # Sequence diagram example
        sequence_data = {
            'participants': ['User', 'Frontend', 'API', 'Database'],
            'messages': [
                {'from': 'User', 'to': 'Frontend', 'message': 'Submit Form', 'type': 'sync'},
                {'from': 'Frontend', 'to': 'API', 'message': 'POST /api/data', 'type': 'async'},
                {'from': 'API', 'to': 'Database', 'message': 'INSERT query', 'type': 'sync'},
                {'from': 'Database', 'to': 'API', 'message': 'Success', 'type': 'response'},
                {'from': 'API', 'to': 'Frontend', 'message': '200 OK', 'type': 'response'}
            ]
        }
        demo_charts['sequence'] = generator.generate_chart('sequence', sequence_data, "API Request Flow")
        
        # Class diagram example
        class_data = {
            'classes': [
                {
                    'name': 'User',
                    'attributes': [
                        {'visibility': '+', 'name': 'id', 'type': 'string'},
                        {'visibility': '+', 'name': 'email', 'type': 'string'}
                    ],
                    'methods': [
                        {'visibility': '+', 'name': 'login', 'params': 'email, password', 'return': 'boolean'},
                        {'visibility': '+', 'name': 'logout', 'params': '', 'return': 'void'}
                    ]
                }
            ],
            'relationships': []
        }
        demo_charts['class'] = generator.generate_chart('class', class_data, "User Class Structure")
        
        # State diagram example
        state_data = {
            'states': [
                {'id': 'idle', 'label': 'Idle'},
                {'id': 'loading', 'label': 'Loading'},
                {'id': 'success', 'label': 'Success'},
                {'id': 'error', 'label': 'Error'}
            ],
            'transitions': [
                {'from': 'idle', 'to': 'loading', 'trigger': 'start'},
                {'from': 'loading', 'to': 'success', 'trigger': 'complete'},
                {'from': 'loading', 'to': 'error', 'trigger': 'fail'},
                {'from': 'error', 'to': 'idle', 'trigger': 'reset'}
            ]
        }
        demo_charts['state'] = generator.generate_chart('state', state_data, "Application State Machine")
        
        # Architecture diagram example
        arch_data = {
            'components': [
                {'id': 'ui', 'name': 'User Interface', 'type': 'system'},
                {'id': 'api', 'name': 'REST API', 'type': 'container'},
                {'id': 'service', 'name': 'Business Logic', 'type': 'component'},
                {'id': 'db', 'name': 'Database', 'type': 'container'}
            ],
            'relationships': [
                {'from': 'ui', 'to': 'api', 'description': 'HTTP requests'},
                {'from': 'api', 'to': 'service', 'description': 'calls'},
                {'from': 'service', 'to': 'db', 'description': 'queries'}
            ]
        }
        demo_charts['architecture'] = generator.generate_chart('architecture', arch_data, "System Architecture")
        
        # Pie chart example
        pie_data = {
            'data': [
                {'label': 'Frontend', 'value': 40},
                {'label': 'Backend', 'value': 35},
                {'label': 'Database', 'value': 15},
                {'label': 'DevOps', 'value': 10}
            ]
        }
        demo_charts['pie'] = generator.generate_chart('pie', pie_data, "Project Complexity Distribution")
        
        # Timeline example
        timeline_data = {
            'events': [
                {
                    'period': 'Phase 1',
                    'items': ['Setup Environment', 'Basic Structure']
                },
                {
                    'period': 'Phase 2', 
                    'items': ['Core Features', 'API Integration']
                },
                {
                    'period': 'Phase 3',
                    'items': ['Testing', 'Deployment']
                }
            ]
        }
        demo_charts['timeline'] = generator.generate_chart('timeline', timeline_data, "Development Timeline")
        
        return {
            "message": "Enhanced Mermaid Chart Generator Demo",
            "available_chart_types": list(generator.chart_types.keys()),
            "demo_charts": demo_charts,
            "usage_examples": {
                "tutorial_integration": "Charts are automatically generated based on chapter content and abstraction types",
                "custom_charts": "Use the MermaidChartGenerator class to create specific chart types",
                "chart_suggestions": "The system provides intelligent chart type suggestions based on content analysis"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating Mermaid chart demo: {str(e)}")
        return {
            "error": "Failed to generate chart demo",
            "message": str(e)
        }

@app.get("/tutorial-system-status")
async def get_tutorial_system_status():
    """Get status and statistics of the intelligent tutorial generation system"""
    try:
        llm_stats = get_llm_stats()
        
        return {
            "status": "operational" if INTELLIGENT_TUTORIAL_AVAILABLE else "dependencies_missing",
            "nodes_available": INTELLIGENT_TUTORIAL_AVAILABLE,
            "system_components": {
                "flow_engine": INTELLIGENT_TUTORIAL_AVAILABLE,
                "llm_integration": INTELLIGENT_TUTORIAL_AVAILABLE,
                "fetch_repo_node": INTELLIGENT_TUTORIAL_AVAILABLE,
                "identify_abstractions_node": INTELLIGENT_TUTORIAL_AVAILABLE,
                "analyze_relationships_node": INTELLIGENT_TUTORIAL_AVAILABLE,
                "order_chapters_node": INTELLIGENT_TUTORIAL_AVAILABLE,
                "write_chapters_node": INTELLIGENT_TUTORIAL_AVAILABLE,
                "combine_tutorial_node": INTELLIGENT_TUTORIAL_AVAILABLE
            },
            "llm_statistics": llm_stats,
            "supported_file_types": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.h", "*.md"],
            "default_settings": {
                "max_abstractions": 12,
                "min_abstractions": 5,
                "max_file_size": 100000
            },
            "missing_dependencies": [] if INTELLIGENT_TUTORIAL_AVAILABLE else ["GitPython", "potentially others"]
        }
    except Exception as e:
        logger.error(f"Error getting tutorial system status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "system_components": {},
            "llm_statistics": {}
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(data: ChatRequest):
    """Enhanced chat with repository using advanced Q&A system with Claude 4 Copilot capabilities"""
    try:
        if not qa.index or not qa.doc_map:
            raise HTTPException(status_code=400, detail="No repository processed. Run /generate-tutorial or /generate-readme first.")
        
        # Use the fixed answer_question function directly
        result = qa.answer_question(data.question)
        
        # Ensure all required fields are present for ChatResponse
        response_data = {
            "answer": result.get("answer", ""),
            "context_chunks_used": result.get("context_chunks_used", 0),
            "total_tokens_used": result.get("total_tokens_used", 0),
            "context_strategy": result.get("context_strategy", "broad_exploration"),
            "intent_type": result.get("intent_type", "general_info"),
            "context_quality": result.get("context_quality", "standard"),
            "history_used": result.get("history_used", False),
            "conversations_referenced": result.get("conversations_referenced", 0),
            "task_type": result.get("task_type", "question"),
            "tasks_completed": result.get("tasks_completed", 0),
            "tasks_successful": result.get("tasks_successful", 0),
            "files_modified": result.get("files_modified", 0),
            "changes": result.get("changes", []),
            "validation_summary": result.get("validation_summary", {})
        }
        
        return ChatResponse(**response_data)
    except Exception as e:
        print(f"[ERROR] /chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/chat/execution-history")
async def get_execution_history_endpoint():
    """Get history of executed coding tasks"""
    try:
        history = get_execution_history()
        return {"history": history, "total_tasks": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")

@app.get("/analysis")
async def get_repository_analysis():
    """Get comprehensive code analysis of the current repository"""
    try:
        if not qa.doc_map:
            raise HTTPException(status_code=400, detail="No repository processed. Run /generate-tutorial or /generate-readme first.")
        
        analysis = get_code_analysis()
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get code analysis: {str(e)}")

@app.get("/analysis/{file_path:path}")
async def get_file_analysis(file_path: str):
    """Get detailed analysis of a specific file"""
    try:
        if not qa.doc_map:
            raise HTTPException(status_code=400, detail="No repository processed. Run /generate-tutorial or /generate-readme first.")
        
        analysis = get_code_analysis(file_path)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return {"file": file_path, "analysis": analysis}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

@app.get("/chat/history")
async def get_chat_history():
    return {"history": qa.get_chat_history()}

@app.delete("/chat/history")
async def clear_chat_history_endpoint():
    qa.clear_chat_history()
    return {"message": "Chat history cleared successfully"}

# ===========================
# GIT HELPER API ENDPOINTS
# ===========================

@app.post("/git-helper/recommendations", response_model=RecommendationResponse)
async def get_repository_recommendations_endpoint(prefs: PreferencesRequest):
    """Git Helper: Get repository recommendations based on user preferences (Legacy)"""
    try:
        return await get_repository_recommendations(prefs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in repository recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get repository recommendations: {str(e)}")

@app.post("/git-helper/intelligent-recommendations", response_model=EnhancedRepoRecommendationResponse)
async def get_intelligent_recommendations_endpoint(prefs: EnhancedPreferencesRequest):
    """Git Helper: Get intelligent, personalized repository recommendations"""
    start_time = time.time()
    
    try:
        logger.info(f"Getting intelligent recommendations for user with {len(prefs.selected_tech)} technologies")
        
        # Create user profile
        user_profile = UserProfile(prefs.dict())
        
        # Get personalized recommendations
        recommended_repos = await intelligent_search.get_personalized_recommendations(
            user_profile=user_profile,
            limit=100  # Increased to return more repositories
        )
        
        # Convert to response format
        enhanced_repos = []
        for repo in recommended_repos:
            # Handle license field - extract key if it's a dict
            license_value = repo.get('license')
            if isinstance(license_value, dict):
                license_value = license_value.get('key')
            elif license_value is None:
                license_value = None
            
            enhanced_repo = EnhancedRepoItem(
                id=repo.get('id', 0),
                full_name=repo.get('full_name', ''),
                description=repo.get('description'),
                html_url=repo.get('html_url', ''),
                stargazers_count=repo.get('stargazers_count', 0),
                forks_count=repo.get('forks_count', 0),
                language=repo.get('language'),
                topics=repo.get('topics', []),
                created_at=repo.get('created_at', ''),
                updated_at=repo.get('updated_at', ''),
                pushed_at=repo.get('pushed_at'),
                license=license_value,
                personalized_score=repo.get('personalized_score', 0.0),
                relevance_reasons=repo.get('relevance_reasons', []),
                learning_level=repo.get('learning_level'),
                contributor_count=repo.get('contributor_count'),
                has_good_first_issues=repo.get('has_good_first_issues', False),
                good_first_issue_count=repo.get('good_first_issue_count', 0),
                activity_score=repo.get('activity_score', 0.0)
            )
            enhanced_repos.append(enhanced_repo)
        
        # Determine strategies used
        strategies_used = [
            "Smart Technology Search",
            "Trending Analysis",
            "Deep Repository Analysis",
            "Personalized Scoring"
        ]
        
        if prefs.github_username:
            strategies_used.insert(0, "GitHub Activity Analysis")
        
        if prefs.wanted_skills:
            strategies_used.append("Learning Path Generation")
        
        # Get personalization factors
        weight_factors = user_profile.get_search_weight_factors()
        personalization_factors = {
            "experience_level": prefs.experience_level,
            "tech_focus": prefs.primary_language,
            "tech_stack": prefs.selected_tech,
            "learning_style": prefs.learning_style,
            "weight_factors": weight_factors,
            "user_context": {
                "has_github_profile": bool(prefs.github_username),
                "skill_gap_analysis": bool(prefs.wanted_skills),
                "contribution_focus": bool(prefs.contribution_types)
            }
        }
        
        # Get cache statistics
        cache_stats = cache.get_stats()
        
        execution_time = time.time() - start_time
        logger.info(f"Intelligent recommendations completed in {execution_time:.2f}s, found {len(enhanced_repos)} repos")
        
        return EnhancedRepoRecommendationResponse(
            repositories=enhanced_repos,
            total_found=len(enhanced_repos),
            search_strategies_used=strategies_used,
            personalization_factors=personalization_factors,
            cache_info={
                **cache_stats,
                "execution_time": execution_time
            }
        )
        
    except Exception as e:
        logger.error(f"Error in intelligent recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get intelligent recommendations: {str(e)}")

@app.get("/git-helper/test-max-repos")
async def test_max_repositories():
    """Test endpoint to verify maximum repository retrieval"""
    try:
        # Create a test profile for maximum retrieval
        test_profile_data = {
            "selected_tech": ["JavaScript"],
            "primary_language": "JavaScript",
            "experience_level": "intermediate",
            "project_goals": ["learning", "building"],
            "domains": ["web_development"],
            "min_stars": 50,
            "activity_preference": "any"
        }
        
        user_profile = UserProfile(test_profile_data)
        
        # Get maximum recommendations
        recommended_repos = await intelligent_search.get_personalized_recommendations(
            user_profile=user_profile,
            limit=500  # Very high limit for testing
        )
        
        return {
            "message": "Maximum repository test completed",
            "total_repositories_found": len(recommended_repos),
            "sample_repositories": [
                {
                    "name": repo.get('full_name', 'Unknown'),
                    "stars": repo.get('stargazers_count', 0),
                    "score": repo.get('personalized_score', 0),
                    "language": repo.get('language', 'Unknown')
                }
                for repo in recommended_repos[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in max repo test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get("/git-helper/test-good-first-issues/{owner}/{repo}")
async def test_good_first_issues(owner: str, repo: str):
    """Test endpoint to get open issues count for a specific repository"""
    try:
        repo_name = f"{owner}/{repo}"
        
        # Create session for API calls
        import requests
        session = requests.Session()
        
        print(f"[DEBUG] Getting open issues count for {repo_name}")
        
        # Get repository info which includes open issues count
        repo_url = f"https://api.github.com/repos/{repo_name}"
        response = session.get(repo_url, timeout=10)
        
        if response.status_code != 200:
            return {
                "repo": repo_name,
                "error": f"API error: {response.status_code}",
                "message": response.text
            }
        
        repo_data = response.json()
        open_issues_count = repo_data.get('open_issues_count', 0)
        
        print(f"[DEBUG] Found {open_issues_count} open issues")
        
        return {
            "repo": repo_name,
            "open_issues_count": open_issues_count,
            "has_open_issues": open_issues_count > 0,
            "repo_info": {
                "name": repo_data.get('name'),
                "full_name": repo_data.get('full_name'),
                "description": repo_data.get('description'),
                "language": repo_data.get('language'),
                "stars": repo_data.get('stargazers_count'),
                "forks": repo_data.get('forks_count')
            }
        }
        
    except Exception as e:
        return {
            "repo": f"{owner}/{repo}",
            "error": str(e)
        }

@app.post("/git-helper/issues", response_model=IssuesResponse)
async def get_github_issues_endpoint(request: IssueRequest):
    """Git Helper: Analyze GitHub issues for a repository"""
    start_time = time.time()
    
    if not request.repoUrl:
        raise HTTPException(status_code=400, detail="Repository URL is required")
    
    try:
        options = {
            "state": request.state,
            "perPage": request.perPage,
            "page": request.page,
            "difficulty": request.difficulty
        }
        
        # Get issues from GitHub
        result = await github_service.get_issues(request.repoUrl, options)
        
        # Apply AI filtering if user query is provided
        if request.userQuery and request.userQuery.strip():
            print(f"[INFO] User query provided: {request.userQuery}")
            
            # Import AI components
            from app.utils.qa import llm, tracked_llm_call
            
            # Filter issues using AI
            issues = result.get("issues", [])
            if issues:
                print(f"[INFO] Filtering {len(issues)} issues with AI...")
                
                # Create a prompt to filter issues based on user query
                filtered_issues = []
                
                # Process issues in batches to avoid token limits
                batch_size = 10
                for i in range(0, len(issues), batch_size):
                    batch = issues[i:i+batch_size]
                    
                    # Create issue summaries for AI filtering
                    issue_summaries = []
                    for idx, issue in enumerate(batch):
                        summary = {
                            "index": i + idx,
                            "title": issue.get("title", ""),
                            "body": (issue.get("body", "") or "")[:200],  # Limit body length
                            "labels": [label.get("name", "") for label in issue.get("labels", [])],
                            "url": issue.get("html_url", "")
                        }
                        issue_summaries.append(summary)
                    
                    # Create AI prompt
                    prompt = f"""
You are an AI assistant that helps filter GitHub issues based on user preferences.

User Query: "{request.userQuery}"

Issues to filter:
{json.dumps(issue_summaries, indent=2)}

Please analyze each issue and return ONLY the indices (numbers) of issues that match the user's query. 
Consider the title, description, and labels. Return the indices as a simple list of numbers separated by commas.
If no issues match, return "NONE".

Example response: "0,2,5" or "NONE"
"""
                    
                    try:
                        # Get AI response using tracked LLM call
                        ai_response = tracked_llm_call(
                            module="issues",
                            function="filter_issues",
                            model="models/gemini-2.0-flash",
                            llm_instance=llm,
                            prompt=prompt
                        )
                        response_text = ai_response.content.strip()
                        
                        print(f"[DEBUG] AI filtering response: {response_text}")
                        
                        # Parse AI response
                        if response_text.upper() != "NONE":
                            try:
                                selected_indices = [int(idx.strip()) for idx in response_text.split(",") if idx.strip().isdigit()]
                                for idx in selected_indices:
                                    if idx < len(batch):
                                        filtered_issues.append(batch[idx])
                            except ValueError as e:
                                print(f"[WARNING] Failed to parse AI response: {e}")
                                # If parsing fails, include all issues from this batch
                                filtered_issues.extend(batch)
                        
                    except Exception as e:
                        print(f"[ERROR] AI filtering failed: {e}")
                        # If AI fails, include all issues from this batch
                        filtered_issues.extend(batch)
                
                # Update result with filtered issues
                result["issues"] = filtered_issues
                result["totalIssues"] = len(filtered_issues)
                result["filteredByAI"] = True
                result["originalCount"] = len(issues)
                
                print(f"[INFO] AI filtering complete: {len(issues)} -> {len(filtered_issues)} issues")
        
        # Add execution time
        result["execution_time"] = time.time() - start_time
        
        return IssuesResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing GitHub issues: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to analyze GitHub issues: {str(e)}")

@app.post("/git-helper/repo-info", response_model=RepositoryInfo)
async def get_repository_info_endpoint(request: RepoInfoRequest):
    """Git Helper: Get detailed repository information"""
    if not request.repoUrl:
        raise HTTPException(status_code=400, detail="Repository URL is required")
    
    try:
        # Get basic repository info
        repo_info = await github_service.get_repository_info(request.repoUrl)
        
        if "error" in repo_info:
            raise HTTPException(status_code=404, detail=repo_info["error"])
        
        # Enhance with additional data
        try:
            parsed = github_service.parse_github_url(request.repoUrl)
            repo_full_name = f"{parsed['owner']}/{parsed['repo']}"
            
            # Get topics and quality score
            topics = get_repo_topics(repo_full_name)
            
            # Get enhanced repo data for quality scoring
            enhanced_data = {
                "stargazers_count": repo_info["stars"],
                "forks_count": repo_info["forks"],
                "open_issues_count": repo_info["openIssues"],
                "description": repo_info.get("description", ""),
                "language": repo_info.get("language"),
                "size": 10000,  # Default size since we don't have it
                "archived": False,
                "disabled": False,
                "fork": False,
                "updated_at": "2024-01-01T00:00:00Z"  # Default update time
            }
            
            quality_score = calculate_repo_quality_score(enhanced_data)
            
            repo_info["quality_score"] = quality_score
            repo_info["topics"] = topics or []
            
        except Exception as e:
            logger.warning(f"Failed to enhance repository info: {e}")
            repo_info["quality_score"] = 0.0
            repo_info["topics"] = []
        
        return RepositoryInfo(**repo_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository info: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get repository information: {str(e)}")

@app.post("/resolve-issue", response_model=IssueResolutionResponse)
async def resolve_github_issue(request: IssueResolutionRequest):
    """Issue Resolution: Generate comprehensive step-by-step solution for GitHub issues"""
    start_time = time.time()
    
    if not request.repo_url or not request.issue_url:
        raise HTTPException(status_code=400, detail="Both repository URL and issue URL are required")
    
    try:
        from app.utils.issue_resolver import issue_resolver
        
        logger.info(f"Starting issue resolution for: {request.issue_url}")
        
        # Step 1: Fetch issue details
        logger.info("Fetching issue details...")
        issue_details = await issue_resolver.fetch_issue_details(request.issue_url)
        
        # Step 2: Fetch repository context
        logger.info("Fetching repository context...")
        repo_context = await issue_resolver.fetch_repository_context(request.repo_url)
        
        # Step 3: Analyze repository structure
        logger.info("Analyzing repository structure...")
        repo_analysis = await issue_resolver.analyze_repository_structure(repo_context)
        
        # Step 4: Setup repository for QA (RAG integration)
        logger.info("Setting up repository for QA analysis...")
        rag_setup = await issue_resolver.setup_repository_for_qa(request.repo_url)
        
        # Step 5: Get contextual information using QA system
        contextual_info = {}
        if rag_setup.get("success", False):
            logger.info("Getting contextual information from codebase...")
            contextual_info = await issue_resolver.get_contextual_information(
                issue_details, repo_analysis
            )
        else:
            logger.warning(f"RAG setup failed: {rag_setup.get('error', 'Unknown error')}")
        
        # Step 6: Generate resolution plan using LLM
        logger.info("Generating resolution plan...")
        resolution_plan = await issue_resolver.generate_resolution_plan(
            issue_details=issue_details,
            repo_context=repo_context,
            repo_analysis=repo_analysis,
            contextual_info=contextual_info,
            user_context=request.user_context,
            difficulty_preference=request.difficulty_preference
        )
        
        # Step 7: Find related issues (optional)
        related_issues = []
        if request.include_related_issues:
            logger.info("Finding related issues...")
            related_issues = await issue_resolver.find_related_issues(repo_context, issue_details)
        
        # Step 8: Build comprehensive response
        execution_time = time.time() - start_time
        
        response_data = {
            "issue_details": IssueDetails(
                number=issue_details["number"],
                title=issue_details["title"],
                body=issue_details.get("body", ""),
                state=issue_details["state"],
                labels=issue_details["labels"],
                assignees=issue_details["assignees"],
                author=issue_details["author"],
                created_at=issue_details["created_at"],
                updated_at=issue_details["updated_at"],
                comments_count=issue_details["comments_count"],
                html_url=issue_details["html_url"]
            ),
            "repository_analysis": RepositoryAnalysis(
                tech_stack=repo_analysis.get("tech_stack", []),
                main_directories=repo_analysis.get("main_directories", []),
                key_files=repo_analysis.get("key_config_files", []),
                testing_setup=repo_analysis.get("testing_setup", "Unknown"),
                build_system=repo_analysis.get("build_system", "Unknown"),
                documentation_quality=repo_analysis.get("documentation_quality", "Unknown"),
                contributor_guidelines=repo_analysis.get("contributor_setup", "Unknown")
            ),
            "resolution_summary": resolution_plan.get("resolution_summary", ""),
            "resolution_steps": [
                ResolutionStep(**step) for step in resolution_plan.get("resolution_steps", [])
            ],
            "alternative_approaches": resolution_plan.get("alternative_approaches", []),
            "related_issues": related_issues,
            "helpful_resources": resolution_plan.get("helpful_resources", []),
            "estimated_total_time": resolution_plan.get("estimated_total_time", "Unknown"),
            "difficulty_level": resolution_plan.get("difficulty_level", "medium"),
            "skills_required": resolution_plan.get("skills_required", []),
            "context_used": {
                "rag_setup_success": rag_setup.get("success", False),
                "chunks_processed": rag_setup.get("chunks_processed", 0),
                "relevant_files_found": len(contextual_info.get("relevant_files", [])),
                "implementation_patterns_found": len(contextual_info.get("implementation_patterns", [])),
                "qa_queries_executed": len(contextual_info.get("implementation_patterns", [])),
                "related_issues_found": len(related_issues)
            },
            "execution_time": execution_time
        }
        
        logger.info(f"Issue resolution completed in {execution_time:.2f} seconds")
        return IssueResolutionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error resolving issue: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to resolve issue: {str(e)}")

@app.post("/resolve-issue-comprehensive")
async def resolve_github_issue_comprehensive(request: IssueResolutionRequest):
    """Enhanced Issue Resolution: Generate comprehensive step-by-step markdown guide from git clone to push"""
    start_time = time.time()
    
    if not request.repo_url or not request.issue_url:
        raise HTTPException(status_code=400, detail="Both repository URL and issue URL are required")
    
    try:
        from app.utils.issue_resolver import issue_resolver
        
        logger.info(f"Starting comprehensive issue resolution for: {request.issue_url}")
        
        # Use the new comprehensive resolution method
        result = await issue_resolver.resolve_issue_comprehensive(
            repo_url=request.repo_url,
            issue_url=request.issue_url,
            user_context=request.user_context,
            difficulty_preference=request.difficulty_preference
        )
        
        execution_time = time.time() - start_time
        
        if result.get("success", False):
            logger.info(f"Comprehensive issue resolution completed in {execution_time:.2f} seconds")
            
            # Return the comprehensive markdown resolution
            return {
                "success": True,
                "issue_details": result.get("issue_details", {}),
                "enhanced_analysis": result.get("enhanced_issue_analysis", {}),
                "repository_analysis": result.get("repository_analysis", {}),
                "resolution_markdown": result.get("resolution_markdown", ""),
                "context_used": result.get("context_used", {}),
                "execution_time": execution_time
            }
        else:
            logger.error(f"Comprehensive issue resolution failed: {result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "fallback_guidance": result.get("fallback_guidance", ""),
                "execution_time": execution_time
            }
        
    except Exception as e:
        logger.error(f"Error in comprehensive issue resolution: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to resolve issue comprehensively: {str(e)}")

@app.get("/git-helper/cache/stats")
async def get_cache_stats():
    """Git Helper: Get cache statistics"""
    try:
        stats = cache.get_stats()
        return {
            "message": "Cache statistics retrieved successfully",
            "stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")

@app.delete("/git-helper/cache")
async def clear_cache():
    """Git Helper: Clear all cache entries"""
    try:
        cache.clear()
        return {
            "message": "Cache cleared successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/git-helper/health")
async def git_helper_health_check():
    """Git Helper: Health check for Git Helper services"""
    try:
        from app.utils.config import GITHUB_TOKEN
        
        # Test GitHub API connectivity
        github_status = "available" if GITHUB_TOKEN else "no_token"
        
        # Test cache system
        cache_test_key = "health_check_test"
        cache.set("test", cache_test_key, {"test": True})
        cache_result = cache.get("test", cache_test_key)
        cache_status = "available" if cache_result else "error"
        
        # Clean up test cache
        cache.clear("test", cache_test_key)
        
        return {
            "message": "Git Helper services health check",
            "status": "healthy",
            "services": {
                "github_api": github_status,
                "cache_system": cache_status,
                "repository_search": "available",
                "issue_analysis": "available"
            },
            "endpoints": {
                "recommendations": "/git-helper/recommendations",
                "issues": "/git-helper/issues",
                "repo_info": "/git-helper/repo-info",
                "cache_stats": "/git-helper/cache/stats",
                "cache_clear": "/git-helper/cache"
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error in Git Helper health check: {str(e)}")
        return {
            "message": "Git Helper health check failed",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/")
async def root():
    return {
        "message": "Enhanced Repository Analysis & Q&A System with Claude 4 Copilot Capabilities, Intelligent Tutorial Generator, and Git Helper",
        "features": [
            "🤖 Advanced Q&A with conversation history",
            "🔧 Code generation and modification",
            "🧠 AST-based code analysis",
            "📋 Task decomposition for complex requests",
            "✅ Code validation and syntax checking",
            "📊 Comprehensive execution tracking",
            "🎯 Multi-file coordination",
            "📚 Intelligent tutorial generation (node-based architecture)" if INTELLIGENT_TUTORIAL_AVAILABLE else "📚 Legacy tutorial generation",
            "🎨 Custom file pattern filtering",
            "🔧 Frontend integration support",
            "🔍 Advanced GitHub repository discovery (Git Helper)",
            "📝 GitHub issue analysis and filtering (Git Helper)",
            "⚡ Smart caching system for API optimization",
            "🎯 Quality-based repository scoring",
            "🔄 Multi-query search strategies"
        ],
        "main_endpoints": {
            "POST /generate-tutorial": "Generate structured tutorial (legacy method)",
            "POST /generate-intelligent-tutorial": "Generate intelligent tutorial with flow-based system" if INTELLIGENT_TUTORIAL_AVAILABLE else "Generate intelligent tutorial (requires dependencies)",
            "POST /generate-tutorial-frontend": "Generate tutorial using frontend data format",
            "POST /generate-readme": "Generate README file",
            "POST /chat": "Enhanced Q&A with coding capabilities",
            "GET /chat/history": "Get conversation history",
            "GET /chat/execution-history": "Get coding task execution history",
            "GET /analysis": "Get repository code analysis",
            "GET /analysis/{file_path}": "Get specific file analysis",
            "POST /resolve-issue": "Generate comprehensive step-by-step solution for GitHub issues"
        },
        "git_helper_endpoints": {
            "POST /git-helper/recommendations": "Get repository recommendations based on tech stack and preferences",
            "POST /git-helper/issues": "Analyze GitHub issues with difficulty filtering",
            "POST /git-helper/repo-info": "Get detailed repository information with quality scoring",
            "GET /git-helper/cache/stats": "Get cache system statistics",
            "DELETE /git-helper/cache": "Clear all cached data",
            "GET /git-helper/health": "Git Helper services health check"
        },
        "tutorial_system_endpoints": {
            "GET /tutorial-system-status": "Check intelligent tutorial system status",
            "GET /mermaid-chart-demo": "Demonstrate Mermaid chart capabilities"
        },
        "git_helper_features": {
            "repository_discovery": {
                "description": "Advanced multi-query GitHub repository search",
                "features": [
                    "Multiple search strategies (language, topic, README content)",
                    "Quality-based scoring and ranking",
                    "Technology stack verification",
                    "Domain-specific filtering",
                    "Contribution type matching",
                    "Smart caching for performance"
                ]
            },
            "issue_analysis": {
                "description": "GitHub issue analysis with difficulty classification",
                "features": [
                    "Difficulty-based filtering (beginner, easy, medium, hard)",
                    "Label-based classification",
                    "Repository activity analysis",
                    "Good first issue identification",
                    "Bulk issue processing with pagination"
                ]
            },
            "caching_system": {
                "description": "Smart caching to reduce API calls and improve performance",
                "features": [
                    "In-memory and file-based caching",
                    "Configurable expiration times",
                    "Cache statistics and management",
                    "Repository data persistence"
                ]
            },
            "issue_resolution": {
                "description": "AI-powered GitHub issue resolution with comprehensive step-by-step guidance",
                "features": [
                    "Repository RAG integration for contextual analysis",
                    "LLM-powered resolution plan generation",
                    "Step-by-step instructions from cloning to PR submission",
                    "Repository structure analysis and technology detection",
                    "Related issue discovery and alternative approaches",
                    "Difficulty assessment and time estimation",
                    "Enhanced QA system integration for code context"
                ]
            }
        },
        "frontend_integration": {
            "custom_file_patterns": True,
            "supported_include_types": "*.py, *.js, *.jsx, *.ts, *.tsx, *.go, *.java, *.md, etc.",
            "supported_exclude_patterns": "node_modules/*, .git/*, __pycache__/*, tests/*, etc.",
            "frontend_endpoint": "/generate-tutorial-frontend",
            "pattern_format": "Comma-separated quoted strings"
        },
        "intelligent_tutorial_system": {
            "available": INTELLIGENT_TUTORIAL_AVAILABLE,
            "status": "operational" if INTELLIGENT_TUTORIAL_AVAILABLE else "dependencies_missing"
        },
        "api_integration": {
            "github_api": "Repository and issue data",
            "gemini_ai": "Code analysis and README generation",
            "faiss_vector_db": "Semantic search and Q&A",
            "caching_layer": "Performance optimization"
        }
    }