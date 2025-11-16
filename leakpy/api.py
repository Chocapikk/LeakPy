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

"""API client for LeakIX."""

from . import __version__
from . import helpers


class LeakIXAPI:
    """Client for interacting with the LeakIX API."""
    
    BASE_URL = "https://leakix.net"
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def __init__(self, api_key, verbose=False, logger=None, use_cache=True):
        """
        Initialize the API client.
        
        Args:
            api_key (str): The API key for authentication.
            verbose (bool): Enable verbose logging.
            logger (callable): Optional logger function (message, level).
            use_cache (bool): Enable response caching. Defaults to True.
        """
        self.api_key = api_key
        self.verbose = verbose
        self.log = logger or (lambda msg, level="info": None)
        self.is_api_pro = None
        self.use_cache = use_cache
        if use_cache:
            from .cache import APICache
            self.cache = APICache()
        else:
            self.cache = None
    
    # ========================================================================
    # PUBLIC API METHODS - HOST/DOMAIN
    # ========================================================================
    
    def get_host_details(self, ip, suppress_logs=False):
        """
        Get host details for a specific IP address.
        
        Args:
            ip (str): The IP address to query.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (dict or None, bool) - Host details with 'services' and 'leaks' keys, 
                  and whether it was cached. Returns None on error.
        """
        return helpers.fetch_details_endpoint(self.BASE_URL, "host", ip, self.api_key, self.cache, self.log, suppress_logs)
    
    def get_domain_details(self, domain, suppress_logs=False):
        """
        Get domain details for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (dict or None, bool) - Domain details with 'services' and 'leaks' keys, 
                  and whether it was cached. Returns None on error.
        """
        return helpers.fetch_details_endpoint(self.BASE_URL, "domain", domain, self.api_key, self.cache, self.log, suppress_logs)
    
    def get_subdomains(self, domain, suppress_logs=False):
        """
        Get subdomains for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (list or None, bool) - List of subdomain dictionaries, 
                  and whether it was cached. Returns None on error.
        """
        endpoint = f"/api/subdomains/{domain}"
        data, cached = helpers.fetch_cached_endpoint(
            self.BASE_URL, endpoint, {}, self.api_key, self.cache,
            f"Fetching subdomains for {domain}...",
            f"Subdomains for {domain} (cached)",
            self.log, suppress_logs
        )
        
        validated_data, is_valid = helpers.validate_list_response(data, "subdomains", self.log)
        if not is_valid:
            return None, False
        return validated_data, cached
    
    # ========================================================================
    # PUBLIC API METHODS - SEARCH
    # ========================================================================
    
    def query_search(self, scope, page, query_param, suppress_logs=False):
        """
        Perform a single page search query.
        
        Args:
            scope (str): The scope of the search.
            page (int): Page number to fetch.
            query_param (str): The query string.
            suppress_logs (bool): If True, suppress debug logs.
            
        Returns:
            tuple: (dict or None, bool) - Response data or None on error, and whether it was cached.
        """
        params = {"page": str(page), "q": query_param, "scope": scope}
        
        data, cached = helpers.fetch_cached_endpoint(
            self.BASE_URL, "/search", params, self.api_key, self.cache,
            f"Query {page + 1}",
            f"Query {page + 1} (cached)",
            self.log, suppress_logs
        )
        
        if data is not None and isinstance(data, dict) and data.get("Error") == "Page limit":
            msg = f"Error: Page Limit for free users and non users ({page})"
            self.log(msg, "error")
            return None, False
        
        if data is None and not cached:
            msg = "No more results available (Please check your query or scope)"
            self.log(msg, "warning")
        
        return data, cached
    
    def query_bulk(self, query_param, suppress_logs=False):
        """
        Perform a bulk search query (stream mode).
        
        Args:
            query_param (str): The query string.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (list, bool) - List of events from the bulk response, and whether it was cached.
        """
        params = {"q": query_param}
        endpoint = "/bulk/search"
        
        # Check cache first
        cached_data, was_cached = helpers.with_cache(self.cache, endpoint, params)
        if was_cached:
            if not suppress_logs:
                self.log("Bulk query (cached)", "debug")
            return cached_data, True
        
        # Bulk endpoint uses stream=True and doesn't need Accept header
        response = helpers.make_api_request(self.BASE_URL, endpoint, self.api_key, params=params, stream=True, include_accept=False, log_func=self.log)
        if not response:
            return [], False
        
        data = helpers.process_bulk_lines(response, self.log)
        
        # Save to cache
        helpers.save_to_cache(self.cache, endpoint, params, data)
        
        return data, False
    
    # ========================================================================
    # PUBLIC API METHODS - PLUGINS
    # ========================================================================
    
    def get_plugins(self):
        """
        Retrieve the list of available plugins from LeakIX.

        Returns:
            list[str]: A list of available plugin names.
        """
        data, _ = helpers.fetch_cached_endpoint(
            self.BASE_URL, "/api/plugins", {}, self.api_key, self.cache,
            "Fetching plugins...",
            "Plugins (cached)",
            self.log, suppress_logs=True
        )
        
        if not data:
            return []
        
        if not isinstance(data, list):
            return []
        
        plugins = []
        for p in data:
            if isinstance(p, dict) and p.get("name"):
                plugins.append(p.get("name"))
        return plugins
    
    # ========================================================================
    # PUBLIC API METHODS - UTILS
    # ========================================================================
    
    def check_privilege(self, plugin="WpUserEnumHttp", scope="leak"):
        """
        Check if the API is pro using a specific plugin and scope.
        
        Args:
            plugin (str): Plugin name to test.
            scope (str): Scope to test.
            
        Returns:
            bool: True if API is pro, False otherwise.
        """
        response = helpers.make_api_request(
            self.BASE_URL, "/search", self.api_key,
            params={"page": "1", "q": plugin, "scope": scope},
            log_func=self.log
        )
        return bool(response.text) if response else False
    
    def build_query_with_plugins(self, query_param, plugins):
        """Build query string with plugin filters."""
        if not plugins:
            return query_param
        
        plugins_list = plugins.split(",") if isinstance(plugins, str) else plugins
        plugin_queries = [p.strip() for p in plugins_list if p.strip()]
        if not plugin_queries:
            return query_param
        return f"{query_param} +plugin:({' '.join(plugin_queries)})"
