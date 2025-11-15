# LeakPy Examples

This document provides examples of how to use LeakPy both as a CLI tool and as a Python library.

## 🔑 API Key Setup

### API Key Setup

Get your API key from [LeakIX](https://leakix.net/) (must be 48 characters).

On first use, you'll be prompted to enter it. To reset: ``leakpy config reset``

## 📋 CLI Examples

### List Available Plugins

```bash
$ leakpy list plugins
```

### List Available Fields

```bash
$ leakpy list fields
```

### Basic Search

```bash
# Search for leaks in France
$ leakpy search -q '+country:"France"' -p 5

# Search with specific plugin
$ leakpy search -q '+country:"France"' -P PulseConnectPlugin -p 3

# Save results to file
$ leakpy search -q '+country:"France"' -p 5 -o results.txt
```

### Extract Specific Fields

```bash
# Extract only protocol, IP, and port (default)
$ leakpy search -q '+country:"France"' -f protocol,ip,port

# Extract custom fields
$ leakpy search -q '+country:"France"' -f protocol,ip,port,host,event_source

# Get complete JSON
$ leakpy search -q '+country:"France"' -f full -o results.json
```

### Bulk Mode (Pro API Required)

```bash
# Use bulk mode for faster results (requires Pro API)
$ leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt
```

### Service Scope

```bash
# Search in service scope instead of leak scope
$ leakpy search -s service -q 'port:3306' -p 3
```

### Silent Mode (Scripting)

```bash
# Silent mode suppresses all logs and progress bars (useful for scripting)
$ leakpy --silent search -q '+country:"France"' -p 5 -o results.txt

# List plugins in silent mode (outputs only plugin names, one per line)
$ leakpy --silent list plugins

# List fields in silent mode (outputs only field names, one per line)
$ leakpy --silent list fields -q '+country:"France"'
```

### Cache Management

LeakPy automatically caches API responses to reduce unnecessary API calls. The cache uses a default TTL of 5 minutes (configurable).

```bash
# Clear the cache manually
$ leakpy cache clear

# Set cache TTL to 10 minutes
$ leakpy cache set-ttl 10

# Show current cache TTL
$ leakpy cache show-ttl
```

### Statistics

```bash
# Display cache statistics
$ leakpy stats cache

# Analyze query statistics (by country, protocol, etc.)
$ leakpy stats query -q '+country:"France"' -p 5

# Analyze statistics from a JSON file
$ leakpy stats query -f results.json

# Analyze specific fields
$ leakpy stats query -f results.json --fields "geoip.country_name,protocol,port"
```

**Cache Location:**
- Linux/macOS: `~/.config/LeakPy/api_cache.json`
- Windows: `%LOCALAPPDATA%\LeakPy\api_cache.json`

## 🐍 Python Library Examples

### Basic Usage

```python
from leakpy import LeakIX

# Initialize client
client = LeakIX()

# Or provide API key directly
client = LeakIX(api_key="your_48_character_api_key_here")

# Save API key for future use
client.save_api_key("your_api_key_here")
```

### Search with Default Fields

```python
from leakpy import LeakIX

client = LeakIX()

# Search for leaks in France
events = client.search(
    scope="leak",
    pages=5,
    query='+country:"France"'
)

for event in events:
    if event.protocol in ('http', 'https') and event.ip and event.port:
        print(f"{event.protocol}://{event.ip}:{event.port}")
    elif event.ip and event.port:
        print(f"{event.protocol} {event.ip}:{event.port}")
```

### Search with Custom Fields

```python
from leakpy import LeakIX

client = LeakIX()

# Extract specific fields
events = client.search(
    scope="leak",
    pages=3,
    query='+country:"France"',
    fields="protocol,ip,port,host"
)

for event in events:
    if event.protocol in ('http', 'https') and event.ip and event.port:
        host_str = f" - {event.host}" if event.host else ""
        print(f"{event.protocol}://{event.ip}:{event.port}{host_str}")
    elif event.ip and event.port:
        host_str = f" - {event.host}" if event.host else ""
        print(f"{event.protocol} {event.ip}:{event.port}{host_str}")
```

### Get Complete JSON

```python
from leakpy import LeakIX

client = LeakIX()

# Get full JSON data
events = client.search(
    scope="leak",
    pages=2,
    query='+country:"France"',
    fields="full"
)

for event in events:
    print(f"IP: {event.ip}, Port: {event.port}")
    if event.geoip:
        print(f"Country: {event.geoip.country_name}")
```

### Search with Plugin

```python
from leakpy import LeakIX

client = LeakIX()

# Search with specific plugin
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5,
    plugin="PulseConnectPlugin"
)

for event in events:
    if event.protocol in ('http', 'https') and event.ip and event.port:
        print(f"{event.protocol}://{event.ip}:{event.port}")
    elif event.ip and event.port:
        print(f"{event.protocol} {event.ip}:{event.port}")
```

### List Plugins

```python
from leakpy import LeakIX

client = LeakIX()

plugins = client.get_plugins()
for plugin in plugins:
    print(plugin)
```

### List Available Fields

```python
from leakpy import LeakIX

client = LeakIX()

# Get a sample event
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=1,
    fields="full"
)

# Get all available fields
if events:
    fields = client.get_all_fields(events[0])
    for field in sorted(fields):
        print(field)
```

### Bulk Mode (Pro API)

```python
from leakpy import LeakIX

client = LeakIX()

# Use bulk mode for faster results (requires Pro API)
events = client.search(
    scope="leak",
    plugin="TraccarPlugin",
    use_bulk=True,
    output="bulk_results.txt"
)

for event in events:
    if event.protocol in ('http', 'https') and event.ip and event.port:
        print(f"{event.protocol}://{event.ip}:{event.port}")
    elif event.ip and event.port:
        print(f"{event.protocol} {event.ip}:{event.port}")
```

### Host Details

```python
from leakpy import LeakIX

client = LeakIX()

# Get detailed information about a specific IP
host_info = client.get_host("157.90.211.37")

# Access services
if host_info.Services:
    for service in host_info.Services:
        if service.protocol in ('http', 'https') and service.ip and service.port:
            print(f"{service.protocol}://{service.ip}:{service.port}")
        elif service.ip and service.port:
            print(f"{service.protocol} {service.ip}:{service.port}")
        if service.http and service.http.title:
            print(f"  Title: {service.http.title}")

# Access leaks
if host_info.Leaks:
    for event in host_info.Leaks:
        if event.leak:
            print(f"Leak: {event.leak.type} ({event.leak.severity})")

# Save to file
client.get_host("157.90.211.37", output="host_details.json")
```

### Domain Details

```python
from leakpy import LeakIX

client = LeakIX()

# Get detailed information about a domain
domain_info = client.get_domain("leakix.net")

# Access services
if domain_info.Services:
    for service in domain_info.Services:
        if service.protocol in ('http', 'https') and service.host and service.port:
            print(f"{service.protocol}://{service.host}:{service.port}")
        elif service.host and service.port:
            print(f"{service.protocol} {service.host}:{service.port}")

# Access leaks
if domain_info.Leaks:
    for event in domain_info.Leaks:
        if event.leak:
            print(f"Leak: {event.leak.type} ({event.leak.severity})")

# Save to file
client.get_domain("leakix.net", output="domain_details.json")
```

### Subdomains

```python
from leakpy import LeakIX

client = LeakIX()

# Get subdomains for a domain
subdomains = client.get_subdomains("leakix.net")

for subdomain in subdomains:
    print(f"{subdomain.subdomain} - {subdomain.distinct_ips} IPs")

# Save to file
client.get_subdomains("leakix.net", output="subdomains.json")
```

### Cache Management

```python
from leakpy import LeakIX

client = LeakIX()

# Get cache statistics
stats = client.get_cache_stats()
print(f"Entries: {stats.active_entries}/{stats.total_entries}")

# Set cache TTL to 10 minutes
client.set_cache_ttl(10)

# Clear cache
client.clear_cache()
```

### Query Statistics

```python
from leakpy import LeakIX

client = LeakIX()

# Search for events
events = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5,
    fields="full"
)

# Analyze statistics using field paths
stats = client.analyze_query_stats(events, fields="geoip.country_name,protocol")

print(f"Total: {stats.total}")
print(f"France: {stats.fields.geoip.country_name.France}")
print(f"HTTP: {stats.fields.protocol.http}")
print(f"HTTPS: {stats.fields.protocol.https}")
```

### Advanced Search

```python
from leakpy import LeakIX

client = LeakIX()

# Search with plugin and custom fields
events = client.search(
    scope="leak",
    pages=3,
    query='+country:"France"',
    plugin="PulseConnectPlugin",
    fields="protocol,ip,port,host"
)

for event in events:
    if event.protocol in ('http', 'https') and event.ip and event.port:
        host_str = f" - {event.host}" if event.host else ""
        print(f"{event.protocol}://{event.ip}:{event.port}{host_str}")
    elif event.ip and event.port:
        host_str = f" - {event.host}" if event.host else ""
        print(f"{event.protocol} {event.ip}:{event.port}{host_str}")
```

## 🔧 Error Handling

### Missing API Key

```python
from leakpy import LeakIX

client = LeakIX()

if not client.has_api_key():
    print("Please set your API key:")
    api_key = input("API Key: ")
    client.save_api_key(api_key)
```

### Invalid API Key

```python
from leakpy import LeakIX

client = LeakIX(api_key="invalid_key")

if not client.has_api_key():
    print("API key is invalid. It must be 48 characters long.")
```

### Query Errors

```python
from leakpy import LeakIX

client = LeakIX(silent=False)

try:
    events = client.search(
        scope="leak",
        pages=5,
        query='invalid query syntax',
    )
    if not events:
        print("No events found. Check your query.")
except ValueError as e:
    print(f"Error: {e}")
```

## 📝 Notes

- API keys are stored securely with proper file permissions (600 on Linux/macOS)
- The API key is automatically migrated from old location (`~/.local/.api.txt`) if it exists
- Bulk mode requires a Pro API key from LeakIX
- Free API keys have page limits

