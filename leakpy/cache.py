"""Cache management for API responses."""

import json
import hashlib
import time
from pathlib import Path
from .config import get_config_dir


class APICache:
    """Simple file-based cache for API responses."""
    
    CACHE_FILE = "api_cache.json"
    DEFAULT_TTL = 300  # 5 minutes in seconds (conservative default)
    
    def __init__(self, ttl=None):
        """
        Initialize the cache.
        
        Args:
            ttl (int, optional): Time to live for cache entries in seconds. Defaults to 1 hour.
        """
        self.ttl = ttl or self.DEFAULT_TTL
        self.cache_dir = get_config_dir()
        self.cache_file = self.cache_dir / self.CACHE_FILE
        self._cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except (IOError, OSError):
            pass
    
    def _make_key(self, endpoint, params=None):
        """Generate a cache key from endpoint and params."""
        key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()
    
    def get(self, endpoint, params=None):
        """
        Get cached response if available and not expired.
        
        Args:
            endpoint (str): API endpoint.
            params (dict, optional): Request parameters.
            
        Returns:
            dict or None: Cached response or None if not found/expired.
        """
        key = self._make_key(endpoint, params)
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        # Use entry-specific TTL if available, otherwise use default
        entry_ttl = entry.get('ttl', self.ttl)
        if time.time() - entry['timestamp'] > entry_ttl:
            # Expired, remove it
            del self._cache[key]
            self._save_cache()
            return None
        
        return entry['data']
    
    def set(self, endpoint, params=None, data=None, ttl=None):
        """
        Cache a response.
        
        Args:
            endpoint (str): API endpoint.
            params (dict, optional): Request parameters.
            data: Response data to cache.
            ttl (int, optional): Time to live in seconds. If None, uses default TTL.
        """
        if data is None:
            return
        
        key = self._make_key(endpoint, params)
        entry_ttl = ttl if ttl is not None else self.ttl
        self._cache[key] = {
            'timestamp': time.time(),
            'ttl': entry_ttl,
            'data': data
        }
        self._save_cache()
    
    def clear(self):
        """Clear all cache entries."""
        self._cache = {}
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except (IOError, OSError):
            pass
    
    def invalidate(self, endpoint, params=None):
        """Invalidate a specific cache entry."""
        key = self._make_key(endpoint, params)
        if key in self._cache:
            del self._cache[key]
            self._save_cache()

