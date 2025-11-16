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


# ============================================================================
# TABLE UTILITIES (DRY)
# ============================================================================

def get_terminal_width(console=None, default=80):
    """Get terminal width with fallback to default.
    
    Args:
        console: Optional Console instance. If None, creates a new one.
        default: Default width if terminal width cannot be determined.
    
    Returns:
        int: Terminal width or default value.
    """
    if console is None:
        console = Console()
    try:
        return console.width or default
    except:
        return default


def create_simple_table():
    """Create a simple table with borders."""
    return Table(box=box.SIMPLE)


def create_borderless_table(show_header=False):
    """Create a borderless table with standard padding."""
    return Table(show_header=show_header, box=None, padding=(0, 2))


def create_multi_column_table(items, column_width, style="yellow", header=None):
    """Create a multi-column table filled column by column (top to bottom).
    
    Args:
        items: List of items to display
        column_width: Width of each column
        style: Style for columns
        header: Optional header text for first column
    
    Returns:
        Table: Configured table with columns and rows filled
    """
    console = Console()
    terminal_width = get_terminal_width(console)
    available_width = terminal_width
    num_columns = max(1, available_width // column_width)
    
    table = Table(show_header=header is not None, box=None)
    if header:
        table.add_column(header, style="bold cyan", width=column_width)
        for i in range(num_columns - 1):
            table.add_column("", style="white", width=column_width)
    else:
        for i in range(num_columns):
            table.add_column("", style=style, no_wrap=False, min_width=column_width)
    
    # Fill column by column (alphabetical order top to bottom)
    num_rows = (len(items) + num_columns - 1) // num_columns
    for row_idx in range(num_rows):
        row_items = []
        for col_idx in range(num_columns):
            item_idx = row_idx + col_idx * num_rows
            if item_idx < len(items):
                row_items.append(items[item_idx])
            else:
                row_items.append("")
        table.add_row(*row_items)
    
    return table


def display_search_results(results, fields=None):
    """Display search results in a formatted table."""
    if not results:
        return
    
    console = Console()
    
    @handle_exceptions(default_return=(None, None, None))
    def _extract_from_url(url_str):
        """Extract protocol, ip, port from URL string."""
        if not url_str:
            return None, None, None
        from urllib.parse import urlparse
        parsed = urlparse(url_str)
        protocol = parsed.scheme
        host = parsed.hostname
        port = parsed.port or (443 if protocol == 'https' else 80 if protocol == 'http' else None)
        return protocol, host, port
    
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
    
    def _has_url(r):
        """Check if result has a valid URL (already constructed by our code)."""
        url = getattr(r, 'url', None)
        return bool(url)  # Return True if URL exists and is not empty/None
    
    def _get_event_key(r):
        """Generate a unique key for an event to identify duplicates.
        
        Uses URL if available, otherwise uses protocol+ip+port combination.
        This allows deduplication of clearly identical events.
        """
        # First try URL (most reliable identifier)
        url = getattr(r, 'url', None)
        if url:
            return ('url', url)
        
        # Otherwise use protocol + ip + port combination
        protocol = getattr(r, 'protocol', None) or ''
        ip = getattr(r, 'ip', None) or ''
        port = getattr(r, 'port', None)
        port_str = str(port) if port is not None else ''
        
        # If we have at least protocol and ip, use that as key
        if protocol and ip:
            return ('protocol_ip_port', (protocol, ip, port_str))
        
        # Fallback: use host if available
        host = getattr(r, 'host', None)
        if host:
            return ('host', host)
        
        # Last resort: return None to indicate we can't create a unique key
        return None
    
    def _get_generic_field(r, field_name):
        """Get a generic field value from result."""
        # Use the same logic as get_field_value for consistency
        # Handle nested fields (e.g., "geoip.country_name" or "geoip.location.lat")
        parts = field_name.split('.')
        value = r
        
        for part in parts:
            if value is None:
                return 'N/A'
            # Handle both dicts and objects
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
        
        if value is None:
            return 'N/A'
        # Handle list/array values (like tags)
        if isinstance(value, list):
            return ', '.join(str(v) for v in value) if value else 'N/A'
        # Handle dict values (for nested objects)
        if isinstance(value, dict):
            return str(value)  # Or could format it better
        return str(value)
    
    def _field_name_to_title(field_name):
        """Convert field name to title case for column header."""
        # Handle nested fields - take the last part
        if '.' in field_name:
            field_name = field_name.split('.')[-1]
        # Convert snake_case to Title Case
        return field_name.replace('_', ' ').title()
    
    # Field definitions: (field_name, column_title, style, width, justify, getter_func)
    # Color scheme: LeakIX (orange/blue) + Python (yellow)
    # yellow=identifiers (IP, Host), cyan=network info (URL, Protocol), white=values, rgb(255,165,0)=tags/metadata
    FIELD_DEFS = {
        "url": ("URL", "cyan", 60, None, lambda r: getattr(r, 'url', None) or 'N/A'),
        "protocol": ("Protocol", "cyan", 8, None, _get_protocol),
        "ip": ("IP", "yellow", 16, None, _get_ip),
        "port": ("Port", "white", 6, "right", _get_port),
        "host": ("Host", "yellow", 40, None, lambda r: getattr(r, 'host', 'N/A') or 'N/A'),
        "tags": ("Tags", "rgb(255,165,0)", 50, None, lambda r: _get_generic_field(r, 'tags')),
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
        else:
            # Generic field not in FIELD_DEFS - add it dynamically with default styling
            title = _field_name_to_title(field)
            results_table.add_column(title, style="white", width=30)
    
    # Track unique events for deduplication
    seen_events = set()
    
    # Add rows
    for result in results:
        # If URL column is displayed, skip rows without a valid URL
        # (URL is already constructed by our code if protocol is http/https and we have ip/port)
        if "url" in field_list:
            if not _has_url(result):
                continue
        
        # Deduplicate events - only show first occurrence of each unique event
        event_key = _get_event_key(result)
        if event_key is not None:
            if event_key in seen_events:
                continue
            seen_events.add(event_key)
        
        row = []
        for field in field_list:
            if field in FIELD_DEFS:
                _, _, _, _, getter = FIELD_DEFS[field]
                row.append(getter(result))
            else:
                # Generic field - use generic getter
                row.append(_get_generic_field(result, field))
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
    
    stats_table = create_borderless_table(show_header=False)
    stats_table.add_column(style="yellow", width=25)
    stats_table.add_column(style="cyan")
    
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
    
    # Don't truncate long values like event_fingerprint - let Rich Table handle wrapping
    # The table column has no_wrap=False and max_width=None, so it will wrap automatically
    return value_str


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
    stats_table = create_borderless_table(show_header=False)
    # Allow wrapping for long values like event_fingerprint, but set a reasonable max width
    # Rich will wrap automatically if no_wrap=False, but we can set max_width to prevent extremely long lines
    stats_table.add_column("Label", style="yellow", no_wrap=False, min_width=1, max_width=None)
    stats_table.add_column("Count", style="cyan", justify="right", width=6, no_wrap=True)
    stats_table.add_column("Percentage", style="dim", justify="right", width=10, no_wrap=True)
    
    # Calculate total counts for this field (sum of all counts)
    # This is needed for fields that are lists (like transport) where counts can exceed total_results
    total_counts = sum(count for _, count in sorted_items if isinstance(count, (int, float)))
    # Use total_counts if it's greater than total_results (indicates list field), otherwise use total_results
    percentage_base = max(total_counts, total_results) if total_counts > total_results else total_results
    
    for value, count in sorted_items:
        if not isinstance(count, (int, float)):
            continue
        
        percentage = (count / percentage_base * 100) if percentage_base > 0 else 0
        
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


# ============================================================================
# LIST COMMANDS DISPLAY FUNCTIONS
# ============================================================================

def _is_output_redirected():
    """Check if stdout is redirected (not a TTY)."""
    return not sys.stdout.isatty()


def _display_items_simple(items):
    """Display items in simple format (one per line) when output is redirected."""
    for item in sorted(items):
        print(item)


def _display_plugins_table(plugins):
    """Display plugins in a Rich table with multiple columns based on terminal width."""
    console = Console()
    sorted_plugins = sorted(plugins)
    plugin_count = len(sorted_plugins)
    
    # Print title separately above the table
    console.print(f"[bold cyan]Plugin Name ({plugin_count} available)[/bold cyan]")
    console.print()
    
    # Find the longest plugin name to determine column width
    max_plugin_length = max(len(p) for p in sorted_plugins) if sorted_plugins else 20
    column_width = max_plugin_length + 2  # +2 for padding
    
    # Create table with multiple columns (no header in table)
    table = create_multi_column_table(
        sorted_plugins,
        column_width,
        style="white"
    )
    console.print(table)


def handle_list_plugins(logger, scraper):
    """Helper function to list plugins."""
    plugins = scraper.get_plugins()
    if not plugins:
        logger.error("Failed to list plugins.")
        return False
    
    if _is_output_redirected():
        _display_items_simple(plugins)
    else:
        _display_plugins_table(plugins)
    
    return True


def _categorize_fields(fields):
    """Group fields by their top-level category prefix."""
    categories = {}
    root_fields = []
    
    for field in fields:
        if '.' in field:
            prefix = field.split('.')[0]
            categories.setdefault(prefix, []).append(field)
        else:
            root_fields.append(field)
    
    return root_fields, sorted(categories.items())


def _format_field_suffix(field, category):
    """Format field suffix by removing category prefix and formatting nested parts."""
    suffix = field[len(category) + 1:]
    if '.' in suffix:
        return " → ".join(suffix.split('.'))
    return suffix


def format_fields_display(fields, show_count=True):
    """Format fields for better display using rich, similar to stats display.
    
    Args:
        fields: List of field names to display
        show_count: If True, display the count of fields in the header
    """
    if not fields:
        return
    
    if _is_output_redirected():
        _display_items_simple(fields)
        return
    
    console = Console()
    
    # Display count if requested
    if show_count:
        field_count = len(fields)
        console.print(f"[bold]Available fields: {field_count}[/bold]")
        console.print()
    
    root_fields, sorted_categories = _categorize_fields(fields)
    
    # Calculate terminal width for multi-column layout
    terminal_width = get_terminal_width(console)
    
    # Display root fields if any (multiple columns to optimize space)
    if root_fields:
        console.print("[bold]Root Fields[/bold]")
        sorted_root = sorted(root_fields)
        
        # Calculate column width
        max_field_length = max(len(f) for f in sorted_root) if sorted_root else 20
        column_width = max_field_length + 2
        
        root_table = create_multi_column_table(sorted_root, column_width, style="yellow")
        console.print(root_table)
        console.print()
    
    # Display categorized fields: categories side by side (multiple columns)
    if not sorted_categories:
        return
    
    # Prepare all categories with their fields
    all_categories = []
    for category, cat_fields in sorted_categories:
        sorted_cat = sorted(cat_fields)
        formatted_fields = [_format_field_suffix(field, category) for field in sorted_cat]
        all_categories.append({
            'name': category.replace('_', ' ').title(),
            'fields': formatted_fields
        })
    
    # Calculate column width based on longest category name and longest field
    max_category_name_length = max(len(cat['name']) for cat in all_categories) if all_categories else 20
    max_field_length = max(
        max(len(f) for f in cat['fields']) if cat['fields'] else 0
        for cat in all_categories
    ) if all_categories else 20
    column_width = max(max_category_name_length, max_field_length) + 2
    
    # Create table with category columns (special case: categories with fields underneath)
    # We can't use create_multi_column_table here because we need special formatting
    console = Console()
    terminal_width = get_terminal_width(console)
    available_width = terminal_width
    num_category_columns = max(1, available_width // column_width)
    
    categories_table = create_borderless_table(show_header=False)
    for i in range(num_category_columns):
        categories_table.add_column("", style="yellow", no_wrap=False, min_width=column_width)
    
    # Fill categories column by column, with fields listed vertically under each category
    num_category_rows = (len(all_categories) + num_category_columns - 1) // num_category_columns
    max_fields_per_category = max(len(cat['fields']) for cat in all_categories) if all_categories else 0
    
    # For each row of categories
    for cat_row_idx in range(num_category_rows):
        # Get categories for this row
        row_categories = []
        for col_idx in range(num_category_columns):
            cat_idx = cat_row_idx + col_idx * num_category_rows
            if cat_idx < len(all_categories):
                row_categories.append(all_categories[cat_idx])
            else:
                row_categories.append(None)
        
        # Calculate max number of rows needed for fields in this category row
        max_fields_in_row = max(
            len(cat['fields']) if cat else 0
            for cat in row_categories
        )
        
        # For each field row
        for field_row_idx in range(max_fields_in_row + 1):  # +1 for category name
            row_cells = []
            for cat in row_categories:
                if cat is None:
                    row_cells.append("")
                elif field_row_idx == 0:
                    # First row: category name
                    row_cells.append(f"[bold]{cat['name']}[/bold]")
                elif field_row_idx - 1 < len(cat['fields']):
                    # Field rows
                    row_cells.append(cat['fields'][field_row_idx - 1])
                else:
                    # Empty cell for this category
                    row_cells.append("")
            categories_table.add_row(*row_cells)
        
        # Add empty row between category groups for spacing
        if cat_row_idx < num_category_rows - 1:
            categories_table.add_row(*[""] * num_category_columns)
    
    console.print(categories_table)


def handle_list_fields(logger, scraper, scope="leak", query="", plugins=None):
    """Helper function to list fields using the l9format library schema.
    
    This function now uses the official l9format library to get the complete
    list of available fields without needing to fetch sample data from the API.
    """
    from leakpy.helpers import get_all_fields_from_l9format_schema
    
    # Get fields directly from l9format schema
    fields = get_all_fields_from_l9format_schema()
    
    if not fields:
        logger.error("Couldn't extract fields from l9format schema. Make sure l9format is installed.")
        return False
    
    format_fields_display(fields, show_count=True)
    return True


def normalize_plugins(plugins):
    """Normalize plugins parameter (string or list) to a list."""
    if plugins is None:
        return None
    if isinstance(plugins, str):
        return [p.strip() for p in plugins.split(",") if p.strip()]
    return plugins
