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

import json
import sys
from rich.panel import Panel
from .constants import _ENCODING_UTF8
from .decorators import handle_file_errors

# ============================================================================
# BATCH PROCESSING UTILITIES
# ============================================================================

def process_subdomains_result(result, item):
    """Process subdomains result list.
    
    Args:
        result: List of subdomain dictionaries
        item: Domain name
    
    Returns:
        list: List of processed subdomain entries
    """
    if not result:
        return [{'domain': item, 'subdomain': None, 'distinct_ips': 0, 'last_seen': None}]
    return [{'domain': item, 'subdomain': sd.get('subdomain', ''), 'distinct_ips': sd.get('distinct_ips', 0), 'last_seen': sd.get('last_seen', '')} for sd in result if sd and isinstance(sd, dict)]


@handle_file_errors()
def save_batch_results(results, output_file, stdout_redirected, silent, console, total, successful, failed):
    """Save batch results to file or stdout and display summary.
    
    Args:
        results: List of results to save
        output_file: Path to output file (None if stdout)
        stdout_redirected: Whether stdout is redirected
        silent: Whether to suppress output
        console: Rich console instance
        total: Total number of items processed
        successful: Number of successful items
        failed: Number of failed items
    """
    if output_file:
        with open(output_file, 'w', encoding=_ENCODING_UTF8) as f:
            json.dump(results, f, indent=2, default=str)
        if not silent:
            console.print(f"\n[green]Results saved to {output_file}[/green]")
    elif stdout_redirected:
        json.dump(results, sys.stdout, indent=2, default=str)
    
    if not silent and Panel:
        console.print()
        console.print(Panel(
            f"[bold]Batch Processing Summary[/bold]\n"
            f"Total: {total}\n"
            f"[green]Successful: {successful}[/green]\n"
            f"[red]Failed: {failed}[/red]",
            border_style="cyan"
        ))

