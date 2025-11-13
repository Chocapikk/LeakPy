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

"""Lookup command for LeakPy CLI."""

import sys
import argparse
import json
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from datetime import datetime


def _add_common_args(parser, include_fields=False, include_limit=False):
    """Add common arguments to a parser.
    
    Args:
        parser: The parser to add arguments to
        include_fields: Whether to include the --fields argument
        include_limit: Whether to include --limit and --all arguments
    """
    parser.add_argument(
        "-i", "--input",
        help="Input file containing items (one per line) for batch processing",
        type=str
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (for batch mode, results are saved as JSON array)",
        type=str
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress all output (useful for scripting)"
    )
    if include_fields:
        parser.add_argument(
            "-f", "--fields",
            help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')",
            type=str,
            default="full"
        )
    if include_limit:
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of services/leaks to display (default: 50, use 0 for all)"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Display all services and leaks (equivalent to --limit 0)"
        )


def setup_parser(subparsers):
    """Set up the lookup command parser."""
    parser = subparsers.add_parser(
        'lookup',
        help='Lookup information about specific IPs, domains, or subdomains',
        description='Retrieve detailed information about specific IP addresses, domains, or subdomains',
        epilog="""
Examples:
  # Lookup host details
  leakpy lookup host 157.90.211.37

  # Lookup domain details
  leakpy lookup domain leakix.net

  # Lookup subdomains
  leakpy lookup subdomains leakix.net
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers_lookup = parser.add_subparsers(dest='lookup_action', help='Lookup actions', required=True)
    
    # host subcommand
    host_parser = subparsers_lookup.add_parser(
        'host',
        help='Get host details for a specific IP address',
        description='Retrieve detailed information about a specific IP address, including services and leaks',
        epilog="""
Examples:
  # Get host details for an IP
  leakpy lookup host 157.90.211.37

  # Get host details and save to file
  leakpy lookup host 157.90.211.37 -o host_details.json

  # Extract specific fields
  leakpy lookup host 157.90.211.37 -f protocol,ip,port,host

  # Batch processing from file (one IP per line)
  leakpy lookup host -i ips.txt -o results.json

  # Silent mode for scripting
  leakpy --silent lookup host 157.90.211.37 -o host.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    host_parser.add_argument(
        'ip',
        nargs='?',
        help='IP address to query (or use -i/--input for batch processing)'
    )
    _add_common_args(host_parser, include_fields=True, include_limit=True)
    
    # domain subcommand
    domain_parser = subparsers_lookup.add_parser(
        'domain',
        help='Get domain details for a specific domain name',
        description='Retrieve detailed information about a specific domain and its subdomains, including services and leaks',
        epilog="""
Examples:
  # Get domain details
  leakpy lookup domain leakix.net

  # Get domain details and save to file
  leakpy lookup domain leakix.net -o domain_details.json

  # Extract specific fields
  leakpy lookup domain leakix.net -f protocol,host,port,ip

  # Batch processing from file (one domain per line)
  leakpy lookup domain -i domains.txt -o results.json

  # Silent mode for scripting
  leakpy --silent lookup domain leakix.net -o domain.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    domain_parser.add_argument(
        'domain',
        nargs='?',
        help='Domain name to query (or use -i/--input for batch processing)'
    )
    _add_common_args(domain_parser, include_fields=True, include_limit=True)
    
    # subdomains subcommand
    subdomains_parser = subparsers_lookup.add_parser(
        'subdomains',
        help='Get subdomains for a specific domain name',
        description='Retrieve list of subdomains for a given domain',
        epilog="""
Examples:
  # Get subdomains for a domain
  leakpy lookup subdomains leakix.net

  # Get subdomains and save to file
  leakpy lookup subdomains leakix.net -o subdomains.json

  # Batch processing from file (one domain per line)
  leakpy lookup subdomains -i domains.txt -o results.json

  # Silent mode for scripting (outputs one subdomain per line)
  leakpy --silent lookup subdomains leakix.net

  # Save to file in silent mode
  leakpy --silent lookup subdomains leakix.net -o subdomains.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subdomains_parser.add_argument(
        'domain',
        nargs='?',
        help='Domain name to query (or use -i/--input for batch processing)'
    )
    _add_common_args(subdomains_parser, include_fields=False, include_limit=False)
    
    return parser


def execute(args, client, stdout_redirected):
    """Execute the lookup command."""
    if args.lookup_action == 'host':
        _execute_host(args, client, stdout_redirected)
    elif args.lookup_action == 'domain':
        _execute_domain(args, client, stdout_redirected)
    elif args.lookup_action == 'subdomains':
        _execute_subdomains(args, client, stdout_redirected)
    else:
        sys.exit(1)


def _execute_single_lookup(args, client, stdout_redirected, lookup_type):
    """Execute a single lookup (non-batch mode).
    
    Args:
        args: Parsed arguments
        client: LeakIX client instance
        stdout_redirected: Whether stdout is redirected
        lookup_type: One of 'host', 'domain', 'subdomains'
    """
    # Determine item name and value based on lookup type
    if lookup_type == 'host':
        item_name = 'ip'
        item_value = args.ip
        error_msg_both = "Error: Cannot specify both IP address and input file\n"
        error_msg_none = "Error: Either IP address or input file (-i/--input) must be provided\n"
    else:
        item_name = 'domain'
        item_value = args.domain
        error_msg_both = "Error: Cannot specify both domain and input file\n"
        error_msg_none = "Error: Either domain or input file (-i/--input) must be provided\n"
    
    # Check if batch mode (input file provided)
    if args.input:
        if not item_value:
            # Batch mode - handled by caller
            return True
        else:
            sys.stderr.write(error_msg_both)
            sys.exit(1)
    elif not item_value:
        sys.stderr.write(error_msg_none)
        sys.exit(1)
    
    # Single lookup
    output_target = sys.stdout if (stdout_redirected and not args.output) else args.output
    
    if lookup_type == 'host':
        result = client.get_host(ip=item_value, fields=args.fields, output=output_target)
        if not args.silent and not args.output and not stdout_redirected:
            _display_host_info(result, item_value)
    elif lookup_type == 'domain':
        result = client.get_domain(domain=item_value, fields=args.fields, output=output_target)
        if not args.silent and not args.output and not stdout_redirected:
            limit = 0 if args.all else args.limit
            _display_domain_info(result, item_value, limit=limit)
    elif lookup_type == 'subdomains':
        result = client.get_subdomains(domain=item_value, output=output_target)
        if not args.silent and not args.output and not stdout_redirected:
            _display_subdomains(result, item_value)
        elif args.silent and not args.output and not stdout_redirected:
            # In silent mode, output one subdomain per line
            for subdomain in result:
                print(subdomain['subdomain'])
    
    return False


def _execute_host(args, client, stdout_redirected):
    """Execute host lookup."""
    is_batch = _execute_single_lookup(args, client, stdout_redirected, 'host')
    if is_batch:
        _execute_host_batch(args, client, stdout_redirected)
    sys.exit(0)


def _execute_domain(args, client, stdout_redirected):
    """Execute domain lookup."""
    is_batch = _execute_single_lookup(args, client, stdout_redirected, 'domain')
    if is_batch:
        _execute_domain_batch(args, client, stdout_redirected)
    sys.exit(0)


def _execute_subdomains(args, client, stdout_redirected):
    """Execute subdomains lookup."""
    is_batch = _execute_single_lookup(args, client, stdout_redirected, 'subdomains')
    if is_batch:
        _execute_subdomains_batch(args, client, stdout_redirected)
    sys.exit(0)


def _extract_software_info(service):
    """Extract software information from a service object."""
    software = "N/A"
    if hasattr(service, 'service') and service.service:
        if hasattr(service.service, 'software') and service.service.software:
            software_name = getattr(service.service.software, 'name', '') or ''
            software_version = getattr(service.service.software, 'version', '') or ''
            if software_name:
                software = f"{software_name}"
                if software_version:
                    software += f" {software_version}"
            elif software_version:
                software = software_version
    return software


def _extract_http_status(service):
    """Extract HTTP status from a service object."""
    status = "N/A"
    if service.http and service.http.status:
        status = str(service.http.status)
    return status


def _extract_leak_info(leak, include_ip=False):
    """Extract leak information from a leak object.
    
    Args:
        leak: Leak object
        include_ip: Whether to include IP address in the result
    
    Returns:
        dict with keys: type, host, port, severity, size, and optionally ip
    """
    leak_type = "N/A"
    if include_ip:
        host = getattr(leak, 'resource_id', '') or getattr(leak, 'Ip', '') or "N/A"
        ip = getattr(leak, 'Ip', '') or "N/A"
    else:
        host = getattr(leak, 'resource_id', '') or "N/A"
        ip = None
    port = "N/A"
    severity = "N/A"
    dataset_size = "N/A"
    
    # Try to get leak info from events list
    if hasattr(leak, 'events') and leak.events and isinstance(leak.events, list) and len(leak.events) > 0:
        first_event = leak.events[0]
        # Check if first_event is a dict or l9event object
        if isinstance(first_event, dict):
            leak_info = first_event.get('leak', {})
            # Get type, use event_source as fallback if type is empty
            leak_type = leak_info.get('type', '') or first_event.get('event_source', '') or "N/A"
            severity = leak_info.get('severity', '') or "N/A"
            dataset_info = leak_info.get('dataset', {})
            if dataset_info and dataset_info.get('size'):
                dataset_size = str(dataset_info['size'])
            
            # Get host, IP, port from event
            host = first_event.get('host', '') or host
            if include_ip:
                ip = first_event.get('ip', '') or ip
            port = first_event.get('port', '') or port
        else:
            # first_event is an l9event object
            if hasattr(first_event, 'leak') and first_event.leak:
                leak_type = getattr(first_event.leak, 'type', '') or getattr(first_event, 'event_source', '') or "N/A"
                severity = getattr(first_event.leak, 'severity', '') or "N/A"
                if hasattr(first_event.leak, 'dataset') and first_event.leak.dataset:
                    dataset_size = str(getattr(first_event.leak.dataset, 'size', 0)) if getattr(first_event.leak.dataset, 'size', 0) else "N/A"
            
            # Get host, IP, port from event
            host = getattr(first_event, 'host', '') or host
            if include_ip:
                ip = getattr(first_event, 'ip', '') or ip
            port = str(getattr(first_event, 'port', '')) if getattr(first_event, 'port', '') else port
    
    result = {
        'type': leak_type,
        'host': host,
        'port': port,
        'severity': severity,
        'size': dataset_size
    }
    if include_ip:
        result['ip'] = ip
    return result


def _display_services_table(console, services, limit, total_count, show_ip=False):
    """Display services in a table.
    
    Args:
        console: Rich console instance
        services: List of services to display
        limit: Maximum number to show (0 for all)
        total_count: Total number of services
        show_ip: Whether to include IP column
    """
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
            software = _extract_software_info(service)
            status = _extract_http_status(service)
            
            if show_ip:
                services_table.add_row(host, protocol, port, ip, software, status)
            else:
                services_table.add_row(protocol, port, host, software, status)
        
        if limit > 0 and total_count > limit:
            console.print(f"[dim]... and {total_count - limit} more services[/dim]")
        
        console.print(services_table)
        console.print()


def _display_leaks_table(console, leaks, limit, total_count, include_ip=False):
    """Display leaks in a table.
    
    Args:
        console: Rich console instance
        leaks: List of leaks to display
        limit: Maximum number to show (0 for all)
        total_count: Total number of leaks
        include_ip: Whether to include IP column
    """
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
            leak_info = _extract_leak_info(leak, include_ip=include_ip)
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


def _display_host_info(host_info, ip, limit=50):
    """Display host information in a formatted way.
    
    Args:
        host_info: Dictionary with 'Services' and 'Leaks' keys
        ip: IP address
        limit: Maximum number of services/leaks to display (0 for all)
    """
    console = Console()
    
    # Create summary table
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    
    services_count = len(host_info['Services']) if host_info['Services'] else 0
    leaks_count = len(host_info['Leaks']) if host_info['Leaks'] else 0
    
    summary_table.add_row("IP Address", f"[bold]{ip}[/bold]")
    summary_table.add_row("Services", f"[bold green]{services_count}[/bold green]")
    summary_table.add_row("Leaks", f"[bold red]{leaks_count}[/bold red]")
    
    console.print(Panel(summary_table, title=f"[bold cyan]Host Details: {ip}[/bold cyan]", border_style="cyan"))
    console.print()
    
    _display_services_table(console, host_info.get('Services', []), limit, services_count, show_ip=False)
    _display_leaks_table(console, host_info.get('Leaks', []), limit, leaks_count, include_ip=False)
    
    if not host_info.get('Services') and not host_info.get('Leaks'):
        console.print("[dim]No information found for this IP address.[/dim]")


def _display_domain_info(domain_info, domain, limit=50):
    """Display domain information in a formatted way.
    
    Args:
        domain_info: Dictionary with 'Services' and 'Leaks' keys
        domain: Domain name
        limit: Maximum number of services/leaks to display (0 for all)
    """
    console = Console()
    
    # Create summary table
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    
    services_count = len(domain_info['Services']) if domain_info['Services'] else 0
    leaks_count = len(domain_info['Leaks']) if domain_info['Leaks'] else 0
    
    summary_table.add_row("Domain", f"[bold]{domain}[/bold]")
    summary_table.add_row("Services", f"[bold green]{services_count}[/bold green]")
    summary_table.add_row("Leaks", f"[bold red]{leaks_count}[/bold red]")
    
    console.print(Panel(summary_table, title=f"[bold cyan]Domain Details: {domain}[/bold cyan]", border_style="cyan"))
    console.print()
    
    _display_services_table(console, domain_info.get('Services', []), limit, services_count, show_ip=True)
    _display_leaks_table(console, domain_info.get('Leaks', []), limit, leaks_count, include_ip=True)
    
    if not domain_info.get('Services') and not domain_info.get('Leaks'):
        console.print("[dim]No information found for this domain.[/dim]")


def _display_subdomains(subdomains, domain):
    """Display subdomains information in a formatted way."""
    console = Console()
    
    # Create summary panel
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    
    # Deduplicate subdomains by name (keep first occurrence)
    seen = set()
    unique_subdomains = []
    for subdomain in subdomains:
        subdomain_name = subdomain.get('subdomain', '')
        if subdomain_name and subdomain_name not in seen:
            seen.add(subdomain_name)
            unique_subdomains.append(subdomain)
    
    # Update count if deduplication removed items
    if len(unique_subdomains) != len(subdomains):
        summary_table.add_row("Subdomains Found", f"[bold green]{len(unique_subdomains)}[/bold green] [dim]({len(subdomains)} before deduplication)[/dim]")
    else:
        summary_table.add_row("Subdomains Found", f"[bold green]{len(unique_subdomains)}[/bold green]")
    
    console.print(Panel(summary_table, title=f"[bold cyan]Subdomains: {domain}[/bold cyan]", border_style="cyan"))
    console.print()
    
    if unique_subdomains:
        # Display subdomains table
        subdomains_table = Table(box=box.SIMPLE)
        subdomains_table.add_column("Subdomain", style="yellow")
        subdomains_table.add_column("Distinct IPs", style="cyan", justify="right")
        subdomains_table.add_column("Last Seen", style="dim")
        
        for subdomain in unique_subdomains:
            subdomain_name = subdomain.get('subdomain', 'N/A')
            distinct_ips = subdomain.get('distinct_ips', 0)
            last_seen = subdomain.get('last_seen', 'N/A')
            
            # Format last_seen date if available
            if last_seen != 'N/A':
                try:
                    # Parse ISO format date
                    dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    last_seen = dt.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, AttributeError):
                    pass
            
            subdomains_table.add_row(subdomain_name, str(distinct_ips), last_seen)
        
        console.print(subdomains_table)
    else:
        console.print("[dim]No subdomains found for this domain.[/dim]")


def _load_input_file(file_path):
    """Load items from input file (one per line, skip empty lines and comments)."""
    from pathlib import Path
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments (lines starting with #)
            if line and not line.startswith('#'):
                items.append(line)
    
    return items


def _save_batch_results(results, output_file, stdout_redirected, silent, console, total, successful, failed):
    """Save batch results to file or stdout and display summary."""
    # Save results to output file
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        if not silent:
            console.print(f"\n[green]Results saved to {output_file}[/green]")
    elif stdout_redirected:
        # Write to stdout as JSON
        json.dump(results, sys.stdout, indent=2, default=str)
    
    # Display summary
    if not silent:
        console.print()
        console.print(Panel(
            f"[bold]Batch Processing Summary[/bold]\n"
            f"Total: {total}\n"
            f"[green]Successful: {successful}[/green]\n"
            f"[red]Failed: {failed}[/red]",
            border_style="cyan"
        ))


def _process_batch_item(func, item, item_key, args_dict, console=None, progress=None, task=None):
    """
    Process a single item in batch mode with error handling.
    
    Args:
        func: Function to call (e.g., client.get_host)
        item: The item to process (e.g., IP address or domain)
        item_key: Key name for the item in result dict (e.g., 'ip' or 'domain')
        args_dict: Dictionary of arguments to pass to func
        console: Rich console for output (optional)
        progress: Rich progress object (optional)
        task: Rich progress task (optional)
    
    Returns:
        tuple: (result_entry dict, success bool)
    """
    try:
        result = func(**args_dict)
        
        # Create result entry based on item type
        if item_key == 'ip':
            result_entry = {item_key: item, 'result': result}
        elif item_key == 'domain':
            # For subdomains, result is a list, not a dict with Services/Leaks
            if isinstance(result, list):
                # Subdomains case
                if result:
                    entries = []
                    seen_subdomains = set()  # Deduplicate by subdomain name
                    for subdomain in result:
                        subdomain_name = subdomain.get('subdomain', '')
                        if subdomain_name and subdomain_name not in seen_subdomains:
                            seen_subdomains.add(subdomain_name)
                            entries.append({
                                'domain': item,
                                'subdomain': subdomain_name,
                                'distinct_ips': subdomain.get('distinct_ips', 0),
                                'last_seen': subdomain.get('last_seen', '')
                            })
                    return entries, True
                else:
                    return [{
                        'domain': item,
                        'subdomain': None,
                        'distinct_ips': 0,
                        'last_seen': None
                    }], True
            else:
                # Domain details case
                result_entry = {item_key: item, 'result': result}
        else:
            result_entry = {item_key: item, 'result': result}
        
        return result_entry, True
        
    except Exception as e:
        if console:
            console.print(f"[red]  ✗ Error for {item}: {e}[/red]")
        return {item_key: item, 'error': str(e)}, False


def _execute_batch_lookup(args, client, stdout_redirected, lookup_type):
    """Execute batch lookups from input file.
    
    Args:
        args: Parsed arguments
        client: LeakIX client instance
        stdout_redirected: Whether stdout is redirected
        lookup_type: One of 'host', 'domain', 'subdomains'
    """
    console = Console()
    
    # Determine item type and client method
    if lookup_type == 'host':
        item_type = 'IP addresses'
        item_key = 'ip'
        client_method = client.get_host
        get_kwargs = lambda item: {'ip': item, 'fields': args.fields, 'output': None}
    elif lookup_type == 'domain':
        item_type = 'domains'
        item_key = 'domain'
        client_method = client.get_domain
        get_kwargs = lambda item: {'domain': item, 'fields': args.fields, 'output': None}
    else:  # subdomains
        item_type = 'domains'
        item_key = 'domain'
        client_method = client.get_subdomains
        get_kwargs = lambda item: {'domain': item, 'output': None}
    
    try:
        items = _load_input_file(args.input)
        if not items:
            console.print(f"[red]No {item_type} found in {args.input}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading input file: {e}[/red]")
        sys.exit(1)
    
    results = []
    successful = 0
    failed = 0
    
    # Show progress bar if not silent
    if not args.silent:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            transient=False,
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Processing {len(items)} {item_type}...",
                total=len(items)
            )
            
            for i, item in enumerate(items, 1):
                progress.update(task, description=f"[cyan]Processing {item} ({i}/{len(items)})...")
                
                result_entry, success = _process_batch_item(
                    client_method,
                    item,
                    item_key,
                    get_kwargs(item),
                    console=console,
                    progress=progress,
                    task=task
                )
                
                if isinstance(result_entry, list):
                    results.extend(result_entry)
                else:
                    results.append(result_entry)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                progress.update(task, advance=1)
    else:
        # Silent mode: no progress bar
        for item in items:
            result_entry, success = _process_batch_item(
                client_method,
                item,
                item_key,
                get_kwargs(item)
            )
            
            if isinstance(result_entry, list):
                results.extend(result_entry)
            else:
                results.append(result_entry)
            
            if success:
                successful += 1
            else:
                failed += 1
    
    _save_batch_results(results, args.output, stdout_redirected, args.silent, console, len(items), successful, failed)


def _execute_host_batch(args, client, stdout_redirected):
    """Execute batch host lookups from input file."""
    _execute_batch_lookup(args, client, stdout_redirected, 'host')


def _execute_domain_batch(args, client, stdout_redirected):
    """Execute batch domain lookups from input file."""
    _execute_batch_lookup(args, client, stdout_redirected, 'domain')


def _execute_subdomains_batch(args, client, stdout_redirected):
    """Execute batch subdomains lookups from input file."""
    _execute_batch_lookup(args, client, stdout_redirected, 'subdomains')

