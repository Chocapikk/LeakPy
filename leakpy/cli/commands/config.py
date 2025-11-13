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

"""Config command for LeakPy CLI."""

import sys
import argparse
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML


def setup_parser(subparsers):
    """Set up the config command parser."""
    parser = subparsers.add_parser(
        'config',
        help='Manage API key configuration',
        description='Configure or manage your LeakIX API key'
    )
    
    subparsers_config = parser.add_subparsers(dest='config_action', help='Config actions')
    
    # reset subcommand
    reset_parser = subparsers_config.add_parser(
        'reset',
        help='Reset/delete saved API key',
        description='Delete the stored API key',
        epilog="""
Examples:
  # Reset/delete saved API key
  leakpy config reset
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # set subcommand
    set_parser = subparsers_config.add_parser(
        'set',
        help='Set API key',
        description='Set or update your API key',
        epilog="""
Examples:
  # Set API key interactively (will prompt for input)
  leakpy config set

  # Set API key directly from command line
  leakpy config set your_48_character_api_key_here
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    set_parser.add_argument(
        'api_key',
        nargs='?',
        help='API key (48 characters). If not provided, will prompt interactively.',
        type=str
    )
    
    return parser


def execute(args, client, logger, silent):
    """Execute the config command."""
    if args.config_action == 'reset':
        client.delete_api_key()
        if not silent:
            logger.info("API key has been reset.")
        sys.exit(0)
    
    elif args.config_action == 'set':
        if args.api_key:
            api_key = args.api_key.strip()
        else:
            if silent:
                logger.error("API key is required in silent mode. Use: leakpy config set <api_key>")
                sys.exit(1)
            session = PromptSession()
            logger.warning("Please enter your API key:")
            api_key = session.prompt(
                HTML("<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> "),
                is_password=True,
            ).strip()
        
        client.save_api_key(api_key)
        
        if not client.has_api_key():
            logger.error("The provided API key is invalid. It must be 48 characters long.")
            sys.exit(1)
        
        if not silent:
            logger.info("API key has been saved successfully.")
        sys.exit(0)
    
    else:
        # No subcommand, show help
        parser = argparse.ArgumentParser()
        parser.print_help()
        sys.exit(1)

