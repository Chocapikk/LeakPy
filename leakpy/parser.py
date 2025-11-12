"""Data parsing and extraction utilities."""

from functools import reduce


def _get_nested_value(obj, keys):
    """Get a nested value from a dictionary using dot-separated keys."""
    try:
        return reduce(lambda d, k: d[k], keys, obj)
    except (KeyError, TypeError):
        return "N/A"


def _extract_from_single_entry(entry, fields_list):
    """Extract fields from a single entry (event)."""
    if isinstance(entry, str):
        return {"message": entry}

    extracted_data = {
        field: _get_nested_value(entry, field.split(".")) 
        for field in fields_list
    }

    # Special handling for default fields: create URL if protocol is http/https
    if fields_list == ["protocol", "ip", "port"]:
        protocol = extracted_data.get("protocol", "")
        ip = extracted_data.get("ip", "")
        port = extracted_data.get("port", "")
        if protocol in ("http", "https"):
            return {"url": f"{protocol}://{ip}:{port}"}

    return extracted_data


def _handle_full_fields(data, fields_list):
    """Handle the 'full' field request - return data as-is."""
    if isinstance(data, list):
        return data
    
    events = data.get("events") if isinstance(data, dict) else None
    if isinstance(events, list):
        return events
    
    return data if isinstance(data, dict) else [data]


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
            if isinstance(item, dict):
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

