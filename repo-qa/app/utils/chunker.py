import os
import fnmatch
from typing import List, Dict, Any
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
MAX_TOKENS = 3000

# Updated include patterns - more comprehensive
INCLUDE_GLOBS = [
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx", 
    "*.c", "*.cc", "*.cpp", "*.h", "*.hpp", "*.cs", "*.php", "*.rb", "*.swift",
    "*.kt", "*.scala", "*.sh", "*.bash", "*.zsh", "*.fish",
    "*.md", "*.rst", "*.txt", "*.rs", "*.toml", "*.ini", "*.cfg", "*.conf",
    "Dockerfile", "Makefile", "*.yaml", "*.yml", "*.json", "*.xml",
    "requirements.txt", "package.json", "Cargo.toml", "go.mod", "pom.xml",
    "*.sql", "*.graphql", "*.proto"
]

# Updated exclude patterns
EXCLUDE_GLOBS = [
    "assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", 
    "temp/*", "docs/*", "documentation/*", "wiki/*",
    "venv/*", ".venv/*", "env/*", ".env/*", "virtualenv/*",
    "*test*", "tests/*", "test/*", "__test__/*", "spec/*",
    "v1/*", "v2/*", "version/*", "dist/*", "build/*", "target/*", "out/*",
    "experimental/*", "deprecated/*", "misc/*", "legacy/*", "archive/*",
    ".git/*", ".github/*", ".gitlab/*", ".svn/*", ".hg/*",
    ".next/*", ".vscode/*", ".idea/*", ".vs/*",
    "obj/*", "bin/*", "node_modules/*", "bower_components/*", "vendor/*",
    "*.log", "*.tmp", "*.temp", "*.cache", "*.bak", "*.swp", "*.swo",
    "*.min.js", "*.min.css", "bundle.*", "*.bundle.*",
    ".pytest_cache/*", "__pycache__/*", "*.pyc", "*.pyo", "*.pyd",
    ".mypy_cache/*", ".coverage", "coverage/*",
    "migrations/*", "locale/*", "locales/*", "i18n/*"
]

def is_included(file_path: str) -> bool:
    """Check if file should be included based on patterns"""
    filename = os.path.basename(file_path)
    return any(fnmatch.fnmatch(filename, pattern) for pattern in INCLUDE_GLOBS)

def is_excluded(file_path: str) -> bool:
    """Check if file should be excluded based on patterns"""
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in EXCLUDE_GLOBS)

def get_file_type(file_path: str) -> str:
    """Determine file type for better categorization"""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path).lower()
    
    if filename in ['dockerfile', 'makefile'] or ext in ['.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf']: return 'config'
    if ext in ['.md', '.rst', '.txt']: return 'docs'
    if filename in ['requirements.txt', 'package.json', 'cargo.toml', 'go.mod', 'pom.xml']: return 'package'
    if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.java', '.c', '.cpp', '.cs', '.php', '.rb', '.swift', '.kt', '.scala', '.rs']: return 'source'
    if ext in ['.sh', '.bash', '.zsh', '.fish']: return 'script'
    if ext in ['.json', '.xml', '.sql', '.graphql', '.proto']: return 'data'
    return 'other'

def estimate_importance(file_path: str, content: str) -> int:
    """Estimate file importance for prioritization (1-10 scale)"""
    filename = os.path.basename(file_path).lower()
    file_type = get_file_type(file_path)
    
    if filename in ['main.py', 'app.py', 'index.js', 'main.js', 'server.js', 'main.go', 'main.java']: return 10
    if filename in ['readme.md', 'requirements.txt', 'package.json', 'dockerfile', 'makefile']: return 9
    if filename.startswith('__init__.py') or filename in ['setup.py', 'config.py', 'settings.py']: return 8
    if file_type == 'package': return 8
    if file_type == 'config': return 7
    if file_type == 'source' and any(kw in content.lower() for kw in ['class ', 'def ', 'function ', 'interface ', 'struct ']): return 7
    if file_type == 'docs': return 6
    if file_type == 'source': return 5
    return 4

def chunk_repo(repo_path: str) -> List[Dict[str, Any]]:
    """Chunk repository with improved metadata and prioritization"""
    chunks = []
    file_stats = {'total': 0, 'processed': 0, 'skipped': 0, 'large': 0, 'by_type': {}}

    print(f"[INFO] Starting to chunk repository: {repo_path}")
    for root, _, files in os.walk(repo_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            file_stats['total'] += 1

            if is_excluded(rel_path) or not is_included(rel_path):
                file_stats['skipped'] += 1
                continue

            try:
                content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(full_path, "r", encoding=encoding) as f: content = f.read()
                        break
                    except UnicodeDecodeError: continue
                
                if content is None or not content.strip():
                    file_stats['skipped'] += 1
                    continue

                file_type = get_file_type(rel_path)
                importance = estimate_importance(rel_path, content)
                file_stats['processed'] += 1
                file_stats['by_type'][file_type] = file_stats['by_type'].get(file_type, 0) + 1
                tokens = tokenizer.encode(content)

                if len(tokens) <= MAX_TOKENS:
                    chunks.append({"file": rel_path, "content": content, "file_type": file_type, "importance": importance, "tokens": len(tokens), "chunk_index": 0, "total_chunks": 1})
                else:
                    file_stats['large'] += 1
                    total_chunks = (len(tokens) + MAX_TOKENS - 1) // MAX_TOKENS
                    for i in range(total_chunks):
                        start, end = i * MAX_TOKENS, (i + 1) * MAX_TOKENS
                        chunk_content = tokenizer.decode(tokens[start:end])
                        chunks.append({"file": f"{rel_path} (part {i+1}/{total_chunks})", "content": chunk_content, "file_type": file_type, "importance": importance, "tokens": len(tokenizer.encode(chunk_content)), "chunk_index": i, "total_chunks": total_chunks, "original_file": rel_path})
            except Exception as e:
                print(f"[ERROR] Failed to process {rel_path}: {e}")
                file_stats['skipped'] += 1

    chunks.sort(key=lambda x: (x['importance'], x['file_type']), reverse=True)
    print(f"[INFO] Repo chunking complete: Processed {file_stats['processed']}/{file_stats['total']} files. Created {len(chunks)} chunks.")
    return chunks