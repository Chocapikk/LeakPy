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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from .file_operations import load_lines_from_file
from .constants import _LOOKUP_ERROR_BOTH_IP, _LOOKUP_ERROR_NONE_IP, _LOOKUP_ERROR_BOTH_DOMAIN, _LOOKUP_ERROR_NONE_DOMAIN
from .batch import save_batch_results, process_subdomains_result
from .service_leak import extract_software_info, extract_http_status, extract_leak_info
from datetime import datetime

# ============================================================================
# LOOKUP COMMAND UTILITIES
# ============================================================================

def add_common_lookup_args(parser, include_fields=False, include_limit=False):
    """Add common arguments to a lookup parser."""
    parser.add_argument("-i", "--input", help="Input file containing items (one per line) for batch processing", type=str)
    parser.add_argument("-o", "--output", help="Output file path (for batch mode, results are saved as JSON array)", type=str)
    # --raw is now in create_common_parser() and inherited by all subparsers
    if include_fields:
        parser.add_argument("-f", "--fields", help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')", type=str, default="full")
    if include_limit:
        parser.add_argument("--limit", type=int, default=50, help="Maximum number of services/leaks to display (default: 50, use 0 for all)")
        parser.add_argument("--all", action="store_true", help="Display all services and leaks (equivalent to --limit 0)")


def execute_single_lookup(args, client, stdout_redirected, lookup_type):
    """Execute a single lookup (non-batch mode)."""
    _LOOKUP_METHODS = {
        'host': (getattr(args, 'ip', None), _LOOKUP_ERROR_BOTH_IP, _LOOKUP_ERROR_NONE_IP, client.get_host, 'ip', display_host_info),
        'domain': (getattr(args, 'domain', None), _LOOKUP_ERROR_BOTH_DOMAIN, _LOOKUP_ERROR_NONE_DOMAIN, client.get_domain, 'domain', lambda r, v: display_domain_info(r, v, limit=0 if args.all else args.limit)),
        'subdomains': (getattr(args, 'domain', None), _LOOKUP_ERROR_BOTH_DOMAIN, _LOOKUP_ERROR_NONE_DOMAIN, client.get_subdomains, 'domain', display_subdomains)
    }
    item_value, error_both, error_none, client_method, item_key, display_func = _LOOKUP_METHODS[lookup_type]
    
    if args.input and not item_value:
        return True
    if args.input and item_value:
        sys.stderr.write(error_both)
        sys.exit(1)
    if not item_value:
        sys.stderr.write(error_none)
        sys.exit(1)
    
    # args.raw and args.silent are guaranteed to be defined in main() before calling helpers
    is_raw = args.raw
    is_silent = args.silent
    # In raw or silent mode, output raw JSON to stdout
    # Otherwise, use stdout only if redirected and no output file specified
    if args.output:
        output_target = args.output
    elif is_raw or is_silent:
        # In raw or silent mode, output raw JSON to stdout
        output_target = sys.stdout
    elif stdout_redirected:
        # If stdout is redirected, output raw JSON to stdout
        output_target = sys.stdout
    else:
        output_target = None
    
    kwargs = {item_key: item_value, 'output': output_target}
    if lookup_type != 'subdomains':
        kwargs['fields'] = args.fields
    result = client_method(**kwargs)
    
    handle_lookup_display(result, args, stdout_redirected, lookup_type, item_value, display_func)
    return False


def handle_lookup_display(result, args, stdout_redirected, lookup_type, item_value, display_func):
    """Handle display logic based on mode."""
    # args.raw and args.silent are guaranteed to be defined in main() before calling helpers
    is_raw = args.raw
    is_silent = args.silent
    # In raw or silent mode, don't display formatted output (data is already written to output if specified)
    if is_raw or is_silent:
        return
    # If output file is specified, data is already written, just display formatted view if TTY
    if args.output:
        if not stdout_redirected:
            display_func(result, item_value)
    # If stdout is redirected, data is already written via output=sys.stdout, nothing to display
    elif stdout_redirected:
        pass  # Data already written to stdout via output parameter
    # Normal TTY mode: display formatted view
    else:
        display_func(result, item_value)


def execute_batch_lookup(args, client, stdout_redirected, lookup_type):
    """Execute batch lookups from input file."""
    _BATCH_METHODS = {
        'host': ('IP addresses', 'ip', client.get_host, lambda item: {'ip': item, 'fields': args.fields, 'output': None}),
        'domain': ('domains', 'domain', client.get_domain, lambda item: {'domain': item, 'fields': args.fields, 'output': None}),
        'subdomains': ('domains', 'domain', client.get_subdomains, lambda item: {'domain': item, 'output': None})
    }
    item_type, item_key, client_method, get_kwargs = _BATCH_METHODS[lookup_type]
    console = Console()
    items = load_batch_lookup_items(args.input, item_type, console)
    results, successful, failed = [], 0, 0
    
    def _process_item(item):
        # args.raw and args.silent are guaranteed to be defined in main() before calling helpers
        is_silent = args.raw or args.silent
        result_entry, success = process_batch_lookup_item(client_method, item, item_key, get_kwargs(item), console=console if not is_silent else None)
        if isinstance(result_entry, list):
            results.extend(result_entry)
        else:
            results.append(result_entry)
        if success:
            nonlocal successful
            successful += 1
        else:
            nonlocal failed
            failed += 1
    
    # args.raw and args.silent are guaranteed to be defined in main() before calling helpers
    is_silent = args.raw or args.silent
    process_batch_lookup_items(items, _process_item, is_silent, item_type, console)
    save_batch_results(results, args.output, stdout_redirected, is_silent, console, len(items), successful, failed)


def load_batch_lookup_items(input_file, item_type, console):
    """Load items from input file with error handling."""
    try:
        items = load_lines_from_file(input_file)
        if not items:
            console.print(f"[red]No {item_type} found in {input_file}[/red]")
            sys.exit(1)
        return items
    except Exception as e:
        console.print(f"[red]Error loading input file: {e}[/red]")
        sys.exit(1)


def process_batch_lookup_items(items, process_func, silent, item_type, console):
    """Process batch items with or without progress bar."""
    if silent:
        for item in items:
            process_func(item)
        return
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), transient=False, console=console) as progress:
        task = progress.add_task(f"[cyan]Processing {len(items)} {item_type}...", total=len(items))
        for i, item in enumerate(items, 1):
            progress.update(task, description=f"[cyan]Processing {item} ({i}/{len(items)})...")
            process_func(item)
            progress.update(task, advance=1)


def process_batch_lookup_item(func, item, item_key, args_dict, console=None):
    """Process a single item in batch mode with error handling."""
    try:
        result = func(**args_dict)
        if item_key == 'domain' and isinstance(result, list):
            return process_subdomains_result(result, item), True
        return {item_key: item, 'result': result}, True
    except Exception as e:
        if console:
            console.print(f"[red]  ✗ Error for {item}: {e}[/red]")
        return {item_key: item, 'error': str(e)}, False


def display_host_info(host_info, ip, limit=50):
    """Display host information in a formatted way."""
    display_lookup_info(host_info, ip, "Host Details", "IP Address", limit, show_ip=False, no_info_msg="[dim]No information found for this IP address.[/dim]")


def display_domain_info(domain_info, domain, limit=50):
    """Display domain information in a formatted way."""
    display_lookup_info(domain_info, domain, "Domain Details", "Domain", limit, show_ip=True, no_info_msg="[dim]No information found for this domain.[/dim]")


def _create_summary_table():
    """Create a standard summary table for lookup info."""
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    return summary_table


def display_subdomains(subdomains, domain):
    """Display subdomains information in a formatted way."""
    console = Console()
    if not subdomains:
        subdomains = []
    
    summary_table = _create_summary_table()
    count_display = f"[bold green]{len(subdomains)}[/bold green]"
    summary_table.add_row("Subdomains Found", count_display)
    
    console.print(Panel(summary_table, title=f"[bold cyan]Subdomains: {domain}[/bold cyan]", border_style="cyan"))
    console.print()
    
    if subdomains:
        subdomains_table = Table(box=box.SIMPLE)
        subdomains_table.add_column("Subdomain", style="yellow")
        subdomains_table.add_column("Distinct IPs", style="cyan", justify="right")
        subdomains_table.add_column("Last Seen", style="dim")
        
        for subdomain in subdomains:
            if not subdomain:
                continue
            # Handle both dict and DotNotationObject
            if isinstance(subdomain, dict):
                subdomain_name = subdomain.get('subdomain', 'N/A')
                distinct_ips = subdomain.get('distinct_ips', 0)
                last_seen = subdomain.get('last_seen', 'N/A')
            else:
                # DotNotationObject - use attribute access
                subdomain_name = getattr(subdomain, 'subdomain', 'N/A') or 'N/A'
                distinct_ips = getattr(subdomain, 'distinct_ips', 0) or 0
                last_seen = getattr(subdomain, 'last_seen', 'N/A') or 'N/A'
            # Format ISO date to readable format
            if last_seen != 'N/A':
                try:
                    last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, AttributeError):
                    pass  # Keep original value on error
            subdomains_table.add_row(subdomain_name, str(distinct_ips), last_seen)
        
        console.print(subdomains_table)
    else:
        console.print("[dim]No subdomains found for this domain.[/dim]")


def display_lookup_info(info, item_value, title, item_name, limit=50, show_ip=False, no_info_msg=None):
    """Display host or domain information in a formatted way."""
    console = Console()
    services_count = len(info.services) if info.services else 0
    leaks_count = len(info.leaks) if info.leaks else 0
    display_lookup_info_summary(console, title, item_name, item_value, services_count, leaks_count)
    display_lookup_services_table(console, info.services or [], limit, services_count, show_ip=show_ip)
    display_lookup_leaks_table(console, info.leaks or [], limit, leaks_count, include_ip=show_ip)
    if not info.services and not info.leaks and no_info_msg:
        console.print(no_info_msg)


def display_lookup_info_summary(console, title, item_name, item_value, services_count, leaks_count):
    """Display summary table for host or domain info."""
    summary_table = _create_summary_table()
    summary_table.add_row(item_name, f"[bold]{item_value}[/bold]")
    summary_table.add_row("Services", f"[bold green]{services_count}[/bold green]")
    summary_table.add_row("Leaks", f"[bold red]{leaks_count}[/bold red]")
    console.print(Panel(summary_table, title=f"[bold cyan]{title}: {item_value}[/bold cyan]", border_style="cyan"))
    console.print()


def display_lookup_services_table(console, services, limit, total_count, show_ip=False):
    """Display services in a table."""
    if not services:
        return
    
    services_to_show = services if limit == 0 else services[:limit]
    
    if services_to_show:
        console.print("[bold]Services:[/bold]")
        services_table = Table(box=box.SIMPLE)
        
        if show_ip:
            services_table.add_column("Host", style="yellow")
            services_table.add_column("Protocol", style="cyan")
            services_table.add_column("Port", style="white")
            services_table.add_column("IP", style="dim")
        else:
            services_table.add_column("Protocol", style="cyan")
            services_table.add_column("Port", style="white")
            services_table.add_column("Host", style="yellow")
        
        services_table.add_column("Software", style="magenta")
        services_table.add_column("Status", style="green")
        
        for service in services_to_show:
            protocol = service.protocol or "N/A"
            port = str(service.port) if service.port else "N/A"
            host = service.host or "N/A"
            ip = service.ip or "N/A" if show_ip else None
            software = extract_software_info(service)
            status = extract_http_status(service)
            
            if show_ip:
                services_table.add_row(host, protocol, port, ip, software, status)
            else:
                services_table.add_row(protocol, port, host, software, status)
        
        if limit > 0 and total_count > limit:
            console.print(f"[dim]... and {total_count - limit} more services[/dim]")
        
        console.print(services_table)
        console.print()


def display_lookup_leaks_table(console, leaks, limit, total_count, include_ip=False):
    """Display leaks in a table."""
    if not leaks:
        return
    
    leaks_to_show = leaks if limit == 0 else leaks[:limit]
    
    if leaks_to_show:
        console.print("[bold]Leaks:[/bold]")
        leaks_table = Table(box=box.SIMPLE)
        leaks_table.add_column("Type", style="red")
        leaks_table.add_column("Host", style="yellow")
        if include_ip:
            leaks_table.add_column("IP", style="cyan")
        leaks_table.add_column("Port", style="white")
        leaks_table.add_column("Severity", style="yellow")
        leaks_table.add_column("Size", style="white", justify="right")
        
        for leak in leaks_to_show:
            leak_info = extract_leak_info(leak, include_ip=include_ip)
            if include_ip:
                leaks_table.add_row(
                    leak_info['type'], leak_info['host'], leak_info['ip'],
                    leak_info['port'], leak_info['severity'], leak_info['size']
                )
            else:
                leaks_table.add_row(
                    leak_info['type'], leak_info['host'], leak_info['port'],
                    leak_info['severity'], leak_info['size']
                )
        
        if limit > 0 and total_count > limit:
            console.print(f"[dim]... and {total_count - limit} more leaks[/dim]")
        
        console.print(leaks_table)

