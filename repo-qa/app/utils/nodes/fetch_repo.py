# FetchRepo Node - Intelligent code file collection and filtering
import os
import git
import tempfile
import shutil
import fnmatch
from pathlib import Path
from typing import List, Tuple, Dict, Any, Set
from urllib.parse import urlparse

from app.utils.flow_engine import Node, NodeResult

class FetchRepo(Node):
    """
    Collects relevant code files from repositories or local directories
    with intelligent filtering and size management
    """
    
    def __init__(self):
        super().__init__(
            name="FetchRepo",
            description="Collect and filter relevant code files from repository or local directory"
        )
        self.supported_extensions = {
            # Programming languages
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
            '.hs', '.ml', '.fs', '.vb', '.pl', '.sh', '.ps1', '.r', '.m', '.mm',
            
            # Web technologies
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            
            # Documentation and config
            '.md', '.rst', '.txt', '.dockerfile', '.gitignore', '.gitattributes',
            '.env', '.example', '.template', '.lock', '.log', '.sql', '.graphql',
            
            # Build and package files
            '.gradle', '.maven', '.pom', '.sbt', '.cabal', '.cmake', '.make',
            'makefile', 'rakefile', 'gemfile', 'pipfile', 'requirements.txt',
            'package.json', 'composer.json', 'cargo.toml', 'go.mod', 'setup.py'
        }
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare file collection by validating inputs and setting up parameters"""
        try:
            repo_url = shared.get("repo_url", "").strip()
            local_dir = shared.get("local_dir", "").strip()
            
            if not repo_url and not local_dir:
                return NodeResult(
                    success=False,
                    error="Either repo_url or local_dir must be provided"
                )
            
            # Determine source type and path
            if repo_url:
                if not self._is_valid_repo_url(repo_url):
                    return NodeResult(
                        success=False,
                        error=f"Invalid repository URL: {repo_url}"
                    )
                source_type = "repository"
                source_path = repo_url
            else:
                if not os.path.exists(local_dir):
                    return NodeResult(
                        success=False,
                        error=f"Local directory does not exist: {local_dir}"
                    )
                source_type = "local"
                source_path = local_dir
            
            # Get filtering parameters
            include_patterns = shared.get("include_patterns", ["*"])
            exclude_patterns = shared.get("exclude_patterns", [])
            selected_files = shared.get("selected_files", [])  # Get selected files list
            max_file_size = shared.get("max_file_size", 100000)  # 100KB default
            
            prep_data = {
                "source_type": source_type,
                "source_path": source_path,
                "include_patterns": include_patterns,
                "exclude_patterns": exclude_patterns,
                "selected_files": selected_files,  # Include selected files in prep data
                "max_file_size": max_file_size,
                "temp_dir": None
            }
            
            print(f"    📁 Source Type: {source_type}")
            print(f"    📍 Source Path: {source_path}")
            if selected_files:
                print(f"    📋 Selected Files: {len(selected_files)} files specified")
            else:
                print(f"    📋 Include Patterns: {include_patterns}")
                print(f"    🚫 Exclude Patterns: {exclude_patterns}")
            print(f"    📏 Max File Size: {max_file_size:,} bytes")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "source_type": source_type,
                    "filtering_config": {
                        "include_patterns": len(include_patterns),
                        "exclude_patterns": len(exclude_patterns),
                        "selected_files": len(selected_files),
                        "max_file_size": max_file_size
                    }
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute file collection from source"""
        try:
            prep_data = prep_result.data
            source_type = prep_data["source_type"]
            source_path = prep_data["source_path"]
            
            # Get working directory
            if source_type == "repository":
                print(f"    📥 Cloning repository: {source_path}")
                working_dir = self._clone_repository(source_path)
                prep_data["temp_dir"] = working_dir
            else:
                print(f"    📂 Using local directory: {source_path}")
                working_dir = source_path
            
            # Collect files
            print(f"    🔍 Scanning for files...")
            selected_files = prep_data.get("selected_files", [])
            
            if selected_files:
                # Use specific selected files
                print(f"    📋 Using {len(selected_files)} selected files")
                file_paths = self._get_selected_files(working_dir, selected_files)
            else:
                # Use pattern-based discovery
                file_paths = self._scan_directory(working_dir, prep_data)
            
            print(f"    📄 Found {len(file_paths)} candidate files")
            
            # Filter and read files
            print(f"    📖 Reading and filtering files...")
            files_content = self._read_and_filter_files(file_paths, prep_data)
            
            # Calculate statistics
            total_size = sum(len(content) for _, content in files_content)
            avg_size = total_size // len(files_content) if files_content else 0
            
            print(f"    ✅ Collected {len(files_content)} files")
            print(f"    📊 Total content size: {total_size:,} bytes")
            print(f"    📊 Average file size: {avg_size:,} bytes")
            
            return NodeResult(
                success=True,
                data={
                    "files": files_content,
                    "working_dir": working_dir,
                    "temp_dir": prep_data["temp_dir"]
                },
                metadata={
                    "total_files": len(files_content),
                    "total_size": total_size,
                    "average_size": avg_size,
                    "file_types": self._analyze_file_types(files_content)
                }
            )
            
        except Exception as e:
            # Cleanup temp directory if it was created
            if prep_data.get("temp_dir") and os.path.exists(prep_data["temp_dir"]):
                shutil.rmtree(prep_data["temp_dir"], ignore_errors=True)
            
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with collected files"""
        try:
            exec_data = exec_result.data
            files = exec_data["files"]
            temp_dir = exec_data.get("temp_dir")
            
            # Update shared state
            shared["files"] = files
            shared["total_files_processed"] = len(files)
            shared["total_content_size"] = sum(len(content) for _, content in files)
            
            # Extract project name if not provided
            if not shared.get("project_name") or shared["project_name"] == "Unknown Project":
                if shared.get("repo_url"):
                    # Extract from repo URL
                    repo_name = shared["repo_url"].rstrip('/').split('/')[-1]
                    if repo_name.endswith('.git'):
                        repo_name = repo_name[:-4]
                    shared["project_name"] = repo_name
                elif shared.get("local_dir"):
                    # Extract from directory name
                    shared["project_name"] = os.path.basename(shared["local_dir"].rstrip('/'))
            
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"    🗑️  Cleaned up temporary directory")
            
            print(f"    📝 Updated shared state with {len(files)} files")
            print(f"    🏷️  Project name: {shared['project_name']}")
            
            return NodeResult(
                success=True,
                data={"files_added": len(files)},
                metadata={
                    "project_name": shared["project_name"],
                    "files_summary": exec_result.metadata
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _is_valid_repo_url(self, url: str) -> bool:
        """Validate repository URL format"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc in ['github.com', 'gitlab.com', 'bitbucket.org'] and
                len(parsed.path.strip('/').split('/')) >= 2
            )
        except:
            return False
    
    def _clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix="tutorial_repo_")
        try:
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            return temp_dir
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {str(e)}")
    
    def _scan_directory(self, directory: str, prep_data: Dict[str, Any]) -> List[str]:
        """Scan directory for files matching criteria"""
        file_paths = []
        include_patterns = prep_data["include_patterns"]
        exclude_patterns = prep_data["exclude_patterns"]
        
        for root, dirs, files in os.walk(directory):
            # Filter directories to skip
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d, exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                
                # Check if file should be included
                if self._should_include_file(relative_path, include_patterns, exclude_patterns):
                    file_paths.append(file_path)
        
        return file_paths
    
    def _should_exclude_dir(self, dirname: str, exclude_patterns: List[str]) -> bool:
        """Check if directory should be excluded"""
        exclude_dirs = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'node_modules', 'dist', 'build', '.next', '.nuxt',
            'target', 'bin', 'obj', '.idea', '.vscode',
            'venv', 'env', '.env', 'virtualenv'
        }
        
        if dirname in exclude_dirs:
            return True
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(dirname, pattern):
                return True
        
        return False
    
    def _should_include_file(self, filepath: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
        """Check if file should be included based on patterns"""
        filename = os.path.basename(filepath)
        
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filename, pattern):
                return False
        
        # Check include patterns
        if include_patterns == ["*"]:
            # Default: include by extension
            ext = os.path.splitext(filename)[1].lower()
            return (
                ext in self.supported_extensions or
                filename.lower() in {'makefile', 'dockerfile', 'rakefile', 'gemfile'}
            )
        
        # Explicit include patterns
        for pattern in include_patterns:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
    
    def _read_and_filter_files(self, file_paths: List[str], prep_data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Read files and filter by size and content"""
        files_content = []
        max_file_size = prep_data["max_file_size"]
        
        for file_path in file_paths:
            try:
                # Check file size
                if os.path.getsize(file_path) > max_file_size:
                    continue
                
                # Try to read as text
                content = self._read_file_safely(file_path)
                if content is not None:
                    # Use relative path from working directory
                    working_dir = prep_data.get("working_dir", os.path.dirname(file_path))
                    if "working_dir" in prep_data:
                        relative_path = os.path.relpath(file_path, working_dir)
                    else:
                        relative_path = os.path.basename(file_path)
                    
                    files_content.append((relative_path, content))
                
            except Exception as e:
                print(f"    ⚠️  Skipped {file_path}: {str(e)}")
                continue
        
        return files_content
    
    def _read_file_safely(self, file_path: str) -> str:
        """Safely read file with encoding detection"""
        encodings = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Check if content is mostly text
                    if self._is_text_content(content):
                        return content
                    else:
                        return None  # Skip binary files
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                return None
        
        return None  # Could not decode
    
    def _is_text_content(self, content: str) -> bool:
        """Check if content appears to be text (not binary)"""
        if not content:
            return True
        
        # Check for null bytes (common in binary files)
        if '\x00' in content:
            return False
        
        # Check ratio of printable characters
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        ratio = printable_chars / len(content)
        
        return ratio > 0.7  # At least 70% printable
    
    def _get_selected_files(self, working_dir: str, selected_files: List[str]) -> List[str]:
        """Get file paths for specifically selected files"""
        file_paths = []
        
        for file_path in selected_files:
            # Handle relative paths by joining with working directory
            if not os.path.isabs(file_path):
                full_path = os.path.join(working_dir, file_path)
            else:
                full_path = file_path
            
            # Normalize the path
            full_path = os.path.normpath(full_path)
            
            # Check if file exists
            if os.path.isfile(full_path):
                file_paths.append(full_path)
            else:
                print(f"    ⚠️  Selected file not found: {file_path}")
        
        return file_paths
    
    def _analyze_file_types(self, files: List[Tuple[str, str]]) -> Dict[str, int]:
        """Analyze distribution of file types"""
        type_counts = {}
        
        for filepath, _ in files:
            ext = os.path.splitext(filepath)[1].lower()
            if not ext:
                ext = os.path.basename(filepath).lower()
            
            type_counts[ext] = type_counts.get(ext, 0) + 1
        
        return type_counts
