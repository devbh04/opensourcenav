# issue_resolver.py - GitHub Issue Resolution System
import re
import requests
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from app.utils.config import GITHUB_TOKEN
from app.utils.qa import llm, tracked_llm_call
from app.utils.cache import cache
import json
import time

class GitHubIssueResolver:
    """GitHub Issue Resolution System with RAG integration"""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        } if GITHUB_TOKEN else {"Accept": "application/vnd.github.v3+json"}
        self.base_url = "https://api.github.com"
    
    async def resolve_issue_comprehensive(self, repo_url: str, issue_url: str, user_context: str = "", 
                                        difficulty_preference: str = "intermediate") -> Dict[str, Any]:
        """Complete comprehensive issue resolution workflow with enhanced RAG and detailed markdown generation"""
        try:
            print(f"[INFO] Starting comprehensive issue resolution for: {issue_url}")
            start_time = time.time()
            
            # Step 1: Enhanced issue intent and context analysis
            print("[INFO] Analyzing issue intent and context with LLM...")
            enhanced_issue_analysis = await self._enhance_issue_intent_and_context(issue_url, user_context)
            
            # Step 2: Fetch repository context
            print("[INFO] Fetching repository context...")
            repo_context = await self.fetch_repository_context(repo_url)
            
            # Step 3: Comprehensive repository analysis
            print("[INFO] Performing comprehensive repository analysis...")
            repo_analysis = await self.analyze_repository_structure(repo_context)
            
            # Step 4: Full RAG pipeline setup (like tutorial system)
            print("[INFO] Setting up comprehensive RAG pipeline...")
            rag_setup = await self.setup_comprehensive_rag_pipeline(repo_url)
            
            # Step 5: Enhanced contextual information gathering
            contextual_info = {}
            if rag_setup.get("success", False):
                print("[INFO] Gathering enhanced contextual information...")
                issue_details = enhanced_issue_analysis.get("original_issue", {})
                contextual_info = await self.get_enhanced_contextual_information(
                    enhanced_issue_analysis, issue_details, repo_analysis
                )
            else:
                print(f"[WARNING] RAG setup failed: {rag_setup.get('error', 'Unknown error')}")
                # Still proceed with basic analysis
                issue_details = enhanced_issue_analysis.get("original_issue", {})
                contextual_info = await self.get_contextual_information(issue_details, repo_analysis)
            
            # Step 6: Generate comprehensive resolution markdown
            print("[INFO] Generating comprehensive resolution markdown...")
            resolution_markdown = await self.generate_comprehensive_resolution_markdown(
                enhanced_issue_analysis=enhanced_issue_analysis,
                issue_details=enhanced_issue_analysis.get("original_issue", {}),
                repo_context=repo_context,
                repo_analysis=repo_analysis,
                contextual_info=contextual_info,
                user_context=user_context,
                difficulty_preference=difficulty_preference
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "enhanced_issue_analysis": enhanced_issue_analysis,
                "issue_details": enhanced_issue_analysis.get("original_issue", {}),
                "repository_analysis": repo_analysis,
                "resolution_markdown": resolution_markdown,
                "context_used": {
                    "rag_setup_success": rag_setup.get("success", False),
                    "chunks_processed": rag_setup.get("chunks_created", 0),
                    "enhanced_qa_used": contextual_info.get("enhanced_qa_used", False),
                    "enhanced_analysis_used": contextual_info.get("enhanced_analysis_used", False),
                    "contextual_queries": len(contextual_info.get("qa_responses", [])),
                    "implementation_insights": len(contextual_info.get("implementation_patterns", [])),
                    "relevant_files_found": len(contextual_info.get("relevant_files", [])),
                    "technical_insights_count": len(contextual_info.get("technical_insights", []))
                },
                "execution_time": execution_time
            }
            
        except Exception as e:
            print(f"[ERROR] Comprehensive issue resolution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_guidance": self._create_fallback_markdown_guidance_sync(
                    issue_url.split("/")[-1] if "/" in issue_url else "Unknown Issue",
                    "Issue resolution",
                    str(e)
                )
            }
    
    def parse_issue_url(self, issue_url: str) -> Dict[str, str]:
        """Extract owner, repo, and issue number from GitHub issue URL"""
        # Match URLs like: https://github.com/owner/repo/issues/123
        pattern = r"github\.com\/([^\/]+)\/([^\/]+)\/issues\/(\d+)"
        match = re.search(pattern, issue_url)
        
        if not match:
            raise ValueError("Invalid GitHub issue URL format. Expected: https://github.com/owner/repo/issues/123")
        
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "issue_number": int(match.group(3)),
            "repo_url": f"https://github.com/{match.group(1)}/{match.group(2)}"
        }
    
    def parse_repo_url(self, repo_url: str) -> Dict[str, str]:
        """Extract owner and repo from GitHub repository URL"""
        pattern = r"github\.com\/([^\/]+)\/([^\/]+)"
        match = re.search(pattern, repo_url)
        
        if not match:
            raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repo")
        
        return {
            "owner": match.group(1),
            "repo": match.group(2).replace(".git", "")  # Remove .git if present
        }
    
    async def fetch_issue_details(self, issue_url: str) -> Dict[str, Any]:
        """Fetch detailed issue information from GitHub API"""
        try:
            parsed = self.parse_issue_url(issue_url)
            owner, repo, issue_number = parsed["owner"], parsed["repo"], parsed["issue_number"]
            
            # Check cache first
            cache_key = f"issue_{owner}_{repo}_{issue_number}"
            cached_issue = cache.get("issue_details", cache_key)
            if cached_issue is not None:
                return cached_issue
            
            # Fetch issue details
            issue_url_api = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(issue_url_api, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch issue: {response.status_code}")
                
                issue_data = response.json()
                
                # Fetch comments for additional context
                comments_url = issue_data.get("comments_url")
                comments_data = []
                
                if comments_url and issue_data.get("comments", 0) > 0:
                    comments_response = await client.get(comments_url, headers=self.headers, timeout=10)
                    if comments_response.status_code == 200:
                        comments_data = comments_response.json()
                
                # Structure the issue details
                issue_details = {
                    "number": issue_data["number"],
                    "title": issue_data["title"],
                    "body": issue_data.get("body", ""),
                    "state": issue_data["state"],
                    "labels": [label["name"] for label in issue_data.get("labels", [])],
                    "assignees": [assignee["login"] for assignee in issue_data.get("assignees", [])],
                    "author": issue_data["user"]["login"],
                    "created_at": issue_data["created_at"],
                    "updated_at": issue_data["updated_at"],
                    "comments_count": issue_data.get("comments", 0),
                    "html_url": issue_data["html_url"],
                    "comments": comments_data[:5],  # Limit to first 5 comments
                    "repository": {
                        "owner": owner,
                        "repo": repo,
                        "full_name": f"{owner}/{repo}"
                    }
                }
                
                # Cache the result
                cache.set("issue_details", cache_key, issue_details)
                return issue_details
                
        except Exception as e:
            raise Exception(f"Error fetching issue details: {str(e)}")
    
    async def fetch_repository_context(self, repo_url: str) -> Dict[str, Any]:
        """Fetch repository context for issue resolution"""
        try:
            parsed = self.parse_repo_url(repo_url)
            owner, repo = parsed["owner"], parsed["repo"]
            
            # Check cache first
            cache_key = f"repo_context_{owner}_{repo}"
            cached_context = cache.get("repo_context", cache_key)
            if cached_context is not None:
                return cached_context
            
            async with httpx.AsyncClient() as client:
                # Fetch repository info
                repo_url_api = f"{self.base_url}/repos/{owner}/{repo}"
                repo_response = await client.get(repo_url_api, headers=self.headers, timeout=10)
                
                if repo_response.status_code != 200:
                    raise Exception(f"Failed to fetch repository: {repo_response.status_code}")
                
                repo_data = repo_response.json()
                
                # Fetch repository contents (root level)
                contents_url = f"{self.base_url}/repos/{owner}/{repo}/contents"
                contents_response = await client.get(contents_url, headers=self.headers, timeout=10)
                
                contents_data = []
                if contents_response.status_code == 200:
                    contents_data = contents_response.json()
                
                # Fetch README if available
                readme_content = ""
                try:
                    readme_url = f"{self.base_url}/repos/{owner}/{repo}/readme"
                    readme_response = await client.get(readme_url, headers=self.headers, timeout=10)
                    if readme_response.status_code == 200:
                        readme_data = readme_response.json()
                        import base64
                        readme_content = base64.b64decode(readme_data["content"]).decode("utf-8")
                except:
                    pass
                
                # Structure repository context
                repo_context = {
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language"),
                    "languages_url": repo_data["languages_url"],
                    "topics": repo_data.get("topics", []),
                    "default_branch": repo_data["default_branch"],
                    "has_issues": repo_data.get("has_issues", True),
                    "has_wiki": repo_data.get("has_wiki", False),
                    "has_pages": repo_data.get("has_pages", False),
                    "open_issues_count": repo_data.get("open_issues_count", 0),
                    "stargazers_count": repo_data.get("stargazers_count", 0),
                    "forks_count": repo_data.get("forks_count", 0),
                    "readme_content": readme_content[:2000],  # Limit README length
                    "root_files": [item["name"] for item in contents_data if item["type"] == "file"],
                    "root_directories": [item["name"] for item in contents_data if item["type"] == "dir"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "pushed_at": repo_data.get("pushed_at")
                }
                
                # Cache the result
                cache.set("repo_context", cache_key, repo_context)
                return repo_context
                
        except Exception as e:
            raise Exception(f"Error fetching repository context: {str(e)}")
    
    async def analyze_repository_structure(self, repo_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository structure using LLM"""
        try:
            # Create prompt for repository analysis
            prompt = f"""
Analyze this GitHub repository structure and provide technical insights for issue resolution.

Repository: {repo_context.get('full_name', 'Unknown')}
Description: {repo_context.get('description', 'No description')}
Primary Language: {repo_context.get('language', 'Unknown')}
Topics: {', '.join(repo_context.get('topics', []))}

Root Files: {', '.join(repo_context.get('root_files', []))}
Root Directories: {', '.join(repo_context.get('root_directories', []))}

README Excerpt:
{repo_context.get('readme_content', 'No README available')[:1000]}

Please analyze and provide a JSON response with:
{{
    "tech_stack": ["list of technologies/frameworks identified"],
    "project_type": "web app / library / cli tool / mobile app / etc",
    "build_system": "detected build system (npm, gradle, maven, poetry, etc)",
    "testing_setup": "testing framework and setup if identifiable",
    "key_config_files": ["important configuration files found"],
    "main_directories": ["most important directories for development"],
    "likely_entry_points": ["main files where execution starts"],
    "documentation_quality": "good / fair / poor",
    "contributor_setup": "clear setup instructions / some guidance / unclear"
}}

Respond ONLY with valid JSON.
"""
            
            # Get LLM analysis
            response = tracked_llm_call(
                module="issue_resolver",
                function="analyze_repository_structure",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=prompt
            )
            
            # Parse LLM response
            response_text = response.content if hasattr(response, "content") else str(response)
            
            try:
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                # Fallback analysis based on available data
                return {
                    "tech_stack": [repo_context.get('language', 'Unknown')] + repo_context.get('topics', []),
                    "project_type": "Unknown",
                    "build_system": "Unknown",
                    "testing_setup": "Unknown",
                    "key_config_files": [f for f in repo_context.get('root_files', []) if any(cfg in f.lower() for cfg in ['config', 'package', 'setup', 'requirements'])],
                    "main_directories": repo_context.get('root_directories', [])[:5],
                    "likely_entry_points": [f for f in repo_context.get('root_files', []) if any(entry in f.lower() for entry in ['main', 'index', 'app'])],
                    "documentation_quality": "fair" if repo_context.get('readme_content') else "poor",
                    "contributor_setup": "unclear"
                }
                
        except Exception as e:
            print(f"Error analyzing repository structure: {e}")
            # Return basic fallback
            return {
                "tech_stack": [repo_context.get('language', 'Unknown')],
                "project_type": "Unknown",
                "build_system": "Unknown", 
                "testing_setup": "Unknown",
                "key_config_files": [],
                "main_directories": repo_context.get('root_directories', []),
                "likely_entry_points": [],
                "documentation_quality": "poor",
                "contributor_setup": "unclear"
            }
    
    async def find_related_issues(self, repo_context: Dict[str, Any], issue_details: Dict[str, Any]) -> List[str]:
        """Find related issues using GitHub API search"""
        try:
            owner = repo_context["full_name"].split("/")[0]
            repo = repo_context["full_name"].split("/")[1]
            
            # Extract keywords from issue title and body
            title = issue_details.get("title", "")
            body = issue_details.get("body", "")
            labels = issue_details.get("labels", [])
            
            # Simple keyword extraction for related issue search
            search_terms = []
            if title:
                search_terms.extend(title.split()[:3])  # First 3 words from title
            if labels:
                search_terms.extend(labels[:2])  # First 2 labels
            
            related_issues = []
            
            if search_terms:
                search_query = " ".join(search_terms[:3])  # Limit search terms
                search_url = f"{self.base_url}/search/issues"
                params = {
                    "q": f"repo:{owner}/{repo} {search_query}",
                    "sort": "created",
                    "order": "desc",
                    "per_page": 5
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(search_url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        search_results = response.json()
                        for item in search_results.get("items", []):
                            if item["number"] != issue_details["number"]:  # Exclude current issue
                                related_issues.append(item["html_url"])
            
            return related_issues[:3]  # Return max 3 related issues
            
        except Exception as e:
            print(f"Error finding related issues: {e}")
            return []
    
    async def setup_repository_for_qa(self, repo_url: str) -> Dict[str, Any]:
        """Setup repository in RAG system using SAME approach as tutorial system"""
        try:
            print(f"[INFO] Setting up repository for QA (tutorial-style): {repo_url}")
            
            # Use EXACT same process as tutorial generation
            from app.utils import github_loader, chunker, embedder, qa
            import faiss
            import pickle
            
            # Clear previous state (same as tutorial system)
            qa.clear_chat_history()
            
            # Download and process repository (same as tutorial)
            print("[INFO] Downloading repository...")
            repo_path = github_loader.download_repo(repo_url)
            
            # Chunk the repository files (same as tutorial)
            print("[INFO] Chunking repository files...")
            chunks = chunker.chunk_repo(repo_path)
            
            if not chunks:
                return {
                    "success": False,
                    "error": "No processable files found in repository",
                    "chunks_processed": 0
                }
            
            # Create embeddings and save index (same as tutorial)
            print("[INFO] Creating embeddings...")
            embedder.embed_chunks(chunks)
            
            # Reload the QA system with new data (same as tutorial)
            print("[INFO] Reloading FAISS index and document map for the Q&A module...")
            qa.index = faiss.read_index("vector.index")
            with open("doc_map.pkl", "rb") as f:
                qa.doc_map = pickle.load(f)
            print("[SUCCESS] Q&A module is ready with the new repository data.")
            
            # Initialize enhanced Q&A system with the new data (same as tutorial)
            try:
                from app.utils.enhanced_qa import initialize_enhanced_qa
                initialize_enhanced_qa()
                print("[SUCCESS] Enhanced Q&A system initialized with repository data.")
                enhanced_qa_ready = True
            except ImportError:
                print("[WARNING] Enhanced QA system not available")
                enhanced_qa_ready = False
            
            print(f"[SUCCESS] Repository processed: {len(chunks)} chunks created")
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "vector_index_loaded": True,
                "enhanced_qa_ready": enhanced_qa_ready,
                "qa_system_ready": True
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to setup repository for QA: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_processed": 0
            }
    
    async def _enhance_issue_intent_and_context(self, issue_url: str, user_context: str = "") -> Dict[str, Any]:
        """Enhanced issue intent detection and context analysis using LLM"""
        try:
            # First fetch the basic issue details
            issue_details = await self.fetch_issue_details(issue_url)
            
            # Prepare enhanced analysis prompt
            prompt = f"""
You are an expert software developer analyzing a GitHub issue for comprehensive resolution planning.
Analyze the following issue and provide detailed intent, context, and planning information.

## ISSUE INFORMATION:
**Repository**: {issue_details.get('repository', {}).get('full_name', 'Unknown')}
**Issue #**: {issue_details.get('number', 'Unknown')}
**Title**: {issue_details.get('title', 'No title')}
**State**: {issue_details.get('state', 'Unknown')}
**Labels**: {', '.join(issue_details.get('labels', []))}
**Author**: {issue_details.get('author', 'Unknown')}

**Description/Body**:
{issue_details.get('body', 'No description provided')[:2000]}

## USER CONTEXT:
{user_context or 'No additional user context provided'}

Based on this information, provide a comprehensive analysis in JSON format:

{{
  "issue_type": "bug|feature|enhancement|documentation|question|other",
  "complexity_level": "beginner|intermediate|advanced|expert",
  "estimated_effort": "quick|moderate|substantial|major",
  "primary_intent": "Describe the main goal of this issue in 1-2 sentences",
  "technical_requirements": [
    "List specific technical requirements",
    "Include programming languages, frameworks, tools needed"
  ],
  "affected_components": [
    "List components/modules/files likely to be affected",
    "Include database, API, frontend, backend, etc."
  ],
  "prerequisites": [
    "List what needs to be understood or set up first",
    "Include domain knowledge, tools, access requirements"
  ],
  "implementation_approach": {{
    "strategy": "Describe the recommended approach",
    "key_steps": [
      "List main implementation phases",
      "Include testing and validation steps"
    ],
    "potential_challenges": [
      "List possible difficulties or edge cases"
    ]
  }},
  "success_criteria": [
    "List how to verify the issue is resolved",
    "Include testing criteria and acceptance criteria"
  ],
  "risk_assessment": {{
    "breaking_changes": "low|medium|high",
    "testing_requirements": "minimal|standard|extensive",
    "rollback_complexity": "easy|moderate|difficult"
  }}
}}

Provide ONLY the JSON response, no additional text.
"""
            
            # Call LLM for enhanced analysis
            from app.utils.llm_tracker import tracked_llm_call
            from app.utils.qa import llm
            
            print("[INFO] Analyzing issue intent and context with LLM...")
            llm_response = tracked_llm_call(
                module="issue_resolver",
                function="enhance_issue_intent_and_context",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=prompt
            )
            
            # Extract content from response
            if hasattr(llm_response, 'content'):
                response_text = llm_response.content
            elif hasattr(llm_response, 'text'):
                response_text = llm_response.text
            else:
                response_text = str(llm_response)
            
            # Parse JSON response
            try:
                import json
                enhanced_analysis = json.loads(response_text)
                enhanced_analysis["original_issue"] = issue_details
                enhanced_analysis["analysis_success"] = True
                
                print(f"[SUCCESS] Enhanced issue analysis complete: {enhanced_analysis.get('issue_type', 'unknown')} / {enhanced_analysis.get('complexity_level', 'unknown')}")
                return enhanced_analysis
                
            except json.JSONDecodeError:
                print("[WARNING] Failed to parse LLM JSON response, using fallback analysis")
                return self._create_fallback_issue_analysis(issue_details, user_context)
                
        except Exception as e:
            print(f"[ERROR] Enhanced issue analysis failed: {e}")
            return self._create_fallback_issue_analysis(issue_details if 'issue_details' in locals() else {}, user_context)
    
    def _create_fallback_issue_analysis(self, issue_details: Dict[str, Any], user_context: str) -> Dict[str, Any]:
        """Create fallback issue analysis when LLM analysis fails"""
        return {
            "issue_type": "other",
            "complexity_level": "intermediate",
            "estimated_effort": "moderate",
            "primary_intent": f"Resolve: {issue_details.get('title', 'Unknown issue')}",
            "technical_requirements": ["Programming knowledge", "Git/GitHub access"],
            "affected_components": ["Unknown - requires investigation"],
            "prerequisites": ["Repository access", "Development environment setup"],
            "implementation_approach": {
                "strategy": "Investigation and step-by-step implementation",
                "key_steps": ["Investigate issue", "Plan solution", "Implement fix", "Test changes"],
                "potential_challenges": ["Requires code analysis"]
            },
            "success_criteria": ["Issue requirements met", "No regressions introduced"],
            "risk_assessment": {
                "breaking_changes": "medium",
                "testing_requirements": "standard",
                "rollback_complexity": "moderate"
            },
            "original_issue": issue_details,
            "analysis_success": False
        }
    
    async def setup_comprehensive_rag_pipeline(self, repo_url: str) -> Dict[str, Any]:
        """Setup comprehensive RAG pipeline exactly like tutorial system"""
        try:
            print(f"[INFO] Setting up comprehensive RAG pipeline for: {repo_url}")
            
            # Use the same repository setup as tutorial system
            result = await self.setup_repository_for_qa(repo_url)
            
            if result.get("success", False):
                print("[SUCCESS] Comprehensive RAG pipeline setup complete")
                return {
                    "success": True,
                    "chunks_created": result.get("chunks_processed", 0),
                    "enhanced_qa_ready": True,
                    "pipeline_type": "comprehensive"
                }
            else:
                raise Exception(f"RAG setup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[ERROR] Comprehensive RAG pipeline setup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_created": 0,
                "enhanced_qa_ready": False
            }
    
    async def get_enhanced_contextual_information(self, enhanced_issue_analysis: Dict[str, Any], 
                                                 issue_details: Dict[str, Any], repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced contextual information using comprehensive analysis"""
        try:
            # Extract information from enhanced analysis
            issue_type = enhanced_issue_analysis.get("issue_type", "other")
            complexity = enhanced_issue_analysis.get("complexity_level", "intermediate")
            technical_reqs = enhanced_issue_analysis.get("technical_requirements", [])
            affected_components = enhanced_issue_analysis.get("affected_components", [])
            
            # Generate specialized queries based on enhanced analysis
            queries = []
            
            # Query 1: Issue-specific implementation query
            primary_intent = enhanced_issue_analysis.get("primary_intent", "")
            if primary_intent:
                queries.append({
                    "question": f"How to implement: {primary_intent}",
                    "context_strategy": "focused_search",
                    "intent_type": "implementation_help"
                })
            
            # Query 2: Technical requirements query
            if technical_reqs:
                tech_query = f"Show code examples and patterns for {' '.join(technical_reqs[:3])}"
                queries.append({
                    "question": tech_query,
                    "context_strategy": "broad_exploration", 
                    "intent_type": "code_exploration"
                })
            
            # Query 3: Component-specific analysis
            if affected_components:
                comp_query = f"Analyze code structure and implementation for {' '.join(affected_components[:2])}"
                queries.append({
                    "question": comp_query,
                    "context_strategy": "comprehensive_analysis",
                    "intent_type": "technical_explanation"
                })
            
            # Query 4: Architecture and file structure
            issue_title = issue_details.get("title", "")
            if issue_title:
                arch_query = f"What files and components handle {issue_title}?"
                queries.append({
                    "question": arch_query,
                    "context_strategy": "architectural_overview",
                    "intent_type": "architectural_understanding"
                })
            
            # Execute enhanced QA queries
            contextual_info = {
                "relevant_files": [],
                "code_snippets": [],
                "implementation_patterns": [],
                "technical_insights": [],
                "architectural_info": [],
                "qa_responses": [],
                "enhanced_qa_used": False,
                "enhanced_analysis_used": True
            }
            
            # Execute using enhanced QA system
            try:
                from app.utils.enhanced_qa import handle_request
                contextual_info["enhanced_qa_used"] = True
                
                for query in queries[:4]:  # Execute up to 4 enhanced queries
                    try:
                        print(f"[INFO] Executing enhanced QA query: {query['question'][:50]}...")
                        
                        # Use enhanced QA system
                        result = handle_request(query["question"])
                        
                        if result and "answer" in result:
                            qa_response = {
                                "query": query["question"],
                                "answer": result["answer"],
                                "chunks_used": result.get("context_chunks_used", 0),
                                "strategy": query["context_strategy"],
                                "intent": query["intent_type"],
                                "confidence": result.get("confidence_score", 0.5)
                            }
                            contextual_info["qa_responses"].append(qa_response)
                            
                            # Categorize insights based on intent type
                            answer_text = result["answer"]
                            if query["intent_type"] == "implementation_help":
                                contextual_info["implementation_patterns"].append(answer_text[:500])
                            elif query["intent_type"] == "code_exploration":
                                contextual_info["code_snippets"].append(answer_text[:400])
                            elif query["intent_type"] == "technical_explanation":
                                contextual_info["technical_insights"].append(answer_text[:400])
                            elif query["intent_type"] == "architectural_understanding":
                                contextual_info["architectural_info"].append(answer_text[:400])
                            
                            # Extract file information from sources
                            sources = result.get("sources", [])
                            for source in sources:
                                if source.get("file"):
                                    contextual_info["relevant_files"].append(source["file"])
                        
                    except Exception as e:
                        print(f"[WARNING] Enhanced QA query failed for '{query['question'][:30]}...': {e}")
                        continue
                        
            except ImportError:
                print("[WARNING] Enhanced QA system not available, falling back to basic QA")
                contextual_info["enhanced_qa_used"] = False
                
                # Fallback to basic contextual information gathering
                basic_info = await self.get_contextual_information(issue_details, repo_analysis)
                contextual_info.update(basic_info)
            
            # Remove duplicates and limit results
            contextual_info["relevant_files"] = list(set(contextual_info["relevant_files"]))[:15]
            contextual_info["implementation_patterns"] = contextual_info["implementation_patterns"][:5]
            contextual_info["technical_insights"] = contextual_info["technical_insights"][:5]
            
            print(f"[SUCCESS] Enhanced contextual analysis complete: {len(contextual_info['qa_responses'])} queries executed")
            
            return contextual_info
            
        except Exception as e:
            print(f"[ERROR] Failed to get enhanced contextual information: {e}")
            return {
                "relevant_files": [],
                "code_snippets": [],
                "implementation_patterns": [],
                "technical_insights": [],
                "architectural_info": [],
                "qa_responses": [],
                "enhanced_qa_used": False,
                "enhanced_analysis_used": False,
                "error": str(e)
            }

    async def get_contextual_information(self, issue_details: Dict[str, Any], repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual information using SAME enhanced QA system as tutorial"""
        try:
            # Generate issue-specific queries based on issue details and repo analysis
            issue_title = issue_details.get("title", "")
            issue_body = issue_details.get("body", "")
            labels = issue_details.get("labels", [])
            tech_stack = repo_analysis.get("tech_stack", [])
            
            # Create enhanced queries using same approach as tutorial system
            queries = []
            
            # Query 1: Direct issue analysis (implementation help)
            if issue_title:
                queries.append({
                    "question": f"How to implement or fix: {issue_title}",
                    "context_strategy": "focused_search",
                    "intent_type": "implementation_help"
                })
            
            # Query 2: Code pattern search based on labels
            if labels:
                label_query = f"Show me code examples and patterns related to {' '.join(labels[:3])}"
                queries.append({
                    "question": label_query,
                    "context_strategy": "broad_exploration",
                    "intent_type": "code_exploration"
                })
            
            # Query 3: Technical context based on tech stack and issue body
            if tech_stack and issue_body:
                tech_query = f"Explain {' '.join(tech_stack[:2])} implementation patterns for: {issue_body[:200]}"
                queries.append({
                    "question": tech_query,
                    "context_strategy": "comprehensive_analysis",
                    "intent_type": "technical_explanation"
                })
            
            # Query 4: Architecture and file structure query
            if issue_title and tech_stack:
                arch_query = f"What files and components are involved in {issue_title} for {' '.join(tech_stack[:2])} projects?"
                queries.append({
                    "question": arch_query,
                    "context_strategy": "architectural_overview",
                    "intent_type": "architectural_understanding"
                })
            
            # Execute enhanced QA queries (same system as tutorial)
            contextual_info = {
                "relevant_files": [],
                "code_snippets": [],
                "implementation_patterns": [],
                "technical_insights": [],
                "architectural_info": [],
                "qa_responses": [],
                "enhanced_qa_used": False
            }
            
            # Try enhanced QA system first (same as tutorial)
            try:
                from app.utils.enhanced_qa import handle_request
                contextual_info["enhanced_qa_used"] = True
                
                for query in queries[:4]:  # Execute up to 4 enhanced queries
                    try:
                        print(f"[INFO] Executing enhanced QA query: {query['question'][:50]}...")
                        
                        # Use enhanced QA system (simplified call)
                        result = handle_request(query["question"])
                        
                        if result and "answer" in result:
                            qa_response = {
                                "query": query["question"],
                                "answer": result["answer"],
                                "chunks_used": result.get("context_chunks_used", 0),
                                "strategy": query["context_strategy"],  # Store intended strategy
                                "intent": query["intent_type"],  # Store intended intent
                                "confidence": result.get("confidence_score", 0.5)
                            }
                            contextual_info["qa_responses"].append(qa_response)
                            
                            # Categorize insights based on intent type (same as tutorial)
                            answer_text = result["answer"]
                            if query["intent_type"] == "implementation_help":
                                contextual_info["implementation_patterns"].append(answer_text[:500])
                            elif query["intent_type"] == "code_exploration":
                                contextual_info["code_snippets"].append(answer_text[:400])
                            elif query["intent_type"] == "technical_explanation":
                                contextual_info["technical_insights"].append(answer_text[:400])
                            elif query["intent_type"] == "architectural_understanding":
                                contextual_info["architectural_info"].append(answer_text[:400])
                            
                            # Extract file information from sources (same as tutorial)
                            sources = result.get("sources", [])
                            for source in sources:
                                if source.get("file"):
                                    contextual_info["relevant_files"].append(source["file"])
                        
                    except Exception as e:
                        print(f"[WARNING] Enhanced QA query failed for '{query['question'][:30]}...': {e}")
                        continue
                        
            except ImportError:
                print("[WARNING] Enhanced QA system not available, falling back to basic QA")
                contextual_info["enhanced_qa_used"] = False
                
                # Fallback to basic QA system (same as original tutorial approach)
                from app.utils import qa
                
                for query in queries[:3]:  # Limit to 3 queries for basic QA
                    try:
                        print(f"[INFO] Executing basic QA query: {query['question'][:50]}...")
                        result = qa.smart_qa_with_enhanced_docs(query["question"], max_chunks=5)
                        
                        if result and "answer" in result:
                            contextual_info["qa_responses"].append({
                                "query": query["question"],
                                "answer": result["answer"],
                                "strategy": "basic_qa",
                                "intent": query["intent_type"]
                            })
                            
                            # Add to relevant files from sources
                            sources = result.get("sources", [])
                            for source in sources:
                                if source.get("file"):
                                    contextual_info["relevant_files"].append(source["file"])
                            
                            # Store insights
                            if query["intent_type"] == "implementation_help":
                                contextual_info["implementation_patterns"].append(result["answer"][:400])
                        
                    except Exception as e:
                        print(f"[WARNING] Basic QA query failed for '{query['question'][:30]}...': {e}")
                        continue
            
            # Remove duplicates and limit results (same cleanup as tutorial)
            contextual_info["relevant_files"] = list(set(contextual_info["relevant_files"]))[:15]
            contextual_info["implementation_patterns"] = contextual_info["implementation_patterns"][:5]
            contextual_info["technical_insights"] = contextual_info["technical_insights"][:5]
            
            print(f"[SUCCESS] Contextual analysis complete: {len(contextual_info['qa_responses'])} queries executed")
            
            return contextual_info
            
        except Exception as e:
            print(f"[ERROR] Failed to get contextual information: {e}")
            return {
                "relevant_files": [],
                "code_snippets": [],
                "implementation_patterns": [],
                "technical_insights": [],
                "architectural_info": [],
                "qa_responses": [],
                "enhanced_qa_used": False
            }
    
    async def generate_resolution_plan(self, issue_details: Dict[str, Any], repo_context: Dict[str, Any], 
                                       repo_analysis: Dict[str, Any], contextual_info: Dict[str, Any], 
                                       user_context: str = None, difficulty_preference: str = "intermediate") -> Dict[str, Any]:
        """Generate comprehensive resolution plan using LLM with enhanced context"""
        try:
            # Prepare enhanced prompt with all available context
            prompt = f"""
You are an expert software developer analyzing a GitHub issue for resolution. 
Provide a comprehensive, step-by-step resolution plan based on the following information:

## ISSUE DETAILS:
**Title:** {issue_details.get('title', 'N/A')}
**Labels:** {', '.join(issue_details.get('labels', []))}
**Body:** {issue_details.get('body', 'N/A')[:1000]}

## REPOSITORY ANALYSIS:
**Tech Stack:** {', '.join(repo_analysis.get('tech_stack', []))}
**Languages:** {', '.join(repo_analysis.get('languages', []))}
**File Structure:** {', '.join(repo_analysis.get('key_files', [])[:10])}

## ENHANCED CONTEXTUAL ANALYSIS:
**Context Retrieval System:** {'Enhanced QA (same as tutorial system)' if contextual_info.get('enhanced_qa_used') else 'Basic QA (fallback)'}
**Relevant Files:** {', '.join(contextual_info.get('relevant_files', [])[:8])}

**Implementation Patterns Found:**
{chr(10).join([f"- {pattern[:200]}..." for pattern in contextual_info.get('implementation_patterns', [])[:3]])}

**Technical Insights:**
{chr(10).join([f"- {insight[:200]}..." for insight in contextual_info.get('technical_insights', [])[:3]])}

**Architectural Information:**
{chr(10).join([f"- {arch[:200]}..." for arch in contextual_info.get('architectural_info', [])[:3]])}

**QA Analysis Results:**
{chr(10).join([f"Q: {qa['query'][:100]}... | Strategy: {qa.get('strategy', 'basic')} | Intent: {qa.get('intent', 'general')}" 
               for qa in contextual_info.get('qa_responses', [])[:3]])}

## USER PREFERENCES:
**Experience Level:** {difficulty_preference}
**Context:** {user_context or 'Not specified'}

## REPOSITORY INFO:
**Full Name:** {repo_context.get('full_name', 'Unknown')}
**Language:** {repo_context.get('language', 'Unknown')}
**Description:** {repo_context.get('description', 'No description available')[:200]}

Based on this comprehensive analysis, provide:

1. **ISSUE DIAGNOSIS** (2-3 sentences):
   - Root cause analysis
   - Complexity assessment

2. **RESOLUTION STEPS** (5-8 detailed steps):
   - Each step should be specific and actionable
   - Include file modifications, code changes, or configurations
   - Reference the relevant files and patterns found
   - Utilize the technical insights and architectural information

3. **IMPLEMENTATION GUIDANCE**:
   - Key files to modify (from relevant files identified)
   - Code patterns to follow (from implementation patterns found)
   - Testing recommendations
   - Potential edge cases

4. **VALIDATION CHECKLIST**:
   - How to verify the fix works
   - Regression testing suggestions

Focus on actionable, specific guidance that leverages the contextual analysis and repository insights.
"""

            # Call LLM with enhanced context (same tracking as tutorial system)
            from app.utils.config import get_tracked_llm_call
            tracked_llm_call = get_tracked_llm_call()
            
            print("[INFO] Generating resolution plan with enhanced context using LLM...")
            llm_response = await tracked_llm_call(prompt)
            
            if not llm_response:
                raise Exception("Empty LLM response")
            
            # Extract content from response object if needed
            if hasattr(llm_response, 'content'):
                response_text = llm_response.content
            elif hasattr(llm_response, 'text'):
                response_text = llm_response.text
            else:
                response_text = str(llm_response)
            
            if not response_text or response_text.strip() == "":
                raise Exception("Empty LLM response content")
            
            # Parse LLM response into structured format
            resolution_plan = self._parse_resolution_response(response_text, contextual_info)
            
            # Add metadata from enhanced analysis
            if not resolution_plan:
                resolution_plan = {}
            
            resolution_plan["metadata"] = {
                "enhanced_qa_used": contextual_info.get("enhanced_qa_used", False) if contextual_info else False,
                "context_queries_executed": len(contextual_info.get("qa_responses", [])) if contextual_info else 0,
                "relevant_files_found": len(contextual_info.get("relevant_files", [])) if contextual_info else 0,
                "implementation_patterns_count": len(contextual_info.get("implementation_patterns", [])) if contextual_info else 0,
                "technical_insights_count": len(contextual_info.get("technical_insights", [])) if contextual_info else 0,
                "architectural_info_count": len(contextual_info.get("architectural_info", [])) if contextual_info else 0,
                "resolution_complexity": self._assess_complexity(issue_details, contextual_info or {}),
                "confidence_score": self._calculate_confidence(contextual_info or {}, repo_analysis or {})
            }
            
            return resolution_plan
            
        except Exception as e:
            print(f"[ERROR] Failed to generate resolution plan: {e}")
            return {
                "diagnosis": f"Error analyzing issue: {str(e)}",
                "steps": [{
                    "step_number": 1,
                    "title": "Manual Investigation Required",
                    "description": "Automated analysis failed. Please investigate manually.",
                    "files_to_modify": [],
                    "code_changes": [],
                    "notes": f"Error: {str(e)}"
                }],
                "implementation_guidance": {
                    "key_files": [],
                    "patterns": [],
                    "testing": [],
                    "edge_cases": []
                },
                "validation_checklist": [],
                "metadata": {
                    "enhanced_qa_used": False,
                    "error": str(e)
                }
            }
    
    async def generate_comprehensive_resolution_markdown(self, enhanced_issue_analysis: Dict[str, Any],
                                                        issue_details: Dict[str, Any], repo_context: Dict[str, Any],
                                                        repo_analysis: Dict[str, Any], contextual_info: Dict[str, Any],
                                                        user_context: str = "", difficulty_preference: str = "intermediate") -> str:
        """Generate comprehensive step-by-step markdown guide from git clone to push"""
        try:
            print("[INFO] Generating comprehensive resolution markdown with LLM...")
            
            # Extract key information for prompt
            repo_full_name = repo_context.get("full_name", "unknown/repo")
            issue_number = issue_details.get("number", "unknown")
            issue_title = issue_details.get("title", "")
            issue_body = issue_details.get("body", "")
            
            # Enhanced issue analysis data
            issue_type = enhanced_issue_analysis.get("issue_type", "other")
            complexity = enhanced_issue_analysis.get("complexity_level", "intermediate")
            primary_intent = enhanced_issue_analysis.get("primary_intent", "")
            technical_reqs = enhanced_issue_analysis.get("technical_requirements", [])
            affected_components = enhanced_issue_analysis.get("affected_components", [])
            implementation_approach = enhanced_issue_analysis.get("implementation_approach", {})
            success_criteria = enhanced_issue_analysis.get("success_criteria", [])
            
            # Contextual information
            relevant_files = contextual_info.get("relevant_files", [])[:10]
            implementation_patterns = contextual_info.get("implementation_patterns", [])[:3]
            technical_insights = contextual_info.get("technical_insights", [])[:3]
            qa_responses = contextual_info.get("qa_responses", [])[:3]
            
            # Repository information
            tech_stack = repo_analysis.get("tech_stack", [])
            main_dirs = repo_analysis.get("main_directories", [])
            
            # Create comprehensive prompt for markdown generation
            prompt = f"""
You are an expert technical writer and software developer. Create a comprehensive, step-by-step markdown guide for resolving the following GitHub issue. The guide should walk a developer through the ENTIRE process from git cloning to pushing the final solution.

## ISSUE CONTEXT
**Repository**: {repo_full_name}
**Issue #{issue_number}**: {issue_title}
**Issue Type**: {issue_type} | **Complexity**: {complexity}
**Primary Goal**: {primary_intent}

**Issue Description**:
{issue_body[:1000]}

## ENHANCED ANALYSIS
**Technical Requirements**: {', '.join(technical_reqs[:5])}
**Affected Components**: {', '.join(affected_components[:5])}
**Tech Stack**: {', '.join(tech_stack[:5])}
**Main Directories**: {', '.join(main_dirs[:5])}

**Implementation Strategy**: {implementation_approach.get('strategy', 'Step-by-step development')}

**Key Implementation Steps**:
{chr(10).join([f"- {step}" for step in implementation_approach.get('key_steps', [])[:5]])}

**Success Criteria**:
{chr(10).join([f"- {criteria}" for criteria in success_criteria[:5]])}

## RELEVANT CODE CONTEXT
**Files to Focus On**: {', '.join(relevant_files[:8])}

**Implementation Patterns Found**:
{chr(10).join([f"- {pattern[:200]}..." for pattern in implementation_patterns])}

**Technical Insights**:
{chr(10).join([f"- {insight[:200]}..." for insight in technical_insights])}

**QA Analysis Results**:
{chr(10).join([f"Q: {qa['query'][:100]}... | Answer: {qa['answer'][:150]}..." for qa in qa_responses])}

## USER CONTEXT
**Experience Level**: {difficulty_preference}
**Additional Context**: {user_context or 'None provided'}

---

Create a comprehensive markdown guide with the following structure:

# Resolving Issue #{issue_number}: {issue_title}

## 🎯 Issue Overview
[Brief summary of what needs to be done]

## 📋 Prerequisites
[List what the developer needs before starting]

## 🚀 Step-by-Step Resolution Guide

### Phase 1: Environment Setup
#### Step 1: Clone the Repository
```bash
# Provide exact git clone commands with branch considerations
```

#### Step 2: Environment Setup
```bash
# Commands for setting up development environment
# Include package installation, dependencies, etc.
```

#### Step 3: Explore the Codebase
```bash
# Commands to understand the repository structure
# Include file exploration and understanding commands
```

### Phase 2: Issue Investigation
#### Step 4: Understand the Problem
[Detailed analysis of the issue with file references]

#### Step 5: Locate Relevant Code
[Guide to finding the specific files and functions involved]

#### Step 6: Analyze Current Implementation
[Understanding the existing code structure]

### Phase 3: Implementation
#### Step 7: Plan the Solution
[Detailed implementation plan with code structure]

#### Step 8: Implement Core Changes
```[programming language]
// Provide specific code changes with full context
// Include file paths and exact modifications needed
```

#### Step 9: Handle Edge Cases
[Address potential issues and edge cases]

#### Step 10: Add/Update Tests
```[programming language]
// Provide test code if applicable
```

### Phase 4: Validation & Testing
#### Step 11: Local Testing
```bash
# Commands to test the changes locally
```

#### Step 12: Verification
[How to verify the fix works according to success criteria]

### Phase 5: Git Workflow
#### Step 13: Commit Changes
```bash
# Exact git commands for staging and committing
git add .
git commit -m "Fix: [descriptive commit message]"
```

#### Step 14: Push and Create Pull Request
```bash
# Commands for pushing and PR creation
git push origin feature-branch-name
```

## 🔍 Testing Checklist
[Specific tests to run to ensure the fix works]

## 🚨 Troubleshooting
[Common issues and solutions during implementation]

## 📝 Additional Notes
[Any important considerations, warnings, or best practices]

## 🎉 Success Verification
[Final steps to confirm the issue is completely resolved]

---

IMPORTANT GUIDELINES:
1. Be extremely specific with file paths, function names, and code snippets
2. Include exact bash/git commands that can be copy-pasted
3. Provide complete code examples with proper syntax highlighting
4. Make the guide suitable for the {difficulty_preference} experience level
5. Include error handling and troubleshooting steps
6. Ensure each step builds logically on the previous one
7. Include verification steps throughout the process
8. Make commit messages and PR descriptions professional
9. Address the specific technical requirements and affected components
10. Use the relevant files and implementation patterns identified

Generate a complete, production-ready markdown guide that a developer can follow from start to finish.
"""

            # Call LLM to generate comprehensive markdown
            from app.utils.llm_tracker import tracked_llm_call
            from app.utils.qa import llm
            
            llm_response = tracked_llm_call(
                module="issue_resolver",
                function="generate_comprehensive_resolution_markdown",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=prompt
            )
            
            # Extract content from response
            if hasattr(llm_response, 'content'):
                markdown_content = llm_response.content
            elif hasattr(llm_response, 'text'):
                markdown_content = llm_response.text
            else:
                markdown_content = str(llm_response)
            
            if not markdown_content or markdown_content.strip() == "":
                raise Exception("Empty markdown response from LLM")
            
            print("[SUCCESS] Comprehensive resolution markdown generated")
            return markdown_content
            
        except Exception as e:
            print(f"[ERROR] Failed to generate comprehensive markdown: {e}")
            return self._create_fallback_markdown_guidance_sync(
                issue_details.get("title", "Unknown Issue"),
                enhanced_issue_analysis.get("primary_intent", ""),
                str(e)
            )
    
    async def _create_fallback_markdown_guidance(self, issue_title: str, primary_intent: str, error: str) -> str:
        """Create fallback markdown guidance when LLM generation fails"""
        return self._create_fallback_markdown_guidance_sync(issue_title, primary_intent, error)
    
    def _create_fallback_markdown_guidance_sync(self, issue_title: str, primary_intent: str, error: str) -> str:
        """Create fallback markdown guidance when LLM generation fails (synchronous version)"""
        return f"""# Resolving Issue: {issue_title}

## ⚠️ Automated Analysis Failed

Unfortunately, the automated analysis encountered an error: `{error}`

However, here's a basic guide to get you started:

## 🚀 Basic Resolution Steps

### Phase 1: Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b fix/issue-resolution
   ```

3. **Install dependencies**
   ```bash
   # Follow repository's README for setup instructions
   ```

### Phase 2: Investigation
4. **Understand the issue**
   - Read the issue description carefully
   - Look for related files and components
   - Check existing tests

5. **Locate relevant code**
   - Search for keywords from the issue
   - Check recent commits for context

### Phase 3: Implementation
6. **Plan your solution**
   - {primary_intent or "Address the issue requirements"}
   - Consider edge cases and potential impacts

7. **Implement the fix**
   - Make targeted changes
   - Follow project coding standards
   - Add or update tests if needed

### Phase 4: Testing & Submission
8. **Test your changes**
   ```bash
   # Run project tests
   npm test  # or appropriate test command
   ```

9. **Commit and push**
   ```bash
   git add .
   git commit -m "Fix: {issue_title}"
   git push origin fix/issue-resolution
   ```

10. **Create pull request**
    - Describe your changes
    - Reference the original issue
    - Request review from maintainers

## 💡 Next Steps
- Manually analyze the repository structure
- Consult project documentation
- Ask maintainers for guidance if needed

**Note**: For a more detailed guide, please retry the analysis or consult the project's contribution guidelines.
"""

    def _parse_resolution_response(self, llm_response: str, contextual_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured resolution plan"""
        try:
            # Basic parsing - in production, this could be more sophisticated
            lines = llm_response.split('\n')
            
            resolution_plan = {
                "diagnosis": "",
                "steps": [],
                "implementation_guidance": {
                    "key_files": [],
                    "patterns": [],
                    "testing": [],
                    "edge_cases": []
                },
                "validation_checklist": []
            }
            
            current_section = None
            step_number = 1
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                line_lower = line.lower()
                if "diagnosis" in line_lower or "issue diagnosis" in line_lower:
                    current_section = "diagnosis"
                    continue
                elif "resolution steps" in line_lower or "steps" in line_lower:
                    current_section = "steps"
                    continue
                elif "implementation" in line_lower:
                    current_section = "implementation"
                    continue
                elif "validation" in line_lower:
                    current_section = "validation"
                    continue
                
                # Parse content based on current section
                if current_section == "diagnosis" and len(line) > 20:
                    resolution_plan["diagnosis"] += line + " "
                
                elif current_section == "steps" and (line.startswith('-') or line.startswith(str(step_number))):
                    # Parse resolution step
                    step_text = line.lstrip('- ').lstrip(f'{step_number}.').strip()
                    if len(step_text) > 10:
                        resolution_plan["steps"].append({
                            "step_number": step_number,
                            "title": step_text[:100],
                            "description": step_text,
                            "files_to_modify": self._extract_files_from_text(step_text, contextual_info),
                            "code_changes": [],
                            "notes": ""
                        })
                        step_number += 1
                
                elif current_section == "implementation":
                    if "file" in line_lower:
                        resolution_plan["implementation_guidance"]["key_files"].append(line)
                    elif "pattern" in line_lower or "code" in line_lower:
                        resolution_plan["implementation_guidance"]["patterns"].append(line)
                    elif "test" in line_lower:
                        resolution_plan["implementation_guidance"]["testing"].append(line)
                
                elif current_section == "validation" and line.startswith('-'):
                    resolution_plan["validation_checklist"].append(line.lstrip('- '))
            
            # Clean up diagnosis
            resolution_plan["diagnosis"] = resolution_plan["diagnosis"].strip()[:500]
            
            # Ensure we have at least one step
            if not resolution_plan["steps"]:
                resolution_plan["steps"] = [{
                    "step_number": 1,
                    "title": "Investigate and Implement Fix",
                    "description": "Based on the analysis, investigate the issue and implement appropriate fixes.",
                    "files_to_modify": contextual_info.get("relevant_files", [])[:5],
                    "code_changes": [],
                    "notes": "Refer to the diagnosis and implementation guidance for details."
                }]
            
            return resolution_plan
            
        except Exception as e:
            print(f"[ERROR] Failed to parse LLM response: {e}")
            return {
                "diagnosis": "Failed to parse resolution analysis",
                "steps": [],
                "implementation_guidance": {
                    "key_files": [],
                    "patterns": [],
                    "testing": [],
                    "edge_cases": []
                },
                "validation_checklist": []
            }
    
    def _extract_files_from_text(self, text: str, contextual_info: Dict[str, Any]) -> List[str]:
        """Extract relevant files mentioned in text"""
        if not contextual_info or not text:
            return []
            
        relevant_files = contextual_info.get("relevant_files", [])
        mentioned_files = []
        
        for file_path in relevant_files:
            file_name = file_path.split('/')[-1]
            if file_name.lower() in text.lower() or file_path.lower() in text.lower():
                mentioned_files.append(file_path)
        
        return mentioned_files[:3]  # Limit to 3 files per step
    
    def _assess_complexity(self, issue_details: Dict[str, Any], contextual_info: Dict[str, Any]) -> str:
        """Assess issue complexity based on available information"""
        try:
            complexity_score = 0
            
            # Label-based complexity
            labels = issue_details.get("labels", [])
            high_complexity_labels = ["bug", "critical", "major", "breaking-change", "architecture"]
            medium_complexity_labels = ["enhancement", "feature", "improvement"]
            
            for label in labels:
                if any(complex_label in label.lower() for complex_label in high_complexity_labels):
                    complexity_score += 3
                elif any(medium_label in label.lower() for medium_label in medium_complexity_labels):
                    complexity_score += 2
                else:
                    complexity_score += 1
            
            # Context-based complexity
            relevant_files_count = len(contextual_info.get("relevant_files", []))
            if relevant_files_count > 10:
                complexity_score += 3
            elif relevant_files_count > 5:
                complexity_score += 2
            elif relevant_files_count > 0:
                complexity_score += 1
            
            # QA response complexity
            qa_responses = contextual_info.get("qa_responses", [])
            if len(qa_responses) >= 3:
                complexity_score += 2
            elif len(qa_responses) >= 1:
                complexity_score += 1
            
            # Determine complexity level
            if complexity_score >= 8:
                return "high"
            elif complexity_score >= 4:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            print(f"[WARNING] Failed to assess complexity: {e}")
            return "unknown"
    
    def _calculate_confidence(self, contextual_info: Dict[str, Any], repo_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the resolution plan"""
        try:
            confidence = 0.0
            max_confidence = 1.0
            
            # Enhanced QA system used (same as tutorial) - higher confidence
            if contextual_info.get("enhanced_qa_used", False):
                confidence += 0.3
            else:
                confidence += 0.1  # Basic QA fallback
            
            # Number of QA responses executed
            qa_count = len(contextual_info.get("qa_responses", []))
            if qa_count >= 4:
                confidence += 0.2
            elif qa_count >= 2:
                confidence += 0.15
            elif qa_count >= 1:
                confidence += 0.1
            
            # Relevant files found
            files_count = len(contextual_info.get("relevant_files", []))
            if files_count >= 8:
                confidence += 0.2
            elif files_count >= 4:
                confidence += 0.15
            elif files_count >= 1:
                confidence += 0.1
            
            # Implementation patterns found
            patterns_count = len(contextual_info.get("implementation_patterns", []))
            if patterns_count >= 3:
                confidence += 0.15
            elif patterns_count >= 1:
                confidence += 0.1
            
            # Technical insights available
            insights_count = len(contextual_info.get("technical_insights", []))
            if insights_count >= 2:
                confidence += 0.1
            elif insights_count >= 1:
                confidence += 0.05
            
            # Repository analysis quality
            tech_stack = repo_analysis.get("tech_stack", [])
            if len(tech_stack) >= 2:
                confidence += 0.1
            elif len(tech_stack) >= 1:
                confidence += 0.05
            
            # Ensure confidence is within bounds
            confidence = min(confidence, max_confidence)
            confidence = max(confidence, 0.1)  # Minimum confidence
            
            return round(confidence, 2)
            
        except Exception as e:
            print(f"[WARNING] Failed to calculate confidence: {e}")
            return 0.5  # Default moderate confidence

    def _create_fallback_resolution_plan(self, issue_details: Dict[str, Any], repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic fallback resolution plan when LLM fails"""
        return {
            "resolution_summary": f"Manual investigation needed for: {issue_details.get('title', 'Unknown issue')}",
            "difficulty_level": "medium",
            "estimated_total_time": "2-4 hours",
            "skills_required": repo_analysis.get("tech_stack", ["programming"]),
            "resolution_steps": [
                {
                    "step_number": 1,
                    "title": "Clone and Setup Repository",
                    "description": "Clone the repository and set up the development environment",
                    "commands": ["git clone <repo_url>", "cd <repo_name>"],
                    "code_changes": [],
                    "files_to_check": ["README.md", "requirements.txt", "package.json"],
                    "estimated_time": "15-30 minutes",
                    "difficulty": "easy",
                    "prerequisites": []
                },
                {
                    "step_number": 2,
                    "title": "Investigate Issue",
                    "description": "Analyze the issue description and reproduce the problem",
                    "commands": [],
                    "code_changes": [],
                    "files_to_check": repo_analysis.get("likely_entry_points", []),
                    "estimated_time": "30-60 minutes",
                    "difficulty": "medium",
                    "prerequisites": ["Environment setup complete"]
                },
                {
                    "step_number": 3,
                    "title": "Implement Solution",
                    "description": "Develop and test the fix for the issue",
                    "commands": [],
                    "code_changes": ["Implement fix based on investigation"],
                    "files_to_check": [],
                    "estimated_time": "1-2 hours",
                    "difficulty": "medium",
                    "prerequisites": ["Issue investigation complete"]
                },
                {
                    "step_number": 4,
                    "title": "Test and Submit",
                    "description": "Test the fix and create a pull request",
                    "commands": ["git add .", "git commit -m 'Fix: issue description'", "git push origin branch-name"],
                    "code_changes": [],
                    "files_to_check": [],
                    "estimated_time": "30 minutes",
                    "difficulty": "easy",
                    "prerequisites": ["Solution implemented and tested"]
                }
            ],
            "alternative_approaches": ["Consult project documentation", "Ask maintainers for guidance"],
            "helpful_resources": ["Project README", "Issue tracker"],
            "potential_pitfalls": ["Not following project conventions", "Missing test coverage"],
            "verification_steps": ["Run existing tests", "Manually verify fix"]
        }

# Global instance
issue_resolver = GitHubIssueResolver()
