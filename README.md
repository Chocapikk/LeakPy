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

# Lookup host details
$ leakpy lookup host 157.90.211.37

# Lookup domain details
$ leakpy lookup domain leakix.net

# Lookup subdomains
$ leakpy lookup subdomains leakix.net

# List plugins
$ leakpy list plugins

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
| `leakpy list fields` | `client.get_all_fields()` + `client.search()` |
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
results = client.search(scope="leak", query='+country:"France"', pages=1, fields="full")
if results:
    fields = client.get_all_fields(results[0])
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

Results are returned as ``l9event`` objects that support dot notation access. Use ``search()`` to get results. If you specify ``output``, results are written to a file but still returned.

```python
from leakpy import LeakIX

# Silent by default (no logs, no progress bars)
client = LeakIX()

# Enable logs and progress bars
client = LeakIX(silent=False)

# Get results as l9event objects
results = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5,
    fields="protocol,ip,port,host"
)

# Access fields using dot notation
for leak in results:
    protocol = leak.protocol  # "http"
    ip = leak.ip              # "1.2.3.4"
    port = leak.port          # 80
    host = leak.host          # "example.com"
    
    # Build URL
    if protocol and ip and port:
        url = f"{protocol}://{ip}:{port}"
        print(f"Target: {url}")
```

**Nested Fields:**

Access nested fields using dot notation:

```python
# Get full JSON to access all nested fields
results = client.search(
    scope="leak",
    query='+country:"France"',
    pages=2,
    fields="full"
)

for leak in results:
    # Root fields
    print(f"IP: {leak.ip}, Port: {leak.port}")
    
    # GeoIP fields
    if leak.geoip:
        print(f"Country: {leak.geoip.country_name}")
        print(f"City: {leak.geoip.city_name}")
    
    # HTTP fields
    if leak.http:
        print(f"HTTP Status: {leak.http.status}")
        print(f"HTTP Title: {leak.http.title}")
    
    # SSL fields
    if leak.ssl and leak.ssl.certificate:
        print(f"SSL CN: {leak.ssl.certificate.cn}")
```

**Host Details:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get detailed information about a specific IP
host_info = client.get_host("157.90.211.37")

# Access services and leaks with dot notation
if host_info['Services']:
    print(f"Found {len(host_info['Services'])} services:")
    for service in host_info['Services']:
        print(f"  {service.protocol}://{service.ip}:{service.port}")
        if service.host:
            print(f"    Host: {service.host}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")

if host_info['Leaks']:
    print(f"\nFound {len(host_info['Leaks'])} leaks:")
    for leak in host_info['Leaks']:
        if leak.leak:
            print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

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
if domain_info['Services']:
    print(f"Found {len(domain_info['Services'])} services:")
    for service in domain_info['Services']:
        print(f"  {service.protocol}://{service.host}:{service.port}")
        if service.ip:
            print(f"    IP: {service.ip}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")

if domain_info['Leaks']:
    print(f"\nFound {len(domain_info['Leaks'])} leaks:")
    for leak in domain_info['Leaks']:
        if leak.leak:
            print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

# Save to file
client.get_domain("leakix.net", output="domain_details.json")
```

**Subdomains:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get subdomains for a specific domain
subdomains = client.get_subdomains("leakix.net")

# Access subdomain details
print(f"Found {len(subdomains)} subdomains:")
for subdomain in subdomains:
    print(f"  {subdomain['subdomain']} - {subdomain['distinct_ips']} IPs")
    print(f"    Last seen: {subdomain['last_seen']}")

# Save to file
client.get_subdomains("leakix.net", output="subdomains.json")
```

**Cache Management:**

```python
from leakpy import LeakIX

client = LeakIX()

# Get cache statistics
stats = client.get_cache_stats()
print(f"Cache entries: {stats['total_entries']}")
print(f"Active entries: {stats['active_entries']}")
print(f"TTL: {stats['ttl_minutes']} minutes")

# Get current TTL
ttl = client.get_cache_ttl()
print(f"Current TTL: {ttl} minutes")

# Set cache TTL to 10 minutes
client.set_cache_ttl(10)

# Clear cache
client.clear_cache()
```

**Query Statistics (Object-Oriented):**

```python
from leakpy import LeakIX

client = LeakIX()

# Search for results
results = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5
)

# Object-oriented approach with callables (recommended)
stats = client.analyze_query_stats(results, fields={
    'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
    'protocol': lambda leak: leak.protocol,
    'port': lambda leak: leak.port
})

# Use dot notation (no dict access!)
print(f"Total results: {stats.total}")
print(f"France: {stats.fields.country.France} leaks")
print(f"HTTP: {stats.fields.protocol.http} services")
print(f"HTTPS: {stats.fields.protocol.https} services")

# Using named functions for complex logic
def get_port_category(leak):
    """Categorize ports into security zones."""
    if not leak.port:
        return None
    port = int(leak.port) if isinstance(leak.port, str) else leak.port
    if port < 1024:
        return "System ports"
    elif port < 49152:
        return "User ports"
    else:
        return "Dynamic ports"

stats = client.analyze_query_stats(results, fields={
    'port_category': get_port_category,
    'protocol': lambda leak: leak.protocol
})

# Access with dot notation (convert to dict for iteration)
port_cat_dict = stats.fields.port_category.to_dict()
for category, count in port_cat_dict.items():
    print(f"{category}: {count}")

# Analyze all fields
all_stats = client.analyze_query_stats(results, all_fields=True)
print(f"Found {len(all_stats.fields.to_dict())} different field types")
```

**Available Fields:**

LeakPy supports 71+ fields organized by category. The field structure follows the official `l9format schema <https://docs.leakix.net/docs/api/l9format/>`_ from LeakIX:
- **Root**: `ip`, `port`, `protocol`, `host`, `event_type`, etc.
- **GeoIP**: `geoip.country_name`, `geoip.city_name`, `geoip.location.lat`, etc.
- **HTTP**: `http.status`, `http.title`, `http.header.server`, etc.
- **SSL**: `ssl.version`, `ssl.certificate.cn`, `ssl.certificate.valid`, etc.
- **Leak**: `leak.type`, `leak.severity`, `leak.dataset.size`, etc.
- **Service**: `service.software.name`, `service.credentials.username`, etc.
- **SSH**: `ssh.version`, `ssh.banner`, etc.
- **Network**: `network.asn`, `network.organization_name`, etc.

See the `fields` documentation page for the complete list.

## 📚 Documentation

Full documentation: **https://leakpy.readthedocs.io/**

See [EXAMPLES.md](EXAMPLES.md) for more examples.

## 🚫 Disclaimer

LeakPy is an independent tool and has no affiliation with LeakIX. The creators of LeakPy cannot be held responsible for any misuse or potential damage resulting from using this tool. Please use responsibly, and ensure you have the necessary permissions when accessing any data.
