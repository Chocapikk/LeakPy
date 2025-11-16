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

import sys
from .l9event import get_all_fields_from_l9format_schema
from .display import display_search_results

# Helper functions

def _is_raw_or_silent(args):
    """Check if raw or silent mode is enabled."""
    return args.raw or args.silent


def _log_or_print(args, logger, message, value=None):
    """Log message or print value based on raw/silent mode."""
    if _is_raw_or_silent(args):
        if value is not None:
            print(value)
    else:
        logger.info(message)


def _error_and_exit(logger, message):
    """Log error message and exit with code 1."""
    logger.error(message)
    sys.exit(1)

# CLI list execution functions

def execute_list_plugins(args, client, logger):
    """Execute list plugins command."""
    if _is_raw_or_silent(args):
        for plugin in client.get_plugins():
            print(plugin)
    else:
        from leakpy.cli_helpers import handle_list_plugins
        handle_list_plugins(logger, client)


def execute_list_fields(args, client, logger):
    """Execute list fields command."""
    if _is_raw_or_silent(args):
        fields = get_all_fields_from_l9format_schema()
        for field in fields:
            print(field)
    else:
        from leakpy.cli_helpers import handle_list_fields
        if not handle_list_fields(logger, client, args.scope, args.query, None):
            sys.exit(1)


# CLI config execution functions

def execute_config_reset(args, client, logger):
    """Execute config reset command."""
    client.delete_api_key()
    if not args.silent:
        logger.info("API key has been reset.")


def execute_config_set(args, client, logger):
    """Execute config set command."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML

    if args.api_key:
        api_key = args.api_key.strip()
    else:
        if args.silent:
            _error_and_exit(logger, "API key is required in silent mode. Use: leakpy config set <api_key>")

        session = PromptSession()
        logger.warning("Please enter your API key:")
        api_key = session.prompt(
            HTML("<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> "),
            is_password=True,
        ).strip()

    client.save_api_key(api_key)

    if not client.has_api_key():
        _error_and_exit(logger, "The provided API key is invalid. It must be 48 characters long.")

    if not args.silent:
        logger.info("API key has been saved successfully.")


# CLI cache execution functions

def execute_cache_clear(args, logger):
    """Execute cache clear command."""
    from ..cache import APICache
    cache = APICache()
    cache.clear()
    if not args.silent:
        logger.info("Cache cleared.")


def execute_cache_set_ttl(args, logger):
    """Execute cache set-ttl command."""
    if args.minutes <= 0:
        _error_and_exit(logger, "TTL must be a positive integer (minutes).")

    from ..config import CacheConfig
    cache_config = CacheConfig()
    cache_config.set_ttl_minutes(args.minutes)
    if not args.silent:
        logger.info(f"Cache TTL set to {args.minutes} minute(s) ({args.minutes * 60} seconds).")


def execute_cache_show_ttl(args, logger):
    """Execute cache show-ttl command."""
    from ..config import CacheConfig
    from ..cache import APICache

    cache_config = CacheConfig()
    ttl_minutes = cache_config.get_ttl_minutes()

    if ttl_minutes is None:
        # Use default
        default_minutes = APICache.DEFAULT_TTL // 60
        _log_or_print(args, logger, f"Cache TTL: {default_minutes} minute(s) (default)", default_minutes)
    else:
        _log_or_print(args, logger, f"Cache TTL: {ttl_minutes} minute(s) ({ttl_minutes * 60} seconds)", ttl_minutes)


# CLI stats execution function

def execute_query_stats(args, logger, client=None):
    """Execute query stats with client initialization if needed."""
    from .display import display_query_stats
    
    if not args.file and not client:
        from ..leakix import LeakIX
        client = LeakIX(silent=args.silent)
        if not client.has_api_key():
            _error_and_exit(logger, "API key is required for query statistics. Use 'leakpy config set' to set it.")
    display_query_stats(args, logger, client)


# CLI search execution function

def execute_search(args, client, stdout_redirected):
    """Execute search command."""
    from leakpy.cli_helpers import normalize_plugins

    # Validate bulk mode: only works with scope="leak"
    if args.bulk and args.scope == "service":
        from ..logger import setup_logger
        logger = setup_logger("LeakPy", verbose=False)
        _error_and_exit(logger, "Bulk mode is only available for scope='leak', not 'service'")

    plugins = normalize_plugins(args.plugins)
    plugin_str = ",".join(plugins) if plugins else ""

    # args.raw and args.silent are guaranteed to be defined in main() before calling helpers
    # In raw or silent mode, output raw JSON to stdout
    # In non-raw mode, use display_search_results() for formatted output
    if args.output:
        output_target = args.output
    elif _is_raw_or_silent(args):
        # In raw or silent mode, output raw JSON to stdout
        output_target = sys.stdout
    else:
        # In non-raw mode, don't pass output to client.search()
        # We'll use display_search_results() instead
        output_target = None

    # For CLI, use "protocol,ip,port" by default to preserve URL formatting in tables
    # If user explicitly specifies fields, use that instead
    from .constants import _DEFAULT_FIELDS
    fields = args.fields if args.fields is not None else _DEFAULT_FIELDS

    results = client.search(scope=args.scope, pages=args.pages, query=args.query, plugin=plugin_str, fields=fields, use_bulk=args.bulk, output=output_target)

    # If output_target is set (raw mode or file output), we need to consume the generator
    # to trigger the writing to output
    if output_target:
        # Consume generator to write to output
        list(results)
    else:
        # Display formatted results if no output file was specified and not in raw or silent mode
        # Only show formatted output in interactive mode (not when stdout is redirected)
        should_display = (
            not _is_raw_or_silent(args) and
            not stdout_redirected
        )
        if should_display:
            # Show progress bar while consuming generator
            from .progress import consume_stream_with_progress
            results_list, interrupted = consume_stream_with_progress(results, args, "Streaming results")
            
            if results_list:
                display_search_results(results_list, fields)
