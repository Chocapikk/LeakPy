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

"""Cache command for LeakPy CLI."""

import sys
import argparse


def setup_parser(subparsers):
    """Set up the cache command parser."""
    parser = subparsers.add_parser(
        'cache',
        help='Manage API response cache',
        description='Clear or manage the API response cache'
    )
    
    subparsers_cache = parser.add_subparsers(dest='cache_action', required=True)
    
    # clear subcommand
    clear_parser = subparsers_cache.add_parser(
        'clear',
        help='Clear the cache',
        description='Clear all cached API responses',
        epilog="""
Examples:
  # Clear all cached API responses
  leakpy cache clear
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # set-ttl subcommand
    set_ttl_parser = subparsers_cache.add_parser(
        'set-ttl',
        help='Set cache TTL (Time To Live)',
        description='Set the cache TTL in minutes. Default is 5 minutes.',
        epilog="""
Examples:
  # Set cache TTL to 10 minutes
  leakpy cache set-ttl 10

  # Set cache TTL to 30 minutes
  leakpy cache set-ttl 30
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    set_ttl_parser.add_argument(
        'minutes',
        type=int,
        help='Cache TTL in minutes (must be a positive integer)'
    )
    
    # show-ttl subcommand (to see current TTL)
    show_ttl_parser = subparsers_cache.add_parser(
        'show-ttl',
        help='Show current cache TTL',
        description='Display the current cache TTL setting',
        epilog="""
Examples:
  # Show current cache TTL
  leakpy cache show-ttl

  # Show TTL in silent mode (for scripting)
  leakpy --silent cache show-ttl
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    return parser


def execute(args, logger, silent):
    """Execute the cache command."""
    if args.cache_action == 'clear':
        from ...cache import APICache
        cache = APICache()
        cache.clear()
        if not silent:
            logger.info("Cache cleared.")
        sys.exit(0)
    
    elif args.cache_action == 'set-ttl':
        if args.minutes <= 0:
            logger.error("TTL must be a positive integer (minutes).")
            sys.exit(1)
        
        from ...config import CacheConfig
        cache_config = CacheConfig()
        cache_config.set_ttl_minutes(args.minutes)
        if not silent:
            logger.info(f"Cache TTL set to {args.minutes} minute(s) ({args.minutes * 60} seconds).")
        sys.exit(0)
    
    elif args.cache_action == 'show-ttl':
        from ...config import CacheConfig
        from ...cache import APICache
        cache_config = CacheConfig()
        ttl_minutes = cache_config.get_ttl_minutes()
        
        if ttl_minutes is None:
            # Use default
            default_minutes = APICache.DEFAULT_TTL // 60
            if silent:
                print(f"{default_minutes}")
            else:
                logger.info(f"Cache TTL: {default_minutes} minute(s) (default)")
        else:
            if silent:
                print(f"{ttl_minutes}")
            else:
                logger.info(f"Cache TTL: {ttl_minutes} minute(s) ({ttl_minutes * 60} seconds)")
        sys.exit(0)
    
    else:
        # No subcommand, show help
        parser = argparse.ArgumentParser()
        parser.print_help()
        sys.exit(1)

