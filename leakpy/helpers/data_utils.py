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

from .constants import _DEFAULT_FIELDS
from .constants import _PARSER_EVENTS_KEY

# ============================================================================
# DATA STRUCTURE UTILITIES
# ============================================================================

def get_events_from_data(data):
    """Extract events list from data structure (handles both list and dict with 'events' key)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        events = data.get(_PARSER_EVENTS_KEY)
        return events if isinstance(events, list) else [data]
    return [data]


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

# ============================================================================
# DATA CONVERSION UTILITIES
# ============================================================================

def to_dict_if_needed(obj):
    """Convert object to dict if it has to_dict method, otherwise return as-is."""
    return getattr(obj, 'to_dict', lambda: obj)()


def normalize_fields(fields):
    """Normalize fields parameter to string format."""
    return _DEFAULT_FIELDS if fields is None else (",".join(fields) if isinstance(fields, list) else fields)


# ============================================================================
# STATISTICS DATA UTILITIES
# ============================================================================

def process_value_for_counting(value, counter_dict):
    """Process a value (list or single) and increment counts."""
    for item in (value if isinstance(value, list) else [value]):
        if item is not None and (value_str := str(item)):
            counter_dict[value_str] = counter_dict.get(value_str, 0) + 1


def has_counts(value):
    """Check if dict has any non-dict values (counts)."""
    return any(not isinstance(v, dict) for v in value.values())


def remove_empty_fields(fields_dict):
    """Remove empty fields from nested dictionary recursively."""
    result = {}
    for key, value in fields_dict.items():
        if isinstance(value, dict):
            if has_counts(value):
                result[key] = value
            elif cleaned := remove_empty_fields(value):
                result[key] = cleaned
    return result
