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
  leakpy --raw lookup host 157.90.211.37 -o host.json"""

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
  leakpy --raw lookup domain leakix.net -o domain.json"""

_SUBDOMAINS_EXAMPLES = """Examples:
  # Get subdomains for a domain
  leakpy lookup subdomains leakix.net

  # Get subdomains and save to file
  leakpy lookup subdomains leakix.net -o subdomains.json

  # Batch processing from file (one domain per line)
  leakpy lookup subdomains -i domains.txt -o results.json

  # Silent mode for scripting (outputs one subdomain per line)
  leakpy --raw lookup subdomains leakix.net

  # Save to file in raw mode
  leakpy --raw lookup subdomains leakix.net -o subdomains.txt"""

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
  leakpy --raw cache show-ttl"""

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
  leakpy --raw list plugins"""

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
  leakpy --raw list fields -q '+country:"France"'"""

# CLI search constants
_SEARCH_EXAMPLES = """Examples:
  # Search for leaks in France
  leakpy search -q '+country:"France"' -p 5

  # Search with specific plugin
  leakpy search -q '+country:"France"' -P PulseConnectPlugin -p 3

  # Extract specific fields (default: protocol,ip,port for URL formatting)
  leakpy search -q '+country:"France"' -f protocol,ip,port,host

  # Get complete JSON and save to file
  leakpy search -q '+country:"France"' -f full -o results.json

  # Use bulk mode (requires Pro API, only works with scope="leak")
  leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

  # Silent mode for scripting
  leakpy --raw search -q '+country:"France"' -p 5 -o results.txt"""

# CLI stats constants
_STATS_CACHE_EXAMPLES = """Examples:
  # Display cache statistics
  leakpy stats cache

  # Display cache stats in silent mode (for scripting)
  leakpy --raw stats cache"""

_STATS_QUERY_EXAMPLES = """Examples:
  # Analyze query statistics from a live query
  leakpy stats query -q '+country:"France"' -p 5

  # Use bulk mode for faster queries (requires Pro API, only works with scope="leak")
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
  leakpy --raw stats query -f results.json"""

