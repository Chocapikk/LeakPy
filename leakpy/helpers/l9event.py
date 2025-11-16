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

from .decorators import handle_attribute_errors, handle_exceptions
from .constants import _PARSER_MESSAGE_KEY, _DEFAULT_FIELDS_LIST, _PARSER_FULL_FIELD_REQUEST, _PARSER_URL_KEY
from .field_utils import extract_fields_to_dict, log_result_items
from .data_utils import get_events_from_data
from .schema import extract_fields_from_l9format_schema

# ============================================================================
# L9EVENT UTILITIES
# ============================================================================

def is_l9event_instance(obj):
    """Check if object is L9Event instance."""
    # Late import to avoid circular dependency
    from ..events import L9Event
    return isinstance(obj, L9Event)


def create_l9event(data):
    """Create L9Event from data (dict or string)."""
    # Late import to avoid circular dependency
    from ..events import L9Event
    if isinstance(data, str):
        return L9Event({_PARSER_MESSAGE_KEY: data})
    return L9Event(data)


def convert_to_l9event(item):
    """Convert item to L9Event if it's a dict, otherwise return as-is."""
    # Late import to avoid circular dependency
    from ..events import L9Event
    return L9Event(item) if isinstance(item, dict) else item


def to_dict_if_l9event(obj):
    """Convert L9Event to dict, otherwise return as-is."""
    if not is_l9event_instance(obj):
        return obj
    @handle_attribute_errors(default_return=obj)
    def _convert():
        return obj.to_dict()
    return _convert()


def extract_from_single_entry(entry, fields_list):
    """Extract fields from a single entry (event)."""
    if isinstance(entry, str):
        return create_l9event(entry)

    extracted_data = extract_fields_to_dict(entry, fields_list)

    # Special handling for default fields: add URL if protocol is http/https
    if fields_list == _DEFAULT_FIELDS_LIST:
        return create_url_from_fields(extracted_data)

    return create_l9event(extracted_data)


def handle_full_fields(data, fields_list):
    """Handle the 'full' field request - return data as L9Event objects."""
    events = get_events_from_data(data)
    return [convert_to_l9event(item) for item in events]


def create_url_from_fields(extracted_data):
    """Create L9Event with protocol, ip, port and url fields if applicable."""
    # Late import to avoid circular dependency
    from ..events import L9Event
    protocol = extracted_data.get("protocol", "")
    ip = extracted_data.get("ip", "")
    port = extracted_data.get("port", "")
    
    # Always return the extracted data, but add URL if protocol is http/https
    result_data = extracted_data.copy()
    if protocol in ("http", "https") and ip and port:
        result_data[_PARSER_URL_KEY] = f"{protocol}://{ip}:{port}"
    
    return L9Event(result_data)


def extract_data_from_json(data, fields):
    """Extract specific fields from the provided JSON data."""
    if fields is None:
        fields_list = _DEFAULT_FIELDS_LIST
    else:
        fields_list = [f.strip() for f in fields.split(",")]
    
    # Handle "full" field request
    if _PARSER_FULL_FIELD_REQUEST in fields_list:
        return handle_full_fields(data, fields_list)
    
    # Extract from entries using common event extraction logic
    events = get_events_from_data(data)
    return [extract_from_single_entry(e, fields_list) for e in events]


def process_and_format_data(data, fields, logger=None):
    """Process the provided data, extract desired fields, and optionally log results."""
    result = extract_data_from_json(data, fields)
    result = result if isinstance(result, list) else [result]
    log_result_items(result, logger, is_l9event_instance, to_dict_if_l9event)
    return result


@handle_exceptions(default_return=[], exception_types=(ImportError,))
def get_all_fields_from_l9format_schema():
    """Extract all field paths from l9format.L9Event schema recursively.
    
    This function uses the official l9format library to get the complete
    list of available fields without needing to fetch sample data from the API.
    
    Returns:
        list: Sorted list of field paths (e.g., ['ip', 'port', 'geoip.country_name', ...])
    """
    # Late import to avoid circular dependency
    from l9format import l9format
    fields = extract_fields_from_l9format_schema(l9format.L9Event)
    return sorted(fields)

