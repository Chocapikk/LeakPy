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

"""Helper functions for the CLI interface."""

import sys

from rich.console import Console
from rich.table import Table
from rich import box


def _is_output_redirected():
    """Check if stdout is redirected (not a TTY)."""
    return not sys.stdout.isatty()


def _create_table(columns):
    """Create a Rich table with standard styling."""
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    for col in columns:
        table.add_column(col['name'], style=col.get('style', 'white'), width=col.get('width'))
    return table


def _display_items_simple(items):
    """Display items in simple format (one per line) when output is redirected."""
    for item in sorted(items):
        print(item)


def _display_items_table(items, column_name):
    """Display items in a Rich table."""
    console = Console()
    table = _create_table([{'name': column_name, 'style': 'white'}])
    for item in sorted(items):
        table.add_row(item)
    console.print(table)


def handle_list_plugins(logger, scraper):
    """Helper function to list plugins."""
    plugins = scraper.get_plugins()
    if not plugins:
        logger.error("Failed to list plugins.")
        return False
    
    logger.info(f"Plugins available: {len(plugins)}")
    
    if _is_output_redirected():
        _display_items_simple(plugins)
    else:
        _display_items_table(plugins, "Plugin Name")
    
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


def format_fields_display(fields):
    """Format fields for better display using rich."""
    if not fields:
        return
    
    if _is_output_redirected():
        _display_items_simple(fields)
        return
    
    root_fields, sorted_categories = _categorize_fields(fields)
    
    console = Console()
    table = _create_table([{'name': 'Category', 'style': 'cyan', 'width': 20}, {'name': 'Fields', 'style': 'white'}])
    
    if root_fields:
        table.add_row("Root", ", ".join(sorted(root_fields)))
    
    for category, cat_fields in sorted_categories:
        formatted_fields = [_format_field_suffix(field, category) for field in sorted(cat_fields)]
        table.add_row(category, ", ".join(formatted_fields))
    
    console.print(table)


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
    
    logger.info(f"Available fields from l9format schema: {len(fields)}")
    
    format_fields_display(fields)
    return True


def normalize_plugins(plugins):
    """Normalize plugins parameter (string or list) to a list."""
    if plugins is None:
        return None
    if isinstance(plugins, str):
        return [p.strip() for p in plugins.split(",") if p.strip()]
    return plugins

