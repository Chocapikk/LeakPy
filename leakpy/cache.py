"""
MIT License

Copyright (c) 2025 Valentin Lobstein (balgogan@protonmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""Cache management for API responses."""

import json
import hashlib
import time
from pathlib import Path
from .config import get_config_dir, CacheConfig


class APICache:
    """Simple file-based cache for API responses."""
    
    CACHE_FILE = "api_cache.json"
    DEFAULT_TTL = 300  # 5 minutes in seconds (conservative default)
    
    def __init__(self, ttl=None):
        """
        Initialize the cache.
        
        Args:
            ttl (int, optional): Time to live for cache entries in seconds. 
                If None, will try to load from config, otherwise defaults to 5 minutes (300 seconds).
        """
        # Try to load TTL from config if not provided
        if ttl is None:
            cache_config = CacheConfig()
            ttl_minutes = cache_config.get_ttl_minutes()
            if ttl_minutes is not None:
                ttl = ttl_minutes * 60  # Convert minutes to seconds
            else:
                ttl = self.DEFAULT_TTL
        self.ttl = ttl
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

