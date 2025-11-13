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

"""Stats command for LeakPy CLI."""

import sys
import argparse
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.bar import Bar
from rich.columns import Columns


def setup_parser(subparsers):
    """Set up the stats command parser."""
    parser = subparsers.add_parser(
        'stats',
        help='Display statistics and metrics',
        description='Display various statistics and metrics with visualizations'
    )
    
    subparsers_stats = parser.add_subparsers(dest='stats_action', required=True)
    
    # cache subcommand
    cache_parser = subparsers_stats.add_parser(
        'cache',
        help='Display cache statistics',
        description='Show cache statistics with visualizations',
        epilog="""
Examples:
  # Display cache statistics
  leakpy stats cache

  # Display cache stats in silent mode (for scripting)
  leakpy --silent stats cache
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # overview subcommand
    overview_parser = subparsers_stats.add_parser(
        'overview',
        help='Display overview statistics',
        description='Show an overview of all statistics',
        epilog="""
Examples:
  # Display overview statistics
  leakpy stats overview
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # query subcommand
    query_parser = subparsers_stats.add_parser(
        'query',
        help='Display query statistics',
        description='Analyze and display statistics from search queries (by country, protocol, port, etc.)'
    )
    query_parser.add_argument(
        '-f', '--file',
        type=str,
        help='JSON file containing query results to analyze'
    )
    query_parser.add_argument(
        '-q', '--query',
        type=str,
        default='',
        help='Query string to search (if no file provided)'
    )
    query_parser.add_argument(
        '-p', '--pages',
        type=int,
        default=2,
        help='Number of pages to fetch (default: 2)'
    )
    query_parser.add_argument(
        '-s', '--scope',
        choices=['service', 'leak'],
        default='leak',
        help='Search scope (default: leak)'
    )
    query_parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top items to display (default: 10)'
    )
    query_parser.add_argument(
        '--fields',
        type=str,
        help='Comma-separated list of fields to analyze (e.g. "country,protocol,port"). If not specified, analyzes all common fields.'
    )
    query_parser.add_argument(
        '--all-fields',
        action='store_true',
        help='Analyze all available fields in the results'
    )
    query_parser.epilog = """
Examples:
  # Analyze query statistics from a live query
  leakpy stats query -q '+country:"France"' -p 5

  # Analyze statistics from a JSON file
  leakpy stats query -f results.json

  # Analyze specific fields only
  leakpy stats query -f results.json --fields "geoip.country_name,protocol,port"

  # Analyze all available fields
  leakpy stats query -f results.json --all-fields

  # Show top 15 items instead of default 10
  leakpy stats query -f results.json --top 15

  # Analyze in silent mode (for scripting)
  leakpy --silent stats query -f results.json
    """
    query_parser.formatter_class = argparse.RawDescriptionHelpFormatter
    
    return parser


def _get_cache_stats():
    """Get cache statistics."""
    from ...cache import APICache
    from ...config import CacheConfig
    
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


def _format_size(size_bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def _format_duration(seconds):
    """Format seconds to human readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def _create_cache_bar(value, max_value, width=50):
    """Create a visual bar for cache statistics."""
    if max_value == 0:
        percentage = 0
    else:
        percentage = min(100, (value / max_value) * 100)
    
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage:.1f}%"


def display_cache_stats(logger, silent):
    """Display cache statistics with visualizations."""
    stats = _get_cache_stats()
    console = Console()
    
    if silent:
        # Output raw data for scripting
        print(f"total_entries:{stats['total_entries']}")
        print(f"active_entries:{stats['active_entries']}")
        print(f"expired_entries:{stats['expired_entries']}")
        print(f"ttl_minutes:{stats['ttl_minutes']}")
        print(f"cache_file_size:{stats['cache_file_size']}")
        return
    
    # Main statistics panel
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan", width=25)
    stats_table.add_column(style="white")
    
    stats_table.add_row("Total entries", f"[bold]{stats['total_entries']}[/bold]")
    stats_table.add_row("Active entries", f"[bold green]{stats['active_entries']}[/bold green]")
    stats_table.add_row("Expired entries", f"[bold red]{stats['expired_entries']}[/bold red]")
    
    ttl_display = f"{stats['ttl_minutes']} minutes"
    if stats['configured_ttl_minutes']:
        ttl_display += f" (configured: {stats['configured_ttl_minutes']} min)"
    else:
        ttl_display += " (default)"
    stats_table.add_row("TTL", ttl_display)
    stats_table.add_row("Cache file size", _format_size(stats['cache_file_size']))
    stats_table.add_row("Cache file path", stats['cache_file_path'])
    
    if stats['active_entries'] > 0:
        if stats['oldest_entry_age'] > 0:
            stats_table.add_row("Oldest entry", _format_duration(stats['oldest_entry_age']))
        if stats['newest_entry_age'] > 0:
            stats_table.add_row("Newest entry", _format_duration(stats['newest_entry_age']))
    
    console.print(Panel(stats_table, title="[bold cyan]Cache Statistics[/bold cyan]", border_style="cyan"))
    
    # Visual bars
    if stats['total_entries'] > 0:
        console.print()
        console.print("[bold]Entry Status Distribution[/bold]")
        
        # Active vs Expired bar
        max_entries = max(stats['active_entries'], stats['expired_entries'], 1)
        active_bar = _create_cache_bar(stats['active_entries'], max_entries)
        expired_bar = _create_cache_bar(stats['expired_entries'], max_entries)
        
        console.print(f"  [green]Active:[/green]   {active_bar}")
        console.print(f"  [red]Expired:[/red]   {expired_bar}")
        
        # Age distribution if we have active entries
        if stats['active_entries'] > 0 and stats['oldest_entry_age'] > 0:
            console.print()
            console.print("[bold]Entry Age Distribution[/bold]")
            
            # Create age buckets
            age_buckets = {
                '0-5 min': 0,
                '5-15 min': 0,
                '15-30 min': 0,
                '30-60 min': 0,
                '1h+': 0
            }
            
            from ...cache import APICache
            cache = APICache()
            current_time = time.time()
            
            for entry in cache._cache.values():
                entry_age = current_time - entry['timestamp']
                entry_ttl = entry.get('ttl', cache.ttl)
                
                if entry_age <= entry_ttl:  # Only count active entries
                    age_minutes = entry_age / 60
                    if age_minutes < 5:
                        age_buckets['0-5 min'] += 1
                    elif age_minutes < 15:
                        age_buckets['5-15 min'] += 1
                    elif age_minutes < 30:
                        age_buckets['15-30 min'] += 1
                    elif age_minutes < 60:
                        age_buckets['30-60 min'] += 1
                    else:
                        age_buckets['1h+'] += 1
            
            max_bucket = max(age_buckets.values()) if age_buckets.values() else 1
            for bucket_name, count in age_buckets.items():
                if count > 0:
                    bar = _create_cache_bar(count, max_bucket)
                    console.print(f"  {bucket_name:12} {bar}")


def display_overview(logger, silent):
    """Display overview statistics."""
    cache_stats = _get_cache_stats()
    console = Console()
    
    if silent:
        # Output raw data
        display_cache_stats(logger, True)
        return
    
    # Display cache stats
    display_cache_stats(logger, False)
    
    console.print()
    
    # Summary panel
    summary_text = Text()
    summary_text.append("LeakPy Statistics Overview\n\n", style="bold cyan")
    summary_text.append(f"Cache: ", style="cyan")
    summary_text.append(f"{cache_stats['total_entries']} entries", style="white")
    summary_text.append(f" ({_format_size(cache_stats['cache_file_size'])})", style="dim")
    summary_text.append("\n")
    summary_text.append(f"TTL: ", style="cyan")
    summary_text.append(f"{cache_stats['ttl_minutes']} minutes", style="white")
    
    console.print(Panel(summary_text, title="[bold]Summary[/bold]", border_style="blue"))


def _load_results_from_file(file_path):
    """Load results from a JSON file."""
    import json
    from pathlib import Path
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'events' in data:
            return data['events']
        elif 'results' in data:
            return data['results']
        else:
            # Try to find a list in the dict
            for key, value in data.items():
                if isinstance(value, list):
                    return value
    return []


# Import shared stats functions
from ...stats import get_field_value as _get_field_value, flatten_dict as _flatten_dict, analyze_query_results as _analyze_query_results


def _get_all_fields_from_result(result):
    """Get all field paths from a result."""
    if isinstance(result, dict):
        return list(_flatten_dict(result).keys())
    else:
        # For l9event objects, we'll use common fields
        # In a real scenario, you might want to introspect the object
        return []


def _display_stat_bar(label, value, max_value, width=40):
    """Create a visual bar for statistics."""
    if max_value == 0:
        percentage = 0
    else:
        percentage = (value / max_value) * 100
    
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{label:20} {bar} {value:6} ({percentage:5.1f}%)"


def display_query_stats(args, logger, silent, client=None):
    """Display query statistics."""
    console = Console()
    
    # Load results
    if args.file:
        try:
            results = _load_results_from_file(args.file)
            if not silent:
                logger.info(f"Loaded {len(results)} results from {args.file}")
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            sys.exit(1)
    elif client:
        # Make a new query
        results = client.search(
            scope=args.scope,
            pages=args.pages,
            query=args.query,
            fields="full"
        )
        # Convert to list if needed
        if not isinstance(results, list):
            results = list(results)
    else:
        logger.error("Either --file or a query must be provided")
        sys.exit(1)
    
    if not results:
        logger.warning("No results to analyze")
        sys.exit(0)
    
    # Analyze results
    stats = _analyze_query_results(results, args.fields, args.all_fields)
    
    if silent:
        # Output raw data
        print(f"total:{stats.total}")
        # Convert to dict for iteration
        stats_dict = stats.to_dict()
        for field_name, field_stats in stats_dict['fields'].items():
            sorted_items = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)[:args.top]
            for value, count in sorted_items:
                print(f"{field_name}:{value}:{count}")
        return
    
    # Display statistics with visualizations
    console.print(Panel(f"[bold cyan]Query Statistics[/bold cyan]\n[dim]Total results: {stats.total}[/dim]", border_style="cyan"))
    console.print()
    
    # Convert to dict for iteration
    stats_dict = stats.to_dict()
    # Display stats for each field
    for field_name, field_stats in sorted(stats_dict['fields'].items()):
        if not field_stats:
            continue
        
        # Format field name for display
        display_name = field_name.replace('_', ' ').title()
        if '.' in display_name:
            # Handle nested fields like "geoip.country_name" -> "GeoIP: Country Name"
            parts = display_name.split('.')
            display_name = f"{parts[0].title()}: {' '.join(parts[1:]).title()}"
        
        console.print(f"[bold]{display_name}[/bold]")
        sorted_items = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)[:args.top]
        max_count = sorted_items[0][1] if sorted_items else 1
        
        for value, count in sorted_items:
            # Try to format port numbers nicely
            if field_name == 'port' and value.isdigit():
                label = f"Port {value}"
            else:
                label = str(value)
            
            console.print(_display_stat_bar(label, count, max_count))
        console.print()


def execute(args, logger, silent, client=None):
    """Execute the stats command."""
    if args.stats_action == 'cache':
        display_cache_stats(logger, silent)
        sys.exit(0)
    
    elif args.stats_action == 'overview':
        display_overview(logger, silent)
        sys.exit(0)
    
    elif args.stats_action == 'query':
        # Need client if querying and not using file
        if not args.file and not client:
            from ...leakix import LeakIX
            client = LeakIX(silent=silent)
            if not client.has_api_key():
                logger.error("API key is required for query statistics. Use 'leakpy config set' to set it.")
                sys.exit(1)
        
        display_query_stats(args, logger, silent, client)
        sys.exit(0)
    
    else:
        parser = argparse.ArgumentParser()
        parser.print_help()
        sys.exit(1)

