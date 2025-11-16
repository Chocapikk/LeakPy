#!/usr/bin/python3
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

import argparse
import os
import platform
import sys
import traceback

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from . import __version__
from . import helpers
from .helpers.constants import (
    _SEARCH_EXAMPLES, _LOOKUP_EXAMPLES, _HOST_EXAMPLES, _DOMAIN_EXAMPLES,
    _SUBDOMAINS_EXAMPLES, _STATS_CACHE_EXAMPLES,
    _STATS_QUERY_EXAMPLES, _LIST_PLUGINS_EXAMPLES, _LIST_FIELDS_EXAMPLES,
    _CONFIG_RESET_EXAMPLES, _CONFIG_SET_EXAMPLES, _CACHE_CLEAR_EXAMPLES,
    _CACHE_SET_TTL_EXAMPLES, _CACHE_SHOW_TTL_EXAMPLES
)
from .logger import setup_logger
from .leakix import LeakIX

from rich.console import Console


def _print_banner(version):
    """Print ASCII art banner to stderr with colors."""
    console = Console(file=sys.stderr, force_terminal=True)
    
    # ASCII art
    console.print("   __            _   _____     ", style="rgb(255,165,0) bold")
    console.print("  |  |   ___ ___| |_|  _  |_ _ ", style="rgb(255,165,0) bold")
    console.print("  |  |__| -_| .'| '_|   __| | | ", style="rgb(255,165,0) bold")
    console.print("  |_____|___|__,|_,_|__|  |_  | ", style="rgb(255,165,0) bold")
    console.print("                          |___|", style="rgb(255,165,0) bold")
    console.print(f"            (v{version})", style="white")
    console.print()
    console.print("Coded by ", style="rgb(255,165,0)", end="")
    console.print("Chocapikk", style="bold rgb(0,191,255)", end="")
    console.print(" | ", style="rgb(255,165,0)", end="")
    console.print("Non-official", style="bold rgb(135,206,250)", end="")
    console.print(" ", style="", end="")
    console.print("LeakIX", style="bold rgb(50,205,50)", end="")
    console.print(" API client", style="rgb(255,165,0)")
    # Flush stderr before stdout output
    sys.stderr.flush()


class BannerArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that displays banner before help."""
    
    def print_help(self, file=None):
        """Override print_help to show banner first."""
        # Check if --silent is in args (before parsing, we check sys.argv)
        show_banner = '--silent' not in sys.argv
        if show_banner:
            _print_banner(__version__)
        super().print_help(file)


# ============================================================================
# COMMAND PARSERS
# ============================================================================

def create_common_parser():
    """Create a parser with common arguments that can be used as parent."""
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--silent", action="store_true", help="Suppress all output (useful for scripting)")
    common_parser.add_argument("--raw", action="store_true", help="Output raw JSON instead of formatted tables")
    return common_parser


def setup_search_parser(subparsers):
    """Set up the search command parser."""
    parser = subparsers.add_parser('search', help='Search LeakIX for leaks or services', description='Search LeakIX API and return results', epilog=_SEARCH_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    parser.add_argument("-s", "--scope", choices=["service", "leak"], default="leak", help="Search scope: 'leak' or 'service' (default: leak)", type=str)
    parser.add_argument("-p", "--pages", help="Number of pages to fetch (default: 2)", default=2, type=int)
    parser.add_argument("-q", "--query", help="Search query string", default="", type=str)
    parser.add_argument("-P", "--plugins", help="Plugin(s) to use (comma-separated)", type=str, default=None)
    parser.add_argument("-o", "--output", help="Output file path", type=str)
    parser.add_argument("-f", "--fields", help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full'). Default: 'protocol,ip,port' (for URL formatting)", type=str)
    parser.add_argument("-b", "--bulk", action="store_true", help="Use bulk mode (requires Pro API)")
    return parser


def setup_lookup_parser(subparsers):
    """Set up the lookup command parser."""
    parser = subparsers.add_parser('lookup', help='Lookup information about specific IPs, domains, or subdomains', description='Retrieve detailed information about specific IP addresses, domains, or subdomains', epilog=_LOOKUP_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    subparsers_lookup = parser.add_subparsers(dest='lookup_action', help='Lookup actions', required=True)
    
    host_parser = subparsers_lookup.add_parser('host', help='Get host details for a specific IP address', description='Retrieve detailed information about a specific IP address, including services and leaks', epilog=_HOST_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    host_parser.add_argument('ip', nargs='?', help='IP address to query (or use -i/--input for batch processing)')
    helpers.add_common_lookup_args(host_parser, include_fields=True, include_limit=True)
    
    domain_parser = subparsers_lookup.add_parser('domain', help='Get domain details for a specific domain name', description='Retrieve detailed information about a specific domain and its subdomains, including services and leaks', epilog=_DOMAIN_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    domain_parser.add_argument('domain', nargs='?', help='Domain name to query (or use -i/--input for batch processing)')
    helpers.add_common_lookup_args(domain_parser, include_fields=True, include_limit=True)
    
    subdomains_parser = subparsers_lookup.add_parser('subdomains', help='Get subdomains for a specific domain name', description='Retrieve list of subdomains for a given domain', epilog=_SUBDOMAINS_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    subdomains_parser.add_argument('domain', nargs='?', help='Domain name to query (or use -i/--input for batch processing)')
    helpers.add_common_lookup_args(subdomains_parser, include_fields=False, include_limit=False)
    
    return parser


def setup_stats_parser(subparsers):
    """Set up the stats command parser."""
    parser = subparsers.add_parser('stats', help='Display statistics and metrics', description='Display various statistics and metrics with visualizations', parents=[create_common_parser()])
    
    subparsers_stats = parser.add_subparsers(dest='stats_action', required=True)
    
    subparsers_stats.add_parser('cache', help='Display cache statistics', description='Show cache statistics with visualizations', epilog=_STATS_CACHE_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    query_parser = subparsers_stats.add_parser('query', help='Display query statistics', description='Analyze and display statistics from search queries (by country, protocol, port, etc.)', epilog=_STATS_QUERY_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    query_parser.add_argument('-f', '--file', type=str, help='JSON file containing query results to analyze')
    query_parser.add_argument('-q', '--query', type=str, default='', help='Query string to search (if no file provided)')
    query_parser.add_argument('-p', '--pages', type=int, default=2, help='Number of pages to fetch (default: 2)')
    query_parser.add_argument('-s', '--scope', choices=['service', 'leak'], default='leak', help='Search scope (default: leak)')
    query_parser.add_argument('--top', type=int, default=10, help='Number of top items to display (default: 10)')
    query_parser.add_argument('--fields', type=str, help='Comma-separated list of fields to analyze (e.g. "country,protocol,port"). If not specified, analyzes all common fields.')
    query_parser.add_argument('--all-fields', action='store_true', help='Analyze all available fields in the results')
    query_parser.add_argument('-b', '--bulk', action='store_true', help='Use bulk mode for faster queries (requires Pro API)')
    
    return parser


def setup_list_parser(subparsers):
    """Set up the list command parser."""
    parser = subparsers.add_parser('list', help='List available plugins or fields', description='List available plugins or fields from LeakIX', parents=[create_common_parser()])
    
    subparsers_list = parser.add_subparsers(dest='list_action', help='List actions', required=True)
    
    # plugins subcommand
    plugins_parser = subparsers_list.add_parser('plugins', help='List available plugins', description='List all available LeakIX plugins', epilog=_LIST_PLUGINS_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    
    # fields subcommand
    fields_parser = subparsers_list.add_parser('fields', help='List available fields', description='List all available fields from a sample query', epilog=_LIST_FIELDS_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    fields_parser.add_argument("-s", "--scope", choices=["service", "leak"], default="leak", help="Search scope: 'leak' or 'service' (default: leak)", type=str)
    fields_parser.add_argument("-q", "--query", help="Query string to fetch sample data", default="", type=str)
    fields_parser.add_argument("-P", "--plugins", help="Plugin(s) to use (comma-separated)", type=str, default=None)
    
    return parser


def setup_config_parser(subparsers):
    """Set up the config command parser."""
    parser = subparsers.add_parser('config', help='Manage API key configuration', description='Configure or manage your LeakIX API key', parents=[create_common_parser()])
    
    subparsers_config = parser.add_subparsers(dest='config_action', help='Config actions')
    
    # reset subcommand
    subparsers_config.add_parser('reset', help='Reset/delete saved API key', description='Delete the stored API key', epilog=_CONFIG_RESET_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    
    # set subcommand
    set_parser = subparsers_config.add_parser('set', help='Set API key', description='Set or update your API key', epilog=_CONFIG_SET_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    set_parser.add_argument('api_key', nargs='?', help='API key (48 characters). If not provided, will prompt interactively.', type=str)
    
    return parser


def setup_cache_parser(subparsers):
    """Set up the cache command parser."""
    parser = subparsers.add_parser('cache', help='Manage API response cache', description='Clear or manage the API response cache', parents=[create_common_parser()])
    
    subparsers_cache = parser.add_subparsers(dest='cache_action', required=True)
    
    # clear subcommand
    subparsers_cache.add_parser('clear', help='Clear the cache', description='Clear all cached API responses', epilog=_CACHE_CLEAR_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    
    # set-ttl subcommand
    set_ttl_parser = subparsers_cache.add_parser('set-ttl', help='Set cache TTL (Time To Live)', description='Set the cache TTL in minutes. Default is 5 minutes.', epilog=_CACHE_SET_TTL_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    set_ttl_parser.add_argument('minutes', type=int, help='Cache TTL in minutes (must be a positive integer)')
    
    # show-ttl subcommand (to see current TTL)
    subparsers_cache.add_parser('show-ttl', help='Show current cache TTL', description='Display the current cache TTL setting', epilog=_CACHE_SHOW_TTL_EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[create_common_parser()])
    
    return parser


# ============================================================================
# COMMAND EXECUTORS
# ============================================================================

def execute_search(args, client, stdout_redirected):
    """Execute the search command."""
    helpers.execute_search(args, client, stdout_redirected)


def execute_lookup(args, client, stdout_redirected):
    """Execute the lookup command."""
    if args.lookup_action not in ('host', 'domain', 'subdomains'):
        sys.exit(1)
    is_batch = helpers.execute_single_lookup(args, client, stdout_redirected, args.lookup_action)
    if is_batch:
        helpers.execute_batch_lookup(args, client, stdout_redirected, args.lookup_action)
    sys.exit(0)


def execute_stats(args, logger, silent, client=None):
    """Execute the stats command."""
    _STATS_ACTIONS = {
        'cache': lambda: helpers.display_cache_stats(args, logger),
        'query': lambda: helpers.execute_query_stats(args, logger, client)
    }
    
    if args.stats_action not in _STATS_ACTIONS:
        sys.exit(1)
    
    _STATS_ACTIONS[args.stats_action]()
    sys.exit(0)


def execute_list(args, client, logger, silent):
    """Execute the list command."""
    _LIST_ACTIONS = {
        'plugins': lambda: helpers.execute_list_plugins(args, client, logger),
        'fields': lambda: helpers.execute_list_fields(args, client, logger)
    }
    
    if args.list_action not in _LIST_ACTIONS:
        sys.exit(1)
    
    _LIST_ACTIONS[args.list_action]()
    sys.exit(0)


def execute_config(args, client, logger, silent):
    """Execute the config command."""
    _CONFIG_ACTIONS = {
        'reset': lambda: helpers.execute_config_reset(args, client, logger),
        'set': lambda: helpers.execute_config_set(args, client, logger)
    }
    
    if args.config_action not in _CONFIG_ACTIONS:
        sys.exit(1)
    
    _CONFIG_ACTIONS[args.config_action]()
    sys.exit(0)


def execute_cache(args, logger, silent):
    """Execute the cache command."""
    _CACHE_ACTIONS = {
        'clear': lambda: helpers.execute_cache_clear(args, logger),
        'set-ttl': lambda: helpers.execute_cache_set_ttl(args, logger),
        'show-ttl': lambda: helpers.execute_cache_show_ttl(args, logger)
    }
    
    if args.cache_action not in _CACHE_ACTIONS:
        sys.exit(1)
    
    _CACHE_ACTIONS[args.cache_action]()
    sys.exit(0)


def main():
    """Main entry point for LeakPy CLI."""
    try:
        parser = BannerArgumentParser(
            description="LeakPy - LeakIX API Client",
            epilog="""
Examples:
  # List available plugins
  leakpy list plugins

  # List available fields
  leakpy list fields

  # Search for leaks in France
  leakpy search -q '+country:"France"' -p 5

  # Search with specific plugin
  leakpy search -q '+country:"France"' -P PulseConnectPlugin -p 3

  # Extract specific fields
  leakpy search -q '+country:"France"' -f protocol,ip,port,host

  # Get complete JSON (all fields) and save to file
  leakpy search -q '+country:"France"' -f full -o results.json

  # Use bulk mode (requires Pro API, only works with scope="leak")
  leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

  # Configure API key
  leakpy config set

  # Reset API key
  leakpy config reset

  # Clear cache
  leakpy cache clear

  # Display cache statistics
  leakpy stats cache


  # Analyze query statistics (by country, protocol, etc.)
  leakpy stats query -q '+country:"France"' -p 5

  # Analyze statistics from a JSON file
  leakpy stats query -f results.json

For more examples, see: https://leakpy.readthedocs.io/
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument("-v", "--version", action="version", version=f"LeakPy {__version__}")
        # --silent and --raw are defined in create_common_parser() and inherited by all subparsers
        # Also add them to main parser so they work at top level: leakpy --silent --raw command
        parser.add_argument("--silent", action="store_true", help="Suppress all output (useful for scripting)")
        parser.add_argument("--raw", action="store_true", help="Output raw JSON instead of formatted tables")

        # Create subparsers for commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands', metavar='COMMAND')
        
        # Register all commands
        setup_search_parser(subparsers)
        setup_list_parser(subparsers)
        setup_cache_parser(subparsers)
        setup_config_parser(subparsers)
        setup_stats_parser(subparsers)
        setup_lookup_parser(subparsers)

        args = parser.parse_args()

        # If no command provided, show help
        if not args.command:
            parser.print_help()
            sys.exit(0)

        # Ensure --silent and --raw are always defined in args namespace
        # This handles cases where parent parser propagation doesn't work correctly
        if not hasattr(args, 'silent'):
            args.silent = False
        if not hasattr(args, 'raw'):
            args.raw = False
        # Also check if they were passed in command line (fallback)
        if '--silent' in sys.argv:
            args.silent = True
        # Track if --raw was explicitly passed by user
        raw_explicit = '--raw' in sys.argv
        if raw_explicit:
            args.raw = True

        # Detect if stdout is redirected (pipe or file redirection)
        # If stdout is redirected, we want raw output only (no logs, no progress bars)
        stdout_redirected = not sys.stdout.isatty()
        if stdout_redirected and not args.raw:
            # Auto-enable raw mode when stdout is redirected
            args.raw = True

        logger = setup_logger("LeakPy", verbose=False)
        
        # Show banner for all commands unless silent or raw mode was explicitly requested
        # Don't hide banner if raw mode was auto-enabled due to stdout redirection
        if not args.silent and not raw_explicit:
            _print_banner(__version__)

        # CLI always respects --silent flag (default is False in CLI, but True in library)
        # --raw also suppresses logs for clean JSON output
        client = LeakIX(silent=args.silent or args.raw)

        # Check API key for commands that need it (except config and cache clear)
        needs_api_key = args.command in ['search', 'list', 'lookup']
        
        if needs_api_key and not client.has_api_key():
            if args.silent:
                logger.error("API key is missing. Use 'leakpy config set' to set it.")
                sys.exit(1)
            session = PromptSession()
            logger.warning("API key is missing. Please enter your API key to continue.")
            api_key = session.prompt(
                HTML("<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> "),
                is_password=True,
            ).strip()
            client.save_api_key(api_key)

            if not client.has_api_key():
                logger.error("The provided API key is invalid. It must be 48 characters long.")
                sys.exit(1)

        # Execute the appropriate command
        if args.command == 'search':
            execute_search(args, client, stdout_redirected)
        elif args.command == 'list':
            execute_list(args, client, logger, args.silent)
        elif args.command == 'cache':
            execute_cache(args, logger, args.silent)
        elif args.command == 'config':
            execute_config(args, client, logger, args.silent)
        elif args.command == 'stats':
            execute_stats(args, logger, args.silent, client)
        elif args.command == 'lookup':
            execute_lookup(args, client, stdout_redirected)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        silent = getattr(args, 'silent', False) if 'args' in locals() else False
        if not silent:
            logger = setup_logger("LeakPy", verbose=False)
            logger.info("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        error_message = traceback.format_exc()
        # Try to get silent flag from args if it exists
        silent = getattr(args, 'silent', False) if 'args' in locals() else False
        if not silent:
            logger = setup_logger("LeakPy", verbose=False)
            logger.error(f"An error occurred: {e}")
            logger.error("")
            logger.error("Please submit an issue at: https://github.com/Chocapikk/LeakPy/issues")
            logger.error("Include the following information in your issue:")
            logger.error("")
            logger.error(f"LeakPy version: {__version__}")
            logger.error(f"OS: {platform.system()} {platform.release()}")
            logger.error(f"Python version: {platform.python_version()}")
            logger.error("")
            logger.error("Traceback:")
            logger.error(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
