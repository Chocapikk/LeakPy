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
        obj = DotNotationObject({"Services": [...], "Leaks": [...]})
        print(obj.Services)  # Access with dot notation
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
            results (list): List of results (dicts or L9Event objects) to analyze.
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
            
                stats = client.analyze_query_stats(results, fields='protocol,port')
            
            Using list of field paths::
            
                stats = client.analyze_query_stats(results, fields=['protocol', 'geoip.country_name'])
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
        """Process Services and Leaks from data and optionally write to file."""
        services = []
        if data.get("Services"):
            processed_services = self.process_and_print_data(
                data["Services"], 
                fields, 
                suppress_debug=self.silent
            )
            services = processed_services
            if output_file:
                for service in processed_services:
                    helpers.write_json_line(output_file, service)
        
        leaks = []
        if data.get("Leaks"):
            processed_leaks = self.process_and_print_data(
                data["Leaks"], 
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
            DotNotationObject: Object with 'Services' and 'Leaks' attributes, each containing a list of L9Event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> host_info = client.get_host("157.90.211.37")
            >>> print(f"Services: {len(host_info.Services or [])}")
            >>> print(f"Leaks: {len(host_info.Leaks or [])}")
            >>> 
            >>> # Access service details
            >>> if host_info.Services:
            ...     for service in host_info.Services:
            ...         print(f"{service.protocol}://{service.ip}:{service.port}")
        """
        
        # Get host details from API
        data, is_cached = self.api.get_host_details(ip, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for IP {ip}", "warning")
            return DotNotationObject({"Services": None, "Leaks": None})
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        
        try:
            services, leaks = self._process_services_and_leaks(data, fields, output_file)
            
            result = DotNotationObject({
                "Services": services if services else None,
                "Leaks": leaks if leaks else None
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
            DotNotationObject: Object with 'Services' and 'Leaks' attributes, each containing a list of L9Event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> domain_info = client.get_domain("leakix.net")
            >>> print(f"Services: {len(domain_info.Services or [])}")
            >>> print(f"Leaks: {len(domain_info.Leaks or [])}")
            >>> 
            >>> # Access service details
            >>> if domain_info.Services:
            ...     for service in domain_info.Services:
            ...         print(f"{service.protocol}://{service.host}:{service.port}")
        """
        
        # Get domain details from API
        data, is_cached = self.api.get_domain_details(domain, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for domain {domain}", "warning")
            return DotNotationObject({"Services": None, "Leaks": None})
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        
        try:
            services, leaks = self._process_services_and_leaks(data, fields, output_file)
            
            result = DotNotationObject({
                "Services": services if services else None,
                "Leaks": leaks if leaks else None
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

    def get_all_fields(self, data, current_path=None):
        """
        Recursively retrieve all field paths from a nested dictionary.

        Args:
            data (dict): The nested dictionary to extract field paths from.
            current_path (list, optional): Current path being traversed. Defaults to None.

        Returns:
            list[str]: A list of field paths sorted alphabetically.
        """
        return helpers.get_all_fields_from_dict(data, current_path)

    @helpers.require_api_key
    def search(
        self,
        scope="leak",
        query="",
        pages=2,
        plugin="",
        fields="protocol,ip,port",
        use_bulk=False,
        output=None,
    ):
        """
        Search LeakIX for data based on provided parameters.
        
        This is the main function for querying LeakIX. It always returns results,
        and optionally writes them to a file if `output` is specified.

        Args:
            scope (str, optional): The scope of the search. Defaults to "leak".
            query (str, optional): Search query string. Defaults to an empty string.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            plugin (str, optional): Comma-separated plugin names. Defaults to an empty string.
            fields (str, optional): Comma-separated list of fields to extract from results. Defaults to "protocol,ip,port".
            use_bulk (bool, optional): Whether to use the bulk functionality. Defaults to False.
            output (str or file object, optional): Path to file or file object (e.g., sys.stdout) to write results. 
                                                   If None, results are only returned. Defaults to None.

        Returns:
            list: A list of scraped results (L9Event objects) based on the provided criteria.
                  Results are always returned, even if `output` is specified.
        
        Examples:
            >>> # Get results only
            >>> results = client.search(scope="leak", query='+country:"France"', pages=2)
            >>> for leak in results:
            ...     print(leak.ip)
            
            >>> # Write to file (results are still returned)
            >>> results = client.search(scope="leak", query='+country:"France"', pages=2, output="results.txt")
            
            >>> # Write to stdout (for piping)
            >>> client.search(scope="leak", query='+country:"France"', pages=2, output=sys.stdout)
        """
        plugins_list = self.get_plugins()
        given_plugins = [item.strip() for item in plugin.split(",") if item.strip()]
        invalid_plugins = [p for p in given_plugins if p not in set(plugins_list)]
        
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins_list}")
        
        output_file, should_close_file = helpers.get_output_file(output, self.silent, self.log)
        if output_file and not self.silent:
            self.log(f"Writing results in real-time to {output if isinstance(output, str) else 'stdout'}...", "info")
        
        try:
            fields_str = helpers.normalize_fields(fields)
            results = self.query(scope, pages, query, given_plugins, fields_str, use_bulk, output_file=output_file)
            return results
        finally:
            if output_file and should_close_file:
                output_file.close()

    def query(
        self,
        scope,
        pages=2,
        query_param="",
        plugins=None,
        fields=None,
        use_bulk=False,
        return_data_only=False,
        output_file=None,
    ):
        """
        Perform a query on the LeakIX website based on provided criteria.

        Args:
            scope (str): The scope of the search.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            query_param (str, optional): The query string to be used. Defaults to an empty string.
            plugins (list or str, optional): List or comma-separated string of plugin names. Defaults to None.
            fields (list of str or None, optional): List of fields to extract from the results.
            return_data_only (bool, optional): Return raw data only without processing. Defaults to False.
            use_bulk (bool, optional): Whether to use bulk mode. Defaults to False.
            output_file (file object, optional): File handle to write results in real-time. Defaults to None.

        Returns:
            list: List of processed strings or raw data based on `return_data_only` flag.
        """
        if self.api.is_api_pro is None:
            self.api.is_api_pro = self.api.check_privilege("WpUserEnumHttp", "leak")

        # Build query with plugins
        query_param = self.api.build_query_with_plugins(query_param, plugins)
        
        start_time = time.time()
        
        def log_execution_time():
            """Log execution time if not in silent mode."""
            if not self.silent:
                elapsed_time = time.time() - start_time
                self.log(f"Execution time: {elapsed_time:.2f} seconds", "info")

        # Use bulk mode if available and requested
        if self.api.is_api_pro and use_bulk:
            # If writing to file, suppress all output except completion message
            if output_file:
                original_silent = self.silent
                self.silent = True
                self.api.verbose = False
            
            # Show spinner in bulk mode if not silent and not writing to file
            use_progress = self._should_use_progress_bulk(return_data_only, output_file)
            
            try:
                if use_progress:
                    console = self._create_console_for_progress()
                    original_level = self._suppress_debug_logging()
                    
                    try:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            transient=False,
                            console=console,
                        ) as progress:
                            task = progress.add_task("[cyan]Downloading and processing...", total=None)
                            
                            # Call API without progress (API doesn't handle UI)
                            data, is_cached = self.api.query_bulk(query_param, suppress_logs=True)
                            
                            if data:
                                progress.update(task, description="[cyan]Processing results...")
                            
                            if return_data_only:
                                log_execution_time()
                                return data
                            
                            # Suppress debug logs during processing
                            results = self.process_and_print_data(data, fields, suppress_debug=True) if data else []
                            
                            # Write results to file if needed
                            if results and output_file:
                                for result in results:
                                    helpers.write_result_item(output_file, result, fields)
                            
                            if results:
                                progress.update(task, description=f"[green]✓ Found {len(results)} results")
                            
                            log_execution_time()
                    finally:
                        self._restore_logging_level(original_level)
                else:
                    data, is_cached = self.api.query_bulk(query_param, suppress_logs=bool(output_file))
                    if return_data_only:
                        log_execution_time()
                        return data
                    # Suppress debug logs when writing to file
                    results = self.process_and_print_data(data, fields, suppress_debug=bool(output_file)) if data else []
                    # Write results to file if needed
                    if results and output_file:
                        for result in results:
                            helpers.write_result_item(output_file, result, fields)
                
                # Restore silent state before showing completion message
                if output_file:
                    self.silent = original_silent
                
                # Show completion message even when writing to file (but only if not silent)
                if not self.silent and output_file and results:
                    self.log(f"✓ Completed - {len(results)} results", "info")
                
                log_execution_time()
                return results
            finally:
                # Restore original silent state
                if output_file:
                    self.silent = original_silent
                    self.api.verbose = False

        # Regular paginated search
        results = []
        last_data = None
        
        # Show progress bar if not silent
        use_progress = self._should_use_progress(return_data_only)
        
        if use_progress:
            # Create a console for rich output that won't conflict with logging
            console = self._create_console_for_progress()
            
            # Temporarily disable debug logging to avoid conflicts with progress bar
            original_level = self._suppress_debug_logging()
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    transient=False,
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"[cyan]Fetching pages (0/{pages})...", 
                        total=pages
                    )
                    
                    for page in range(pages):
                        data, is_cached = self.api.query_search(scope, page, query_param, suppress_logs=True)
                        if not data:
                            break
                        last_data = data
                        # Suppress debug logs during processing
                        page_results = self.process_and_print_data(data, fields, suppress_debug=True)
                        
                        # Process page results and write to file if needed
                        results.extend(page_results)
                        if output_file:
                            for result in page_results:
                                helpers.write_result_item(output_file, result, fields)
                        
                        # Update progress bar
                        progress.update(
                            task, 
                            advance=1,
                            description=f"[cyan]Fetching pages ({page + 1}/{pages}) - {len(results)} results..."
                        )
                        
                        # Only respect rate limit if we made an actual API request
                        self._rate_limit_sleep(is_cached)
                    
                    # Final update
                    progress.update(
                        task,
                        description=f"[green]✓ Completed - {len(results)} results"
                    )
            finally:
                # Restore original logging level
                self._restore_logging_level(original_level)
        else:
            # No progress bar, use simple logging
            for page in range(pages):
                data, is_cached = self.api.query_search(scope, page, query_param)
                if not data:
                    break
                last_data = data
                page_results = self.process_and_print_data(data, fields)
                
                # Process page results and write to file if needed
                results.extend(page_results)
                if output_file:
                    for result in page_results:
                        helpers.write_result_item(output_file, result, fields)
                
                # Only respect rate limit if we made an actual API request
                self._rate_limit_sleep(is_cached)

        log_execution_time()
        return last_data if return_data_only else results
