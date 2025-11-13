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

import json
import time
import logging
import sys

from .config import APIKeyManager
from .api import LeakIXAPI
from .parser import get_all_fields, process_and_format_data
from .logger import setup_logger

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console


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
        self.logger = setup_logger("LeakPy", verbose=False)
        self.key_manager = APIKeyManager()

        if api_key:
            api_key_read = api_key
        else:
            api_key_read = self.key_manager.read() or self.key_manager.migrate_old_location()
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
        if message is None:
            message = ""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(str(message))

    def has_api_key(self):
        """Check if an API key is available and valid (48 characters)."""
        self.api_key = self.api_key or self.key_manager.read()
        return self.key_manager.is_valid(self.api_key)

    def save_api_key(self, api_key):
        """
        Save the API key securely for later use.

        Args:
            api_key (str): The API key to be saved.
        """
        self.key_manager.save(api_key)
        self.api_key = api_key
        # Reinitialize API client with new key
        self.api = LeakIXAPI(self.api_key, False, self.log)
    
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
            dict: Dictionary containing cache statistics with keys:
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
            >>> print(f"Cache has {stats['total_entries']} entries")
        """
        from .cache import APICache
        from .config import CacheConfig
        import time
        
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
        
        # Calculate file size
        if cache.cache_file.exists():
            stats['cache_file_size'] = cache.cache_file.stat().st_size
        
        # Analyze entries
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
            results (list): List of results (dicts or l9event objects) to analyze.
            fields (str, list, dict, or callable, optional): Fields to analyze. Can be:
                - str: Comma-separated field paths (e.g., "protocol,geoip.country_name")
                - list: List of field paths (strings) or callables
                - dict: Mapping of field names to callables (object-oriented approach)
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
            # Using string field paths (backward compatible)
            >>> stats = client.analyze_query_stats(results, fields='protocol,port')
            
            # Using object-oriented approach with callables
            >>> stats = client.analyze_query_stats(results, fields={
            ...     'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
            ...     'protocol': lambda leak: leak.protocol,
            ...     'port': lambda leak: leak.port
            ... })
            
            # Using list of callables
            >>> stats = client.analyze_query_stats(results, fields=[
            ...     lambda leak: leak.protocol,
            ...     lambda leak: leak.geoip.country_name if leak.geoip else None
            ... ])
        """
        from .stats import analyze_query_results
        
        # Analyze results
        stats = analyze_query_results(results, fields, all_fields)
        
        # Limit to top N values per field
        if top > 0:
            # Convert to dict for manipulation, then back to QueryStats
            stats_dict = stats.to_dict()
            for field_name in stats_dict['fields']:
                field_stats = stats_dict['fields'][field_name]
                # Sort by count (descending) and keep only top N
                sorted_items = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)
                stats_dict['fields'][field_name] = dict(sorted_items[:top])
            
            # Convert back to QueryStats object
            from .stats import QueryStats
            stats = QueryStats(stats_dict)
        
        return stats
    
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
            dict: Dictionary with 'Services' and 'Leaks' keys, each containing a list of l9event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> host_info = client.get_host("157.90.211.37")
            >>> print(f"Services: {len(host_info['Services'] or [])}")
            >>> print(f"Leaks: {len(host_info['Leaks'] or [])}")
            >>> 
            >>> # Access service details
            >>> if host_info['Services']:
            ...     for service in host_info['Services']:
            ...         print(f"{service.protocol}://{service.ip}:{service.port}")
        """
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        
        self.api = self.api or LeakIXAPI(self.api_key, False, self.log)
        
        # Get host details from API
        data, is_cached = self.api.get_host_details(ip, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for IP {ip}", "warning")
            return {"Services": None, "Leaks": None}
        
        # Handle output file
        output_file = None
        should_close_file = False
        if output:
            if isinstance(output, str):
                try:
                    output_file = open(output, "w", encoding="utf-8")
                    should_close_file = True
                    if not self.silent:
                        self.log(f"Writing results to {output}...", "info")
                except (IOError, OSError) as e:
                    if not self.silent:
                        self.log(f"Error opening output file {output}: {e}", "error")
                    output_file = None
            else:
                output_file = output
                if not self.silent:
                    self.log("Writing results to stdout...", "info")
        
        try:
            # Process Services
            services = []
            if data.get("Services"):
                processed_services = self.process_and_print_data(
                    data["Services"], 
                    fields, 
                    suppress_debug=self.silent
                )
                services = processed_services
                
                # Write to file if specified
                if output_file:
                    for service in processed_services:
                        if hasattr(service, 'to_dict'):
                            service_dict = service.to_dict()
                        else:
                            service_dict = service
                        output_file.write(f"{json.dumps(service_dict)}\n")
                    output_file.flush()
            
            # Process Leaks
            leaks = []
            if data.get("Leaks"):
                processed_leaks = self.process_and_print_data(
                    data["Leaks"], 
                    fields, 
                    suppress_debug=self.silent
                )
                leaks = processed_leaks
                
                # Write to file if specified
                if output_file:
                    for leak in processed_leaks:
                        if hasattr(leak, 'to_dict'):
                            leak_dict = leak.to_dict()
                        else:
                            leak_dict = leak
                        output_file.write(f"{json.dumps(leak_dict)}\n")
                    output_file.flush()
            
            result = {
                "Services": services if services else None,
                "Leaks": leaks if leaks else None
            }
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(services)} services, {len(leaks)} leaks", "info")
            
            return result
        finally:
            if output_file and should_close_file:
                output_file.close()
    
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
            dict: Dictionary with 'Services' and 'Leaks' keys, each containing a list of l9event objects.
                  Both can be None if no information was found.
        
        Example:
            >>> client = LeakIX()
            >>> domain_info = client.get_domain("leakix.net")
            >>> print(f"Services: {len(domain_info['Services'] or [])}")
            >>> print(f"Leaks: {len(domain_info['Leaks'] or [])}")
            >>> 
            >>> # Access service details
            >>> if domain_info['Services']:
            ...     for service in domain_info['Services']:
            ...         print(f"{service.protocol}://{service.host}:{service.port}")
        """
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        
        self.api = self.api or LeakIXAPI(self.api_key, False, self.log)
        
        # Get domain details from API
        data, is_cached = self.api.get_domain_details(domain, suppress_logs=self.silent)
        
        if not data:
            if not self.silent:
                self.log(f"No information found for domain {domain}", "warning")
            return {"Services": None, "Leaks": None}
        
        # Handle output file
        output_file = None
        should_close_file = False
        if output:
            if isinstance(output, str):
                try:
                    output_file = open(output, "w", encoding="utf-8")
                    should_close_file = True
                    if not self.silent:
                        self.log(f"Writing results to {output}...", "info")
                except (IOError, OSError) as e:
                    if not self.silent:
                        self.log(f"Error opening output file {output}: {e}", "error")
                    output_file = None
            else:
                output_file = output
                if not self.silent:
                    self.log("Writing results to stdout...", "info")
        
        try:
            # Process Services
            services = []
            if data.get("Services"):
                processed_services = self.process_and_print_data(
                    data["Services"], 
                    fields, 
                    suppress_debug=self.silent
                )
                services = processed_services
                
                # Write to file if specified
                if output_file:
                    for service in processed_services:
                        if hasattr(service, 'to_dict'):
                            service_dict = service.to_dict()
                        else:
                            service_dict = service
                        output_file.write(f"{json.dumps(service_dict)}\n")
                    output_file.flush()
            
            # Process Leaks
            leaks = []
            if data.get("Leaks"):
                processed_leaks = self.process_and_print_data(
                    data["Leaks"], 
                    fields, 
                    suppress_debug=self.silent
                )
                leaks = processed_leaks
                
                # Write to file if specified
                if output_file:
                    for leak in processed_leaks:
                        if hasattr(leak, 'to_dict'):
                            leak_dict = leak.to_dict()
                        else:
                            leak_dict = leak
                        output_file.write(f"{json.dumps(leak_dict)}\n")
                    output_file.flush()
            
            result = {
                "Services": services if services else None,
                "Leaks": leaks if leaks else None
            }
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(services)} services, {len(leaks)} leaks", "info")
            
            return result
        finally:
            if output_file and should_close_file:
                output_file.close()
    
    def get_subdomains(self, domain, output=None):
        """
        Get subdomains for a specific domain name.
        
        Args:
            domain (str): The domain name to query.
            output (str or file object, optional): Path to file or file object to write results.
                                                   If None, results are only returned. Defaults to None.
        
        Returns:
            list: List of dictionaries containing subdomain information.
                  Each dictionary has 'subdomain', 'distinct_ips', and 'last_seen' keys.
                  Returns empty list if no subdomains found or on error.
        
        Example:
            >>> client = LeakIX()
            >>> subdomains = client.get_subdomains("leakix.net")
            >>> print(f"Found {len(subdomains)} subdomains")
            >>> 
            >>> # Access subdomain details
            >>> for subdomain in subdomains:
            ...     print(f"{subdomain['subdomain']} - {subdomain['distinct_ips']} IPs")
        """
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        
        self.api = self.api or LeakIXAPI(self.api_key, False, self.log)
        
        # Get subdomains from API
        data, is_cached = self.api.get_subdomains(domain, suppress_logs=self.silent)
        
        # Check for rate limiting
        if data and isinstance(data, dict) and data.get('_rate_limited'):
            raise ValueError(f"Rate limited. Wait {data.get('_wait_seconds', 60)} seconds before retrying.")
        
        if not data:
            if not self.silent:
                self.log(f"No subdomains found for domain {domain}", "warning")
            return []
        
        # Deduplicate subdomains by subdomain name (keep first occurrence)
        seen = set()
        unique_subdomains = []
        for subdomain in data:
            subdomain_name = subdomain.get('subdomain', '')
            if subdomain_name and subdomain_name not in seen:
                seen.add(subdomain_name)
                unique_subdomains.append(subdomain)
        
        data = unique_subdomains
        
        # Handle output file
        output_file = None
        should_close_file = False
        if output:
            if isinstance(output, str):
                try:
                    output_file = open(output, "w", encoding="utf-8")
                    should_close_file = True
                    if not self.silent:
                        self.log(f"Writing results to {output}...", "info")
                except (IOError, OSError) as e:
                    if not self.silent:
                        self.log(f"Error opening output file {output}: {e}", "error")
                    output_file = None
            else:
                output_file = output
                if not self.silent:
                    self.log("Writing results to stdout...", "info")
        
        try:
            # Write to file if specified
            if output_file:
                for subdomain in data:
                    output_file.write(f"{json.dumps(subdomain)}\n")
                output_file.flush()
            
            if not self.silent and output_file:
                self.log(f"✓ Completed - {len(data)} subdomains", "info")
            
            return data
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
        return get_all_fields(data, current_path)

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
            list: A list of scraped results (l9event objects) based on the provided criteria.
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
        given_plugins = [p.strip() for p in plugin.split(",") if p.strip()]
        invalid_plugins = [p for p in given_plugins if p not in set(plugins_list)]
        
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins_list}")
        
        # Handle output: can be a string (file path) or a file object (e.g., sys.stdout)
        output_file = None
        should_close_file = False
        if output:
            if isinstance(output, str):
                # It's a file path, open it
                try:
                    output_file = open(output, "w", encoding="utf-8")
                    should_close_file = True
                    if not self.silent:
                        self.log(f"Writing results in real-time to {output}...", "info")
                except (IOError, OSError) as e:
                    if not self.silent:
                        self.log(f"Error opening output file {output}: {e}", "error")
                    output_file = None
            else:
                # It's already a file object (e.g., sys.stdout)
                output_file = output
                if not self.silent:
                    self.log("Writing results to stdout...", "info")
        
        try:
            # Convert fields to string format if it's a list
            fields_str = fields
            if isinstance(fields, list):
                fields_str = ",".join(fields)
            elif fields is None:
                fields_str = "protocol,ip,port"
            
            results = self.query(scope, pages, query, given_plugins, fields_str, use_bulk, output_file=output_file)
            return results
        finally:
            # Close the file only if we opened it (not if it was passed as a file object)
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
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")

        self.api = self.api or LeakIXAPI(self.api_key, False, self.log)
        if self.api.is_api_pro is None:
            self.api.is_api_pro = self.api.check_privilege("WpUserEnumHttp", "leak")

        # Build query with plugins
        query_param = self.api.build_query_with_plugins(query_param, plugins)

        def get_dedup_key(result, fields):
            """Generate a deduplication key based on the selected fields."""
            # Handle l9event objects - convert to dict for key generation
            if hasattr(result, '__dict__'):
                result_dict = result.__dict__()
            elif isinstance(result, dict):
                result_dict = result
            else:
                return str(result)
            
            # If "full" is requested, use event_fingerprint if available, otherwise use the full JSON
            if fields and "full" in [f.strip() for f in fields.split(",")]:
                # For full JSON, try to use event_fingerprint as unique identifier
                if "event_fingerprint" in result_dict:
                    return result_dict["event_fingerprint"]
                # Fallback: use a combination of key fields that should be unique
                key_fields = ["ip", "port", "host", "event_type", "event_source", "time"]
                key_values = tuple(result_dict.get(k) for k in key_fields if k in result_dict)
                return str(key_values) if any(key_values) else json.dumps(result_dict, sort_keys=True)
            
            # For specific fields, create a key from the selected fields
            if fields:
                fields_list = [f.strip() for f in fields.split(",")]
            else:
                # Default fields: protocol, ip, port
                fields_list = ["protocol", "ip", "port"]
            
            # Special case: if result has been transformed to URL (default fields case)
            if "url" in result_dict and fields_list == ["protocol", "ip", "port"]:
                return result_dict["url"]
            
            # Extract values for the selected fields
            key_values = []
            for field in fields_list:
                if field == "url" and "url" in result_dict:
                    key_values.append(result_dict["url"])
                elif field in result_dict:
                    key_values.append(result_dict[field])
                else:
                    # For nested fields, try to get the value
                    try:
                        keys = field.split(".")
                        value = result_dict
                        for k in keys:
                            value = value[k]
                        key_values.append(value)
                    except (KeyError, TypeError):
                        key_values.append(None)
            
            return tuple(key_values)
        
        def _write_result_to_file(result, output_file, fields):
            """Write a single result to file."""
            try:
                # Handle l9event objects - convert to dict for JSON serialization
                if hasattr(result, 'to_dict'):
                    result_dict = result.to_dict()
                else:
                    result_dict = result
                
                if not fields and isinstance(result_dict, dict) and result_dict.get('url'):
                    output_file.write(f"{result_dict.get('url')}\n")
                else:
                    output_file.write(f"{json.dumps(result_dict)}\n")
                output_file.flush()
                return True
            except (IOError, OSError) as e:
                self.log(f"Error writing to file: {e}", "warning")
                return False
        
        def _process_page_results(page_results, seen_keys, output_file, fields):
            """
            Process page results: filter duplicates, write to file, and return unique results.
            
            Returns:
                tuple: (unique_results, new_duplicate_count)
            """
            unique_results = []
            new_duplicates = 0
            
            for result in page_results:
                dedup_key = get_dedup_key(result, fields)
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    unique_results.append(result)
                    
                    # Write result to file in real-time
                    if output_file:
                        _write_result_to_file(result, output_file, fields)
                else:
                    # This is a duplicate
                    new_duplicates += 1
            
            return unique_results, new_duplicates

        # Track seen keys for deduplication
        seen_keys = set()
        duplicate_count = 0
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
            use_progress = not return_data_only and not self.silent and not output_file
            
            try:
                if use_progress:
                    console = Console(file=sys.stderr if hasattr(sys, 'stderr') else None)
                    original_level = self.logger.level
                    self.logger.setLevel(logging.INFO)
                    
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
                            
                            # Process bulk results with deduplication
                            if results:
                                unique_results, new_duplicates = _process_page_results(
                                    results, seen_keys, output_file, fields
                                )
                                duplicate_count += new_duplicates
                                results = unique_results
                            
                            if results:
                                progress.update(task, description=f"[green]✓ Found {len(results)} unique results")
                            
                            log_execution_time()
                    finally:
                        self.logger.setLevel(original_level)
                else:
                    data, is_cached = self.api.query_bulk(query_param, suppress_logs=bool(output_file))
                    if return_data_only:
                        log_execution_time()
                        return data
                    # Suppress debug logs when writing to file
                    results = self.process_and_print_data(data, fields, suppress_debug=bool(output_file)) if data else []
                    # Process bulk results with deduplication
                    if results:
                        unique_results, new_duplicates = _process_page_results(
                            results, seen_keys, output_file, fields
                        )
                        duplicate_count += new_duplicates
                        results = unique_results
                
                # Restore silent state before showing completion message
                if output_file:
                    self.silent = original_silent
                
                # Show completion message even when writing to file (but only if not silent)
                if not self.silent and output_file and results:
                    if duplicate_count > 0:
                        self.log(f"✓ Completed - {len(results)} unique results ({duplicate_count} duplicates skipped)", "info")
                    else:
                        self.log(f"✓ Completed - {len(results)} results", "info")
                elif duplicate_count > 0 and not self.silent:
                    self.log(f"Skipped {duplicate_count} duplicate result(s)", "debug")
                
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
        use_progress = not return_data_only and not self.silent
        
        if use_progress:
            # Create a console for rich output that won't conflict with logging
            console = Console(file=sys.stderr if hasattr(sys, 'stderr') else None)
            
            # Temporarily disable debug logging to avoid conflicts with progress bar
            original_level = self.logger.level
            original_handlers = self.logger.handlers[:]
            
            # Set logger to INFO level to suppress DEBUG messages during progress bar
            self.logger.setLevel(logging.INFO)
            
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
                        
                        # Process page results (deduplication and file writing)
                        unique_page_results, new_duplicates = _process_page_results(
                            page_results, seen_keys, output_file, fields
                        )
                        duplicate_count += new_duplicates
                        results.extend(unique_page_results)
                        
                        # Update progress bar
                        progress.update(
                            task, 
                            advance=1,
                            description=f"[cyan]Fetching pages ({page + 1}/{pages}) - {len(results)} unique results..."
                        )
                        
                        # Only respect rate limit if we made an actual API request
                        if not is_cached:
                            time.sleep(1.2)
                    
                    # Final update
                    if duplicate_count > 0:
                        progress.update(
                            task,
                            description=f"[green]✓ Completed - {len(results)} unique results ({duplicate_count} duplicates skipped)"
                        )
                    else:
                        progress.update(
                            task,
                            description=f"[green]✓ Completed - {len(results)} results"
                        )
            finally:
                # Restore original logging level
                self.logger.setLevel(original_level)
        else:
            # No progress bar, use simple logging
            for page in range(pages):
                data, is_cached = self.api.query_search(scope, page, query_param)
                if not data:
                    break
                last_data = data
                page_results = self.process_and_print_data(data, fields)
                
                # Process page results (deduplication and file writing)
                unique_page_results, new_duplicates = _process_page_results(
                    page_results, seen_keys, output_file, fields
                )
                duplicate_count += new_duplicates
                results.extend(unique_page_results)
                
                # Only respect rate limit if we made an actual API request
                if not is_cached:
                    time.sleep(1.2)

        if duplicate_count > 0 and not self.silent:
            self.log(f"Skipped {duplicate_count} duplicate result(s)", "debug")

        log_execution_time()
        return last_data if return_data_only else results
