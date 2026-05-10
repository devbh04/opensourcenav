"""
Application configuration — loads from .env and provides typed settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


# ── LLM (Vertex AI or Google AI Studio) ─────────────────────────────
GCP_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", ""))
GCP_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", os.getenv("GCP_LOCATION", "us-central1"))
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# ── GitHub ───────────────────────────────────────────────────────────
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

# ── MongoDB ──────────────────────────────────────────────────────────
MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "EasyGit")

# ── Qdrant ───────────────────────────────────────────────────────────
QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost").strip()
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333").strip())
QDRANT_API_KEY: str = os.getenv("QDRANT_API", "").strip()  # For Qdrant Cloud
QDRANT_IS_CLOUD: bool = QDRANT_HOST.startswith("https://") or QDRANT_HOST.startswith("http://")

# ── App ──────────────────────────────────────────────────────────────
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# ── Embedding ────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "3072"))

# ── Repo Processing ─────────────────────────────────────────────────
CLONE_BASE_DIR: str = os.getenv("CLONE_BASE_DIR", "/tmp/EasyGit_clones")
MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", "100000"))

DEFAULT_INCLUDE_PATTERNS: list[str] = [
    "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
    "*.java", "*.go", "*.rs", "*.cpp", "*.c", "*.h",
    "*.rb", "*.php", "*.swift", "*.kt",
    "*.md", "*.txt", "*.yaml", "*.yml", "*.toml", "*.json",
    "*.css", "*.html",
    "Dockerfile", "Makefile", "*.sh",
]

DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    "node_modules/*", ".git/*", "__pycache__/*", "*.pyc",
    "dist/*", "build/*", ".next/*", ".venv/*", "venv/*",
    "*.lock", "package-lock.json", "yarn.lock",
    "*.min.js", "*.min.css", "*.map",
    ".DS_Store", "*.ico", "*.png", "*.jpg", "*.svg",
]
