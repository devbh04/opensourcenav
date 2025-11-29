import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

class GitHubCache:
    """
    Smart caching system for GitHub API responses.
    Reduces API calls while maintaining data freshness.
    """

    def __init__(self, cache_dir: str = "cache", expiry_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.expiry_hours = expiry_hours
        self.cache_dir.mkdir(exist_ok=True)

        # In-memory cache for faster access
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, operation: str, identifier: str) -> str:
        """Generate a unique cache key"""
        return f"{operation}_{identifier.replace('/', '_').replace('-', '_')}"

    def _get_cache_file(self, key: str) -> Path:
        """Get the cache file path"""
        return self.cache_dir / f"{key}.json"

    def _is_expired(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cache data has expired"""
        cached_time = cache_data.get('cached_at', 0)
        expiry_time = self.expiry_hours * 3600  # Convert hours to seconds
        return (time.time() - cached_time) > expiry_time

    def _save_to_file(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to cache file"""
        try:
            cache_data = {
                'cached_at': time.time(),
                'data': data
            }
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache for {key}: {e}")

    def _load_from_file(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from cache file"""
        try:
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            if self._is_expired(cache_data):
                # Remove expired cache file
                cache_file.unlink(missing_ok=True)
                return None

            return cache_data['data']
        except Exception as e:
            print(f"Warning: Failed to load cache for {key}: {e}")
            return None

    def get(self, operation: str, identifier: str) -> Optional[Any]:
        """
        Get data from cache.
        Returns None if not cached or expired.
        """
        key = self._get_cache_key(operation, identifier)

        # Check memory cache first
        if key in self.memory_cache:
            cache_data = self.memory_cache[key]
            if not self._is_expired(cache_data):
                return cache_data['data']
            else:
                # Remove expired memory cache
                del self.memory_cache[key]

        # Check file cache
        data = self._load_from_file(key)
        if data is not None:
            # Update memory cache
            self.memory_cache[key] = {
                'cached_at': time.time(),
                'data': data
            }
            return data

        return None

    def set(self, operation: str, identifier: str, data: Any) -> None:
        """
        Save data to cache.
        """
        key = self._get_cache_key(operation, identifier)

        # Save to memory cache
        self.memory_cache[key] = {
            'cached_at': time.time(),
            'data': data
        }

        # Save to file cache
        self._save_to_file(key, data)

    def clear(self, operation: str = None, identifier: str = None) -> None:
        """
        Clear cache entries.
        If operation is None, clears all cache.
        If identifier is None, clears all entries for that operation.
        """
        if operation is None:
            # Clear all cache
            self.memory_cache.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
        elif identifier is None:
            # Clear all entries for operation
            keys_to_remove = [k for k in self.memory_cache.keys() if k.startswith(f"{operation}_")]
            for key in keys_to_remove:
                del self.memory_cache[key]

            # Remove matching files
            for cache_file in self.cache_dir.glob(f"{operation}_*.json"):
                cache_file.unlink(missing_ok=True)
        else:
            # Clear specific entry
            key = self._get_cache_key(operation, identifier)
            if key in self.memory_cache:
                del self.memory_cache[key]

            cache_file = self._get_cache_file(key)
            cache_file.unlink(missing_ok=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_files = len(list(self.cache_dir.glob("*.json")))
        memory_entries = len(self.memory_cache)

        return {
            'cache_dir': str(self.cache_dir),
            'total_cache_files': total_files,
            'memory_cache_entries': memory_entries,
            'expiry_hours': self.expiry_hours
        }

# Global cache instance
cache = GitHubCache()
