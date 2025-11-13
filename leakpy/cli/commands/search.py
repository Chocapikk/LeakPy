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

"""Search command for LeakPy CLI."""

import argparse
import sys
from ..helpers import normalize_plugins


def setup_parser(subparsers):
    """Set up the search command parser."""
    parser = subparsers.add_parser(
        'search',
        help='Search LeakIX for leaks or services',
        description='Search LeakIX API and return results',
        epilog="""
Examples:
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

  # Silent mode for scripting
  leakpy search --silent -q '+country:"France"' -p 5 -o results.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-s", "--scope",
        choices=["service", "leak"],
        default="leak",
        help="Search scope: 'leak' or 'service' (default: leak)",
        type=str
    )
    parser.add_argument(
        "-p", "--pages",
        help="Number of pages to fetch (default: 2)",
        default=2,
        type=int
    )
    parser.add_argument(
        "-q", "--query",
        help="Search query string",
        default="",
        type=str
    )
    parser.add_argument(
        "-P", "--plugins",
        help="Plugin(s) to use (comma-separated)",
        type=str,
        default=None
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path",
        type=str
    )
    parser.add_argument(
        "-f", "--fields",
        help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')",
        type=str
    )
    parser.add_argument(
        "-b", "--bulk",
        action="store_true",
        help="Use bulk mode (requires Pro API)"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress all output (useful for scripting)"
    )
    
    return parser


def execute(args, client, stdout_redirected):
    """Execute the search command."""
    # Normalize plugins parameter
    normalized_plugins = normalize_plugins(args.plugins)
    plugin_str = normalized_plugins if isinstance(normalized_plugins, str) else (",".join(normalized_plugins) if normalized_plugins else "")
    
    # If stdout is redirected and no output file specified, write raw output to stdout
    if stdout_redirected and not args.output:
        # Pass sys.stdout as output file to write raw results
        client.search(
            scope=args.scope,
            pages=args.pages,
            query=args.query,
            plugin=plugin_str,
            fields=args.fields,
            use_bulk=args.bulk,
            output=sys.stdout,  # Write to stdout instead of a file
        )
    else:
        client.search(
            scope=args.scope,
            pages=args.pages,
            query=args.query,
            plugin=plugin_str,
            fields=args.fields,
            use_bulk=args.bulk,
            output=args.output,
        )

