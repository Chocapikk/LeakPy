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
    
    def _get_cache_ttl_from_response(self, response):
        """
        Extract cache TTL from HTTP response headers.
        
        Args:
            response: requests.Response object.
            
        Returns:
            int: TTL in seconds, or None to use default.
        """
        if not response:
            return None
        
        # Check Cache-Control header
        cache_control = response.headers.get('Cache-Control', '')
        if cache_control:
            # Parse max-age directive
            for directive in cache_control.split(','):
                directive = directive.strip()
                if directive.startswith('max-age='):
                    try:
                        max_age = int(directive.split('=')[1])
                        return max_age
                    except (ValueError, IndexError):
                        pass
        
        # Check Expires header
        expires = response.headers.get('Expires')
        if expires:
            try:
                from email.utils import parsedate_to_datetime
                from datetime import datetime, timezone
                expire_time = parsedate_to_datetime(expires)
                now = datetime.now(timezone.utc)
                if expire_time.tzinfo is None:
                    expire_time = expire_time.replace(tzinfo=timezone.utc)
                delta = (expire_time - now).total_seconds()
                if delta > 0:
                    return int(delta)
            except (ValueError, TypeError):
                pass
        
        return None
    
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
            )
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
            dict or None: Response data or None on error.
        """
        params = {"page": str(page), "q": query_param, "scope": scope}
        
        # Check cache first
        if self.cache:
            cached = self.cache.get("/search", params)
            if cached is not None:
                if not suppress_logs:
                    self.log(f"Query {page + 1} (cached)", "debug")
                return cached
        
        if not suppress_logs:
            self.log(f"Query {page + 1}", "debug")

        response = self._make_request("/search", params=params)
        
        if not response or not response.text:
            return None

        try:
            data = json.loads(response.text)
            
            if isinstance(data, dict) and data.get("Error") == "Page limit":
                msg = f"Error: Page Limit for free users and non users ({page})"
                self.log(msg, "error")
                return None
            
            # Cache the result with TTL based on Cache-Control header if available
            if self.cache:
                ttl = self._get_cache_ttl_from_response(response)
                self.cache.set("/search", params, data, ttl=ttl)
            
            return data
        except json.JSONDecodeError:
            msg = "No more results available (Please check your query or scope)"
            self.log(msg, "warning")
            return None
    
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
    
    def query_bulk(self, query_param, suppress_logs=False):
        """
        Perform a bulk search query (stream mode).
        
        Args:
            query_param (str): The query string.
            suppress_logs (bool): If True, suppress info logs. Defaults to False.
            
        Returns:
            list: List of events from the bulk response.
        """
        if not suppress_logs:
            msg = "Opting for bulk search due to the availability of a Pro API Key."
            self.log(msg, "info")
        
        # Bulk endpoint doesn't need Accept header
        try:
            response = requests.get(
                f"{self.BASE_URL}/bulk/search",
                params={"q": query_param},
                headers=self._get_headers(include_accept=False),
                stream=True,
            )
        except requests.RequestException as e:
            self.log(f"Request error: {e}", "error")
            response = None
        
        if not response:
            return []
        
        return self._process_bulk_lines(response)
    
    def build_query_with_plugins(self, query_param, plugins):
        """Build query string with plugin filters."""
        if not plugins:
            return query_param
        
        plugins_list = plugins.split(",") if isinstance(plugins, str) else plugins
        plugin_queries = [p.strip() for p in plugins_list if p.strip()]
        if not plugin_queries:
            return query_param
        return f"{query_param} +plugin:({' '.join(plugin_queries)})"

