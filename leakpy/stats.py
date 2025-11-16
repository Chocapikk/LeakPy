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

from . import helpers


class QueryStats:
    """
    Wrapper class for query statistics that allows dot notation access.
    
    Example:
        stats = QueryStats({"total": 10, "fields": {"protocol": {"http": 5}}})
        print(stats.total)  # 10
        print(stats.fields.protocol.http)  # 5
    """
    
    _empty = None
    
    @classmethod
    def _get_empty(cls):
        """Get empty QueryStats instance for chaining."""
        if cls._empty is None:
            cls._empty = cls({})
        return cls._empty
    
    def __init__(self, data):
        """
        Initialize QueryStats with a dictionary.
        
        Args:
            data (dict): Dictionary containing statistics data.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, self._convert_value(value))
        else:
            self._data = data
    
    def _convert_value(self, value):
        """Convert value to QueryStats if it's a dict, otherwise return as-is."""
        return QueryStats(value) if isinstance(value, dict) else value
    
    def _is_private_attr(self, key):
        """Check if attribute key is private."""
        from .helpers.constants import _PRIVATE_PREFIX
        return key.startswith(_PRIVATE_PREFIX)
    
    def _get_public_attrs(self):
        """Get public attributes (excluding private ones)."""
        return {k: v for k, v in self.__dict__.items() if not self._is_private_attr(k)}
    
    def _convert_value_for_dict(self, value):
        """Convert value for dictionary representation."""
        return value.to_dict() if isinstance(value, QueryStats) else value
    
    def __getattr__(self, name):
        """Return empty QueryStats for missing attributes to allow chaining."""
        from .helpers.constants import _STATS_DICT_LIKE_METHODS
        if name in _STATS_DICT_LIKE_METHODS:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'. Use dot notation instead (e.g., stats.total instead of stats['total']).")
        return self._get_empty()
    
    def __repr__(self):
        """String representation of the QueryStats."""
        return f"QueryStats({self._get_public_attrs()})"
    
    def to_dict(self):
        """Return dictionary representation."""
        return {k: self._convert_value_for_dict(v) for k, v in self._get_public_attrs().items()}


def analyze_query_results(results, fields_to_analyze=None, all_fields=False):
    """
    Analyze query results and extract statistics.
    
    Args:
        results: Iterable of results (list, generator, etc.) containing dicts or L9Event objects to analyze
        fields_to_analyze: Can be:
            - None: Use default fields
            - str: Comma-separated field paths (e.g., "protocol,geoip.country_name")
            - list: List of field paths (strings)
        all_fields: If True, analyze all available fields (only works with dict results)
    
    Returns:
        QueryStats: Statistics object with 'total' and 'fields' keys
    """
    import itertools
    
    # Convert to list if needed for all_fields sampling, otherwise keep as iterable
    # For all_fields, we need to sample first 10 items, so we need to handle iterables
    results_list = None
    if all_fields:
        # For all_fields, we need to peek at first items, so convert to list
        results_list = list(results) if not isinstance(results, list) else results
        results = results_list
    
    stats = {
        'total': 0,  # Will be counted during iteration
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
    
    def _get_fields_list():
        """Determine which fields to analyze."""
        if all_fields and results_list:
            all_field_paths = set()
            # Sample first 10 to get field structure
            for result in itertools.islice(results_list, 10):
                if isinstance(result, dict):
                    all_field_paths.update(helpers.flatten_dict(result).keys())
            return list(all_field_paths)
        elif fields_to_analyze is None:
            return default_fields
        elif isinstance(fields_to_analyze, str):
            return [f.strip() for f in fields_to_analyze.split(',')]
        elif isinstance(fields_to_analyze, list):
            return fields_to_analyze
        return []
    
    fields_list = _get_fields_list()
    
    # Initialize stats for each field (convert paths to nested structure)
    for field_path in fields_list:
        path_parts = field_path.split('.')
        helpers.ensure_nested_path(stats['fields'], path_parts)
    
    # Analyze each result and count total
    for result in results:
        stats['total'] += 1
        for field_path in fields_list:
            value = helpers.get_field_value(result, field_path)
            if value is not None:
                path_parts = field_path.split('.')
                field_dict = helpers.ensure_nested_path(stats['fields'], path_parts)
                helpers.process_value_for_counting(value, field_dict)
    
    stats['fields'] = helpers.remove_empty_fields(stats['fields'])
    
    return QueryStats(stats)

