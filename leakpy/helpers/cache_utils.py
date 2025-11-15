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

from .constants import _ENCODING_UTF8
from .decorators import handle_exceptions
import hashlib
import json
import time
from ..cache import APICache
from ..config import CacheConfig

# ========================================================================
# CACHE HELPERS
# ========================================================================

def _has_cache(cache):
    """Check if cache is available."""
    return cache is not None


@handle_exceptions(default_return=(None, False))
def with_cache(cache, endpoint, params):
    """Check cache and return if found."""
    if not _has_cache(cache):
        return None, False
    cached = cache.get(endpoint, params)
    return (cached, True) if cached is not None else (None, False)


@handle_exceptions(default_return=None)
def save_to_cache(cache, endpoint, params, data):
    """Save data to cache."""
    if _has_cache(cache) and data is not None:
        cache.set(endpoint, params, data)

# ============================================================================
# HASH AND KEY GENERATION
# ============================================================================

def make_hash_key(endpoint, params=None):
    """Generate a hash key from endpoint and params (for cache keys)."""
    key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
    return hashlib.sha256(key_data.encode(_ENCODING_UTF8)).hexdigest()


# ============================================================================
# CACHE STATISTICS
# ============================================================================

def get_cache_stats():
    """Get cache statistics."""
    cache = APICache()
    cache_config = CacheConfig()
    
    stats = {
        'total_entries': len(cache._cache),
        'ttl_seconds': cache.ttl,
        'ttl_minutes': cache.ttl // 60,
        'configured_ttl_minutes': cache_config.get_ttl_minutes(),
        'cache_file_size': 0,
        'cache_file_path': str(cache.cache_file),
        'expired_entries': 0,
        'active_entries': 0,
        'oldest_entry_age': 0,
        'newest_entry_age': 0,
    }
    
    if cache.cache_file.exists():
        stats['cache_file_size'] = cache.cache_file.stat().st_size
    
    current_time = time.time()
    entry_ages = []
    
    for key, entry in cache._cache.items():
        entry_ttl = entry.get('ttl', cache.ttl)
        entry_age = current_time - entry['timestamp']
        
        if entry_age > entry_ttl:
            stats['expired_entries'] += 1
        else:
            stats['active_entries'] += 1
            entry_ages.append(entry_age)
    
    if entry_ages:
        stats['oldest_entry_age'] = max(entry_ages)
        stats['newest_entry_age'] = min(entry_ages)
    
    return stats
