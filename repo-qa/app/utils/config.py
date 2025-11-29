import os
from dotenv import load_dotenv

load_dotenv()

# GitHub API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = "models/embedding-001"
CHAT_MODEL = "models/gemini-2.0-flash"

# Git Helper Configuration
DEFAULT_MIN_STARS = 100
DEFAULT_MIN_FORKS = 0
DEFAULT_MIN_OPEN_ISSUES = 10
DEFAULT_PER_PAGE = 200
MAX_SEARCH_RESULTS = 500

# Cache Configuration
CACHE_EXPIRY_HOURS = 24
CACHE_DIR = "cache"

# Rate Limiting Configuration
GITHUB_API_DELAY = 1  # seconds between API calls
MAX_RETRIES = 3