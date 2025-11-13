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

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class LeakIXScraper:
    """Main scraper class for interacting with LeakIX API."""
    
    def __init__(self, api_key=None, verbose=False, silent=False):
        """
        Initialize a new instance of the LeakIXScraper.

        Args:
            api_key (str, optional): The API key for accessing LeakIX services. Defaults to None.
            verbose (bool, optional): Flag to enable verbose logging. Defaults to False.
            silent (bool, optional): Flag to suppress all output (no logs, no progress bar). Defaults to False.
        """
        self.silent = silent
        # In silent mode, disable all logging
        if silent:
            verbose = False
        self.logger = setup_logger("LeakPy", verbose=verbose)
        self.verbose = verbose
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
        self.api = LeakIXAPI(self.api_key, verbose, api_logger) if self.api_key else None

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
        self.api = LeakIXAPI(self.api_key, self.verbose, self.log)
    
    def delete_api_key(self):
        """Delete the stored API key from secure storage."""
        self.key_manager.delete()
        self.api_key = ""
        self.api = None

    def get_plugins(self):
        """Retrieve the list of available plugins from LeakIX."""
        return self.api.get_plugins() if self.api else []

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

    def execute(
        self,
        scope="leak",
        query="",
        pages=2,
        plugin="",
        fields="protocol,ip,port",
        use_bulk=False,
    ):
        """
        Execute the scraper to fetch data based on provided parameters.

        Args:
            scope (str, optional): The scope of the search. Defaults to "leak".
            query (str, optional): Search query string. Defaults to an empty string.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            plugin (str, optional): Comma-separated plugin names. Defaults to an empty string.
            fields (str, optional): Comma-separated list of fields to extract from results. Defaults to "protocol,ip,port".
            use_bulk (bool, optional): Whether to use the bulk functionality. Defaults to False.

        Returns:
            list: A list of scraped results based on the provided criteria.
        """
        plugins_list = self.get_plugins()
        given_plugins = [p.strip() for p in plugin.split(",") if p.strip()]
        invalid_plugins = [p for p in given_plugins if p not in set(plugins_list)]
        
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins_list}")
        
        return self.query(scope, pages, query, given_plugins, fields, use_bulk)

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

        self.api = self.api or LeakIXAPI(self.api_key, self.verbose, self.log)
        if self.api.is_api_pro is None:
            self.api.is_api_pro = self.api.check_privilege("WpUserEnumHttp", "leak")

        # Build query with plugins
        query_param = self.api.build_query_with_plugins(query_param, plugins)

        def get_dedup_key(result, fields):
            """Generate a deduplication key based on the selected fields."""
            if not isinstance(result, dict):
                return str(result)
            
            # If "full" is requested, use event_fingerprint if available, otherwise use the full JSON
            if fields and "full" in [f.strip() for f in fields.split(",")]:
                # For full JSON, try to use event_fingerprint as unique identifier
                if "event_fingerprint" in result:
                    return result["event_fingerprint"]
                # Fallback: use a combination of key fields that should be unique
                key_fields = ["ip", "port", "host", "event_type", "event_source", "time"]
                key_values = tuple(result.get(k) for k in key_fields if k in result)
                return str(key_values) if any(key_values) else json.dumps(result, sort_keys=True)
            
            # For specific fields, create a key from the selected fields
            if fields:
                fields_list = [f.strip() for f in fields.split(",")]
            else:
                # Default fields: protocol, ip, port
                fields_list = ["protocol", "ip", "port"]
            
            # Special case: if result has been transformed to URL (default fields case)
            if "url" in result and fields_list == ["protocol", "ip", "port"]:
                return result["url"]
            
            # Extract values for the selected fields
            key_values = []
            for field in fields_list:
                if field == "url" and "url" in result:
                    key_values.append(result["url"])
                elif field in result:
                    key_values.append(result[field])
                else:
                    # For nested fields, try to get the value
                    try:
                        keys = field.split(".")
                        value = result
                        for k in keys:
                            value = value[k]
                        key_values.append(value)
                    except (KeyError, TypeError):
                        key_values.append(None)
            
            return tuple(key_values)
        
        def _write_result_to_file(result, output_file, fields):
            """Write a single result to file."""
            try:
                if not fields and isinstance(result, dict) and result.get('url'):
                    output_file.write(f"{result.get('url')}\n")
                else:
                    output_file.write(f"{json.dumps(result)}\n")
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
                original_verbose = self.verbose
                original_silent = self.silent
                self.verbose = False
                self.silent = True
                self.api.verbose = False
            
            # Show spinner in bulk mode if verbose and not silent and not writing to file
            use_progress = self.verbose and RICH_AVAILABLE and not return_data_only and not self.silent and not output_file
            
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
                elif duplicate_count > 0 and not self.silent and not use_progress:
                    self.log(f"Skipped {duplicate_count} duplicate result(s)", "debug")
                
                log_execution_time()
                return results
            finally:
                # Restore original verbose/silent state
                if output_file:
                    self.verbose = original_verbose
                    self.silent = original_silent
                    self.api.verbose = original_verbose

        # Regular paginated search
        results = []
        last_data = None
        
        # Show progress bar if verbose and rich is available, but not in silent mode
        use_progress = self.verbose and RICH_AVAILABLE and not return_data_only and not self.silent
        
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

    def run(
        self,
        scope,
        pages=2,
        query="",
        plugins=None,
        output=None,
        fields=None,
        use_bulk=False,
    ):
        """
        Initiate the scraping process based on provided criteria and optionally save results to a file.

        Args:
            scope (str): The scope of the search.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            query (str, optional): The query string for the search. Defaults to an empty string.
            plugins (list or str, optional): List or comma-separated string of plugin names. Defaults to None.
            output (str, optional): Path to the file where results should be saved. If None, results won't be saved. Defaults to None.
            fields (list of str or None, optional): List of fields to extract from results. Defaults to None.
            use_bulk (bool, optional): Whether to use bulk mode. Defaults to False.

        Returns:
            None: This method does not return any value.
        """
        all_plugins = self.get_plugins()
        plugin_names = set(all_plugins)
        if isinstance(plugins, str):
            plugins_list = plugins.split(",")
        else:
            plugins_list = plugins or []
        potentially_invalid_plugins = []
        for p in plugins_list:
            p_stripped = p.strip()
            if p_stripped and p_stripped not in plugin_names:
                potentially_invalid_plugins.append(p_stripped)

        # Suppress all output in bulk mode when writing to file
        suppress_output = use_bulk and output
        
        if not self.silent and not suppress_output:
            self.log("Using API Key for queries...", "info")
        
        # Open output file in write mode (creates/overwrites) for real-time writing
        output_file = None
        if output:
            try:
                output_file = open(output, "w", encoding="utf-8")
                if not self.silent and not suppress_output:
                    self.log(f"Writing results in real-time to {output}...", "info")
            except (IOError, OSError) as e:
                if not self.silent:
                    self.log(f"Error opening output file {output}: {e}", "error")
                output_file = None
        
        try:
            results = self.query(scope, pages, query, plugins_list, fields, use_bulk, output_file=output_file)
        finally:
            # Close the file if it was opened
            if output_file:
                output_file.close()

        if not self.silent and not suppress_output:
            if not results:
                if potentially_invalid_plugins:
                    self.log("No results found. The issue might be due to invalid plugin names.", "warning")
                    invalid_list = ', '.join(potentially_invalid_plugins)
                    self.log(f"Check if these plugin names are correct: {invalid_list}", "warning")
                    self.log("Here's a list of available plugins for reference:", "info")
                    self.log(f"Plugins available: {len(all_plugins)}", "info")
                    for plugin_name in all_plugins:
                        self.log(f"  - {plugin_name}", "info")
                else:
                    self.log("No results found. Please verify your query and try again.", "warning")
            elif output:
                self.log(f"File written successfully to {output} with {len(results)} lines", "info")
