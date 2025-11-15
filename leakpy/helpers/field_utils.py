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

from .decorators import handle_key_errors, handle_attribute_errors
from .constants import _PARSER_DEFAULT_NESTED_VALUE, _PARSER_SEPARATOR
from .data_utils import to_dict_if_needed

# ============================================================================
# FIELD AND PATH MANIPULATION
# ============================================================================

@handle_key_errors(default_return=_PARSER_DEFAULT_NESTED_VALUE)
def get_nested_value(obj, keys):
    """Get a nested value from a dictionary using dot-separated keys."""
    value = obj
    for key in keys:
        value = value[key]
    return value


def ensure_nested_path(data, path_parts):
    """Ensure nested path exists in data, creating dicts as needed."""
    current = data
    for part in path_parts:
        if part not in current:
            current[part] = {}
        current = current[part]
    return current


def set_nested_value(data, field_path, value, separator=None):
    """Set a value in nested dictionary using dot-separated field path."""
    separator = separator or _PARSER_SEPARATOR
    parts = field_path.split(separator)
    parent = ensure_nested_path(data, parts[:-1])
    parent[parts[-1]] = value


def set_field_value(extracted_data, field, value, separator=None):
    """Set field value in extracted_data, handling nested paths."""
    separator = separator or _PARSER_SEPARATOR
    if separator in field:
        set_nested_value(extracted_data, field, value, separator)
    else:
        extracted_data[field] = value


@handle_attribute_errors(default_return=None)
def get_field_value(result, field_path):
    """
    Get a field value from a result (dict or L9Event object).
    
    Args:
        result: A dict or L9Event object
        field_path: String path (e.g., "geoip.country_name")
    
    Returns:
        The field value or None
    """
    parts = field_path.split('.')
    value = result
    
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
            if value is None:
                return None
        else:
            value = getattr(value, part, None)
            if value is None:
                return None
    
    return value

# ============================================================================
# FIELD EXTRACTION UTILITIES
# ============================================================================

def extract_fields_to_dict(entry, fields_list):
    """Extract fields from entry into a dictionary."""
    extracted_data = {}
    for field in fields_list:
        keys = field.split(_PARSER_SEPARATOR)
        value = get_nested_value(entry, keys)
        set_field_value(extracted_data, field, value)
    return extracted_data


@handle_key_errors(default_return=[])
def get_all_fields_from_dict(data, current_path=None):
    """Recursively retrieve all field paths from a nested dictionary."""
    if not isinstance(data, dict):
        return []
    
    current_path = current_path or []
    fields = []
    for key, value in sorted(data.items()):
        new_path = current_path + [key]
        if isinstance(value, dict):
            fields.extend(get_all_fields_from_dict(value, new_path))
        else:
            fields.append(_PARSER_SEPARATOR.join(new_path))
    return sorted(fields)


def format_item_for_logging(item_dict):
    """Format item dictionary for logging."""
    return f"{', '.join(f'{k}: {v}' for k, v in item_dict.items())}"


def is_loggable_item(item, is_instance_func=None):
    """Check if item can be logged (dict or specific instance type)."""
    return isinstance(item, dict) or (is_instance_func and is_instance_func(item))


def log_result_items(result, logger, is_instance_func=None, to_dict_func=None):
    """Log result items if logger is provided."""
    if not logger or not isinstance(result, list):
        return
    
    for item in result:
        if is_loggable_item(item, is_instance_func):
            item_dict = (to_dict_func(item) if to_dict_func else to_dict_if_needed(item))
            logger(format_item_for_logging(item_dict), "debug")
