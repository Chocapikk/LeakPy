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
    console.print()


class BannerArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that displays banner before help."""
    
    def print_help(self, file=None):
        """Override print_help to show banner first."""
        # Check if --silent is in args (before parsing, we check sys.argv)
        show_banner = '--silent' not in sys.argv
        if show_banner:
            _print_banner(__version__)
        super().print_help(file)


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

  # Get complete JSON and save to file
  leakpy search -q '+country:"France"' -f full -o results.json

  # Use bulk mode (requires Pro API)
  leakpy search -q '+country:"France"' -b -o results.txt

  # Configure API key
  leakpy config set

  # Reset API key
  leakpy config reset

  # Clear cache
  leakpy cache clear

  # Display cache statistics
  leakpy stats cache

  # Display overview statistics
  leakpy stats overview

  # Analyze query statistics (by country, protocol, etc.)
  leakpy stats query -q '+country:"France"' -p 5

  # Analyze statistics from a JSON file
  leakpy stats query -f results.json

For more examples, see: https://leakpy.readthedocs.io/
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument("-v", "--version", action="version", version=f"LeakPy {__version__}")
        parser.add_argument("--silent", action="store_true", help="Suppress all output (useful for scripting)")

        # Create subparsers for commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands', metavar='COMMAND')
        
        # Import and register all command modules
        from leakpy.cli.commands import search, list as list_cmd, cache, config, stats
        
        # Register search command
        search.setup_parser(subparsers)
        
        # Register list command
        list_cmd.setup_parser(subparsers)
        
        # Register cache command
        cache.setup_parser(subparsers)
        
        # Register config command
        config.setup_parser(subparsers)
        
        # Register stats command
        stats.setup_parser(subparsers)
        
        # Register lookup command (host, domain, subdomains)
        from .cli.commands import lookup
        lookup.setup_parser(subparsers)

        args = parser.parse_args()

        # If no command provided, show help
        if not args.command:
            parser.print_help()
            sys.exit(0)

        # Detect if stdout is redirected (pipe or file redirection)
        # If stdout is redirected, we want raw output only (no logs, no progress bars)
        stdout_redirected = not sys.stdout.isatty()
        if stdout_redirected and not args.silent:
            # Auto-enable silent mode when stdout is redirected
            args.silent = True

        logger = setup_logger("LeakPy", verbose=False)
        
        # Show banner unless silent or config/cache commands
        if not args.silent and args.command in ['search', 'list', 'lookup']:
            _print_banner(__version__)

        # CLI always respects --silent flag (default is False in CLI, but True in library)
        client = LeakIX(silent=args.silent)

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
            search.execute(args, client, stdout_redirected)
        elif args.command == 'list':
            list_cmd.execute(args, client, logger, args.silent)
        elif args.command == 'cache':
            cache.execute(args, logger, args.silent)
        elif args.command == 'config':
            config.execute(args, client, logger, args.silent)
        elif args.command == 'stats':
            stats.execute(args, logger, args.silent, client)
        elif args.command == 'lookup':
            lookup.execute(args, client, stdout_redirected)
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
