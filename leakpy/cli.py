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
from .cli.helpers import (
    _extract_sample_event,
    handle_list_fields,
    handle_list_plugins,
    normalize_plugins,
)
from .logger import setup_logger
from .scraper import LeakIXScraper

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


def _print_banner(version):
    """Print ASCII art banner to stderr with colors."""
    # Cloud art with LeakPy text integrated in the middle
    banner = f"""
    ⠀⠀⠀⠀⠀⠀⠀⠀⣀⡤⠴⠢⠤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⡔⣝⢏⠁⠀⠀⠀⢀⣉⣀⣀⡀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⠤⢉⡩⠟⣓⡿⠁⠀⠀⡖⠁⠀⠀⠀⠀⠀⠉⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⡠⣒⢯⢕⣫⡯⠗⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡗⡆⠀⠀⠀⠀⠀⠀
 ⠉⡜⢛⣿⡇⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡄⠀⠀⠀⠀⠀
  ⠈⠉⠉⠁⠉⠛⠛⠉⠉⠉⠉⠁⠉⠁⠁⠁⠉⠉⠉⠒⠉⠉⠉⠉⠉

                        (v{version})

 __            _   _____     
|  |   ___ ___| |_|  _  |_ _ 
|  |__| -_| .'| '_|   __| | |
|_____|___|__,|_,_|__|  |_  |
                        |___|

[rgb(255,165,0)]Coded by[/rgb(255,165,0)] [bold rgb(0,191,255)]Chocapikk[/bold rgb(0,191,255)] [rgb(255,165,0)]|[/rgb(255,165,0)] [bold rgb(135,206,250)]Non-official[/bold rgb(135,206,250)] [bold rgb(50,205,50)]LeakIX[/bold rgb(50,205,50)] [rgb(255,165,0)]API client[/rgb(255,165,0)]

"""
    
    if RICH_AVAILABLE:
        console = Console(file=sys.stderr, force_terminal=True)
        lines = banner.split('\n')
        for line in lines:
            # Lines with rich markers
            if '[bold rgb' in line or '[rgb' in line:
                console.print(line, markup=True)
                continue
            # LeakPy ASCII art lines
            if any(char in line for char in ['|', '_']) and ('__' in line or '|' in line):
                console.print(line, style="rgb(255,165,0) bold")
                continue
            # Cloud lines (default)
            console.print(line, style="white")
    else:
        # Fallback: strip rich markers if rich is not available
        import re
        banner_no_markers = re.sub(r'\[/?[^\]]+\]', '', banner)
        print(banner_no_markers, file=sys.stderr, end='')


def main():
    try:
        parser = argparse.ArgumentParser(
            description="LeakPy - LeakIX API Client",
            epilog="""
Examples:
  # List available plugins
  leakpy --list-plugins

  # Search for leaks in France
  leakpy -q '+country:"France"' -p 5

  # Search with specific plugin
  leakpy -q '+country:"France"' -P PulseConnectPlugin -p 3

  # Extract specific fields
  leakpy -q '+country:"France"' -f protocol,ip,port,host

  # Get complete JSON and save to file
  leakpy -q '+country:"France"' -f full -o results.json

  # Use bulk mode (requires Pro API)
  leakpy -q '+country:"France"' -b -o results.txt

  # Silent mode for scripting
  leakpy --silent -q '+country:"France"' -p 5 -o results.txt

For more examples, see: https://leakpy.readthedocs.io/
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument("-s", "--scope", choices=["service", "leak"], default="leak", help="Search scope: 'leak' or 'service' (default: leak)", type=str)
        parser.add_argument("-p", "--pages", help="Number of pages to fetch (default: 2)", default=2, type=int)
        parser.add_argument("-q", "--query", help="Search query string", default="", type=str)
        parser.add_argument("-P", "--plugins", help="Plugin(s) to use (comma-separated)", type=str, default=None)
        parser.add_argument("-o", "--output", help="Output file path", type=str)
        parser.add_argument("-f", "--fields", help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')", type=str)
        parser.add_argument("-b", "--bulk", action="store_true", help="Use bulk mode (requires Pro API)")
        parser.add_argument("-r", "--reset-api", action="store_true", help="Reset saved API key")
        parser.add_argument("--clear-cache", action="store_true", help="Clear the API response cache")
        parser.add_argument("-lp", "--list-plugins", action="store_true", help="List available plugins")
        parser.add_argument("-lf", "--list-fields", action="store_true", help="List all possible fields from sample data")
        parser.add_argument("-v", "--version", action="version", version=f"LeakPy {__version__}")
        parser.add_argument("--silent", action="store_true", help="Suppress all output (useful for scripting)")

        args = parser.parse_args()

        # Set verbose based on silent flag
        verbose = not args.silent
        logger = setup_logger("LeakPy", verbose=verbose)
        silent = args.silent
        
        if not silent:
            _print_banner(__version__)

        scraper = LeakIXScraper(verbose=verbose, silent=silent)

        if not scraper.has_api_key():
            if silent:
                sys.exit(1)
            session = PromptSession()
            logger.warning("API key is missing. Please enter your API key to continue.")
            api_key = session.prompt(
                HTML("<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> "),
                is_password=True,
            ).strip()
            scraper.save_api_key(api_key)

            if not scraper.has_api_key():
                logger.error("The provided API key is invalid. It must be 48 characters long.")
                sys.exit(1)

        if args.reset_api:
            scraper.delete_api_key()
            if not silent:
                logger.info("API key has been reset.")
            sys.exit(0)
        
        if args.clear_cache:
            from .cache import APICache
            cache = APICache()
            cache.clear()
            if not silent:
                logger.info("Cache cleared.")
            sys.exit(0)

        if args.list_plugins:
            if silent:
                for plugin in scraper.get_plugins():
                    print(plugin)
            else:
                handle_list_plugins(logger, scraper)
            sys.exit(0)

        if args.list_fields:
            if silent:
                sample_data = scraper.query(args.scope, 1, args.query, args.plugins, None, False, return_data_only=True)
                sample_event = _extract_sample_event(sample_data)
                if sample_event:
                    for field in scraper.get_all_fields(sample_event):
                        print(field)
            else:
                if not handle_list_fields(logger, scraper, args.scope, args.query, args.plugins):
                    sys.exit(1)
            sys.exit(0)

        # Normalize plugins parameter before passing to scraper.run()
        normalized_plugins = normalize_plugins(args.plugins)
        scraper.run(
            args.scope,
            args.pages,
            args.query,
            normalized_plugins,
            args.output,
            args.fields,
            args.bulk,
        )

    except Exception as e:
        error_message = traceback.format_exc()
        if not silent:
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
