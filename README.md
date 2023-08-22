# 🚀 LeakPy

LeakPy is a third-party client designed to seamlessly interact with the leakix.net API using Python.

> ❗ **Note:** This is **not** the official LeakIX client. Always refer to the [Official LeakIX Python Client](https://github.com/LeakIX/LeakIXClient-Python) for the official client.

## 📥 Installation

To install LeakPy via PyPi:

```bash
pip install leakpy
```

## 🖥️ CLI Usage 

To see all available commands and options:

```bash
$ leakpy -h
```

Options:

```plaintext
usage: leakpy [-h] [-s {service,leak}] [-p PAGES] [-q QUERY] [-P PLUGINS] [-o OUTPUT]
              [-f FIELDS] [-r] [-lp] [-lf]

options:
  -h, --help            show this help message and exit
  -s {service,leak}, --scope {service,leak}
                        Specify the type of information you're looking for.
  -p PAGES, --pages PAGES
                        Specify the number of pages to retrieve.
  -q QUERY, --query QUERY
                        Specify your search query.
  -P PLUGINS, --plugins PLUGINS
                        Specify the plugin(s) to use.
  -o OUTPUT, --output OUTPUT
                        Specify the output file path.
  -f FIELDS, --fields FIELDS
                        Fields to extract from the JSON data, comma-separated (e.g., 'protocol,ip,port').
  -r, --reset-api       Reset the saved API key.
  -lp, --list-plugins   List all available plugins.
  -lf, --list-fields    List all possible fields from a sample JSON.
```

## 📘 Library Documentation

### LeakixScraper

The `LeakixScraper` class offers a direct and user-friendly interface to the leakix.net API.

**Initialization:**

```python
from leakpy.scraper import LeakixScraper

scraper = LeakixScraper(api_key="Your_API_Key")
```

**Methods:**

- **execute(scope, query, pages, plugin, fields)**

    Conduct a search on leakix.net.

    Arguments:
    - `scope` (str): Type of information to search for (e.g., "service" or "leak").
    - `query` (str): The specific search query.
    - `pages` (int): The number of pages to fetch.
    - `plugin` (str): Specify the plugins to use (e.g., "PulseConnectPlugin, SharePointPlugin").
    - `fields` (str): Specify the fields to extract from the JSON data, separated by commas (e.g., "event_source, host, ip, port").

    Example:

    ```python
    results = scraper.execute(scope="leak", query='+country:"France"', pages=5, plugin="PulseConnectPlugin", fields="event_source, host, ip, port")
    for result in results:
        print("Event Source:", result.get("event_source"))
        print("Host:", result.get("host"))
        print("IP:", result.get("ip"))
        print("Port:", result.get("port"))
        print("-" * 20)
    ```

## 🚫 Disclaimer

LeakPy is an independent tool and has no affiliation with leakix.net. The creators of LeakPy cannot be held responsible for any misuse or potential damage resulting from using this tool. Please use responsibly, and ensure you have the necessary permissions when accessing any data.
