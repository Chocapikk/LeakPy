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
$ leakpy search -q '+country:"France"' -b -o results.txt
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
from leakpy import LeakIXScraper

# Initialize scraper (API key will be loaded from config if available)
scraper = LeakIXScraper(verbose=True)

# Or provide API key directly
scraper = LeakIXScraper(api_key="your_48_character_api_key_here", verbose=True)

# Silent mode (no logs, no progress bar) - useful for scripting
scraper = LeakIXScraper(api_key="your_48_character_api_key_here", verbose=False, silent=True)

# Check if API key is valid
if not scraper.has_api_key():
    print("API key is missing or invalid")
    # You can save it:
    scraper.save_api_key("your_api_key_here")
```

### Search with Default Fields

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Search for leaks in France (default: protocol, ip, port)
results = scraper.run(
    scope="leak",
    pages=5,
    query='+country:"France"',
    output="results.txt"
)

# Results will contain URLs like: http://1.2.3.4:80
for result in results:
    print(result.get('url'))
```

### Search with Custom Fields

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Extract specific fields
results = scraper.run(
    scope="leak",
    pages=3,
    query='+country:"France"',
    fields="protocol,ip,port,host,event_source",
    output="results.json"
)

for result in results:
    print(f"IP: {result.get('ip')}")
    print(f"Port: {result.get('port')}")
    print(f"Host: {result.get('host')}")
    print("-" * 20)
```

### Get Complete JSON

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Get full JSON data
results = scraper.run(
    scope="leak",
    pages=2,
    query='+country:"France"',
    fields="full",
    output="full_results.json"
)

# Each result contains the complete JSON object
for result in results:
    print(result)  # Complete JSON object
```

### Using execute() Method

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Use execute() method (returns results directly)
results = scraper.execute(
    scope="leak",
    query='+country:"France"',
    pages=5,
    plugin="PulseConnectPlugin",
    fields="protocol,ip,port,host",
    use_bulk=False
)

for result in results:
    print(f"IP: {result.get('ip')}, Port: {result.get('port')}")
```

### List Plugins

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

plugins = scraper.get_plugins()
print(f"Available plugins: {len(plugins)}")
for plugin in plugins:
    print(f"  - {plugin}")
```

### List Available Fields

```python
from leakpy import LeakIXScraper
from leakpy.cli.helpers import _extract_sample_event

scraper = LeakIXScraper(verbose=True)

# Get sample data and extract all possible fields
sample_data = scraper.query(scope="leak", pages=1, query_param='+country:"France"', return_data_only=True)
sample_event = _extract_sample_event(sample_data)
if sample_event:
    fields = scraper.get_all_fields(sample_event)
    for field in fields:
        print(field)
```

### Bulk Mode (Pro API)

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Use bulk mode for faster results (requires Pro API)
results = scraper.run(
    scope="leak",
    pages=1,  # Not used in bulk mode
    query='+country:"France"',
    use_bulk=True,
    output="bulk_results.txt"
)
```

### Host Details

```python
from leakpy import LeakIX

client = LeakIX()

# 🔍 Get detailed information about a specific IP
host_info = client.get_host("157.90.211.37")

# Access services with dot notation
if host_info['Services']:
    print(f"🌐 Found {len(host_info['Services'])} services:")
    for service in host_info['Services']:
        print(f"  {service.protocol}://{service.ip}:{service.port}")
        if service.host:
            print(f"    Hostname: {service.host}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")
        if service.http and service.http.title:
            print(f"    Page Title: {service.http.title}")
        if service.ssl and service.ssl.certificate:
            print(f"    SSL CN: {service.ssl.certificate.cn}")

# Access leaks
if host_info['Leaks']:
    print(f"\n⚠️  Found {len(host_info['Leaks'])} leaks:")
    for leak in host_info['Leaks']:
        if leak.leak:
            print(f"  Type: {leak.leak.type}")
            print(f"  Severity: {leak.leak.severity}")
            if leak.leak.dataset:
                print(f"  Dataset Size: {leak.leak.dataset.size}")

# 🎯 Fun Example: Security Reconnaissance
def recon_ip(ip):
    """Perform reconnaissance on an IP address."""
    host_info = client.get_host(ip)
    
    print(f"\n{'='*50}")
    print(f"🔍 RECONNAISSANCE REPORT: {ip}")
    print(f"{'='*50}")
    
    if host_info['Services']:
        print(f"\n🌐 Services ({len(host_info['Services'])}):")
        for service in host_info['Services']:
            url = f"{service.protocol}://{service.ip}:{service.port}"
            print(f"  • {url}")
            if service.host:
                print(f"    └─ Host: {service.host}")
    
    if host_info['Leaks']:
        print(f"\n⚠️  Leaks Found ({len(host_info['Leaks'])}):")
        for leak in host_info['Leaks']:
            if leak.leak:
                severity_emoji = "🔴" if leak.leak.severity == "high" else "🟡" if leak.leak.severity == "medium" else "🟢"
                print(f"  {severity_emoji} {leak.leak.type} ({leak.leak.severity})")
    else:
        print("\n✅ No leaks found")
    
    print(f"\n{'='*50}")

# Use it!
recon_ip("157.90.211.37")

# Save to file
client.get_host("157.90.211.37", output="recon_report.json")
```

### Domain Details

```python
from leakpy import LeakIX

client = LeakIX()

# 🔍 Get detailed information about a specific domain
domain_info = client.get_domain("leakix.net")

# Access services with dot notation
if domain_info['Services']:
    print(f"🌐 Found {len(domain_info['Services'])} services:")
    for service in domain_info['Services']:
        print(f"  {service.protocol}://{service.host}:{service.port}")
        if service.ip:
            print(f"    IP: {service.ip}")
        if service.http and service.http.status:
            print(f"    HTTP Status: {service.http.status}")
        if service.http and service.http.title:
            print(f"    Page Title: {service.http.title}")
        if service.ssl and service.ssl.certificate:
            print(f"    SSL CN: {service.ssl.certificate.cn}")

# Access leaks
if domain_info['Leaks']:
    print(f"\n⚠️  Found {len(domain_info['Leaks'])} leaks:")
    for leak in domain_info['Leaks']:
        if leak.leak:
            print(f"  Type: {leak.leak.type}")
            print(f"  Severity: {leak.leak.severity}")
            if leak.leak.dataset:
                print(f"  Dataset Size: {leak.leak.dataset.size}")

# 🎯 Fun Example: Domain Reconnaissance
def recon_domain(domain):
    """Perform reconnaissance on a domain."""
    domain_info = client.get_domain(domain)
    
    print(f"\n{'='*50}")
    print(f"🔍 DOMAIN RECONNAISSANCE: {domain}")
    print(f"{'='*50}")
    
    if domain_info['Services']:
        print(f"\n🌐 Services ({len(domain_info['Services'])}):")
        # Group by subdomain
        subdomains = {}
        for service in domain_info['Services']:
            host = service.host or "N/A"
            if host not in subdomains:
                subdomains[host] = []
            subdomains[host].append(service)
        
        for host, services in sorted(subdomains.items()):
            print(f"  📍 {host}:")
            for service in services:
                url = f"{service.protocol}://{host}:{service.port}"
                print(f"    • {url}")
                if service.ip:
                    print(f"      └─ IP: {service.ip}")
    
    if domain_info['Leaks']:
        print(f"\n⚠️  Leaks Found ({len(domain_info['Leaks'])}):")
        for leak in domain_info['Leaks']:
            if leak.leak:
                severity_emoji = "🔴" if leak.leak.severity == "high" else "🟡" if leak.leak.severity == "medium" else "🟢"
                print(f"  {severity_emoji} {leak.leak.type} ({leak.leak.severity})")
    else:
        print("\n✅ No leaks found")
    
    print(f"\n{'='*50}")

# Use it!
recon_domain("leakix.net")

# Save to file
client.get_domain("leakix.net", output="domain_recon.json")
```

### Subdomains

```python
from leakpy import LeakIX

client = LeakIX()

# 🔍 Get subdomains for a specific domain
subdomains = client.get_subdomains("leakix.net")

# Access subdomain details
print(f"🌐 Found {len(subdomains)} subdomains:")
for subdomain in subdomains:
    print(f"  • {subdomain['subdomain']}")
    print(f"    └─ {subdomain['distinct_ips']} distinct IP(s)")
    print(f"    └─ Last seen: {subdomain['last_seen']}")

# 🎯 Fun Example: Subdomain Discovery
def discover_subdomains(domain):
    """Discover and analyze subdomains for a domain."""
    subdomains = client.get_subdomains(domain)
    
    print(f"\n{'='*50}")
    print(f"🔍 SUBDOMAIN DISCOVERY: {domain}")
    print(f"{'='*50}")
    
    if subdomains:
        print(f"\n📋 Found {len(subdomains)} subdomains:\n")
        
        # Sort by last_seen (most recent first)
        sorted_subs = sorted(
            subdomains, 
            key=lambda x: x.get('last_seen', ''), 
            reverse=True
        )
        
        for i, subdomain in enumerate(sorted_subs, 1):
            subdomain_name = subdomain['subdomain']
            distinct_ips = subdomain.get('distinct_ips', 0)
            last_seen = subdomain.get('last_seen', 'N/A')
            
            print(f"  {i}. {subdomain_name}")
            print(f"     IPs: {distinct_ips} | Last seen: {last_seen}")
    else:
        print("\n❌ No subdomains found")
    
    print(f"\n{'='*50}")
    
    return subdomains

# Use it!
discover_subdomains("leakix.net")

# Save to file
client.get_subdomains("leakix.net", output="subdomains.json")
```

### Cache Management

```python
from leakpy import LeakIX

client = LeakIX()

# Get cache statistics
stats = client.get_cache_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Active entries: {stats['active_entries']}")
print(f"Expired entries: {stats['expired_entries']}")
print(f"Cache size: {stats['cache_file_size']} bytes")
print(f"TTL: {stats['ttl_minutes']} minutes")

# Get current TTL
ttl = client.get_cache_ttl()
print(f"Current TTL: {ttl} minutes")

# Set cache TTL to 10 minutes
client.set_cache_ttl(10)

# Clear all cache entries
client.clear_cache()
```

### Query Statistics (Object-Oriented)

```python
from leakpy import LeakIX

client = LeakIX()

# Search for results
results = client.search(
    scope="leak",
    query='+country:"France"',
    pages=5,
    fields="full"
)

# 🎯 Object-oriented approach with callables (RECOMMENDED)
# Use direct dot notation - clean and Pythonic!
stats = client.analyze_query_stats(results, fields={
    'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
    'protocol': lambda leak: leak.protocol,
    'port': lambda leak: leak.port,
    'city': lambda leak: leak.geoip.city_name if leak.geoip else None
}, top=10)

# ✨ Use dot notation (no dict access!)
print(f"📊 Total results: {stats.total}")
print(f"🇫🇷 France: {stats.fields.country.France} leaks")
print(f"🌐 HTTP: {stats.fields.protocol.http} services")
print(f"🔒 HTTPS: {stats.fields.protocol.https} services")
print(f"🏙️  Paris: {stats.fields.city.Paris} leaks")

# 🎨 Using named functions for complex logic
def get_severity_level(leak):
    """Categorize leaks by port security level."""
    if not leak.port:
        return "Unknown"
    port = int(leak.port) if isinstance(leak.port, str) else leak.port
    
    # Common dangerous ports
    dangerous = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 5432, 6379, 27017]
    if port in dangerous:
        return "⚠️  High Risk"
    elif port < 1024:
        return "🔐 System Port"
    else:
        return "✅ User Port"

def get_port_category(leak):
    """Categorize ports into ranges."""
    if not leak.port:
        return None
    port = int(leak.port) if isinstance(leak.port, str) else leak.port
    if port < 1024:
        return "Well-known (0-1023)"
    elif port < 49152:
        return "Registered (1024-49151)"
    else:
        return "Dynamic (49152-65535)"

stats = client.analyze_query_stats(results, fields={
    'severity': get_severity_level,
    'port_category': get_port_category,
    'protocol': lambda leak: leak.protocol
})

# Access with dot notation
print(f"\n🔍 Security Analysis:")
# Note: For values with special characters, convert to dict first
severity_dict = stats.fields.severity.to_dict()
print(f"High Risk: {severity_dict.get('⚠️  High Risk', 0)}")
port_cat_dict = stats.fields.port_category.to_dict()
print(f"System Ports: {port_cat_dict.get('Well-known (0-1023)', 0)}")

# 🚀 Real-world example: Find most common protocols
stats = client.analyze_query_stats(results, fields={
    'protocol': lambda leak: leak.protocol
}, top=5)

print(f"\n📈 Top Protocols:")
# Convert to dict to iterate
stats_dict = stats.fields.protocol.to_dict()
for protocol, count in sorted(stats_dict.items(), key=lambda x: x[1], reverse=True):
    print(f"  {protocol}: {count} leaks")

# 🌍 Geographic distribution
stats = client.analyze_query_stats(results, fields={
    'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
    'city': lambda leak: leak.geoip.city_name if leak.geoip else None
})

print(f"\n🌍 Geographic Distribution:")
print(f"Countries found: {len(stats.fields.country.to_dict())}")
print(f"Cities found: {len(stats.fields.city.to_dict())}")

# Analyze all available fields
all_stats = client.analyze_query_stats(
    results,
    all_fields=True,
    top=5  # Top 5 values per field
)
print(f"\n📋 Found {len(all_stats.fields.to_dict())} different field types to analyze!")

# 🎮 Fun Example: Create a security report
def create_security_report(results):
    """Generate a fun security report with emojis."""
    stats = client.analyze_query_stats(results, fields={
        'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
        'protocol': lambda leak: leak.protocol,
        'port': lambda leak: leak.port
    })
    
    print("=" * 50)
    print("🔐 SECURITY REPORT 🔐")
    print("=" * 50)
    print(f"\n📊 Total Leaks Found: {stats.total}")
    
    # Geographic breakdown
    print("\n🌍 Geographic Distribution:")
    country_dict = stats.fields.country.to_dict()
    for country, count in sorted(country_dict.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * count
        print(f"  {country}: {bar} {count}")
    
    # Protocol breakdown
    print("\n🌐 Protocol Distribution:")
    protocol_dict = stats.fields.protocol.to_dict()
    for protocol, count in sorted(protocol_dict.items(), key=lambda x: x[1], reverse=True):
        emoji = "🔒" if protocol == "https" else "🌐" if protocol == "http" else "🔑"
        print(f"  {emoji} {protocol.upper()}: {count}")
    
    print("\n" + "=" * 50)

# Use it!
create_security_report(results)
```

### Direct Query (Advanced)

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

# Direct query with more control (advanced usage)
# Use scraper.run() for simpler usage
results = scraper.query(
    scope="leak",
    pages=3,
    query_param='+country:"France"',
    plugins=["PulseConnectPlugin"],
    fields="protocol,ip,port",
    use_bulk=False
)
```

## 🔧 Error Handling

### Missing API Key

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper()

if not scraper.has_api_key():
    print("Please set your API key:")
    api_key = input("API Key: ")
    scraper.save_api_key(api_key)
```

### Invalid API Key

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(api_key="invalid_key")

if not scraper.has_api_key():
    print("API key is invalid. It must be 48 characters long.")
```

### Query Errors

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(verbose=True)

try:
    results = scraper.run(
        scope="leak",
        pages=5,
        query='invalid query syntax',
    )
    if not results:
        print("No results found. Check your query.")
except ValueError as e:
    print(f"Error: {e}")
```

## 📝 Notes

- API keys are stored securely with proper file permissions (600 on Linux/macOS)
- The API key is automatically migrated from old location (`~/.local/.api.txt`) if it exists
- Bulk mode requires a Pro API key from LeakIX
- Free API keys have page limits
- All timestamps in logs follow the format: `[YYYY-MM-DD HH:MM:SS]`

