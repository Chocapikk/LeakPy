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

import json
import requests
from itertools import chain

from . import __version__


class LeakIXAPI:
    """Client for interacting with the LeakIX API."""
    
    BASE_URL = "https://leakix.net"
    
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
    
    def _get_headers(self, include_accept=True):
        """Get standard headers for API requests."""
        headers = {
            "api-key": self.api_key,
            "User-Agent": f"LeakPy/{__version__}"
        }
        if include_accept:
            headers["Accept"] = "application/json"
        return headers
    
    def _make_request(self, endpoint, params=None, stream=False):
        """
        Make a GET request to the API.
        
        Args:
            endpoint (str): API endpoint (without base URL).
            params (dict, optional): Query parameters.
            stream (bool): Whether to stream the response.
            
        Returns:
            requests.Response: Response object or None on error.
        """
        try:
            return requests.get(
                f"{self.BASE_URL}{endpoint}",
                params=params,
                headers=self._get_headers(),
                stream=stream,
                timeout=30,  # 30 seconds timeout
            )
        except requests.Timeout as e:
            self.log(f"Request timeout: {e}", "error")
            return None
        except requests.RequestException as e:
            self.log(f"Request error: {e}", "error")
            return None
    
    def check_privilege(self, plugin="WpUserEnumHttp", scope="leak"):
        """
        Check if the API is pro using a specific plugin and scope.
        
        Args:
            plugin (str): Plugin name to test.
            scope (str): Scope to test.
            
        Returns:
            bool: True if API is pro, False otherwise.
        """
        response = self._make_request(
            "/search",
            params={"page": "1", "q": plugin, "scope": scope}
        )
        return bool(response.text) if response else False
    
    def get_plugins(self):
        """
        Retrieve the list of available plugins from LeakIX.

        Returns:
            list[str]: A list of available plugin names.
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get("/api/plugins")
            if cached is not None:
                return cached
        
        response = self._make_request("/api/plugins")
        if not response:
            return []
        
        try:
            response.raise_for_status()
            plugins = [p.get("name") for p in json.loads(response.text) if p.get("name")]
            # Cache the result
            if self.cache:
                self.cache.set("/api/plugins", data=plugins)
            return plugins
        except (requests.RequestException, json.JSONDecodeError):
            return []
    
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
        
        # Check cache first
        if self.cache:
            cached = self.cache.get("/search", params)
            if cached is not None:
                if not suppress_logs:
                    self.log(f"Query {page + 1} (cached)", "debug")
                return cached, True
        
        if not suppress_logs:
            self.log(f"Query {page + 1}", "debug")

        response = self._make_request("/search", params=params)
        
        if not response or not response.text:
            return None, False

        try:
            data = json.loads(response.text)
            
            if isinstance(data, dict) and data.get("Error") == "Page limit":
                msg = f"Error: Page Limit for free users and non users ({page})"
                self.log(msg, "error")
                return None, False
            
            # Cache the result (uses default TTL since LeakIX doesn't send cache headers)
            if self.cache:
                self.cache.set("/search", params, data)
            
            return data, False
        except json.JSONDecodeError:
            msg = "No more results available (Please check your query or scope)"
            self.log(msg, "warning")
            return None, False
    
    def _process_bulk_lines(self, response):
        """
        Process lines from bulk response stream.
        
        Args:
            response: Response object with stream=True.
            
        Returns:
            list: List of events extracted from bulk response.
        """
        try:
            lines = []
            for line in response.iter_lines(decode_unicode=True):
                if line and line.strip():
                    lines.append(line.strip())
            
            loaded_data = []
            for line in lines:
                try:
                    loaded_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            
            events = []
            for item in loaded_data:
                if isinstance(item, dict) and "events" in item:
                    events.append(item.get("events", []))
            
            data = list(chain.from_iterable(events))
            
            if not data:
                self.log("No results returned from bulk query.", "warning")
                return []
            
            return data
        except json.JSONDecodeError:
            self.log("Error processing bulk query response.", "error")
            return []
        except Exception as e:
            self.log(f"Error during bulk query: {e}", "error")
            return []
    
    def get_host_details(self, ip, suppress_logs=False):
        """
        Get host details for a specific IP address.
        
        Args:
            ip (str): The IP address to query.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (dict or None, bool) - Host details with 'Services' and 'Leaks' keys, 
                  and whether it was cached. Returns None on error.
        """
        endpoint = f"/host/{ip}"
        params = {}
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(endpoint, params)
            if cached is not None:
                if not suppress_logs:
                    self.log(f"Host details for {ip} (cached)", "debug")
                return cached, True
        
        if not suppress_logs:
            self.log(f"Fetching host details for {ip}...", "info")
        
        response = self._make_request(endpoint, params=params)
        
        if not response:
            return None, False
        
        try:
            # Check for rate limiting first
            if response.status_code == 429:
                limited_for = response.headers.get('x-limited-for', '60')
                try:
                    limited_for = int(limited_for)
                except (ValueError, TypeError):
                    limited_for = 60  # Default to 60 seconds
                self.log(f"Rate limited. Wait {limited_for} before next request.", "warning")
                # Return a special marker to indicate rate limit
                return {'_rate_limited': True, '_wait_seconds': limited_for}, False
            
            response.raise_for_status()
            data = json.loads(response.text)
            
            # Cache the result
            if self.cache:
                self.cache.set(endpoint, params, data)
            
            return data, False
        except requests.HTTPError as e:
            self.log(f"HTTP error: {e}", "error")
            return None, False
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.log(f"Error fetching host details: {e}", "error")
            return None, False
    
    def get_domain_details(self, domain, suppress_logs=False):
        """
        Get domain details for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            tuple: (dict or None, bool) - Domain details with 'Services' and 'Leaks' keys, 
                  and whether it was cached. Returns None on error.
        """
        endpoint = f"/domain/{domain}"
        params = {}
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(endpoint, params)
            if cached is not None:
                if not suppress_logs:
                    self.log(f"Domain details for {domain} (cached)", "debug")
                return cached, True
        
        if not suppress_logs:
            self.log(f"Fetching domain details for {domain}...", "info")
        
        response = self._make_request(endpoint, params=params)
        
        if not response:
            return None, False
        
        try:
            # Check for rate limiting first
            if response.status_code == 429:
                limited_for = response.headers.get('x-limited-for', '60')
                try:
                    limited_for = int(limited_for)
                except (ValueError, TypeError):
                    limited_for = 60  # Default to 60 seconds
                self.log(f"Rate limited. Wait {limited_for} before next request.", "warning")
                # Return a special marker to indicate rate limit
                return {'_rate_limited': True, '_wait_seconds': limited_for}, False
            
            response.raise_for_status()
            data = json.loads(response.text)
            
            # Cache the result
            if self.cache:
                self.cache.set(endpoint, params, data)
            
            return data, False
        except requests.HTTPError as e:
            self.log(f"HTTP error: {e}", "error")
            return None, False
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.log(f"Error fetching domain details: {e}", "error")
            return None, False
    
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
        params = {}
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(endpoint, params)
            if cached is not None:
                if not suppress_logs:
                    self.log(f"Subdomains for {domain} (cached)", "debug")
                return cached, True
        
        if not suppress_logs:
            self.log(f"Fetching subdomains for {domain}...", "info")
        
        response = self._make_request(endpoint, params=params)
        
        if not response:
            return None, False
        
        try:
            # Check for rate limiting first
            if response.status_code == 429:
                limited_for = response.headers.get('x-limited-for', '60')
                try:
                    limited_for = int(limited_for)
                except (ValueError, TypeError):
                    limited_for = 60  # Default to 60 seconds
                self.log(f"Rate limited. Wait {limited_for} before next request.", "warning")
                # Return a special marker to indicate rate limit
                return {'_rate_limited': True, '_wait_seconds': limited_for}, False
            
            response.raise_for_status()
            data = json.loads(response.text)
            
            # Ensure data is a list
            if not isinstance(data, list):
                self.log(f"Unexpected response format for subdomains", "warning")
                return None, False
            
            # Cache the result
            if self.cache:
                self.cache.set(endpoint, params, data)
            
            return data, False
        except requests.HTTPError as e:
            self.log(f"HTTP error: {e}", "error")
            return None, False
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.log(f"Error fetching subdomains: {e}", "error")
            return None, False
    
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
        
        # Check cache first
        if self.cache:
            cached = self.cache.get("/bulk/search", params)
            if cached is not None:
                if not suppress_logs:
                    self.log("Bulk query (cached)", "debug")
                return cached, True
        
        if not suppress_logs:
            msg = "Opting for bulk search due to the availability of a Pro API Key."
            self.log(msg, "info")
        
        # Bulk endpoint doesn't need Accept header
        try:
            response = requests.get(
                f"{self.BASE_URL}/bulk/search",
                params=params,
                headers=self._get_headers(include_accept=False),
                stream=True,
            )
        except requests.RequestException as e:
            self.log(f"Request error: {e}", "error")
            response = None
        
        if not response:
            return [], False
        
        data = self._process_bulk_lines(response)
        
        # Cache the result (even if empty, as it's a valid response)
        if self.cache:
            self.cache.set("/bulk/search", params, data)
        
        return data, False
    
    def build_query_with_plugins(self, query_param, plugins):
        """Build query string with plugin filters."""
        if not plugins:
            return query_param
        
        plugins_list = plugins.split(",") if isinstance(plugins, str) else plugins
        plugin_queries = [p.strip() for p in plugins_list if p.strip()]
        if not plugin_queries:
            return query_param
        return f"{query_param} +plugin:({' '.join(plugin_queries)})"

