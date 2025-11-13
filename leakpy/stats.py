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

"""Statistics helper functions for analyzing query results."""


class QueryStats:
    """
    Wrapper class for query statistics that allows dot notation access.
    
    Example:
        stats = QueryStats({"total": 10, "fields": {"protocol": {"http": 5}}})
        print(stats.total)  # 10
        print(stats.fields.protocol.http)  # 5
    """
    
    def __init__(self, data):
        """
        Initialize QueryStats with a dictionary.
        
        Args:
            data (dict): Dictionary containing statistics data.
        """
        if isinstance(data, dict):
            # Convert nested dicts to QueryStats objects recursively
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, QueryStats(value))
                else:
                    setattr(self, key, value)
        else:
            # If not a dict, store as-is
            self._data = data
    
    def __getattr__(self, name):
        """Return None for missing attributes instead of raising AttributeError."""
        # Raise AttributeError for dict-like methods to prevent confusion
        if name in ('get', '__getitem__', 'keys', 'values', 'items', 'update', 'pop', 'popitem', 'clear', 'copy'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'. Use dot notation instead (e.g., stats.total instead of stats['total']).")
        return None
    
    def __repr__(self):
        """String representation of the QueryStats."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        return f"QueryStats({attrs})"
    
    def to_dict(self):
        """Return dictionary representation."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, QueryStats):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        return result


def get_field_value(result, field_path_or_callable):
    """
    Get a field value from a result (dict or l9event object).
    
    Args:
        result: A dict or l9event object
        field_path_or_callable: Either a string path (e.g., "geoip.country_name") 
                                or a callable that takes the result and returns a value
    
    Returns:
        The field value or None
    """
    # If it's a callable, use it directly (object-oriented approach)
    if callable(field_path_or_callable):
        try:
            return field_path_or_callable(result)
        except (AttributeError, TypeError):
            return None
    
    # Otherwise, treat it as a string path (backward compatibility)
    field_path = field_path_or_callable
    if isinstance(result, dict):
        # Handle dict
        parts = field_path.split('.')
        value = result
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    else:
        # Handle l9event object
        try:
            parts = field_path.split('.')
            value = result
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            return value
        except AttributeError:
            return None


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_all_fields_from_result(result):
    """Get all field paths from a result."""
    if isinstance(result, dict):
        return list(flatten_dict(result).keys())
    else:
        # For l9event objects, we'll use common fields
        # In a real scenario, you might want to introspect the object
        return []


def analyze_query_results(results, fields_to_analyze=None, all_fields=False):
    """
    Analyze query results and extract statistics.
    
    Args:
        results: List of results (dicts or l9event objects) to analyze
        fields_to_analyze: Can be:
            - None: Use default fields
            - str: Comma-separated field paths (e.g., "protocol,geoip.country_name")
            - list: List of field paths (strings) or callables
            - dict: Mapping of field names to callables (object-oriented approach)
        all_fields: If True, analyze all available fields (only works with dict results)
    
    Returns:
        dict: Statistics with 'total' and 'fields' keys
    """
    stats = {
        'total': len(results),
        'fields': {}
    }
    
    # Default fields to analyze if not specified
    default_fields = [
        'geoip.country_name',
        'geoip.city_name',
        'protocol',
        'port',
        'event_type',
        'event_source',
        'host',
        'transport',
    ]
    
    # Determine which fields to analyze
    if all_fields and results:
        # Get all unique field paths from all results
        all_field_paths = set()
        for result in results[:10]:  # Sample first 10 to get field structure
            if isinstance(result, dict):
                all_field_paths.update(flatten_dict(result).keys())
        fields_to_analyze = list(all_field_paths)
    elif fields_to_analyze is None:
        # Use default fields
        fields_to_analyze = default_fields
    elif isinstance(fields_to_analyze, str):
        # Comma-separated string
        fields_to_analyze = [f.strip() for f in fields_to_analyze.split(',')]
    elif isinstance(fields_to_analyze, dict):
        # Object-oriented approach: dict mapping field names to callables
        # Keep as dict, we'll iterate over items
        pass
    # If it's already a list, use it as is
    
    # Normalize to a dict format for consistent processing
    if isinstance(fields_to_analyze, dict):
        # Already in the right format: {field_name: callable}
        field_specs = fields_to_analyze
    elif isinstance(fields_to_analyze, list):
        # Convert list to dict: {field_name: field_name_or_callable}
        field_specs = {}
        for i, field in enumerate(fields_to_analyze):
            if callable(field):
                # Use function name, or __qualname__ for nested functions, or create a label
                field_name = getattr(field, '__name__', None)
                if field_name in (None, '<lambda>', '<listcomp>', '<genexpr>'):
                    # Try to get a better name from __qualname__ or use index
                    qualname = getattr(field, '__qualname__', None)
                    if qualname and qualname not in ('<lambda>', '<listcomp>', '<genexpr>'):
                        field_name = qualname.split('.')[-1]
                    else:
                        field_name = f'field_{i}'
                field_specs[field_name] = field
            else:
                # String field path
                field_specs[field] = field
    else:
        field_specs = {}
    
    # Initialize stats for each field
    for field_name in field_specs.keys():
        stats['fields'][field_name] = {}
    
    # Analyze each result
    for result in results:
        for field_name, field_spec in field_specs.items():
            value = get_field_value(result, field_spec)
            
            if value is not None:
                # Convert to string for counting
                value_str = str(value)
                if value_str:  # Only count non-empty values
                    if value_str not in stats['fields'][field_name]:
                        stats['fields'][field_name][value_str] = 0
                    stats['fields'][field_name][value_str] += 1
    
    # Remove empty fields
    stats['fields'] = {k: v for k, v in stats['fields'].items() if v}
    
    # Return as QueryStats object for dot notation access
    return QueryStats(stats)

