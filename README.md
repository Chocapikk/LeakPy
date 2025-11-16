# 🚀 LeakPy

```
   __            _   _____     
  |  |   ___ ___| |_|  _  |_ _ 
  |  |__| -_| .'| '_|   __| | | 
  |_____|___|__,|_,_|__|  |_  | 
                          |___|
```

[![PyPI version](https://badge.fury.io/py/leakpy.svg)](https://badge.fury.io/py/leakpy)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/leakpy?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/leakpy) [![Official Client Downloads](https://static.pepy.tech/personalized-badge/leakix?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=BLUE&left_text=official)](https://pepy.tech/projects/leakix)
[![Python 3.9-3.12](https://img.shields.io/badge/python-3.9--3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/Chocapikk/LeakPy/actions/workflows/tests.yml/badge.svg)](https://github.com/Chocapikk/LeakPy/actions/workflows/tests.yml)
[![Documentation](https://readthedocs.org/projects/leakpy/badge/?version=latest)](https://leakpy.readthedocs.io/)

LeakPy is a third-party client designed to seamlessly interact with the LeakIX API using Python.

> ❗ **Note:** This is **not** the official LeakIX client. Always refer to the [Official LeakIX Python Client](https://github.com/LeakIX/LeakIXClient-Python) for the official client.

## 📥 Installation

To install LeakPy via PyPi:

```bash
pip install leakpy
```

## 🔑 API Key

Get your API key from [LeakIX](https://leakix.net/) (48 characters). On first use, you'll be prompted to enter it. Reset: ``leakpy config reset``

**Secure Storage:** The API key is stored securely using your system's keychain (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux). If keyring is not available, it falls back to file storage with restrictive permissions (600).

**API Response Caching:** LeakPy automatically caches API responses to reduce unnecessary API calls. The cache uses a default TTL of 5 minutes (configurable). Clear the cache with ``leakpy cache clear`` or configure TTL with ``leakpy cache set-ttl``.

## 🖥️ CLI Usage 

LeakPy uses a subcommand-based CLI structure (similar to git). To see all available commands:

```bash
$ leakpy -h
```

Main commands:

- ``search`` - Search LeakIX for leaks or services
- ``lookup`` - Lookup information about specific IPs, domains, or subdomains
  - ``lookup host`` - Get detailed information about a specific IP address
  - ``lookup domain`` - Get detailed information about a specific domain and its subdomains
  - ``lookup subdomains`` - Get list of subdomains for a specific domain
- ``list`` - List available plugins or fields
- ``config`` - Manage API key configuration
- ``cache`` - Manage API response cache
- ``stats`` - Display statistics and metrics

Quick examples:

```bash
# Search
$ leakpy search -q '+country:"France"' -p 5

# Raw JSON output (for scripting/piping)
$ leakpy --raw search -q '+country:"France"' -p 5
$ leakpy --raw lookup host 157.90.211.37
$ leakpy --raw list plugins

# Lookup host details
$ leakpy lookup host 157.90.211.37

# Lookup domain details
$ leakpy lookup domain leakix.net

# Lookup subdomains
$ leakpy lookup subdomains leakix.net

# List plugins
$ leakpy list plugins

# List available fields
$ leakpy list fields

# Configure API key
$ leakpy config set

# Cache management
$ leakpy cache clear
$ leakpy cache set-ttl 10

# Statistics
$ leakpy stats cache
$ leakpy stats query -q '+country:"France"' -p 5
```

For detailed CLI documentation, see the `docs/cli.rst` file or run ``leakpy COMMAND --help`` for specific command help.

## 🔄 CLI vs Library

**All CLI functionalities are available via the Python library!**

| CLI Command | Library Method |
|------------|----------------|
| `leakpy search` | `client.search()` |
| `leakpy lookup host` | `client.get_host()` |
| `leakpy lookup domain` | `client.get_domain()` |
| `leakpy lookup subdomains` | `client.get_subdomains()` |
| `leakpy list plugins` | `client.get_plugins()` |
| `leakpy list fields` | `client.get_all_fields()` |
| `leakpy config set` | `client.save_api_key()` |
| `leakpy cache clear` | `client.clear_cache()` |
| `leakpy cache set-ttl` | `client.set_cache_ttl(minutes)` |
| `leakpy cache show-ttl` | `client.get_cache_ttl()` |
| `leakpy stats cache` | `client.get_cache_stats()` |
| `leakpy stats query` | `client.analyze_query_stats()` |

**Example:** To get available fields like `leakpy list fields`:

```python
from leakpy import LeakIX

client = LeakIX()

# Get all fields from schema (no API call needed)
fields = client.get_all_fields()
for field in sorted(fields):
    print(field)

# Or get fields from a specific event
events = list(client.search(scope="leak", query='+country:"France"', pages=1, fields="full"))
if events:
    fields = client.get_all_fields(events[0])
    for field in sorted(fields):
        print(field)
```

## 📘 Library Documentation

### LeakIX

The `LeakIX` class offers a direct and user-friendly interface to the LeakIX API.

**Key Features:**

* **Simple API**: One main method ``search()`` for all queries
* **Dot Notation**: Access fields with ``leak.ip`` instead of ``leak.get('ip')``
* **Silent by Default**: Perfect for scripting (no logs, no progress bars)
* **Always Returns Results**: Even when writing to a file, results are still returned

**Retrieving Results:**

Results are returned as ``L9Event`` objects that support dot notation access. Use ``search()`` to get events. If you specify ``output``, events are written to a file but still returned.

**Streaming:** ``search()`` returns a generator that streams events in real-time using HTTP streaming. Events are yielded as soon as they are received from the API, allowing you to process results immediately without waiting for all pages to be fetched.

```python
from leakpy import LeakIX

# Silent by default (no logs, no progress bars)
client = LeakIX()

# Enable logs and progress bars
client = LeakIX(silent=False)

# Get events as L9Event objects - events are streamed page by page in real-time
# By default, all fields are returned (fields="full")
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5
)

# Access fields using dot notation - events are processed as they arrive
for event in events:
    protocol = event.protocol  # "http"
    ip = event.ip              # "1.2.3.4"
    port = event.port          # 80
    host = event.host          # "example.com"
    
    # Access nested fields (available because fields="full" by default)
    if event.geoip:
        country = event.geoip.country_name
        city = event.geoip.city_name
    
    # Build URL
    if protocol and ip and port:
        url = f"{protocol}://{ip}:{port}"
        print(f"Target: {url}")

# Example output:
# Target: http://192.168.1.1:80
# Target: https://10.0.0.1:443
# Target: ssh://172.16.0.1:22
```

**Nested Fields:**

Access nested fields using dot notation:

```python
from leakpy import LeakIX

client = LeakIX()

# Get full JSON to access all nested fields (this is the default behavior)
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=2
)
# Or explicitly specify fields="full" if you prefer
# events = client.search(scope="leak", query='+country:"France"', pages=2, fields="full")

for event in events:
    # Root fields
    print(f"IP: {event.ip}, Port: {event.port}")
    
    # GeoIP fields
    if event.geoip:
        print(f"Country: {event.geoip.country_name}")
        print(f"City: {event.geoip.city_name}")
    
    # HTTP fields
    if event.http:
        print(f"HTTP Status: {event.http.status}")
        print(f"HTTP Title: {event.http.title}")
    
    # SSL fields
    if event.ssl and event.ssl.certificate:
        print(f"SSL CN: {event.ssl.certificate.cn}")

# Example output:
# IP: 192.168.1.1, Port: 80
# Country: France
# City: Paris
# HTTP Status: 200
# HTTP Title: Welcome to nginx
```

**Host Details:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get detailed information about a specific IP
host_info = client.get_host("157.90.211.37")

# Access services and leaks with dot notation
if host_info.services:
    print(f"Found {len(host_info.services)} services:")
    for service in host_info.services:
        print(f"  {service.protocol}://{service.ip}:{service.port}")
        if service.host:
            print(f"    Host: {service.host}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")

if host_info.leaks:
    print(f"\nFound {len(host_info.leaks)} leaks:")
    for leak in host_info.leaks:
        if leak.leak:
            print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

# Example output:
# Found 3 services:
#   http://157.90.211.37:80
#     Host: example.com
#     HTTP Status: 200
#   https://157.90.211.37:443
#   ssh://157.90.211.37:22
#
# Found 1 leaks:
#   Type: credential, Severity: high

# Save to file
client.get_host("157.90.211.37", output="host_details.json")
```

**Domain Details:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get detailed information about a specific domain
domain_info = client.get_domain("leakix.net")

# Access services and leaks with dot notation
if domain_info.services:
    print(f"Found {len(domain_info.services)} services:")
    for service in domain_info.services:
        print(f"  {service.protocol}://{service.host}:{service.port}")
        if service.ip:
            print(f"    IP: {service.ip}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")

if domain_info.leaks:
    print(f"\nFound {len(domain_info.leaks)} leaks:")
    for leak in domain_info.leaks:
        if leak.leak:
            print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

# Example output:
# Found 2 services:
#   https://leakix.net:443
#     IP: 157.90.211.37
#     HTTP Status: 200
#   http://leakix.net:80
#
# Found 1 leaks:
#   Type: credential, Severity: high

# Save to file
client.get_domain("leakix.net", output="domain_details.json")
```

**Subdomains:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get subdomains for a specific domain
subdomains = client.get_subdomains("leakix.net")

# Access subdomain details with dot notation
print(f"Found {len(subdomains)} subdomains:")
for subdomain in subdomains:
    print(f"  {subdomain.subdomain} - {subdomain.distinct_ips} IPs")
    print(f"    Last seen: {subdomain.last_seen}")

# Example output:
# Found 3 subdomains:
#   www.leakix.net - 1 IPs
#     Last seen: 2024-01-15T10:30:00Z
#   staging.leakix.net - 1 IPs
#     Last seen: 2024-01-14T15:20:00Z
#   blog.leakix.net - 2 IPs
#     Last seen: 2024-01-13T09:10:00Z

# Save to file
client.get_subdomains("leakix.net", output="subdomains.json")
```

**Cache Management:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get cache statistics
stats = client.get_cache_stats()
print(f"Cache entries: {stats.total_entries}")
print(f"Active entries: {stats.active_entries}")
print(f"TTL: {stats.ttl_minutes} minutes")

# Get current TTL
ttl = client.get_cache_ttl()
print(f"Current TTL: {ttl} minutes")

# Set cache TTL to 10 minutes
client.set_cache_ttl(10)

# Clear cache
client.clear_cache()

# Example output:
# Cache entries: 42
# Active entries: 15
# TTL: 5 minutes
# Current TTL: 5 minutes
```

**Query Statistics (Object-Oriented):**

```python
from leakpy import LeakIX

client = LeakIX()

# Search for events
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5
)

# Simple approach using field paths
stats = client.analyze_query_stats(events, fields='geoip.country_name,protocol')

# Use dot notation
print(f"Total results: {stats.total}")
print(f"France: {stats.fields.geoip.country_name.France} leaks")
print(f"HTTP: {stats.fields.protocol.http} services")
print(f"HTTPS: {stats.fields.protocol.https} services")

# Analyze all fields
all_stats = client.analyze_query_stats(events, all_fields=True)
print(f"Found {len(all_stats.fields.to_dict())} different field types")
```

**Large Queries:**

The generator-based approach is especially beneficial for large queries. You can process results in real-time and stop early if needed:

```python
from leakpy import LeakIX
import time

client = LeakIX()

start_time = time.time()
count = 0

events = client.search(scope="leak", query="country:France", use_bulk=True)

for event in events:
    count += 1
    if event.ip and event.port:
        print(f"{count}. {event.protocol}://{event.ip}:{event.port}")
    if count >= 2000:
        break

# HTTP connection is automatically closed when generator is garbage collected
# For immediate closure, you can explicitly call: events.close()

elapsed = time.time() - start_time
print(f"Processed {count} results in {elapsed:.2f} seconds")
print(f"Speed: {count/elapsed:.1f} results/second")

# Example output:
# 1. https://192.168.1.1:443
# 2. http://10.0.0.1:80
# 3. https://172.16.0.1:443
# ...
# Processed 2000 results in 5.29 seconds
# Speed: 378.4 results/second
```

**Note:** When you stop early with a `break`, the HTTP connection is automatically closed when the generator is garbage collected (which happens automatically in Python). For immediate closure to stop fetching data right away, you can explicitly call `events.close()` after the break.

**Available Fields:**

LeakPy supports 82+ fields organized by category. Get all available fields:

```python
from leakpy import LeakIX

client = LeakIX()
fields = client.get_all_fields()  # No API call needed
for field in sorted(fields):
    print(field)
```

The field structure follows the official [l9format schema](https://docs.leakix.net/docs/api/l9format/) from LeakIX:
- **Root**: `ip`, `port`, `protocol`, `host`, `event_type`, etc.
- **GeoIP**: `geoip.country_name`, `geoip.city_name`, `geoip.location.lat`, etc.
- **HTTP**: `http.status`, `http.title`, `http.header.server`, etc.
- **SSL**: `ssl.version`, `ssl.certificate.cn`, `ssl.certificate.valid`, etc.
- **Leak**: `leak.type`, `leak.severity`, `leak.dataset.size`, etc.
- **Service**: `service.software.name`, `service.credentials.username`, etc.
- **SSH**: `ssh.version`, `ssh.banner`, etc.
- **Network**: `network.asn`, `network.organization_name`, etc.

See the [fields documentation page](https://leakpy.readthedocs.io/en/latest/fields.html) for the complete list.

## 📚 Documentation

Full documentation: **https://leakpy.readthedocs.io/**

See [EXAMPLES.md](EXAMPLES.md) for more examples.

## 🚫 Disclaimer

LeakPy is an independent tool and has no affiliation with LeakIX. The creators of LeakPy cannot be held responsible for any misuse or potential damage resulting from using this tool. Please use responsibly, and ensure you have the necessary permissions when accessing any data.
