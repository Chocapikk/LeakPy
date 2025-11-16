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

"""Main scraper class for LeakPy."""

import sys
import time

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from . import helpers
from .api import LeakIXAPI
from .config import APIKeyManager
from .logger import setup_logger
from .helpers import ensure_api_initialized, process_and_format_data


# ============================================================================
# HELPER CLASSES
# ============================================================================

class DotNotationObject:
    """
    Generic wrapper class that converts dictionaries to objects with dot notation access.
    
    Example:
        obj = DotNotationObject({"services": [...], "leaks": [...]})
        print(obj.services)  # Access with dot notation
    """
    
    def __init__(self, data):
        """
        Initialize DotNotationObject with a dictionary.
        
        Args:
            data (dict): Dictionary to convert to object with dot notation.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, self._convert_value(value))
        else:
            self._data = data
    
    def _convert_value(self, value):
        """Convert value to DotNotationObject if it's a dict, otherwise return as-is."""
        if isinstance(value, dict):
            return DotNotationObject(value)
        elif isinstance(value, list):
            return [self._convert_value(item) for item in value]
        return value
    
    def __getattr__(self, name):
        """Return None for missing attributes to allow safe chaining."""
        return None
    
    def __repr__(self):
        """String representation for debugging."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        return f"DotNotationObject({attrs})"


# ============================================================================
# MAIN CLASS
# ============================================================================

class LeakIX:
    """Main class for interacting with LeakIX API."""
    
    # Default number of pages for search queries
    DEFAULT_PAGES = 2
    
    def __init__(self, api_key=None, silent=True):
        """
        Initialize a new instance of LeakIX.

        Args:
            api_key (str, optional): The API key for accessing LeakIX services. Defaults to None.
            silent (bool, optional): Flag to suppress all output (no logs, no progress bar). Defaults to True.
        """
        self.silent = silent
        from .helpers.constants import _DEFAULT_LOGGER_NAME
        self.logger = setup_logger(_DEFAULT_LOGGER_NAME, verbose=False)
        self.key_manager = APIKeyManager()

        api_key_read = api_key or (self.key_manager.read() or self.key_manager.migrate_old_location())
        self.api_key = (api_key_read or "").strip()
        if api_key:
            self.key_manager.save(self.api_key)
        # In silent mode, pass a no-op logger to API
        api_logger = (lambda msg, level="info": None) if silent else self.log
        self.api = LeakIXAPI(self.api_key, False, api_logger) if self.api_key else None

    def log(self, message, level="info"):
        """
        Log messages with proper formatting.

        Args:
            message (str): Message to log.
            level (str): Log level (info, debug, warning, error).
        """
        normalized_message = str(message or "")
        log_func = helpers.get_log_function(self.logger, level)
        log_func(normalized_message)

    def has_api_key(self):
        """Check if an API key is available and valid (48 characters)."""
        self.api_key = self.api_key or self.key_manager.read()
        return self.key_manager.is_valid(self.api_key)
    
    
    def _create_console_for_progress(self):
        """Create console for rich progress output."""
        return Console(file=sys.stderr if hasattr(sys, 'stderr') else None)
    
    def _suppress_debug_logging(self):
        """Suppress debug logging and return original level."""
        original_level = self.logger.level
        self.logger.setLevel(20)  # logging.INFO
        return original_level
    
    def _restore_logging_level(self, original_level):
        """Restore original logging level."""
        self.logger.setLevel(original_level)
    
    def _should_use_progress_bulk(self, return_data_only, output_file):
        """Check if progress should be shown in bulk mode."""
        return not return_data_only and not self.silent and not output_file
    
    def _should_use_progress(self, return_data_only):
        """Check if progress should be shown in regular mode."""
        return not return_data_only and not self.silent
    
    def _rate_limit_sleep(self, is_cached):
        """Sleep for rate limit if not cached."""
        if not is_cached:
            from .helpers.constants import _RATE_LIMIT_SLEEP
            time.sleep(_RATE_LIMIT_SLEEP)

    def save_api_key(self, api_key):
        """
        Save the API key securely for later use.

        Args:
            api_key (str): The API key to be saved.
        """
        self.key_manager.save(api_key)
        self.api_key = api_key
        # Reinitialize API client with new key
        self.api = ensure_api_initialized(None, self.api_key, self.log)
    
    def delete_api_key(self):
        """Delete the stored API key from secure storage."""
        self.key_manager.delete()
        self.api_key = ""
        self.api = None

    def get_plugins(self):
        """Retrieve the list of available plugins from LeakIX."""
        return self.api.get_plugins() if self.api else []
    
    def get_cache_stats(self):
        """
        Get cache statistics.
        
        Returns:
            DotNotationObject: Object containing cache statistics with attributes:
                - total_entries (int): Total number of cache entries
                - active_entries (int): Number of active (non-expired) entries
                - expired_entries (int): Number of expired entries
                - ttl_seconds (int): Current TTL in seconds
                - ttl_minutes (int): Current TTL in minutes
                - configured_ttl_minutes (int or None): Configured TTL in minutes
                - cache_file_size (int): Size of cache file in bytes
                - cache_file_path (str): Path to cache file
                - oldest_entry_age (float): Age of oldest entry in seconds
                - newest_entry_age (float): Age of newest entry in seconds
        
        Example:
            >>> client = LeakIX()
            >>> stats = client.get_cache_stats()
            >>> print(f"Cache has {stats.total_entries} entries")
        """
        return DotNotationObject(helpers.get_cache_stats())
    
    def clear_cache(self):
        """
        Clear all cache entries.
        
        Example:
            >>> client = LeakIX()
            >>> client.clear_cache()
        """
        from .cache import APICache
        cache = APICache()
        cache.clear()
    
    def get_cache_ttl(self):
        """
        Get the current cache TTL in minutes.
        
        Returns:
            int or None: TTL in minutes, or None if using default.
        
        Example:
            >>> client = LeakIX()
            >>> ttl = client.get_cache_ttl()
            >>> print(f"Cache TTL: {ttl} minutes")
        """
        from .config import CacheConfig
        cache_config = CacheConfig()
        return cache_config.get_ttl_minutes()
    
    def set_cache_ttl(self, minutes):
        """
        Set the cache TTL (Time To Live) in minutes.
        
        Args:
            minutes (int): TTL in minutes (must be positive).
        
        Raises:
            ValueError: If minutes is not a positive integer.
        
        Example:
            >>> client = LeakIX()
            >>> client.set_cache_ttl(10)  # Set TTL to 10 minutes
        """
        if not isinstance(minutes, int) or minutes <= 0:
            raise ValueError("TTL must be a positive integer (minutes).")
        
        from .config import CacheConfig
        cache_config = CacheConfig()
        cache_config.set_ttl_minutes(minutes)
    
    def analyze_query_stats(self, results, fields=None, top=10, all_fields=False):
        """
        Analyze query results and extract statistics.
        
        Args:
            results (iterable): Iterable of results (list, generator, etc.) containing dicts or L9Event objects to analyze.
            fields (str or list, optional): Fields to analyze. Can be:
                - str: Comma-separated field paths (e.g., "protocol,geoip.country_name")
                - list: List of field paths (strings)
                - None: Uses default fields
            top (int, optional): Maximum number of top values to return per field.
                                Defaults to 10.
            all_fields (bool, optional): If True, analyze all available fields.
                                        Defaults to False.
        
        Returns:
            QueryStats: QueryStats object with dot notation access:
                - total (int): Total number of results
                - fields (QueryStats): QueryStats object mapping field names to their statistics.
                  Each field contains a dict mapping values to their counts.
                  Access with: stats.fields.protocol, stats.fields.port, etc.
        
        Examples:
            Using string field paths::
            
                stats = client.analyze_query_stats(events, fields='protocol,port')
            
            Using list of field paths::
            
                stats = client.analyze_query_stats(events, fields=['protocol', 'geoip.country_name'])
        """
        from .stats import analyze_query_results
        
        # Analyze results
        stats = analyze_query_results(results, fields, all_fields)
        
        # Limit to top N values per field
        if top > 0:
            stats = self._limit_stats_to_top(stats, top)
        
        return stats
    
    def _limit_stats_to_top(self, stats, top):
        """Limit stats to top N values per field."""
        def _limit_nested_dict(fields_dict):
            """Recursively limit nested dict to top N values."""
            result = {}
            for key, value in fields_dict.items():
                if isinstance(value, dict):
                    # Check if this dict contains counts (non-dict values)
                    if helpers.has_counts(value):
                        # This is a leaf dict with counts, limit to top N
                        sorted_items = sorted(value.items(), key=lambda x: x[1], reverse=True)
                        result[key] = dict(sorted_items[:top])
                    else:
                        # This is a nested dict, recurse
                        result[key] = _limit_nested_dict(value)
            return result
        
        stats_dict = stats.to_dict()
        stats_dict['fields'] = _limit_nested_dict(stats_dict['fields'])
        
        from .stats import QueryStats
        return QueryStats(stats_dict)
    
    def _process_services_and_leaks(self, data, fields, output_file):
        """Process services and leaks from data and optionally write to file."""
        services = []
        # Handle both "Services" (API format) and "services" (normalized)
        services_data = data.get("services") or data.get("Services")
        if services_data:
            processed_services = self.process_and_print_data(
                services_data, 
                fields, 
                suppress_debug=self.silent
            )
            services = processed_services
            if output_file:
                for service in processed_services:
                    helpers.write_json_line(output_file, service)
        
        leaks = []
        # Handle both "Leaks" (API format) and "leaks" (normalized)
        leaks_data = data.get("leaks") or data.get("Leaks")
        if leaks_data:
            processed_leaks = self.process_and_print_data(
                leaks_data, 
                fields, 
                suppress_debug=self.silent
            )
            leaks = processed_leaks
            if output_file:
                for leak in processed_leaks:
                    helpers.write_json_line(output_file, leak)
        
        return services, leaks
    
    @helpers.require_api_key
    def get_host(self, ip, fields="full", output=None):
        """
        Get host details for a specific IP address.
        
        Args:
            ip (str): The IP address to query.
            fields (str, optional): Comma-separated list of fields to extract.
                                    Defaults to "full" to get all details.
            output (str or file object, optional): Path to file or file object to write results.
                                                   If None, results are only returned. Defaults to None.
        
        Returns:
            DotNotationObject: Object with 'services' and 'leaks' attributes, each containing a list of L9Event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> host_info = client.get_host("157.90.211.37")
            >>> print(f"Services: {len(host_info.services or [])}")
            >>> print(f"Leaks: {len(host_info.leaks or [])}")
            >>> 
            >>> # Access service details
            >>> if host_info.services:
            ...     for service in host_info.services:
            ...         print(f"{service.protocol}://{service.ip}:{service.port}")
        """
        
        # Get host details from API
        data, is_cached = self.api.get_host_details(ip, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for IP {ip}", "warning")
            return DotNotationObject({"services": None, "leaks": None})
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        
        try:
            services, leaks = self._process_services_and_leaks(data, fields, output_file)
            
            result = DotNotationObject({
                "services": services if services else None,
                "leaks": leaks if leaks else None
            })
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(services)} services, {len(leaks)} leaks", "info")
            
            return result
        finally:
            if output_file and should_close_file:
                output_file.close()
    
    @helpers.require_api_key
    def get_domain(self, domain, fields="full", output=None):
        """
        Get domain details for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            fields (str, optional): Comma-separated list of fields to extract.
                                    Defaults to "full" to get all details.
            output (str or file object, optional): Path to file or file object to write results.
                                                   If None, results are only returned. Defaults to None.
        
        Returns:
            DotNotationObject: Object with 'services' and 'leaks' attributes, each containing a list of L9Event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> domain_info = client.get_domain("leakix.net")
            >>> print(f"Services: {len(domain_info.services or [])}")
            >>> print(f"Leaks: {len(domain_info.leaks or [])}")
            >>> 
            >>> # Access service details
            >>> if domain_info.services:
            ...     for service in domain_info.services:
            ...         print(f"{service.protocol}://{service.host}:{service.port}")
        """
        
        # Get domain details from API
        data, is_cached = self.api.get_domain_details(domain, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for domain {domain}", "warning")
            return DotNotationObject({"services": None, "leaks": None})
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        
        try:
            services, leaks = self._process_services_and_leaks(data, fields, output_file)
            
            result = DotNotationObject({
                "services": services if services else None,
                "leaks": leaks if leaks else None
            })
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(services)} services, {len(leaks)} leaks", "info")
            
            return result
        finally:
            if output_file and should_close_file:
                output_file.close()
    
    def _deduplicate_subdomains(self, subdomains):
        """Deduplicate subdomains by subdomain name (keep first occurrence)."""
        seen = set()
        unique_subdomains = []
        for subdomain in subdomains:
            subdomain_name = subdomain.get('subdomain', '')
            if subdomain_name and subdomain_name not in seen:
                seen.add(subdomain_name)
                unique_subdomains.append(subdomain)
        return unique_subdomains
    
    def _check_rate_limit(self, data):
        """Check if data indicates rate limiting and raise ValueError if so."""
        if data and isinstance(data, dict) and data.get('_rate_limited'):
            wait_seconds = data.get('_wait_seconds', 60)
            raise ValueError(f"Rate limited. Wait {wait_seconds} seconds before retrying.")
    
    @helpers.require_api_key
    def get_subdomains(self, domain, output=None):
        """
        Get subdomains for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            output (str or file object, optional): Path to file or file object to write results.
                                                   If None, results are only returned. Defaults to None.
        
        Returns:
            list: List of DotNotationObject containing subdomain information.
                  Each object has 'subdomain', 'distinct_ips', and 'last_seen' attributes.
                  Returns empty list if no subdomains found or on error.
        
        Example:
            >>> client = LeakIX()
            >>> subdomains = client.get_subdomains("leakix.net")
            >>> print(f"Found {len(subdomains)} subdomains")
            >>> 
            >>> # Access subdomain details with dot notation
            >>> for subdomain in subdomains:
            ...     print(f"{subdomain.subdomain} - {subdomain.distinct_ips} IPs")
        """
        
        # Get subdomains from API
        data, is_cached = self.api.get_subdomains(domain, suppress_logs=self.silent)
        
        self._check_rate_limit(data)
        
        if not data:
            if not self.silent:
                self.log(f"No subdomains found for domain {domain}", "warning")
            return []
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        
        try:
            if output_file:
                for subdomain in data:
                    helpers.write_json_line(output_file, subdomain)
            
            # Convert list of dicts to list of DotNotationObject
            result = [DotNotationObject(subdomain) for subdomain in data]
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(result)} subdomains", "info")
            
            return result
        finally:
            if output_file and should_close_file:
                output_file.close()

    def process_and_print_data(self, data, fields, suppress_debug=False):
        """
        Process the provided data, extract desired fields, and print the results.

        Args:
            data (list or dict): Either a list of dictionaries or a single dictionary.
            fields (str or None): Comma-separated list of fields to extract.
            suppress_debug (bool): If True, suppress debug logs during processing.

        Returns:
            list: A list of dictionaries containing the extracted fields from the data.
        """
        # Temporarily disable debug logging if suppress_debug is True
        if suppress_debug:
            return process_and_format_data(data, fields, None)  # Pass None to disable logging
        return process_and_format_data(data, fields, self.log)
    
    def _process_data_generator(self, data, fields, suppress_debug=False):
        """
        Generator that processes data and yields events one by one as they are extracted.
        
        This allows for streaming processing where events are yielded immediately
        without waiting for the entire page to be processed.
        
        Args:
            data (list or dict): Either a list of dictionaries or a single dictionary.
            fields (str or None): Comma-separated list of fields to extract.
            suppress_debug (bool): If True, suppress debug logs during processing.
        
        Yields:
            L9Event or dict: Processed events one by one.
        """
        from .helpers.l9event import (
            get_events_from_data, extract_from_single_entry, convert_to_l9event,
            is_l9event_instance, to_dict_if_l9event
        )
        from .helpers.constants import _DEFAULT_FIELDS_LIST, _PARSER_FULL_FIELD_REQUEST
        from .helpers.field_utils import log_result_items
        
        if fields is None:
            fields_list = _DEFAULT_FIELDS_LIST
        else:
            fields_list = [f.strip() for f in fields.split(",")]
        
        events = get_events_from_data(data)
        logger = None if suppress_debug else self.log
        is_full = _PARSER_FULL_FIELD_REQUEST in fields_list
        
        for entry in events:
            event = convert_to_l9event(entry) if is_full else extract_from_single_entry(entry, fields_list)
            
            if logger:
                log_result_items([event], logger, is_l9event_instance, to_dict_if_l9event)
            
            yield event
    
    def _process_bulk_stream(self, query_param, fields, output_file=None):
        """
        Generator that processes bulk stream and yields events one by one as they arrive.
        
        Args:
            query_param (str): The query string.
            fields (str or None): Comma-separated list of fields to extract.
            output_file (file object, optional): File handle to write results in real-time.
        
        Yields:
            L9Event: Events as they are processed from the bulk stream.
        """
        import json
        from .helpers.l9event import (
            extract_from_single_entry, convert_to_l9event,
            is_l9event_instance, to_dict_if_l9event
        )
        from .helpers.constants import _DEFAULT_FIELDS_LIST, _PARSER_FULL_FIELD_REQUEST
        from .helpers.field_utils import log_result_items
        
        # Check cache first
        params = {"q": query_param}
        endpoint = "/bulk/search"
        cached_data, was_cached = helpers.with_cache(self.api.cache, endpoint, params)
        
        if was_cached:
            # Process cached data as a generator
            if cached_data:
                for event in self._process_data_generator(cached_data, fields, suppress_debug=self.silent):
                    if output_file:
                        helpers.write_result_item(output_file, event, fields)
                    yield event
            return
        
        # Make streaming request
        # Use None for log_func if silent to suppress logs
        log_func = None if self.silent else self.log
        response = helpers.make_api_request(
            self.api.BASE_URL, endpoint, self.api.api_key,
            params=params, stream=True, include_accept=False, log_func=log_func
        )
        
        if not response:
            return
        
        # Parse fields
        if fields is None:
            fields_list = _DEFAULT_FIELDS_LIST
        else:
            fields_list = [f.strip() for f in fields.split(",")]
        
        # Don't log in silent mode
        logger = None if self.silent else self.log
        is_full = _PARSER_FULL_FIELD_REQUEST in fields_list
        all_events = []  # For caching later
        
        try:
            # Stream and process events line by line
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                text = line.strip()
                if not text or not (text.startswith('{') or text.startswith('[')):
                    continue
                
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and "events" in parsed:
                        events_list = parsed.get("events", [])
                        if events_list:
                            all_events.extend(events_list)
                            
                            # Process and yield each event immediately
                            for entry in events_list:
                                event = convert_to_l9event(entry) if is_full else extract_from_single_entry(entry, fields_list)
                                
                                if logger:
                                    log_result_items([event], logger, is_l9event_instance, to_dict_if_l9event)
                                
                                if output_file:
                                    helpers.write_result_item(output_file, event, fields)
                                
                                yield event
                except (json.JSONDecodeError, TypeError):
                    continue
        except GeneratorExit:
            # Generator was closed (e.g., break in loop) - close connection immediately
            response.close()
            raise
        finally:
            # Always close response when generator finishes
            response.close()
        
        # Save to cache for future use
        if all_events:
            helpers.save_to_cache(self.api.cache, endpoint, params, all_events)
        elif not self.silent:
            self.log("No results returned from bulk query.", "warning")

    def get_all_fields(self, data=None, current_path=None):
        """
        Get all available field paths.
        
        If no data is provided, returns all fields from the l9format schema
        (no API call needed). If data is provided, extracts fields from that data.

        Args:
            data (dict, optional): The nested dictionary to extract field paths from.
                                  If None, returns all fields from l9format schema.
            current_path (list, optional): Current path being traversed. Defaults to None.

        Returns:
            list[str]: A list of field paths sorted alphabetically.
            
        Examples:
            >>> # Get all fields from schema (no API call needed)
            >>> fields = client.get_all_fields()
            >>> for field in sorted(fields):
            ...     print(field)
            
            >>> # Get fields from a specific event
            >>> events = list(client.search(scope="leak", query='+country:"France"', pages=1))
            >>> if events:
            ...     fields = client.get_all_fields(events[0])
            ...     for field in sorted(fields):
            ...         print(field)
        """
        if data is None:
            # Return fields from l9format schema (no API call needed)
            return helpers.get_all_fields_from_l9format_schema()
        # Extract fields from provided data
        # Convert L9Event to dict if needed
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        return helpers.get_all_fields_from_dict(data, current_path)

    @helpers.require_api_key
    def search(
        self,
        scope="leak",
        query="",
        pages=None,
        plugin="",
        fields="full",
        use_bulk=False,
        output=None,
    ):
        """
        Search LeakIX for data based on provided parameters.
        
        This is the main function for querying LeakIX. It returns a generator that streams
        events in real-time using HTTP streaming. Events are yielded as soon as they are
        received from the API, allowing you to process results immediately without waiting
        for all pages to be fetched.
        
        **Streaming Behavior:**
        
        - **Pagination mode** (default): Events are streamed page by page. Each page is fetched,
          processed, and events are yielded immediately. You don't wait for all pages
          before processing the first events. The `pages` parameter controls how many pages to fetch.
        - **Bulk mode** (`use_bulk=True`): Events are streamed line by line from the HTTP response using
          true HTTP streaming. Events are parsed and yielded as they arrive from the server.
          **Note:** In bulk mode, the `pages` parameter is ignored as all results are retrieved automatically.
        
        **Connection Management:**
        
        When you stop consuming the generator early (e.g., using `break`), the HTTP connection is
        automatically closed when the generator is garbage collected (which happens automatically in Python).
        This prevents unnecessary bandwidth and API quota consumption. For immediate closure, you can
        explicitly call `generator.close()` after stopping the loop.
        
        Optionally writes them to a file if `output` is specified.

        Args:
            scope (str, optional): The scope of the search. Defaults to "leak".
            query (str, optional): Search query string. Defaults to an empty string.
            pages (int, optional): Number of pages to scrape. Defaults to 2 (or LeakIX.DEFAULT_PAGES).
                                  **Note:** This parameter is ignored when `use_bulk=True` (bulk mode retrieves all results automatically).
            plugin (str, optional): Comma-separated plugin names. Defaults to an empty string.
            fields (str, optional): Comma-separated list of fields to extract from results. Defaults to "full" (all fields).
            use_bulk (bool, optional): Whether to use the bulk functionality (requires Pro API). 
                                      When True, retrieves all results automatically and ignores the `pages` parameter. Defaults to False.
            output (str or file object, optional): Path to file or file object (e.g., sys.stdout) to write results. 
                                                   If None, results are only returned. Defaults to None.

        Returns:
            generator: A generator that yields L9Event objects in real-time via HTTP streaming.
                      Events are yielded as soon as they are received and processed.
                      If you need a list, use: list(client.search(...))
        
        Examples:
            >>> # Stream events page by page (events processed as they arrive)
            >>> events = client.search(scope="leak", query='+country:"France"', pages=5)
            >>> for event in events:
            ...     print(event.ip)  # Events are streamed in real-time, no waiting for all pages
            
            >>> # Stream events with bulk mode (HTTP streaming, line by line)
            >>> events = client.search(scope="leak", query='plugin:TraccarPlugin', use_bulk=True)
            >>> for event in events:
            ...     print(event.ip)  # Events streamed directly from HTTP response
            
            >>> # Get all events as a list (if needed)
            >>> events = list(client.search(scope="leak", query='+country:"France"', pages=2))
            
            >>> # Write to file while streaming (events still yielded)
            >>> events = client.search(scope="leak", query='+country:"France"', pages=2, output="results.txt")
            >>> for event in events:
            ...     print(event.ip)  # Events streamed and written to file simultaneously
            
            >>> # Stream to stdout (for piping) - need to consume generator
            >>> list(client.search(scope="leak", query='+country:"France"', pages=2, output=sys.stdout))
        """
        plugins_list = self.get_plugins()
        given_plugins = [item.strip() for item in plugin.split(",") if item.strip()]
        invalid_plugins = [p for p in given_plugins if p not in set(plugins_list)]
        
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins_list}")
        
        # Use default pages if not specified
        if pages is None:
            pages = self.DEFAULT_PAGES
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        if output_file and not self.silent:
            self.log(f"Writing results in real-time to {output if isinstance(output, str) else 'stdout'}...", "info")
        
        try:
            fields_str = helpers.normalize_fields(fields)
            # Use the new generator-based query method
            yield from self._query_generator(scope, pages, query, given_plugins, fields_str, use_bulk, output_file=output_file)
        finally:
            if output_file and should_close_file:
                output_file.close()

    def _query_generator(
        self,
        scope,
        pages=None,
        query_param="",
        plugins=None,
        fields=None,
        use_bulk=False,
        output_file=None,
    ):
        """
        Generator-based query that yields events page by page.
        
        This method yields events as soon as each page is processed,
        allowing for streaming processing of results.
        
        Args:
            scope (str): The scope of the search.
            pages (int, optional): Number of pages to scrape. Defaults to LeakIX.DEFAULT_PAGES (2).
                                  **Note:** Ignored when `use_bulk=True` (bulk mode retrieves all results).
            query_param (str, optional): The query string to be used. Defaults to an empty string.
            plugins (list or str, optional): List or comma-separated string of plugin names. Defaults to None.
            fields (list of str or None, optional): List of fields to extract from the results.
            use_bulk (bool, optional): Whether to use bulk mode. When True, retrieves all results
                                      automatically and ignores `pages`. Defaults to False.
            output_file (file object, optional): File handle to write results in real-time. Defaults to None.
        
        Yields:
            L9Event: Events as they are processed from each page (or from bulk stream if use_bulk=True).
        """
        # Use default pages if not specified
        if pages is None:
            pages = self.DEFAULT_PAGES
        
        if self.api.is_api_pro is None:
            self.api.is_api_pro = self.api.check_privilege("WpUserEnumHttp", "leak")

        # Build query with plugins
        query_param = self.api.build_query_with_plugins(query_param, plugins)
        
        # Use bulk mode if available and requested
        if self.api.is_api_pro and use_bulk:
            # Warn if pages is specified (bulk mode retrieves all results, pages is ignored)
            # Only warn if pages is explicitly set to a non-default value
            if pages != self.DEFAULT_PAGES:
                if not self.silent:
                    self.log(f"Warning: 'pages' parameter ({pages}) is ignored in bulk mode. Bulk mode retrieves all results automatically.", "warning")
            for event in self._process_bulk_stream(query_param, fields, output_file):
                yield event
            return

        # Regular paginated search - yield events as they are processed
        for page in range(pages):
            data, is_cached = self.api.query_search(scope, page, query_param, suppress_logs=self.silent)
            if not data:
                if not self.silent:
                    self.log(f"No more data available at page {page + 1}", "warning")
                break
            
            for event in self._process_data_generator(data, fields, suppress_debug=self.silent):
                if output_file:
                    helpers.write_result_item(output_file, event, fields)
                yield event
            
            self._rate_limit_sleep(is_cached)
