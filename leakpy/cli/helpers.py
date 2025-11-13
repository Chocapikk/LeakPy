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

from rich.console import Console
from rich.table import Table
from rich import box


def handle_list_plugins(logger, scraper):
    """Helper function to list plugins."""
    plugins = scraper.get_plugins()
    if not plugins:
        logger.error("Failed to list plugins.")
        return False
    
    logger.info(f"Plugins available: {len(plugins)}")
    
    # Use rich table for better formatting
    console = Console()
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Plugin Name", style="white")
    
    # Display plugins in a single column for better readability
    for plugin in sorted(plugins):
        table.add_row(plugin)
    
    console.print(table)
    
    return True


def format_fields_display(fields, use_rich=True):
    """Format fields for better display using rich."""
    if not fields:
        return []
    
    # Group fields by prefix (category) and handle nested fields
    categories = {}
    root_fields = []
    
    for field in fields:
        if '.' in field:
            # Get the top-level category (first segment)
            prefix = field.split('.')[0]
            if prefix not in categories:
                categories[prefix] = []
            categories[prefix].append(field)
        else:
            root_fields.append(field)
    
    # Sort categories
    sorted_categories = sorted(categories.items())
    
    if use_rich:
        # Use rich table for better formatting
        console = Console()
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Fields", style="white")
        
        # Add root fields
        if root_fields:
            table.add_row("Root", ", ".join(sorted(root_fields)))
        
        # Add categorized fields with better formatting
        for category, cat_fields in sorted_categories:
            # Group fields by their hierarchy level
            formatted_fields = []
            for field in sorted(cat_fields):
                # Remove the category prefix
                suffix = field[len(category) + 1:]
                # If there are more dots, show the full path with proper formatting
                if '.' in suffix:
                    # For nested fields like "dataset.collections", show as "dataset → collections"
                    parts = suffix.split('.')
                    formatted = " → ".join(parts)
                    formatted_fields.append(formatted)
                else:
                    # Simple field, just show the name
                    formatted_fields.append(suffix)
            
            # Join with commas, but wrap long lines better
            fields_str = ", ".join(formatted_fields)
            table.add_row(category, fields_str)
        
        console.print(table)
        return True
    else:
        # Simple text format
        lines = []
        if root_fields:
            lines.append("Root fields:")
            for field in sorted(root_fields):
                lines.append(f"  • {field}")
        
        for category, cat_fields in sorted_categories:
            lines.append(f"\n{category}.* fields:")
            for field in sorted(cat_fields):
                suffix = field[len(category) + 1:]
                if '.' in suffix:
                    parts = suffix.split('.')
                    formatted = " → ".join(parts)
                    lines.append(f"  • {category}.{formatted}")
                else:
                    lines.append(f"  • {category}.{suffix}")
        
        return lines


def _extract_sample_event(sample_data):
    """Extract first sample event from various data structures."""
    if isinstance(sample_data, dict) and "events" in sample_data:
        return sample_data["events"][0] if sample_data["events"] else None
    elif isinstance(sample_data, list) and sample_data:
        return sample_data[0]
    return sample_data if sample_data else None


def handle_list_fields(logger, scraper, scope="leak", query="", plugins=None):
    """Helper function to list fields."""
    # Temporarily disable output to avoid showing query results
    original_silent = scraper.silent
    scraper.silent = True
    # Temporarily disable logger handlers to prevent all logs
    import logging
    original_logger_level = scraper.logger.level
    original_handlers = scraper.logger.handlers[:]  # Copy handlers list
    scraper.logger.setLevel(logging.CRITICAL)  # Set to highest level
    # Remove all handlers temporarily
    for handler in original_handlers:
        scraper.logger.removeHandler(handler)
    
    try:
        sample_data = scraper.query(scope, 1, query, plugins, None, False, return_data_only=True)
    finally:
        scraper.silent = original_silent
        scraper.logger.setLevel(original_logger_level)
        # Restore handlers
        for handler in original_handlers:
            scraper.logger.addHandler(handler)

    sample_event = _extract_sample_event(sample_data)
    if not sample_event:
        msg = "Couldn't fetch valid sample data. (Please check your query, scope or plugins)"
        logger.error(msg)
        return False

    fields = scraper.get_all_fields(sample_event)
    logger.info(f"Possible fields from sample JSON: {len(fields)}")
    
    # Format and display fields
    format_fields_display(fields, use_rich=True)
    
    return True


def normalize_plugins(plugins):
    """Normalize plugins parameter (string or list) to a list."""
    if plugins is None:
        return None
    if isinstance(plugins, str):
        return [p.strip() for p in plugins.split(",") if p.strip()]
    return plugins

