# LeakPy Examples

This document provides examples of how to use LeakPy both as a CLI tool and as a Python library.

## 🔑 API Key Setup

### API Key Setup

Get your API key from [LeakIX](https://leakix.net/) (must be 48 characters).

On first use, you'll be prompted to enter it. To reset: ``leakpy -r``

## 📋 CLI Examples

### List Available Plugins

```bash
$ leakpy -lp
```

### List Available Fields

```bash
$ leakpy -lf
```

### Basic Search

```bash
# Search for leaks in France
$ leakpy -q '+country:"France"' -p 5

# Search with specific plugin
$ leakpy -q '+country:"France"' -P PulseConnectPlugin -p 3

# Save results to file
$ leakpy -q '+country:"France"' -p 5 -o results.txt
```

### Extract Specific Fields

```bash
# Extract only protocol, IP, and port (default)
$ leakpy -q '+country:"France"' -f protocol,ip,port

# Extract custom fields
$ leakpy -q '+country:"France"' -f protocol,ip,port,host,event_source

# Get complete JSON
$ leakpy -q '+country:"France"' -f full -o results.json
```

### Bulk Mode (Pro API Required)

```bash
# Use bulk mode for faster results (requires Pro API)
$ leakpy -q '+country:"France"' -b -o results.txt
```

### Service Scope

```bash
# Search in service scope instead of leak scope
$ leakpy -s service -q 'port:3306' -p 3
```

### Silent Mode (Scripting)

```bash
# Silent mode suppresses all logs and progress bars (useful for scripting)
$ leakpy --silent -q '+country:"France"' -p 5 -o results.txt

# List plugins in silent mode (outputs only plugin names, one per line)
$ leakpy --silent --list-plugins

# List fields in silent mode (outputs only field names, one per line)
$ leakpy --silent --list-fields -q '+country:"France"'
```

### Cache Management

LeakPy automatically caches API responses to reduce unnecessary API calls. The cache respects HTTP headers (`Cache-Control: max-age` or `Expires`) when available, otherwise uses a default TTL of 5 minutes.

```bash
# Clear the cache manually
$ leakpy --clear-cache
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

