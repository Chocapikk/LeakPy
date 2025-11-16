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

from .cache_utils import with_cache, save_to_cache
import json
import requests


def get_api_headers(api_key, include_accept=True):
    """Get standard headers for API requests."""
    from .. import __version__
    headers = {
        "api-key": api_key,
        "User-Agent": f"LeakPy/{__version__}"
    }
    if include_accept:
        headers["Accept"] = "application/json"
    return headers


def make_api_request(base_url, endpoint, api_key, params=None, stream=False, include_accept=True, log_func=None):
    """Make a GET request to the API."""
    response = requests.get(
        f"{base_url}{endpoint}",
        params=params,
        headers=get_api_headers(api_key, include_accept=include_accept),
        stream=stream,
        timeout=30,
    )
    if not response:
        if log_func:
            log_func("Request failed: no response", "error")
        return None
    return response


def fetch_cached_endpoint(base_url, endpoint, params, api_key, cache, fetch_msg, cached_msg, log_func=None, suppress_logs=False):
    """Generic method to fetch data from an endpoint with caching and error handling."""
    # Check cache first
    cached_data, was_cached = with_cache(cache, endpoint, params)
    if was_cached:
        if not suppress_logs and log_func:
            log_func(cached_msg, "debug")
        return cached_data, True
    
    if not suppress_logs and log_func:
        log_func(fetch_msg, "debug")
    
    response = make_api_request(base_url, endpoint, api_key, params=params, log_func=log_func)
    if not response:
        return None, False
    
    # Handle rate limiting
    if response.status_code == requests.codes.too_many_requests:
        limited_for_header = response.headers.get('x-limited-for')
        limited_for = None
        if limited_for_header:
            try:
                limited_for = int(limited_for_header)
            except (ValueError, TypeError):
                pass
        wait_msg = f"{limited_for} seconds" if limited_for is not None else "time not specified"
        if log_func:
            log_func(f"Rate limited. Wait {wait_msg} before next request.", "warning")
        return {'_rate_limited': True, '_wait_seconds': limited_for}, False
    
    # Parse JSON response
    if response.status_code >= requests.codes.bad_request:
        if log_func:
            log_func(f"HTTP error: {response.status_code}", "error")
        return None, False
    if not response.text:
        return None, False
    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return None, False
    
    # Save to cache
    save_to_cache(cache, endpoint, params, data)
    
    return data, False


def fetch_details_endpoint(base_url, resource_type, resource_id, api_key, cache, log_func=None, suppress_logs=False):
    """Generic method to fetch details for a resource (host/domain)."""
    endpoint = f"/{resource_type}/{resource_id}"
    resource_name = f"{resource_type} details"
    return fetch_cached_endpoint(
        base_url, endpoint, {}, api_key, cache,
        f"Fetching {resource_name} for {resource_id}...",
        f"{resource_name.capitalize()} for {resource_id} (cached)",
        log_func, suppress_logs
    )


def validate_list_response(data, resource_name, log_func=None):
    """Validate that response is a list or rate limit marker."""
    if data is not None and not isinstance(data, list):
        if isinstance(data, dict) and '_rate_limited' in data:
            return data, True  # Rate limit marker, allow it through
        if log_func:
            log_func(f"Unexpected response format for {resource_name}", "warning")
        return None, False
    return data, True
