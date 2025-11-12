# 🚀 LeakPy

[![PyPI version](https://badge.fury.io/py/leakpy.svg)](https://badge.fury.io/py/leakpy)
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

Get your API key from [LeakIX](https://leakix.net/) (48 characters). On first use, you'll be prompted to enter it. Reset: ``leakpy -r``

**Secure Storage:** The API key is stored securely using your system's keychain (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux). If keyring is not available, it falls back to file storage with restrictive permissions (600).

**API Response Caching:** LeakPy automatically caches API responses to reduce unnecessary API calls. The cache respects HTTP headers (`Cache-Control: max-age` or `Expires`) when available, otherwise uses a default TTL of 5 minutes. Clear the cache with ``leakpy --clear-cache``.

## 🖥️ CLI Usage 

To see all available commands and options:

```bash
$ leakpy -h
```

Options:

```plaintext
[~] LeakPy 2.0.0
usage: leakpy [-h] [-s {service,leak}] [-p PAGES] [-q QUERY] [-P PLUGINS] [-o OUTPUT] [-f FIELDS] [-b]
              [-r] [--clear-cache] [-lp] [-lf] [-v] [--silent]

options:
  -h, --help            show this help message and exit
  -s {service,leak}, --scope {service,leak}
                        Search scope: 'leak' or 'service' (default: leak)
  -p PAGES, --pages PAGES
                        Number of pages to fetch (default: 2)
  -q QUERY, --query QUERY
                        Search query string
  -P PLUGINS, --plugins PLUGINS
                        Plugin(s) to use (comma-separated)
  -o OUTPUT, --output OUTPUT
                        Output file path
  -f FIELDS, --fields FIELDS
                        Fields to extract (comma-separated, e.g. 'protocol,ip,port' or 'full')
  -b, --bulk            Use bulk mode (requires Pro API)
  -r, --reset-api       Reset saved API key
  --clear-cache         Clear the API response cache
  -lp, --list-plugins   List available plugins
  -lf, --list-fields    List all possible fields from sample data
  -v, --version         show program's version number and exit
  --silent              Suppress all output (useful for scripting)
```


## 📘 Library Documentation

### LeakIXScraper

The `LeakIXScraper` class offers a direct and user-friendly interface to the LeakIX API.

**Usage:**

```python
from leakpy import LeakIXScraper

scraper = LeakIXScraper(api_key="Your_API_Key", verbose=False)

# Search
results = scraper.run(
    scope="leak",
    pages=5,
    query='+country:"France"',
    fields="protocol,ip,port",
    output="results.txt"
)
```

## 📚 Documentation

Full documentation: **https://leakpy.readthedocs.io/**

See [EXAMPLES.md](EXAMPLES.md) for more examples.

## 🚫 Disclaimer

LeakPy is an independent tool and has no affiliation with LeakIX. The creators of LeakPy cannot be held responsible for any misuse or potential damage resulting from using this tool. Please use responsibly, and ensure you have the necessary permissions when accessing any data.
