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

"""List command for LeakPy CLI."""

import sys
import argparse
from ..helpers import handle_list_plugins, handle_list_fields, _extract_sample_event


def setup_parser(subparsers):
    """Set up the list command parser."""
    parser = subparsers.add_parser(
        'list',
        help='List available plugins or fields',
        description='List available plugins or fields from LeakIX'
    )
    
    subparsers_list = parser.add_subparsers(dest='list_action', help='List actions', required=True)
    
    # plugins subcommand
    plugins_parser = subparsers_list.add_parser(
        'plugins',
        help='List available plugins',
        description='List all available LeakIX plugins',
        epilog="""
Examples:
  # List all available plugins
  leakpy list plugins

  # List plugins in silent mode (for scripting)
  leakpy --silent list plugins
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    plugins_parser.add_argument(
        '--silent',
        action='store_true',
        help='Output only plugin names (one per line)'
    )
    
    # fields subcommand
    fields_parser = subparsers_list.add_parser(
        'fields',
        help='List available fields',
        description='List all available fields from a sample query',
        epilog="""
Examples:
  # List all available fields
  leakpy list fields

  # List fields from a specific query
  leakpy list fields -q '+country:"France"'

  # List fields from service scope
  leakpy list fields -s service -q 'port:3306'

  # List fields with specific plugin
  leakpy list fields -P PulseConnectPlugin

  # List fields in silent mode (for scripting)
  leakpy --silent list fields -q '+country:"France"'
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    fields_parser.add_argument(
        "-s", "--scope",
        choices=["service", "leak"],
        default="leak",
        help="Search scope: 'leak' or 'service' (default: leak)",
        type=str
    )
    fields_parser.add_argument(
        "-q", "--query",
        help="Query string to fetch sample data",
        default="",
        type=str
    )
    fields_parser.add_argument(
        "-P", "--plugins",
        help="Plugin(s) to use (comma-separated)",
        type=str,
        default=None
    )
    fields_parser.add_argument(
        '--silent',
        action='store_true',
        help='Output only field names (one per line)'
    )
    
    return parser


def execute(args, client, logger, silent):
    """Execute the list command."""
    if args.list_action == 'plugins':
        if args.silent or silent:
            for plugin in client.get_plugins():
                print(plugin)
        else:
            handle_list_plugins(logger, client)
        sys.exit(0)
    
    elif args.list_action == 'fields':
        from ..helpers import normalize_plugins
        normalized_plugins = normalize_plugins(args.plugins)
        
        if args.silent or silent:
            sample_data = client.query(args.scope, 1, args.query, normalized_plugins, None, False, return_data_only=True)
            sample_event = _extract_sample_event(sample_data)
            if sample_event:
                for field in client.get_all_fields(sample_event):
                    print(field)
        else:
            if not handle_list_fields(logger, client, args.scope, args.query, normalized_plugins):
                sys.exit(1)
        sys.exit(0)
    
    else:
        parser = argparse.ArgumentParser()
        parser.print_help()
        sys.exit(1)

