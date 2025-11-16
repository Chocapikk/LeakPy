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
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from ..cache import APICache
from .field_utils import get_field_value
from .cache_utils import get_cache_stats
from .data_utils import has_counts
from .file_operations import load_results_from_file
from .decorators import handle_exceptions


def display_search_results(results, fields=None):
    """Display search results in a formatted table."""
    if not results:
        return
    
    console = Console()
    
    def _extract_from_url(url_str):
        """Extract protocol, ip, port from URL string."""
        if not url_str:
            return None, None, None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url_str)
            protocol = parsed.scheme
            host = parsed.hostname
            port = parsed.port or (443 if protocol == 'https' else 80 if protocol == 'http' else None)
            return protocol, host, port
        except:
            return None, None, None
    
    def _get_protocol(r):
        """Get protocol from event, or extract from URL if available."""
        protocol = getattr(r, 'protocol', None)
        if protocol:
            return protocol
        url = getattr(r, 'url', None)
        if url:
            protocol, _, _ = _extract_from_url(url)
            return protocol or 'N/A'
        return 'N/A'
    
    def _get_ip(r):
        """Get IP from event, or extract from URL if available."""
        ip = getattr(r, 'ip', None)
        if ip:
            return ip
        url = getattr(r, 'url', None)
        if url:
            _, ip, _ = _extract_from_url(url)
            return ip or 'N/A'
        return 'N/A'
    
    def _get_port(r):
        """Get port from event, or extract from URL if available."""
        port = getattr(r, 'port', None)
        if port:
            return str(port)
        url = getattr(r, 'url', None)
        if url:
            _, _, port = _extract_from_url(url)
            return str(port) if port else 'N/A'
        return 'N/A'
    
    # Field definitions: (field_name, column_title, style, width, justify, getter_func)
    FIELD_DEFS = {
        "url": ("URL", "cyan", 60, None, lambda r: getattr(r, 'url', None) or 'N/A'),
        "protocol": ("Protocol", "cyan", 8, None, _get_protocol),
        "ip": ("IP", "yellow", 16, None, _get_ip),
        "port": ("Port", "white", 6, "right", _get_port),
        "host": ("Host", "green", 40, None, lambda r: getattr(r, 'host', 'N/A') or 'N/A'),
    }
    
    # Determine which fields to display
    if fields and fields != "full":
        field_list = [f.strip() for f in fields.split(',')]
        # If fields are "protocol,ip,port" (or similar) but we have URL, prefer URL
        if field_list == ["protocol", "ip", "port"] or (len(field_list) == 3 and "protocol" in field_list and "ip" in field_list and "port" in field_list):
            # Check if results have URL instead of separate fields
            if results and hasattr(results[0], 'url') and results[0].url:
                # If URL exists, show URL instead of protocol, ip, port
                field_list = ["url"]
    else:
        # Default: show url if available, otherwise protocol, ip, port
        field_list = ["url"] if hasattr(results[0], 'url') and results[0].url else ["protocol", "ip", "port", "host"]
    
    # Create table
    results_table = Table(box=box.SIMPLE)
    
    # Add columns based on available fields
    for field in field_list:
        if field in FIELD_DEFS:
            title, style, width, justify, _ = FIELD_DEFS[field]
            kwargs = {"style": style, "width": width}
            if justify:
                kwargs["justify"] = justify
            results_table.add_column(title, **kwargs)
    
    # Add rows
    for result in results:
        row = []
        for field in field_list:
            if field in FIELD_DEFS:
                _, _, _, _, getter = FIELD_DEFS[field]
                row.append(getter(result))
        results_table.add_row(*row)
    
    console.print(results_table)


# ============================================================================
# FORMATTING UTILITIES
# ============================================================================

def format_size(size_bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_duration(seconds):
    """Format seconds to human readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def create_cache_bar(value, max_value, width=50):
    """Create a visual bar for cache statistics."""
    if max_value == 0:
        percentage = 0
    else:
        percentage = min(100, (value / max_value) * 100)
    
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage:.1f}%"


# ============================================================================
# STATS DISPLAY FUNCTIONS
# ============================================================================

def _get_age_bucket(age_minutes):
    """Get age bucket name for given age in minutes."""
    buckets = [(5, '0-5 min'), (15, '5-15 min'), (30, '15-30 min'), (60, '30-60 min')]
    return next((label for threshold, label in buckets if age_minutes < threshold), '1h+')


def display_cache_stats(args, logger):
    """Display cache statistics with visualizations."""
    stats = get_cache_stats()
    console = Console()
    
    if args.raw or args.silent:
        print(f"total_entries:{stats['total_entries']}")
        print(f"active_entries:{stats['active_entries']}")
        print(f"ttl_minutes:{stats['ttl_minutes']}")
        print(f"cache_file_size:{stats['cache_file_size']}")
        return
    
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan", width=25)
    stats_table.add_column(style="white")
    
    stats_table.add_row("Total entries", f"[bold]{stats['total_entries']}[/bold]")
    stats_table.add_row("Active entries", f"[bold green]{stats['active_entries']}[/bold green]")
    
    ttl_display = f"{stats['ttl_minutes']} minutes"
    ttl_display += f" (configured: {stats['configured_ttl_minutes']} min)" if stats['configured_ttl_minutes'] else " (default)"
    stats_table.add_row("TTL", ttl_display)
    stats_table.add_row("Cache file size", format_size(stats['cache_file_size']))
    stats_table.add_row("Cache file path", stats['cache_file_path'])
    
    if stats['active_entries'] > 0:
        if stats['oldest_entry_age'] > 0:
            stats_table.add_row("Oldest entry", format_duration(stats['oldest_entry_age']))
        if stats['newest_entry_age'] > 0:
            stats_table.add_row("Newest entry", format_duration(stats['newest_entry_age']))
    
    # Add age distribution info to table if there are multiple entries
    if stats['total_entries'] > 1 and stats['oldest_entry_age'] > 0:
        age_buckets = {'0-5 min': 0, '5-15 min': 0, '15-30 min': 0, '30-60 min': 0, '1h+': 0}
        cache = APICache()
        current_time = time.time()
        
        for entry in cache._cache.values():
            entry_age = current_time - entry['timestamp']
            entry_ttl = entry.get('ttl', cache.ttl)
            if entry_age <= entry_ttl:
                age_buckets[_get_age_bucket(entry_age / 60)] += 1
        
        # Show age distribution as percentages in table
        age_distribution = []
        for bucket_name, count in age_buckets.items():
            if count > 0:
                percentage = (count / stats['total_entries']) * 100
                age_distribution.append(f"{bucket_name}: {percentage:.1f}%")
        
        if age_distribution:
            stats_table.add_row("Age distribution", ", ".join(age_distribution))
    
    console.print(Panel(stats_table, title="[bold cyan]Cache Statistics[/bold cyan]", border_style="cyan"))


@handle_exceptions(default_return='')
def _get_country_flag(country_name):
    """Get country flag emoji from country name using emoji-country-flag library."""
    if not country_name:
        return ''
    
    import pycountry
    import flag as flag_lib
    
    country_aliases = {'USA': 'US', 'United States of America': 'US', 'UK': 'GB', 'United Kingdom': 'GB'}
    
    if len(country_name) == 2 and country_name.isalpha():
        code = country_name.upper()
    elif country_name in country_aliases:
        code = country_aliases[country_name]
    else:
        country = pycountry.countries.get(name=country_name) or pycountry.countries.search_fuzzy(country_name)[0]
        code = country.alpha_2.upper()
    
    return flag_lib.flag(code) if code and len(code) == 2 else ''


def _format_label(value, field_name, field_path, city_country_map):
    """Format label for statistics table."""
    value_str = str(value)
    is_country = field_path == "geoip.country_name" or (field_name == "geoip" and "country" in field_path.lower())
    is_city = field_path == "geoip.city_name" or (field_name == "geoip" and "city" in field_path.lower())
    
    if is_country:
        flag = _get_country_flag(value_str)
        return f"{flag} {value_str}" if flag else value_str
    if is_city:
        if city_country_map and value in city_country_map:
            country = city_country_map[value]
            flag = _get_country_flag(country)
            return f"{flag} {value_str} ({country})" if flag else f"{value_str} ({country})"
        return value_str
    if field_name == 'port' and isinstance(value, str) and value.isdigit():
        return f"Port {value}"
    
    label = value_str
    return label[:47] + "..." if len(label) > 50 else label


def _format_display_name(field_name):
    """Format field name for display."""
    display_name = field_name.replace('_', ' ').title()
    if '.' in display_name:
        parts = display_name.split('.')
        return f"{parts[0].title()}: {' '.join(parts[1:]).title()}"
    return display_name


@handle_exceptions(default_return=None, exception_types=(ValueError, SyntaxError))
def _parse_list_value(value):
    """Try to parse string as list representation."""
    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        import ast
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else None
    return None


def _print_raw_stats(stats_result, top):
    """Print raw statistics output."""
    print(f"total:{stats_result.total}")
    stats_dict = stats_result.to_dict()
    _sort_key = lambda x: x[1] if isinstance(x[1], (int, float)) else 0
    
    for field_name, field_stats in stats_dict['fields'].items():
        is_nested = isinstance(field_stats, dict) and all(isinstance(v, dict) for v in field_stats.values() if v)
        if is_nested:
            for sub_field, sub_stats in field_stats.items():
                if not sub_stats or not isinstance(sub_stats, dict) or not has_counts(sub_stats):
                    continue
                for value, count in sorted(sub_stats.items(), key=_sort_key, reverse=True)[:top]:
                    print(f"{field_name}.{sub_field}:{value}:{count}")
        else:
            for value, count in sorted(field_stats.items(), key=_sort_key, reverse=True)[:top]:
                print(f"{field_name}:{value}:{count}")


def _display_nested_stats(console, field_name, field_stats, top, total, stats_dict, city_country_map):
    """Display statistics for nested field structure."""
    _sort_key = lambda x: x[1] if isinstance(x[1], (int, float)) else 0
    
    for sub_field, sub_stats in sorted(field_stats.items()):
        if not sub_stats or not isinstance(sub_stats, dict) or not has_counts(sub_stats):
            continue
        
        sorted_items = sorted(sub_stats.items(), key=_sort_key, reverse=True)[:top]
        if not sorted_items:
            continue
        
        display_name = f"{field_name.replace('_', ' ').title()}: {sub_field.replace('_', ' ').title()}"
        console.print(f"[bold]{display_name}[/bold]")
        max_count = sorted_items[0][1] if isinstance(sorted_items[0][1], (int, float)) else 1
        _display_stats_table(console, sorted_items, max_count, field_name, total, stats_dict, f"{field_name}.{sub_field}", city_country_map)


def _display_simple_stats(console, field_name, field_stats, top, total, stats_dict, city_country_map):
    """Display statistics for simple field structure."""
    _sort_key = lambda x: x[1] if isinstance(x[1], (int, float)) else 0
    
    sorted_items = sorted(field_stats.items(), key=_sort_key, reverse=True)[:top]
    if not sorted_items:
        return
    
    console.print(f"[bold]{_format_display_name(field_name)}[/bold]")
    max_count = sorted_items[0][1] if isinstance(sorted_items[0][1], (int, float)) else 1
    _display_stats_table(console, sorted_items, max_count, field_name, total, stats_dict, field_name, city_country_map)


def _display_stats_table(console, sorted_items, max_count, field_name="", total_results=0, stats_dict=None, field_path="", city_country_map=None):
    """Display statistics table for a list of items."""
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column("Label", style="yellow", no_wrap=False, min_width=1)
    stats_table.add_column("Count", style="white", justify="right", width=6, no_wrap=True)
    stats_table.add_column("Percentage", style="dim", justify="right", width=10, no_wrap=True)
    
    for value, count in sorted_items:
        if not isinstance(count, (int, float)):
            continue
        
        percentage = (count / total_results * 100) if total_results > 0 else 0
        
        if parsed_list := _parse_list_value(value):
            for item in parsed_list:
                stats_table.add_row(str(item), str(count), f"({percentage:5.1f}%)")
            continue
        
        label = _format_label(value, field_name, field_path, city_country_map)
        stats_table.add_row(label, str(count), f"({percentage:5.1f}%)")
    
    console.print(stats_table)
    console.print()


def _load_query_results(args, logger, client):
    """Load results from file or API."""
    import sys
    
    def _error_and_exit(logger, message):
        logger.error(message)
        sys.exit(1)
    
    if args.file:
        results = load_results_from_file(args.file)
        if not results:
            _error_and_exit(logger, f"Error loading file: {args.file}")
        if not args.silent:
            logger.info(f"Loaded {len(results)} results from {args.file}")
        return results
    
    if not client:
        _error_and_exit(logger, "Either --file or a query must be provided")
    
    # Validate bulk mode: only works with scope="leak"
    if args.bulk and args.scope == "service":
        _error_and_exit(logger, "Bulk mode is only available for scope='leak', not 'service'")
    
    results = client.search(scope=args.scope, pages=args.pages, query=args.query, fields="full", use_bulk=args.bulk)
    
    # Show progress bar when loading from API (not in raw/silent mode and stdout is a TTY)
    if not args.raw and not args.silent and sys.stdout.isatty():
        from .progress import consume_stream_with_progress
        results_list, interrupted = consume_stream_with_progress(results, args, "Streaming results for statistics")
        return results_list
    
    return list(results) if not isinstance(results, list) else results


def display_query_stats(args, logger, client=None):
    """Display query statistics."""
    console = Console()
    
    results = _load_query_results(args, logger, client)
    if not results:
        logger.warning("No results to analyze")
        sys.exit(0)
    
    from ..stats import analyze_query_results
    stats_result = analyze_query_results(results, args.fields, args.all_fields)
    
    city_country_map = {}
    if not args.raw and not args.silent:
        for result in results:
            city = get_field_value(result, 'geoip.city_name')
            country = get_field_value(result, 'geoip.country_name')
            if city and country:
                if city not in city_country_map:
                    city_country_map[city] = country
    
    if args.raw or args.silent:
        _print_raw_stats(stats_result, args.top)
        return
    
    console.print(Panel(f"[bold cyan]Query Statistics[/bold cyan]\n[dim]Total results: {stats_result.total}[/dim]", border_style="cyan"))
    console.print()
    
    stats_dict = stats_result.to_dict()
    _sort_key = lambda x: x[1] if isinstance(x[1], (int, float)) else 0
    
    for field_name, field_stats in sorted(stats_dict['fields'].items()):
        if not field_stats:
            continue
        
        is_nested = isinstance(field_stats, dict) and all(isinstance(v, dict) for v in field_stats.values() if v)
        if is_nested:
            _display_nested_stats(console, field_name, field_stats, args.top, stats_result.total, stats_dict, city_country_map)
        else:
            _display_simple_stats(console, field_name, field_stats, args.top, stats_result.total, stats_dict, city_country_map)
