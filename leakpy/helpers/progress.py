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
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


def _get_event_key(event):
    """Generate a unique key for an event to identify duplicates.
    
    Uses URL if available, otherwise uses protocol+ip+port combination.
    This allows deduplication of clearly identical events.
    """
    # First try URL (most reliable identifier)
    url = getattr(event, 'url', None)
    if url:
        return ('url', url)
    
    # Otherwise use protocol + ip + port combination
    protocol = getattr(event, 'protocol', None) or ''
    ip = getattr(event, 'ip', None) or ''
    port = getattr(event, 'port', None)
    port_str = str(port) if port is not None else ''
    
    # If we have at least protocol and ip, use that as key
    if protocol and ip:
        return ('protocol_ip_port', (protocol, ip, port_str))
    
    # Fallback: use host if available
    host = getattr(event, 'host', None)
    if host:
        return ('host', host)
    
    # Last resort: return None to indicate we can't create a unique key
    return None


def consume_stream_with_progress(results, args, description_prefix="Streaming results"):
    """
    Consume a generator stream with progress bar and return results list.
    
    Args:
        results: Generator that yields events
        args: Arguments object with bulk, pages attributes
        description_prefix: Prefix for progress bar description (default: "Streaming results")
    
    Returns:
        tuple: (list of events, bool indicating if interrupted)
    """
    console = Console(file=sys.stderr)
    results_list = []
    unique_events = set()  # Track unique events for deduplication
    unique_urls = set()  # Track unique URLs separately for display
    
    # Determine progress bar configuration based on mode
    if args.bulk:
        initial_desc = f"[cyan]{description_prefix}..."
        events_per_page = None
    elif args.pages > 1:
        initial_desc = f"[cyan]{description_prefix} (0 events, page 1/{args.pages})..."
        events_per_page = 20  # For page estimation only
    else:
        initial_desc = f"[cyan]{description_prefix}..."
        events_per_page = None
    
    # Common progress bar setup - simplified description
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=False,
        console=console,
    ) as progress:
        task = progress.add_task(initial_desc, total=None)
        
        event_count = 0
        start_time = time.time()
        interrupted = False
        
        try:
            for event in results:
                results_list.append(event)
                event_count += 1
                
                # Track unique events using same logic as display
                event_key = _get_event_key(event)
                if event_key is not None:
                    unique_events.add(event_key)
                
                # Track unique URLs separately for display
                url = getattr(event, 'url', None)
                if url:
                    unique_urls.add(url)
                
                current_time = time.time()
                elapsed = current_time - start_time
                rate = event_count / elapsed if elapsed > 0 else 0
                
                # Build description based on mode
                # Show unique events count (and unique URLs if available)
                unique_count = len(unique_events)
                if unique_urls:
                    unique_url_count = len(unique_urls)
                    if args.bulk:
                        desc = f"[cyan]{description_prefix}... [yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)"
                    elif args.pages > 1:
                        estimated_page = min((event_count - 1) // events_per_page + 1, args.pages)
                        desc = f"[cyan]{description_prefix} ([yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique ({unique_url_count} URLs), page {estimated_page}/{args.pages}) - {rate:.1f} events/s"
                    else:
                        desc = f"[cyan]{description_prefix}... [yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)"
                else:
                    if args.bulk:
                        desc = f"[cyan]{description_prefix}... [yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique ({rate:.1f} events/s)"
                    elif args.pages > 1:
                        estimated_page = min((event_count - 1) // events_per_page + 1, args.pages)
                        desc = f"[cyan]{description_prefix} ([yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique, page {estimated_page}/{args.pages}) - {rate:.1f} events/s"
                    else:
                        desc = f"[cyan]{description_prefix}... [yellow]{event_count}[/yellow] events, [green]{unique_count}[/green] unique ({rate:.1f} events/s)"
                
                # Update progress bar at each streamed event
                progress.update(task, advance=1, description=desc)
        except KeyboardInterrupt:
            interrupted = True
            # Close the generator to stop fetching more data
            if hasattr(results, 'close'):
                try:
                    results.close()
                except:
                    pass
            
            # Calculate final stats
            elapsed = time.time() - start_time
            rate = event_count / elapsed if elapsed > 0 else 0
            
            # Stop the progress bar and remove it (transient)
            progress.stop()
            
            # Print a simple message on a new line
            unique_count = len(unique_events)
            unique_url_count = len(unique_urls)
            if unique_urls:
                if args.bulk:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)")
                elif args.pages > 1:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique ({unique_url_count} URLs) from {args.pages} pages ({rate:.1f} events/s)")
                else:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)")
            else:
                if args.bulk:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique ({rate:.1f} events/s)")
                elif args.pages > 1:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique from {args.pages} pages ({rate:.1f} events/s)")
                else:
                    console.print(f"[yellow]⚠ Interrupted - {event_count} events collected, [green]{unique_count}[/green] unique ({rate:.1f} events/s)")
        
        # Final update (only if not interrupted, as interrupted case is handled above)
        if not interrupted:
            elapsed = time.time() - start_time
            rate = event_count / elapsed if elapsed > 0 else 0
            unique_count = len(unique_events)
            unique_url_count = len(unique_urls)
            if unique_urls:
                if args.bulk:
                    final_desc = f"[green]✓ Completed - {event_count} events streamed, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)"
                elif args.pages > 1:
                    final_desc = f"[green]✓ Completed - {event_count} events streamed, [green]{unique_count}[/green] unique ({unique_url_count} URLs) from {args.pages} pages ({rate:.1f} events/s)"
                else:
                    final_desc = f"[green]✓ Completed - {event_count} events, [green]{unique_count}[/green] unique ({unique_url_count} URLs) ({rate:.1f} events/s)"
            else:
                if args.bulk:
                    final_desc = f"[green]✓ Completed - {event_count} events streamed, [green]{unique_count}[/green] unique ({rate:.1f} events/s)"
                elif args.pages > 1:
                    final_desc = f"[green]✓ Completed - {event_count} events streamed, [green]{unique_count}[/green] unique from {args.pages} pages ({rate:.1f} events/s)"
                else:
                    final_desc = f"[green]✓ Completed - {event_count} events, [green]{unique_count}[/green] unique ({rate:.1f} events/s)"
            progress.update(task, description=final_desc)
    
    return results_list, interrupted

