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

"""Data parsing and extraction utilities."""

from functools import reduce


class l9event:
    """
    Wrapper class for leak data that allows dot notation access.
    
    Example:
        leak = l9event({"protocol": "http", "ip": "1.2.3.4"})
        print(leak.protocol)  # "http"
        print(leak.ip)         # "1.2.3.4"
    """
    
    def __init__(self, data):
        """
        Initialize l9event with a dictionary.
        
        Args:
            data (dict): Dictionary containing leak data.
        """
        if isinstance(data, dict):
            # Convert nested dicts to l9event objects recursively
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, l9event(value))
                else:
                    setattr(self, key, value)
        else:
            # If not a dict, store as-is
            self._data = data
    
    def __getattr__(self, name):
        """Return None for missing attributes instead of raising AttributeError."""
        return None
    
    def __getitem__(self, key):
        """Allow dictionary-style access."""
        if isinstance(key, int):
            # For list-like access, raise TypeError (not a sequence)
            raise TypeError("'l9event' object is not subscriptable with integer indices")
        return getattr(self, key, None)
    
    def get(self, key, default=None):
        """Dictionary-style get method."""
        return getattr(self, key, default)
    
    def __repr__(self):
        """String representation of the l9event."""
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        return f"l9event({attrs})"
    
    def to_dict(self):
        """Return dictionary representation."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, l9event):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        return result


def _get_nested_value(obj, keys):
    """Get a nested value from a dictionary using dot-separated keys."""
    try:
        return reduce(lambda d, k: d[k], keys, obj)
    except (KeyError, TypeError):
        return "N/A"


def _extract_from_single_entry(entry, fields_list):
    """Extract fields from a single entry (event)."""
    if isinstance(entry, str):
        return l9event({"message": entry})

    # Build nested structure for fields with dots
    extracted_data = {}
    for field in fields_list:
        value = _get_nested_value(entry, field.split("."))
        # If field has dots, create nested structure
        if "." in field:
            parts = field.split(".")
            current = extracted_data
            # Create nested dict structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            # Set the final value
            current[parts[-1]] = value
        else:
            # Simple field, add directly
            extracted_data[field] = value

    # Special handling for default fields: create URL if protocol is http/https
    if fields_list == ["protocol", "ip", "port"]:
        protocol = extracted_data.get("protocol", "")
        ip = extracted_data.get("ip", "")
        port = extracted_data.get("port", "")
        if protocol in ("http", "https"):
            return l9event({"url": f"{protocol}://{ip}:{port}"})

    return l9event(extracted_data)


def _handle_full_fields(data, fields_list):
    """Handle the 'full' field request - return data as l9event objects."""
    if isinstance(data, list):
        return [l9event(item) if isinstance(item, dict) else item for item in data]
    
    events = data.get("events") if isinstance(data, dict) else None
    if isinstance(events, list):
        return [l9event(item) if isinstance(item, dict) else item for item in events]
    
    if isinstance(data, dict):
        return l9event(data)
    return [data]


def extract_data_from_json(data, fields):
    """Extract specific fields from the provided JSON data."""
    if fields is None:
        fields_list = ["protocol", "ip", "port"]
    else:
        fields_list = [f.strip() for f in fields.split(",")]
    
    # Handle "full" field request
    if "full" in fields_list:
        return _handle_full_fields(data, fields_list)
    
    # Handle if data is a list (from bulk mode or direct list)
    if isinstance(data, list):
        return [_extract_from_single_entry(e, fields_list) for e in data]

    # Handle dict with events key
    if isinstance(data, dict):
        events = data.get("events")
        if isinstance(events, list):
            return [_extract_from_single_entry(e, fields_list) for e in events]
        return _extract_from_single_entry(data, fields_list)
    
    # Fallback for other types
    return _extract_from_single_entry(data, fields_list)


def get_all_fields(data, current_path=None):
    """Recursively retrieve all field paths from a nested dictionary."""
    if not isinstance(data, dict):
        return []
    
    current_path = current_path or []
    fields = []
    for key, value in sorted(data.items()):
        new_path = current_path + [key]
        if isinstance(value, dict):
            fields.extend(get_all_fields(value, new_path))
        else:
            fields.append(".".join(new_path))
    return sorted(fields)


def _log_result_items(result, logger):
    """Log result items if logger is provided."""
    if logger and isinstance(result, list):
        for item in result:
            if isinstance(item, (dict, l9event)):
                # Handle both dict and l9event objects
                if isinstance(item, l9event):
                    attrs = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                    logger(f"{', '.join(f'{k}: {v}' for k, v in attrs.items())}", "debug")
                else:
                    logger(f"{', '.join(f'{k}: {v}' for k, v in item.items())}", "debug")


def process_and_format_data(data, fields, logger=None):
    """Process the provided data, extract desired fields, and optionally log results."""
    result = extract_data_from_json(data, fields)
    
    # Ensure result is always a list
    if not isinstance(result, list):
        result = [result]
    
    # Log results if logger is provided
    _log_result_items(result, logger)
    
    return result

