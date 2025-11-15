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

"""Helper functions for LeakPy."""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path

# ========================================================================
# PARSING HELPERS
# ========================================================================

def parse_int_safe(value):
    """Safely parse integer."""
    if not value or not isinstance(value, (str, int)):
        return None
    if isinstance(value, int):
        return value
    if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
        return int(value)
    return None


def parse_json_safe(text):
    """Parse JSON - may raise JSONDecodeError if invalid."""
    if not text:
        return None
    return json.loads(text)


def parse_json_line_safe(line):
    """Parse a single JSON line - returns None if invalid."""
    if not line or not line.strip():
        return None
    text = line.strip()
    if not (text.startswith('{') or text.startswith('[')):
        return None
    # json.loads may raise JSONDecodeError if invalid - exception will propagate
    return parse_json_safe(text)


# ========================================================================
# HTTP HELPERS
# ========================================================================

def get_api_headers(api_key, include_accept=True):
    """Get standard headers for API requests."""
    from . import __version__
    headers = {
        "api-key": api_key,
        "User-Agent": f"LeakPy/{__version__}"
    }
    if include_accept:
        headers["Accept"] = "application/json"
    return headers


def make_api_request(base_url, endpoint, api_key, params=None, stream=False, include_accept=True, log_func=None):
    """Make a GET request to the API."""
    import requests
    response = requests.get(
        f"{base_url}{endpoint}",
        params=params,
        headers=get_api_headers(api_key, include_accept=include_accept),
        stream=stream,
        timeout=30,
    )
    if not response:
        _log_if(log_func, "Request failed: no response", "error")
        return None
    return response


def _log_if(log_func, message, level="info"):
    """Helper to log only if log_func is provided."""
    if log_func:
        log_func(message, level)


def _log_if_not_suppressed(log_func, message, level, suppress_logs):
    """Helper to log only if log_func is provided and logs are not suppressed."""
    if not suppress_logs and log_func:
        log_func(message, level)

def check_response_status(response, log_func=None):
    """Check if response status is OK."""
    if response.status_code >= 400:
        _log_if(log_func, f"HTTP error: {response.status_code}", "error")
        return False
    return True


def handle_rate_limit(response, log_func=None):
    """Handle rate limiting (429) response."""
    if response.status_code == 429:
        limited_for_header = response.headers.get('x-limited-for')
        limited_for = parse_int_safe(limited_for_header) if limited_for_header else None
        
        wait_msg = f"{limited_for} seconds" if limited_for is not None else "time not specified"
        _log_if(log_func, f"Rate limited. Wait {wait_msg} before next request.", "warning")
        return {'_rate_limited': True, '_wait_seconds': limited_for}
    return None


def parse_json_response(response, log_func=None):
    """Parse JSON response with error handling."""
    if not check_response_status(response, log_func) or not response.text:
        return None
    return parse_json_safe(response.text)


# ========================================================================
# CACHE HELPERS
# ========================================================================

def _has_cache(cache):
    """Check if cache is available."""
    return cache is not None


def with_cache(cache, endpoint, params):
    """Check cache and return if found."""
    if not _has_cache(cache):
        return None, False
    cached = cache.get(endpoint, params)
    return (cached, True) if cached is not None else (None, False)


def save_to_cache(cache, endpoint, params, data):
    """Save data to cache."""
    if _has_cache(cache) and data is not None:
        cache.set(endpoint, params, data)


# ========================================================================
# BULK PROCESSING
# ========================================================================

def process_bulk_lines(response, log_func=None):
    """Process lines from bulk response stream."""
    from itertools import chain
    
    if not response:
        return []
    
    lines = []
    for line in response.iter_lines(decode_unicode=True):
        if line and line.strip():
            lines.append(line.strip())
    
    loaded_data = []
    for line in lines:
        # parse_json_line_safe may raise JSONDecodeError - skip invalid lines
        parsed = parse_json_line_safe(line)
        if parsed is not None:
            loaded_data.append(parsed)
    
    events = []
    for item in loaded_data:
        if isinstance(item, dict) and "events" in item:
            events.append(item.get("events", []))
    
    data = list(chain.from_iterable(events))
    
    if not data:
        _log_if(log_func, "No results returned from bulk query.", "warning")
        return []
    
    return data


# ========================================================================
# GENERIC FETCH HELPERS
# ========================================================================

def fetch_cached_endpoint(base_url, endpoint, params, api_key, cache, fetch_msg, cached_msg, log_func=None, suppress_logs=False):
    """Generic method to fetch data from an endpoint with caching and error handling."""
    # Check cache first
    cached_data, was_cached = with_cache(cache, endpoint, params)
    if was_cached:
        _log_if_not_suppressed(log_func, cached_msg, "debug", suppress_logs)
        return cached_data, True
    
    _log_if_not_suppressed(log_func, fetch_msg, "info", suppress_logs)
    
    response = make_api_request(base_url, endpoint, api_key, params=params, log_func=log_func)
    if not response:
        return None, False
    
    # Handle rate limiting
    rate_limit_data = handle_rate_limit(response, log_func)
    if rate_limit_data:
        return rate_limit_data, False
    
    # Parse JSON response
    data = parse_json_response(response, log_func)
    if data is None:
        return None, False
    
    # Save to cache
    save_to_cache(cache, endpoint, params, data)
    
    return data, False


def fetch_details_endpoint(base_url, resource_type, resource_id, api_key, cache, log_func=None, suppress_logs=False):
    """Generic method to fetch details for a resource (host/domain)."""
    endpoint = f"/{resource_type}/{resource_id}"
    resource_name = f"{resource_type} details"
    return fetch_cached_endpoint(
        base_url, endpoint, {}, api_key, cache,
        f"Fetching {resource_name} for {resource_id}...",
        f"{resource_name.capitalize()} for {resource_id} (cached)",
        log_func, suppress_logs
    )


def validate_list_response(data, resource_name, log_func=None):
    """Validate that response is a list or rate limit marker."""
    if data is not None and not isinstance(data, list):
        if isinstance(data, dict) and '_rate_limited' in data:
            return data, True  # Rate limit marker, allow it through
        _log_if(log_func, f"Unexpected response format for {resource_name}", "warning")
        return None, False
    return data, True


# Late import to avoid circular dependency
from .api import LeakIXAPI

# Late import for Rich components (optional dependency)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
except ImportError:
    Console = None
    Table = None
    Panel = None
    box = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None
    BarColumn = None
    TaskProgressColumn = None


# ============================================================================
# CONSTANTS
# ============================================================================

# General constants
_DEFAULT_LOGGER_NAME = "LeakPy"
_DEFAULT_FIELDS = "protocol,ip,port"
_DEFAULT_FIELDS_LIST = ["protocol", "ip", "port"]
_ENCODING_UTF8 = "utf-8"
_MODE_WRITE = "w"
_RATE_LIMIT_SLEEP = 1.2
_LOG_FORMAT = '%(levelname)s: %(message)s'

# Parser-specific constants
_PARSER_SEPARATOR = "."
_PARSER_DEFAULT_NESTED_VALUE = "N/A"
_PARSER_FULL_FIELD_REQUEST = "full"
_PARSER_EVENTS_KEY = "events"
_PARSER_MESSAGE_KEY = "message"
_PARSER_URL_KEY = "url"
_PARSER_HTTP_PROTOCOLS = ("http", "https")
_PARSER_MODEL_ATTRS = ('_model_cls', 'model')

# Statistics-specific constants
_STATS_DICT_LIKE_METHODS = ('get', '__getitem__', 'keys', 'values', 'items', 'update', 'pop', 'popitem', 'clear', 'copy')

# Shared constants
_PRIVATE_PREFIX = '_'  # Used by both parser and stats

# CLI lookup constants
_LOOKUP_ERROR_BOTH_IP = "Error: Cannot specify both IP address and input file\n"
_LOOKUP_ERROR_NONE_IP = "Error: Either IP address or input file (-i/--input) must be provided\n"
_LOOKUP_ERROR_BOTH_DOMAIN = "Error: Cannot specify both domain and input file\n"
_LOOKUP_ERROR_NONE_DOMAIN = "Error: Either domain or input file (-i/--input) must be provided\n"

_LOOKUP_EXAMPLES = """Examples:
  # Lookup host details
  leakpy lookup host 157.90.211.37

  # Lookup domain details
  leakpy lookup domain leakix.net

  # Lookup subdomains
  leakpy lookup subdomains leakix.net"""

_HOST_EXAMPLES = """Examples:
  # Get host details for an IP
  leakpy lookup host 157.90.211.37

  # Get host details and save to file
  leakpy lookup host 157.90.211.37 -o host_details.json

  # Extract specific fields
  leakpy lookup host 157.90.211.37 -f protocol,ip,port,host

  # Batch processing from file (one IP per line)
  leakpy lookup host -i ips.txt -o results.json

  # Silent mode for scripting
  leakpy --silent lookup host 157.90.211.37 -o host.json"""

_DOMAIN_EXAMPLES = """Examples:
  # Get domain details
  leakpy lookup domain leakix.net

  # Get domain details and save to file
  leakpy lookup domain leakix.net -o domain_details.json

  # Extract specific fields
  leakpy lookup domain leakix.net -f protocol,host,port,ip

  # Batch processing from file (one domain per line)
  leakpy lookup domain -i domains.txt -o results.json

  # Silent mode for scripting
  leakpy --silent lookup domain leakix.net -o domain.json"""

_SUBDOMAINS_EXAMPLES = """Examples:
  # Get subdomains for a domain
  leakpy lookup subdomains leakix.net

  # Get subdomains and save to file
  leakpy lookup subdomains leakix.net -o subdomains.json

  # Batch processing from file (one domain per line)
  leakpy lookup subdomains -i domains.txt -o results.json

  # Silent mode for scripting (outputs one subdomain per line)
  leakpy --silent lookup subdomains leakix.net

  # Save to file in silent mode
  leakpy --silent lookup subdomains leakix.net -o subdomains.txt"""

# CLI cache constants
_CACHE_CLEAR_EXAMPLES = """Examples:
  # Clear all cached API responses
  leakpy cache clear"""

_CACHE_SET_TTL_EXAMPLES = """Examples:
  # Set cache TTL to 10 minutes
  leakpy cache set-ttl 10

  # Set cache TTL to 30 minutes
  leakpy cache set-ttl 30"""

_CACHE_SHOW_TTL_EXAMPLES = """Examples:
  # Show current cache TTL
  leakpy cache show-ttl

  # Show TTL in silent mode (for scripting)
  leakpy --silent cache show-ttl"""

# CLI config constants
_CONFIG_RESET_EXAMPLES = """Examples:
  # Reset/delete saved API key
  leakpy config reset"""

_CONFIG_SET_EXAMPLES = """Examples:
  # Set API key interactively (will prompt for input)
  leakpy config set

  # Set API key directly from command line
  leakpy config set your_48_character_api_key_here"""

# CLI list constants
_LIST_PLUGINS_EXAMPLES = """Examples:
  # List all available plugins
  leakpy list plugins

  # List plugins in silent mode (for scripting)
  leakpy --silent list plugins"""

_LIST_FIELDS_EXAMPLES = """Examples:
  # List all available fields
  leakpy list fields

  # List fields from a specific query
  leakpy list fields -q '+country:"France"'

  # List fields from service scope
  leakpy list fields -s service -q 'port:3306'

  # List fields with specific plugin
  leakpy list fields -P PulseConnectPlugin

  # List fields in silent mode (for scripting)
  leakpy --silent list fields -q '+country:"France"'"""

# CLI search constants
_SEARCH_EXAMPLES = """Examples:
  # Search for leaks in France
  leakpy search -q '+country:"France"' -p 5

  # Search with specific plugin
  leakpy search -q '+country:"France"' -P PulseConnectPlugin -p 3

  # Extract specific fields
  leakpy search -q '+country:"France"' -f protocol,ip,port,host

  # Get complete JSON and save to file
  leakpy search -q '+country:"France"' -f full -o results.json

  # Use bulk mode (requires Pro API)
  leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

  # Silent mode for scripting
  leakpy search --silent -q '+country:"France"' -p 5 -o results.txt"""

# CLI stats constants
_STATS_CACHE_EXAMPLES = """Examples:
  # Display cache statistics
  leakpy stats cache

  # Display cache stats in silent mode (for scripting)
  leakpy --silent stats cache"""

_STATS_OVERVIEW_EXAMPLES = """Examples:
  # Display overview statistics
  leakpy stats overview"""

_STATS_QUERY_EXAMPLES = """Examples:
  # Analyze query statistics from a live query
  leakpy stats query -q '+country:"France"' -p 5

  # Use bulk mode for faster queries (requires Pro API)
  leakpy stats query -q 'plugin:TraccarPlugin' -b

  # Analyze statistics from a JSON file
  leakpy stats query -f results.json

  # Analyze specific fields only
  leakpy stats query -f results.json --fields "geoip.country_name,protocol,port"

  # Analyze all available fields
  leakpy stats query -f results.json --all-fields

  # Show top 15 items instead of default 10
  leakpy stats query -f results.json --top 15

  # Analyze in silent mode (for scripting)
  leakpy --silent stats query -f results.json"""


# ============================================================================
# DECORATORS
# ============================================================================

def handle_exceptions(default_return=None, exception_types=(Exception,)):
    """Decorator to handle specific exceptions with default return."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types:
                return default_return
        return wrapper
    return decorator


def handle_file_errors(default_return=None):
    """Decorator to handle file operation errors (IOError, OSError, JSONDecodeError)."""
    return handle_exceptions(default_return, (IOError, OSError, json.JSONDecodeError))


def handle_key_errors(default_return=None):
    """Decorator to handle KeyError and TypeError (for nested dict access)."""
    return handle_exceptions(default_return, (KeyError, TypeError))


def handle_attribute_errors(default_return=None):
    """Decorator to handle AttributeError."""
    return handle_exceptions(default_return, (AttributeError,))


def require_api_key(func):
    """Decorator to require valid API key before executing method."""
    def wrapper(self, *args, **kwargs):
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        self.api = ensure_api_initialized(self.api, self.api_key, self.log)
        return func(self, *args, **kwargs)
    return wrapper


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def get_log_function(logger, level):
    """Get appropriate log function from logger."""
    return getattr(logger, level.lower(), logger.info)


def _calculate_log_level(verbose, level):
    """Calculate the appropriate logging level."""
    return logging.DEBUG if verbose else (level or logging.INFO)




def _create_console_handler(log_level):
    """Create and configure console handler with formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)
    return handler


def _configure_logger(logger, log_level):
    """Configure logger with level and handler."""
    logger.setLevel(log_level)
    handler = _create_console_handler(log_level)
    logger.addHandler(handler)
    logger.propagate = False


def setup_logger(name=_DEFAULT_LOGGER_NAME, verbose=False, level=None):
    """
    Setup and configure the logger.
    
    Args:
        name (str): Logger name.
        verbose (bool): Enable verbose logging (DEBUG level).
        level: Optional logging level override.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    log_level = _calculate_log_level(verbose, level)
    _configure_logger(logger, log_level)
    
    return logger


# ============================================================================
# API UTILITIES
# ============================================================================

def ensure_api_initialized(api, api_key, log_func):
    """Ensure API client is initialized."""
    return api or LeakIXAPI(api_key, False, log_func)


# ============================================================================
# DATA CONVERSION UTILITIES
# ============================================================================

def to_dict_if_needed(obj):
    """Convert object to dict if it has to_dict method, otherwise return as-is."""
    return obj.to_dict() if hasattr(obj, 'to_dict') else obj


def normalize_fields(fields):
    """Normalize fields parameter to string format."""
    if fields is None:
        return _DEFAULT_FIELDS
    return ",".join(fields) if isinstance(fields, list) else fields


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
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
    
    return value


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
# STATISTICS UTILITIES
# ============================================================================

def get_all_fields_from_result(result):
    """Get all field paths from a result."""
    if isinstance(result, dict):
        return list(flatten_dict(result).keys())
    else:
        # For L9Event objects, we'll use common fields
        # In a real scenario, you might want to introspect the object
        return []


def process_value_for_counting(value, counter_dict):
    """Process a value (list or single) and increment counts."""
    items = value if isinstance(value, list) else [value]
    for item in items:
        if item is not None:
            value_str = str(item)
            if value_str:
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
            else:
                cleaned = remove_empty_fields(value)
                if cleaned:
                    result[key] = cleaned
    return result


# ============================================================================
# FILE OUTPUT UTILITIES
# ============================================================================

def open_output_file(output_path, silent, log_func):
    """Open output file and return file handle and close flag."""
    try:
        output_file = open(output_path, _MODE_WRITE, encoding=_ENCODING_UTF8)
        if not silent:
            log_func(f"Writing results to {output_path}...", "info")
        return output_file, True
    except (IOError, OSError) as e:
        if not silent:
            log_func(f"Error opening output file {output_path}: {e}", "error")
        return None, False


def get_output_file(output, silent, log_func):
    """Get output file handle from output parameter (string path or file object)."""
    if not output:
        return None, False
    
    if isinstance(output, str):
        return open_output_file(output, silent, log_func)
    else:
        # It's already a file object (e.g., sys.stdout)
        if not silent:
            log_func("Writing results to stdout...", "info")
        return output, False


def write_json_line(file_handle, obj):
    """Write object as JSON line to file."""
    obj_dict = to_dict_if_needed(obj)
    file_handle.write(f"{json.dumps(obj_dict)}\n")
    file_handle.flush()


def write_result_item(file_handle, result, fields):
    """Write a single result item to file."""
    if not fields:
        # Use dot notation to access url field
        if hasattr(result, 'url') and result.url:
            file_handle.write(f"{result.url}\n")
        else:
            result_dict = to_dict_if_needed(result)
            if isinstance(result_dict, dict) and result_dict.get('url'):
                file_handle.write(f"{result_dict.get('url')}\n")
            else:
                file_handle.write(f"{json.dumps(result_dict)}\n")
    else:
        write_json_line(file_handle, result)
    file_handle.flush()


# ============================================================================
# FILE OPERATIONS
# ============================================================================

@handle_file_errors()
def delete_file_safe(file_path):
    """Safely delete a file, ignoring errors."""
    if file_path.exists():
        file_path.unlink()


@handle_file_errors(default_return=None)
def read_file_safe(file_path, encoding=None):
    """Safely read a file, returning None on error."""
    encoding = encoding or _ENCODING_UTF8
    if not file_path.exists():
        return None
    return file_path.read_text(encoding=encoding).strip()


@handle_file_errors()
def write_file_safe(file_path, content, encoding=None, restrict_permissions=False):
    """Safely write content to a file with optional restrictive permissions."""
    encoding = encoding or _ENCODING_UTF8
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    if restrict_permissions and os.name != "nt":
        file_path.chmod(0o600)


# ============================================================================
# HASH AND KEY GENERATION
# ============================================================================

def make_hash_key(endpoint, params=None):
    """Generate a hash key from endpoint and params (for cache keys)."""
    key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
    return hashlib.sha256(key_data.encode(_ENCODING_UTF8)).hexdigest()


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

# Try to import keyring for secure storage
try:
    import keyring  # type: ignore
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None  # type: ignore


def get_config_dir():
    """Get the configuration directory for the current OS."""
    if os.name == "nt":  # Windows
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        config_dir = Path(base) / "LeakPy"
    else:  # Linux, macOS, etc.
        base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        config_dir = Path(base) / "LeakPy"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@handle_file_errors(default_return={})
def read_json_file(file_path):
    """Read JSON data from a file."""
    if not file_path.exists():
        return {}
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        return json.load(f)


@handle_file_errors()
def write_json_file(file_path, data, ensure_dir=True):
    """Write JSON data to a file."""
    if ensure_dir:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding=_ENCODING_UTF8) as f:
        json.dump(data, f, indent=2)


# ============================================================================
# URL UTILITIES
# ============================================================================

def get_url_fields(extracted_data):
    """Extract protocol, ip, port from extracted data."""
    return (
        extracted_data.get("protocol", ""),
        extracted_data.get("ip", ""),
        extracted_data.get("port", "")
    )


def is_http_protocol(protocol):
    """Check if protocol is HTTP or HTTPS."""
    return protocol in _PARSER_HTTP_PROTOCOLS


def build_url(protocol, ip, port):
    """Build URL string from protocol, ip, port."""
    return f"{protocol}://{ip}:{port}"


# ============================================================================
# SCHEMA EXTRACTION UTILITIES
# ============================================================================

# Constants for l9format schema extraction
try:
    from l9format import l9format
    
    _SCHEMA_FIELD_TO_MODEL_MAP = {
        'geoip': l9format.GeoLocation,
        'http': l9format.L9HttpEvent,
        'ssl': l9format.L9SSLEvent,
        'ssh': l9format.L9SSHEvent,
        'leak': l9format.L9LeakEvent,
        'service': l9format.L9ServiceEvent,
        'network': l9format.Network,
    }
    
    _SCHEMA_NESTED_FIELD_TO_MODEL_MAP = {
        'certificate': l9format.Certificate,
        'location': l9format.GeoPoint,
        'dataset': l9format.DatasetSummary,
        'header': None,  # Dict-like, extract keys dynamically
        'credentials': l9format.ServiceCredentials,
        'software': l9format.Software,
    }
except ImportError:
    l9format = None
    _SCHEMA_FIELD_TO_MODEL_MAP = {}
    _SCHEMA_NESTED_FIELD_TO_MODEL_MAP = {}


def _is_valid_schema_model(model_cls, current_class):
    """Check if a model class is valid (not self-reference)."""
    if not l9format:
        return False
    return model_cls != current_class and model_cls != l9format.L9Event


@handle_attribute_errors(default_return=None)
def _get_model_from_field_obj(field_obj, model_class):
    """Extract model from field object attributes (_model_cls or model)."""
    for attr_name in _PARSER_MODEL_ATTRS:
        if hasattr(field_obj, attr_name):
            model = getattr(field_obj, attr_name)
            if model and _is_valid_schema_model(model, model_class):
                return model
    return None


def _get_model_for_schema_field(field_name, prefix, field_obj, model_class):
    """Get the model class for a field, checking multiple sources."""
    # First, check if the field name itself maps to a known model
    if field_name in _SCHEMA_FIELD_TO_MODEL_MAP:
        return _SCHEMA_FIELD_TO_MODEL_MAP[field_name]
    
    # Check nested field map
    if prefix and field_name in _SCHEMA_NESTED_FIELD_TO_MODEL_MAP:
        nested_model = _SCHEMA_NESTED_FIELD_TO_MODEL_MAP[field_name]
        if nested_model:
            return nested_model
    
    # Try to get model from field object
    return _get_model_from_field_obj(field_obj, model_class)


def _build_schema_field_path(prefix, field_name):
    """Build full field path from prefix and field name."""
    return f"{prefix}{_PARSER_SEPARATOR}{field_name}" if prefix else field_name


def _init_visited_set(visited):
    """Initialize visited set if None."""
    return visited or set()


def _is_model_already_visited(model_class, visited):
    """Check if model class has already been visited."""
    model_id = id(model_class)
    if model_id in visited:
        return True
    visited.add(model_id)
    return False


@handle_attribute_errors(default_return=[])
def extract_fields_from_l9format_schema(model_class, prefix="", visited=None):
    """Recursively extract fields from a model class.
    
    Args:
        model_class: The model class to extract fields from
        prefix: Current field path prefix
        visited: Set of already visited model classes to prevent infinite recursion
    """
    if not hasattr(model_class, '_fields'):
        return []
    
    visited = _init_visited_set(visited)
    if _is_model_already_visited(model_class, visited):
        return []  # Already processed, skip to avoid infinite recursion
    
    nested_fields = []
    for field_name, field_obj in model_class._fields.items():
        full_path = _build_schema_field_path(prefix, field_name)
        nested_fields.append(full_path)
        
        # Check if this field maps to a known model
        model_to_check = _get_model_for_schema_field(field_name, prefix, field_obj, model_class)
        
        if model_to_check and model_to_check != model_class:
            # Recursively extract nested fields
            deeper = extract_fields_from_l9format_schema(model_to_check, full_path, visited.copy())
            nested_fields.extend(deeper)
    
    return nested_fields


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
    if isinstance(item, dict):
        return True
    if is_instance_func:
        return is_instance_func(item)
    return False


def log_result_items(result, logger, is_instance_func=None, to_dict_func=None):
    """Log result items if logger is provided."""
    if not logger or not isinstance(result, list):
        return
    
    for item in result:
        if is_loggable_item(item, is_instance_func):
            item_dict = (to_dict_func(item) if to_dict_func else to_dict_if_needed(item))
            logger(format_item_for_logging(item_dict), "debug")


# ============================================================================
# L9EVENT UTILITIES
# ============================================================================

def is_l9event_instance(obj):
    """Check if object is L9Event instance."""
    # Late import to avoid circular dependency
    from .events import L9Event
    return isinstance(obj, L9Event)


def create_l9event(data):
    """Create L9Event from data (dict or string)."""
    # Late import to avoid circular dependency
    from .events import L9Event
    if isinstance(data, str):
        return L9Event({_PARSER_MESSAGE_KEY: data})
    return L9Event(data)


def convert_to_l9event(item):
    """Convert item to L9Event if it's a dict, otherwise return as-is."""
    # Late import to avoid circular dependency
    from .events import L9Event
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

    # Special handling for default fields: create URL if protocol is http/https
    if fields_list == _DEFAULT_FIELDS_LIST:
        url_event = create_url_from_fields(extracted_data)
        if url_event:
            return url_event

    return create_l9event(extracted_data)


def handle_full_fields(data, fields_list):
    """Handle the 'full' field request - return data as L9Event objects."""
    events = get_events_from_data(data)
    return [convert_to_l9event(item) for item in events]


def create_url_from_fields(extracted_data):
    """Create URL from protocol, ip, port fields if applicable."""
    # Late import to avoid circular dependency
    from .events import L9Event
    protocol, ip, port = get_url_fields(extracted_data)
    if is_http_protocol(protocol) and ip and port:
        return L9Event({_PARSER_URL_KEY: build_url(protocol, ip, port)})
    return None


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


def get_all_fields_from_l9format_schema():
    """Extract all field paths from l9format.L9Event schema recursively.
    
    This function uses the official l9format library to get the complete
    list of available fields without needing to fetch sample data from the API.
    
    Returns:
        list: Sorted list of field paths (e.g., ['ip', 'port', 'geoip.country_name', ...])
    """
    # Late import to avoid circular dependency
    try:
        from l9format import l9format
    except ImportError:
        return []
    fields = extract_fields_from_l9format_schema(l9format.L9Event)
    return sorted(fields)


# ============================================================================
# DATE AND TIME UTILITIES
# ============================================================================

def format_iso_date(date_str, default='N/A'):
    """Format ISO date string to readable format.
    
    Args:
        date_str: ISO format date string (e.g., '2024-01-01T12:00:00Z')
        default: Default value to return if date_str is invalid or equals default
    
    Returns:
        str: Formatted date string (e.g., '2024-01-01 12:00:00') or default value
    """
    if date_str == default:
        return date_str
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return date_str


# ============================================================================
# FILE INPUT UTILITIES
# ============================================================================

def load_lines_from_file(file_path, skip_comments=True, skip_empty=True):
    """Load lines from a text file.
    
    Args:
        file_path: Path to the file (str or Path)
        skip_comments: Whether to skip lines starting with '#' (default: True)
        skip_empty: Whether to skip empty lines (default: True)
    
    Returns:
        list: List of non-empty lines (stripped)
    
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        lines = []
        for line in f:
            line = line.strip()
            if skip_empty and not line:
                continue
            if skip_comments and line.startswith('#'):
                continue
            lines.append(line)
        return lines


# ============================================================================
# SERVICE AND LEAK EXTRACTION UTILITIES
# ============================================================================

def extract_software_info(service):
    """Extract software information from a service object.
    
    Args:
        service: Service object with potential software information
    
    Returns:
        str: Software name and version, or "N/A" if not available
    """
    if not (hasattr(service, 'service') and service.service and hasattr(service.service, 'software') and service.service.software):
        return "N/A"
    software_name = getattr(service.service.software, 'name', '') or ''
    software_version = getattr(service.service.software, 'version', '') or ''
    if software_name:
        return f"{software_name} {software_version}".strip() if software_version else software_name
    return software_version if software_version else "N/A"


def extract_http_status(service):
    """Extract HTTP status from a service object.
    
    Args:
        service: Service object with potential HTTP information
    
    Returns:
        str: HTTP status code, or "N/A" if not available
    """
    return str(service.http.status) if service.http and service.http.status else "N/A"


def extract_leak_info(leak, include_ip=False):
    """Extract leak information from a leak object.
    
    Args:
        leak: Leak object
        include_ip: Whether to include IP address in the result
    
    Returns:
        dict with keys: type, host, port, severity, size, and optionally ip
    """
    defaults = _get_leak_defaults(leak, include_ip)
    if not _has_events(leak):
        return _build_leak_result(defaults, include_ip)
    
    first_event = leak.events[0]
    if isinstance(first_event, dict):
        return _extract_from_dict_event(first_event, defaults, include_ip)
    return _extract_from_l9event(first_event, defaults, include_ip)


def _get_leak_defaults(leak, include_ip):
    """Get default leak values."""
    host = getattr(leak, 'resource_id', '') or getattr(leak, 'Ip', '') or "N/A" if include_ip else getattr(leak, 'resource_id', '') or "N/A"
    return {
        'type': "N/A",
        'host': host,
        'ip': getattr(leak, 'Ip', '') or "N/A" if include_ip else None,
        'port': "N/A",
        'severity': "N/A",
        'size': "N/A"
    }


def _has_events(leak):
    """Check if leak has events."""
    return hasattr(leak, 'events') and leak.events and isinstance(leak.events, list) and len(leak.events) > 0


def _extract_from_dict_event(event, defaults, include_ip):
    """Extract leak info from dict event."""
    leak_info = event.get('leak', {})
    defaults['type'] = leak_info.get('type', '') or event.get('event_source', '') or "N/A"
    defaults['severity'] = leak_info.get('severity', '') or "N/A"
    dataset_info = leak_info.get('dataset', {})
    if dataset_info and dataset_info.get('size'):
        defaults['size'] = str(dataset_info['size'])
    defaults['host'] = event.get('host', '') or defaults['host']
    if include_ip:
        defaults['ip'] = event.get('ip', '') or defaults['ip']
    defaults['port'] = event.get('port', '') or defaults['port']
    return _build_leak_result(defaults, include_ip)


def _extract_from_l9event(event, defaults, include_ip):
    """Extract leak info from L9Event."""
    if hasattr(event, 'leak') and event.leak:
        defaults['type'] = getattr(event.leak, 'type', '') or getattr(event, 'event_source', '') or "N/A"
        defaults['severity'] = getattr(event.leak, 'severity', '') or "N/A"
        if hasattr(event.leak, 'dataset') and event.leak.dataset:
            defaults['size'] = str(getattr(event.leak.dataset, 'size', 0)) if getattr(event.leak.dataset, 'size', 0) else "N/A"
    defaults['host'] = getattr(event, 'host', '') or defaults['host']
    if include_ip:
        defaults['ip'] = getattr(event, 'ip', '') or defaults['ip']
    defaults['port'] = str(getattr(event, 'port', '')) if getattr(event, 'port', '') else defaults['port']
    return _build_leak_result(defaults, include_ip)


def _build_leak_result(defaults, include_ip):
    """Build final leak result dict."""
    result = {k: v for k, v in defaults.items() if k != 'ip'}
    if include_ip:
        result['ip'] = defaults['ip']
    return result


# ============================================================================
# BATCH PROCESSING UTILITIES
# ============================================================================

def process_subdomains_result(result, item):
    """Process subdomains result list and deduplicate.
    
    Args:
        result: List of subdomain dictionaries
        item: Domain name
    
    Returns:
        list: List of processed subdomain entries
    """
    if not result:
        return [{'domain': item, 'subdomain': None, 'distinct_ips': 0, 'last_seen': None}]
    seen = set()
    return [{'domain': item, 'subdomain': name, 'distinct_ips': sd.get('distinct_ips', 0), 'last_seen': sd.get('last_seen', '')} for sd in result if (name := sd.get('subdomain', '')) and name not in seen and not seen.add(name)]


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


# ============================================================================
# LOOKUP COMMAND UTILITIES
# ============================================================================

def add_common_lookup_args(parser, include_fields=False, include_limit=False):
    """Add common arguments to a lookup parser."""
    parser.add_argument("-i", "--input", help="Input file containing items (one per line) for batch processing", type=str)
    parser.add_argument("-o", "--output", help="Output file path (for batch mode, results are saved as JSON array)", type=str)
    parser.add_argument("--silent", action="store_true", help="Suppress all output (useful for scripting)")
    if include_fields:
        parser.add_argument("-f", "--fields", help="Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')", type=str, default="full")
    if include_limit:
        parser.add_argument("--limit", type=int, default=50, help="Maximum number of services/leaks to display (default: 50, use 0 for all)")
        parser.add_argument("--all", action="store_true", help="Display all services and leaks (equivalent to --limit 0)")


def execute_single_lookup(args, client, stdout_redirected, lookup_type):
    """Execute a single lookup (non-batch mode)."""
    _LOOKUP_METHODS = {
        'host': (getattr(args, 'ip', None), _LOOKUP_ERROR_BOTH_IP, _LOOKUP_ERROR_NONE_IP, client.get_host, 'ip', display_host_info),
        'domain': (getattr(args, 'domain', None), _LOOKUP_ERROR_BOTH_DOMAIN, _LOOKUP_ERROR_NONE_DOMAIN, client.get_domain, 'domain', lambda r, v: display_domain_info(r, v, limit=0 if args.all else args.limit)),
        'subdomains': (getattr(args, 'domain', None), _LOOKUP_ERROR_BOTH_DOMAIN, _LOOKUP_ERROR_NONE_DOMAIN, client.get_subdomains, 'domain', display_subdomains)
    }
    item_value, error_both, error_none, client_method, item_key, display_func = _LOOKUP_METHODS[lookup_type]
    
    if args.input and not item_value:
        return True
    if args.input and item_value:
        sys.stderr.write(error_both)
        sys.exit(1)
    if not item_value:
        sys.stderr.write(error_none)
        sys.exit(1)
    
    output_target = sys.stdout if (stdout_redirected and not args.output) else args.output
    kwargs = {item_key: item_value, 'output': output_target}
    if lookup_type != 'subdomains':
        kwargs['fields'] = args.fields
    result = client_method(**kwargs)
    
    handle_lookup_display(result, args, stdout_redirected, lookup_type, item_value, display_func)
    return False


def handle_lookup_display(result, args, stdout_redirected, lookup_type, item_value, display_func):
    """Handle display logic based on mode."""
    # If output file is specified, data is already written, just display formatted view if not silent and TTY
    if args.output:
        if not args.silent and not stdout_redirected:
            display_func(result, item_value)
    # If stdout is redirected, data is already written via output=sys.stdout, nothing to display
    elif stdout_redirected:
        pass  # Data already written to stdout via output parameter
    # Normal TTY mode: display formatted view
    elif not args.silent:
        display_func(result, item_value)
    # Silent mode with subdomains: print one per line
    elif lookup_type == 'subdomains' and args.silent:
        for subdomain in result:
            print(subdomain['subdomain'])


def execute_batch_lookup(args, client, stdout_redirected, lookup_type):
    """Execute batch lookups from input file."""
    _BATCH_METHODS = {
        'host': ('IP addresses', 'ip', client.get_host, lambda item: {'ip': item, 'fields': args.fields, 'output': None}),
        'domain': ('domains', 'domain', client.get_domain, lambda item: {'domain': item, 'fields': args.fields, 'output': None}),
        'subdomains': ('domains', 'domain', client.get_subdomains, lambda item: {'domain': item, 'output': None})
    }
    item_type, item_key, client_method, get_kwargs = _BATCH_METHODS[lookup_type]
    console = Console()
    items = load_batch_lookup_items(args.input, item_type, console)
    results, successful, failed = [], 0, 0
    
    def _process_item(item):
        result_entry, success = process_batch_lookup_item(client_method, item, item_key, get_kwargs(item), console=console if not args.silent else None)
        if isinstance(result_entry, list):
            results.extend(result_entry)
        else:
            results.append(result_entry)
        if success:
            nonlocal successful
            successful += 1
        else:
            nonlocal failed
            failed += 1
    
    process_batch_lookup_items(items, _process_item, args.silent, item_type, console)
    save_batch_results(results, args.output, stdout_redirected, args.silent, console, len(items), successful, failed)


def load_batch_lookup_items(input_file, item_type, console):
    """Load items from input file with error handling."""
    try:
        items = load_lines_from_file(input_file)
        if not items:
            console.print(f"[red]No {item_type} found in {input_file}[/red]")
            sys.exit(1)
        return items
    except Exception as e:
        console.print(f"[red]Error loading input file: {e}[/red]")
        sys.exit(1)


def process_batch_lookup_items(items, process_func, silent, item_type, console):
    """Process batch items with or without progress bar."""
    if silent:
        for item in items:
            process_func(item)
        return
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), transient=False, console=console) as progress:
        task = progress.add_task(f"[cyan]Processing {len(items)} {item_type}...", total=len(items))
        for i, item in enumerate(items, 1):
            progress.update(task, description=f"[cyan]Processing {item} ({i}/{len(items)})...")
            process_func(item)
            progress.update(task, advance=1)


def process_batch_lookup_item(func, item, item_key, args_dict, console=None):
    """Process a single item in batch mode with error handling."""
    try:
        result = func(**args_dict)
        if item_key == 'domain' and isinstance(result, list):
            return process_subdomains_result(result, item), True
        return {item_key: item, 'result': result}, True
    except Exception as e:
        if console:
            console.print(f"[red]  ✗ Error for {item}: {e}[/red]")
        return {item_key: item, 'error': str(e)}, False


def display_host_info(host_info, ip, limit=50):
    """Display host information in a formatted way."""
    display_lookup_info(host_info, ip, "Host Details", "IP Address", limit, show_ip=False, no_info_msg="[dim]No information found for this IP address.[/dim]")


def display_domain_info(domain_info, domain, limit=50):
    """Display domain information in a formatted way."""
    display_lookup_info(domain_info, domain, "Domain Details", "Domain", limit, show_ip=True, no_info_msg="[dim]No information found for this domain.[/dim]")


def display_subdomains(subdomains, domain):
    """Display subdomains information in a formatted way."""
    console = Console()
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    
    seen = set()
    unique_subdomains = [sd for sd in subdomains if (name := sd.get('subdomain', '')) and name not in seen and not seen.add(name)]
    
    if len(unique_subdomains) != len(subdomains):
        summary_table.add_row("Subdomains Found", f"[bold green]{len(unique_subdomains)}[/bold green] [dim]({len(subdomains)} before deduplication)[/dim]")
    else:
        summary_table.add_row("Subdomains Found", f"[bold green]{len(unique_subdomains)}[/bold green]")
    
    console.print(Panel(summary_table, title=f"[bold cyan]Subdomains: {domain}[/bold cyan]", border_style="cyan"))
    console.print()
    
    if unique_subdomains:
        subdomains_table = Table(box=box.SIMPLE)
        subdomains_table.add_column("Subdomain", style="yellow")
        subdomains_table.add_column("Distinct IPs", style="cyan", justify="right")
        subdomains_table.add_column("Last Seen", style="dim")
        
        for subdomain in unique_subdomains:
            subdomain_name = subdomain.get('subdomain', 'N/A')
            distinct_ips = subdomain.get('distinct_ips', 0)
            last_seen = format_iso_date(subdomain.get('last_seen', 'N/A'))
            subdomains_table.add_row(subdomain_name, str(distinct_ips), last_seen)
        
        console.print(subdomains_table)
    else:
        console.print("[dim]No subdomains found for this domain.[/dim]")


def display_lookup_info(info, item_value, title, item_name, limit=50, show_ip=False, no_info_msg=None):
    """Display host or domain information in a formatted way."""
    console = Console()
    services_count = len(info.Services) if info.Services else 0
    leaks_count = len(info.Leaks) if info.Leaks else 0
    display_lookup_info_summary(console, title, item_name, item_value, services_count, leaks_count)
    display_lookup_services_table(console, info.Services or [], limit, services_count, show_ip=show_ip)
    display_lookup_leaks_table(console, info.Leaks or [], limit, leaks_count, include_ip=show_ip)
    if not info.Services and not info.Leaks and no_info_msg:
        console.print(no_info_msg)


def display_lookup_info_summary(console, title, item_name, item_value, services_count, leaks_count):
    """Display summary table for host or domain info."""
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="cyan", width=20)
    summary_table.add_column(style="white")
    summary_table.add_row(item_name, f"[bold]{item_value}[/bold]")
    summary_table.add_row("Services", f"[bold green]{services_count}[/bold green]")
    summary_table.add_row("Leaks", f"[bold red]{leaks_count}[/bold red]")
    console.print(Panel(summary_table, title=f"[bold cyan]{title}: {item_value}[/bold cyan]", border_style="cyan"))
    console.print()


def display_lookup_services_table(console, services, limit, total_count, show_ip=False):
    """Display services in a table."""
    if not services:
        return
    
    services_to_show = services if limit == 0 else services[:limit]
    
    if services_to_show:
        console.print("[bold]Services:[/bold]")
        services_table = Table(box=box.SIMPLE)
        
        if show_ip:
            services_table.add_column("Host", style="yellow")
            services_table.add_column("Protocol", style="cyan")
            services_table.add_column("Port", style="white")
            services_table.add_column("IP", style="dim")
        else:
            services_table.add_column("Protocol", style="cyan")
            services_table.add_column("Port", style="white")
            services_table.add_column("Host", style="yellow")
        
        services_table.add_column("Software", style="magenta")
        services_table.add_column("Status", style="green")
        
        for service in services_to_show:
            protocol = service.protocol or "N/A"
            port = str(service.port) if service.port else "N/A"
            host = service.host or "N/A"
            ip = service.ip or "N/A" if show_ip else None
            software = extract_software_info(service)
            status = extract_http_status(service)
            
            if show_ip:
                services_table.add_row(host, protocol, port, ip, software, status)
            else:
                services_table.add_row(protocol, port, host, software, status)
        
        if limit > 0 and total_count > limit:
            console.print(f"[dim]... and {total_count - limit} more services[/dim]")
        
        console.print(services_table)
        console.print()


def display_lookup_leaks_table(console, leaks, limit, total_count, include_ip=False):
    """Display leaks in a table."""
    if not leaks:
        return
    
    leaks_to_show = leaks if limit == 0 else leaks[:limit]
    
    if leaks_to_show:
        console.print("[bold]Leaks:[/bold]")
        leaks_table = Table(box=box.SIMPLE)
        leaks_table.add_column("Type", style="red")
        leaks_table.add_column("Host", style="yellow")
        if include_ip:
            leaks_table.add_column("IP", style="cyan")
        leaks_table.add_column("Port", style="white")
        leaks_table.add_column("Severity", style="yellow")
        leaks_table.add_column("Size", style="white", justify="right")
        
        for leak in leaks_to_show:
            leak_info = extract_leak_info(leak, include_ip=include_ip)
            if include_ip:
                leaks_table.add_row(
                    leak_info['type'], leak_info['host'], leak_info['ip'],
                    leak_info['port'], leak_info['severity'], leak_info['size']
                )
            else:
                leaks_table.add_row(
                    leak_info['type'], leak_info['host'], leak_info['port'],
                    leak_info['severity'], leak_info['size']
                )
        
        if limit > 0 and total_count > limit:
            console.print(f"[dim]... and {total_count - limit} more leaks[/dim]")
        
        console.print(leaks_table)


# ============================================================================
# STATS COMMAND UTILITIES
# ============================================================================

def get_cache_stats():
    """Get cache statistics."""
    import time
    from .cache import APICache
    from .config import CacheConfig
    
    cache = APICache()
    cache_config = CacheConfig()
    
    stats = {
        'total_entries': len(cache._cache),
        'ttl_seconds': cache.ttl,
        'ttl_minutes': cache.ttl // 60,
        'configured_ttl_minutes': cache_config.get_ttl_minutes(),
        'cache_file_size': 0,
        'cache_file_path': str(cache.cache_file),
        'expired_entries': 0,
        'active_entries': 0,
        'oldest_entry_age': 0,
        'newest_entry_age': 0,
    }
    
    # Calculate file size
    if cache.cache_file.exists():
        stats['cache_file_size'] = cache.cache_file.stat().st_size
    
    # Analyze entries
    current_time = time.time()
    entry_ages = []
    
    for key, entry in cache._cache.items():
        entry_ttl = entry.get('ttl', cache.ttl)
        entry_age = current_time - entry['timestamp']
        
        if entry_age > entry_ttl:
            stats['expired_entries'] += 1
        else:
            stats['active_entries'] += 1
            entry_ages.append(entry_age)
    
    if entry_ages:
        stats['oldest_entry_age'] = max(entry_ages)
        stats['newest_entry_age'] = min(entry_ages)
    
    return stats


def format_size(size_bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_duration(seconds):
    """Format seconds to human readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def create_cache_bar(value, max_value, width=50):
    """Create a visual bar for cache statistics."""
    if max_value == 0:
        percentage = 0
    else:
        percentage = min(100, (value / max_value) * 100)
    
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage:.1f}%"


def display_cache_stats(logger, silent):
    """Display cache statistics with visualizations."""
    stats = get_cache_stats()
    console = Console()
    
    if silent:
        # Output raw data for scripting
        print(f"total_entries:{stats['total_entries']}")
        print(f"active_entries:{stats['active_entries']}")
        print(f"expired_entries:{stats['expired_entries']}")
        print(f"ttl_minutes:{stats['ttl_minutes']}")
        print(f"cache_file_size:{stats['cache_file_size']}")
        return
    
    # Main statistics panel
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="cyan", width=25)
    stats_table.add_column(style="white")
    
    stats_table.add_row("Total entries", f"[bold]{stats['total_entries']}[/bold]")
    stats_table.add_row("Active entries", f"[bold green]{stats['active_entries']}[/bold green]")
    stats_table.add_row("Expired entries", f"[bold red]{stats['expired_entries']}[/bold red]")
    
    ttl_display = f"{stats['ttl_minutes']} minutes"
    if stats['configured_ttl_minutes']:
        ttl_display += f" (configured: {stats['configured_ttl_minutes']} min)"
    else:
        ttl_display += " (default)"
    stats_table.add_row("TTL", ttl_display)
    stats_table.add_row("Cache file size", format_size(stats['cache_file_size']))
    stats_table.add_row("Cache file path", stats['cache_file_path'])
    
    if stats['active_entries'] > 0:
        if stats['oldest_entry_age'] > 0:
            stats_table.add_row("Oldest entry", format_duration(stats['oldest_entry_age']))
        if stats['newest_entry_age'] > 0:
            stats_table.add_row("Newest entry", format_duration(stats['newest_entry_age']))
    
    console.print(Panel(stats_table, title="[bold cyan]Cache Statistics[/bold cyan]", border_style="cyan"))
    
    # Visual bars
    if stats['total_entries'] > 0:
        console.print()
        console.print("[bold]Entry Status Distribution[/bold]")
        
        # Active vs Expired bar
        max_entries = max(stats['active_entries'], stats['expired_entries'], 1)
        active_bar = create_cache_bar(stats['active_entries'], max_entries)
        expired_bar = create_cache_bar(stats['expired_entries'], max_entries)
        
        console.print(f"  [green]Active:[/green]   {active_bar}")
        console.print(f"  [red]Expired:[/red]   {expired_bar}")
        
        # Age distribution if we have active entries
        if stats['active_entries'] > 0 and stats['oldest_entry_age'] > 0:
            console.print()
            console.print("[bold]Entry Age Distribution[/bold]")
            
            # Create age buckets
            age_buckets = {
                '0-5 min': 0,
                '5-15 min': 0,
                '15-30 min': 0,
                '30-60 min': 0,
                '1h+': 0
            }
            
            from .cache import APICache
            import time
            cache = APICache()
            current_time = time.time()
            
            for entry in cache._cache.values():
                entry_age = current_time - entry['timestamp']
                entry_ttl = entry.get('ttl', cache.ttl)
                
                if entry_age <= entry_ttl:  # Only count active entries
                    age_minutes = entry_age / 60
                    if age_minutes < 5:
                        age_buckets['0-5 min'] += 1
                    elif age_minutes < 15:
                        age_buckets['5-15 min'] += 1
                    elif age_minutes < 30:
                        age_buckets['15-30 min'] += 1
                    elif age_minutes < 60:
                        age_buckets['30-60 min'] += 1
                    else:
                        age_buckets['1h+'] += 1
            
            max_bucket = max(age_buckets.values()) if age_buckets.values() else 1
            for bucket_name, count in age_buckets.items():
                if count > 0:
                    bar = create_cache_bar(count, max_bucket)
                    console.print(f"  {bucket_name:12} {bar}")


def display_overview(logger, silent):
    """Display overview statistics."""
    cache_stats = get_cache_stats()
    console = Console()
    
    if silent:
        # Output raw data
        display_cache_stats(logger, True)
        return
    
    # Display cache stats
    display_cache_stats(logger, False)
    
    console.print()
    
    # Summary panel
    from rich.text import Text
    summary_text = Text()
    summary_text.append("LeakPy Statistics Overview\n\n", style="bold cyan")
    summary_text.append(f"Cache: ", style="cyan")
    summary_text.append(f"{cache_stats['total_entries']} entries", style="white")
    summary_text.append(f" ({format_size(cache_stats['cache_file_size'])})", style="dim")
    summary_text.append("\n")
    summary_text.append(f"TTL: ", style="cyan")
    summary_text.append(f"{cache_stats['ttl_minutes']} minutes", style="white")
    
    console.print(Panel(summary_text, title="[bold]Summary[/bold]", border_style="blue"))


def load_results_from_file(file_path):
    """Load results from a JSON file."""
    import json
    from pathlib import Path
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'events' in data:
            return data['events']
        elif 'results' in data:
            return data['results']
        else:
            # Try to find a list in the dict
            for key, value in data.items():
                if isinstance(value, list):
                    return value
    return []


def display_stat_bar(label, value, max_value, width=40):
    """Create a visual bar for statistics."""
    if max_value == 0:
        percentage = 0
    else:
        percentage = (value / max_value) * 100
    
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    # Truncate label if too long (max 50 chars)
    if len(label) > 50:
        label = label[:47] + "..."
    return f"{label:<50} {bar} {value:>6} ({percentage:>5.1f}%)"


def execute_query_stats(args, logger, silent, client=None):
    """Execute query stats with client initialization if needed."""
    if not args.file and not client:
        from .leakix import LeakIX
        client = LeakIX(silent=silent)
        if not client.has_api_key():
            logger.error("API key is required for query statistics. Use 'leakpy config set' to set it.")
            sys.exit(1)
    display_query_stats(args, logger, silent, client)


def display_query_stats(args, logger, silent, client=None):
    """Display query statistics."""
    console = Console()
    
    # Load results
    if args.file:
        try:
            results = load_results_from_file(args.file)
            if not silent:
                logger.info(f"Loaded {len(results)} results from {args.file}")
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            sys.exit(1)
    elif client:
        # Make a new query
        results = client.search(
            scope=args.scope,
            pages=args.pages,
            query=args.query,
            fields="full",
            use_bulk=args.bulk
        )
        # Convert to list if needed
        if not isinstance(results, list):
            results = list(results)
    else:
        logger.error("Either --file or a query must be provided")
        sys.exit(1)
    
    if not results:
        logger.warning("No results to analyze")
        sys.exit(0)
    
    # Import stats module
    from . import stats as stats_module
    
    # Analyze results
    stats_result = stats_module.analyze_query_results(results, args.fields, args.all_fields)
    
    if silent:
        # Output raw data
        print(f"total:{stats_result.total}")
        # Convert to dict for iteration
        stats_dict = stats_result.to_dict()
        for field_name, field_stats in stats_dict['fields'].items():
            sorted_items = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)[:args.top]
            for value, count in sorted_items:
                print(f"{field_name}:{value}:{count}")
        return
    
    # Display statistics with visualizations
    console.print(Panel(f"[bold cyan]Query Statistics[/bold cyan]\n[dim]Total results: {stats_result.total}[/dim]", border_style="cyan"))
    console.print()
    
    # Convert to dict for iteration
    stats_dict = stats_result.to_dict()
    # Display stats for each field
    for field_name, field_stats in sorted(stats_dict['fields'].items()):
        if not field_stats:
            continue
        
        # Format field name for display
        display_name = field_name.replace('_', ' ').title()
        if '.' in display_name:
            # Handle nested fields like "geoip.country_name" -> "GeoIP: Country Name"
            parts = display_name.split('.')
            display_name = f"{parts[0].title()}: {' '.join(parts[1:]).title()}"
        
        console.print(f"[bold]{display_name}[/bold]")
        sorted_items = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)[:args.top]
        max_count = sorted_items[0][1] if sorted_items else 1
        
        # Create a table for better alignment
        stats_table = Table(show_header=False, box=None, padding=(0, 1))
        stats_table.add_column("Label", style="yellow", no_wrap=False)
        stats_table.add_column("Bar", style="cyan", width=40, no_wrap=True)
        stats_table.add_column("Count", style="white", justify="right", width=6, no_wrap=True)
        stats_table.add_column("Percentage", style="dim", justify="right", width=10, no_wrap=True)
        
        for value, count in sorted_items:
            # Handle list values (e.g., transport field)
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                # Try to parse as list representation
                try:
                    import ast
                    parsed_list = ast.literal_eval(value)
                    if isinstance(parsed_list, list):
                        # Display each item in the list separately
                        for item in parsed_list:
                            label = str(item)
                            percentage = (count / max_count) * 100 if max_count > 0 else 0
                            filled = int(40 * percentage / 100) if max_count > 0 else 0
                            bar = "█" * filled + "░" * (40 - filled)
                            stats_table.add_row(label, bar, str(count), f"({percentage:5.1f}%)")
                        continue
                except (ValueError, SyntaxError):
                    pass
            
            # Try to format port numbers nicely
            if field_name == 'port' and isinstance(value, str) and value.isdigit():
                label = f"Port {value}"
            else:
                label = str(value)
                # Truncate very long labels
                if len(label) > 60:
                    label = label[:57] + "..."
            
            percentage = (count / max_count) * 100 if max_count > 0 else 0
            filled = int(40 * percentage / 100) if max_count > 0 else 0
            bar = "█" * filled + "░" * (40 - filled)
            stats_table.add_row(label, bar, str(count), f"({percentage:5.1f}%)")
        
        console.print(stats_table)
        console.print()


# CLI list execution functions
def execute_list_plugins(args, client, logger, silent):
    """Execute list plugins command."""
    if args.silent or silent:
        for plugin in client.get_plugins():
            print(plugin)
    else:
        from leakpy.cli_helpers import handle_list_plugins
        handle_list_plugins(logger, client)


def execute_list_fields(args, client, logger, silent):
    """Execute list fields command."""
    if args.silent or silent:
        fields = get_all_fields_from_l9format_schema()
        for field in fields:
            print(field)
    else:
        from leakpy.cli_helpers import handle_list_fields
        if not handle_list_fields(logger, client, args.scope, args.query, None):
            import sys
            sys.exit(1)


# CLI config execution functions
def execute_config_reset(client, logger, silent):
    """Execute config reset command."""
    client.delete_api_key()
    if not silent:
        logger.info("API key has been reset.")


def execute_config_set(args, client, logger, silent):
    """Execute config set command."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    
    if args.api_key:
        api_key = args.api_key.strip()
    else:
        if silent:
            logger.error("API key is required in silent mode. Use: leakpy config set <api_key>")
            import sys
            sys.exit(1)
        session = PromptSession()
        logger.warning("Please enter your API key:")
        api_key = session.prompt(
            HTML("<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> "),
            is_password=True,
        ).strip()
    
    client.save_api_key(api_key)
    
    if not client.has_api_key():
        logger.error("The provided API key is invalid. It must be 48 characters long.")
        import sys
        sys.exit(1)
    
    if not silent:
        logger.info("API key has been saved successfully.")


# CLI cache execution functions
def execute_cache_clear(logger, silent):
    """Execute cache clear command."""
    from .cache import APICache
    cache = APICache()
    cache.clear()
    if not silent:
        logger.info("Cache cleared.")


def execute_cache_set_ttl(args, logger, silent):
    """Execute cache set-ttl command."""
    if args.minutes <= 0:
        logger.error("TTL must be a positive integer (minutes).")
        import sys
        sys.exit(1)
    
    from .config import CacheConfig
    cache_config = CacheConfig()
    cache_config.set_ttl_minutes(args.minutes)
    if not silent:
        logger.info(f"Cache TTL set to {args.minutes} minute(s) ({args.minutes * 60} seconds).")


def execute_cache_show_ttl(logger, silent):
    """Execute cache show-ttl command."""
    from .config import CacheConfig
    from .cache import APICache
    cache_config = CacheConfig()
    ttl_minutes = cache_config.get_ttl_minutes()
    
    if ttl_minutes is None:
        # Use default
        default_minutes = APICache.DEFAULT_TTL // 60
        if silent:
            print(f"{default_minutes}")
        else:
            logger.info(f"Cache TTL: {default_minutes} minute(s) (default)")
    else:
        if silent:
            print(f"{ttl_minutes}")
        else:
            logger.info(f"Cache TTL: {ttl_minutes} minute(s) ({ttl_minutes * 60} seconds)")


# CLI search execution function
def execute_search(args, client, stdout_redirected):
    """Execute search command."""
    import json
    import sys
    from leakpy.cli_helpers import normalize_plugins
    
    plugins = normalize_plugins(args.plugins)
    plugin_str = ",".join(plugins) if plugins else ""
    output_target = args.output or (sys.stdout if stdout_redirected else None)
    results = client.search(scope=args.scope, pages=args.pages, query=args.query, plugin=plugin_str, fields=args.fields, use_bulk=args.bulk, output=output_target)
    if not output_target and results and not args.silent:
        for result in results:
            print(json.dumps(to_dict_if_l9event(result)))
