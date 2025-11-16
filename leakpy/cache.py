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
import time
from pathlib import Path
from . import helpers
from .config import CacheConfig


class APICache:
    """Simple file-based cache for API responses."""
    
    # ========================================================================
    # CLASS CONSTANTS
    # ========================================================================
    
    CACHE_FILE = "api_cache.json"
    DEFAULT_TTL = 300  # 5 minutes in seconds (conservative default)
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def __init__(self, ttl=None):
        """
        Initialize the cache.
        
        Args:
            ttl (int, optional): Time to live for cache entries in seconds. 
                If None, will try to load from config, otherwise defaults to 5 minutes (300 seconds).
        """
        self.ttl = self._determine_ttl(ttl)
        self.cache_dir = helpers.get_config_dir()
        self.cache_file = self.cache_dir / self.CACHE_FILE
        self._cache = self._load_cache()
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
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
        if self._is_entry_expired(entry):
            self._remove_entry_and_save(key)
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
        helpers.delete_file_safe(self.cache_file)
    
    def invalidate(self, endpoint, params=None):
        """Invalidate a specific cache entry."""
        key = self._make_key(endpoint, params)
        if key in self._cache:
            self._remove_entry_and_save(key)
    
    # ========================================================================
    # PRIVATE: INITIALIZATION HELPERS
    # ========================================================================
    
    def _determine_ttl(self, ttl):
        """Determine TTL value from parameter or config."""
        if ttl is not None:
            return ttl
        cache_config = CacheConfig()
        ttl_minutes = cache_config.get_ttl_minutes()
        return (ttl_minutes * 60) if ttl_minutes is not None else self.DEFAULT_TTL
    
    # ========================================================================
    # PRIVATE: FILE OPERATIONS
    # ========================================================================
    
    @helpers.handle_file_errors(default_return={})
    def _load_cache(self):
        """Load cache from file and remove expired entries."""
        if not self.cache_file.exists():
            return {}
        
        from .helpers.constants import _ENCODING_UTF8
        with open(self.cache_file, 'r', encoding=_ENCODING_UTF8) as f:
            cache_data = json.load(f)
        
        # Remove expired entries immediately
        current_time = time.time()
        expired_keys = []
        for key, entry in cache_data.items():
            if self._is_entry_expired(entry):
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del cache_data[key]
        
        # Save cleaned cache if we removed any entries
        if expired_keys:
            self._cache = cache_data
            self._save_cache()
        
        return cache_data
    
    @helpers.handle_file_errors()
    def _save_cache(self):
        """Save cache to file."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        from .helpers.constants import _ENCODING_UTF8
        with open(self.cache_file, 'w', encoding=_ENCODING_UTF8) as f:
            json.dump(self._cache, f, indent=2)
    
    # ========================================================================
    # PRIVATE: CACHE ENTRY OPERATIONS
    # ========================================================================
    
    def _make_key(self, endpoint, params=None):
        """Generate a cache key from endpoint and params."""
        return helpers.make_hash_key(endpoint, params)
    
    def _is_entry_expired(self, entry):
        """Check if cache entry is expired."""
        entry_ttl = entry.get('ttl', self.ttl)
        return time.time() - entry['timestamp'] > entry_ttl
    
    def _remove_entry_and_save(self, key):
        """Remove cache entry and save cache."""
        del self._cache[key]
        self._save_cache()

