# 🚀 LeakPy

LeakPy is a third-party client designed to seamlessly interact with the leakix.net API using Python.

> ❗ **Note:** This is **not** the official LeakIX client. Always refer to the [Official LeakIX Python Client](https://github.com/LeakIX/LeakIXClient-Python) for the official client.

## 📥 Installation

To install LeakPy via PyPi:

```bash
pip install leakpy
```

## 🖥️ CLI Usage 

```bash
$ leakpy -h
```

Options:

```plaintext
$ leakpy -h                                                                               

usage: leakpy [-h] [-s {service,leak}] [-p PAGES] [-q QUERY] [-P PLUGINS] [-o OUTPUT]
              [-f FIELDS] [-r] [-lp]

options:
  -h, --help            show this help message and exit
  -s {service,leak}, --scope {service,leak}
                        Type Of Informations
  -p PAGES, --pages PAGES
                        Number Of Pages
  -q QUERY, --query QUERY
                        Specify The Query
  -P PLUGINS, --plugins PLUGINS
                        Specify The Plugin(s)
  -o OUTPUT, --output OUTPUT
                        Output File
  -f FIELDS, --fields FIELDS
                        Fields to extract from the JSON, comma-separated. For example:
                        'protocol,ip,port'
  -r, --reset-api       Reset the saved API key
  -lp, --list-plugins   List Available Plugins
```

## 📘 Library Documentation

### LeakixScraper

The `LeakixScraper` class provides a direct and simple interface to the leakix.net API.

**Initialization:**

```python
from leakpy.scraper import LeakixScraper

scraper = LeakixScraper(api_key="Your_API_Key")
```

**Methods:**

- **execute(scope, query, pages, plugin, fields)**

    Conduct a search on leakix.net.

    Arguments:
    - `scope` (str): Type of information (e.g., "service" or "leak").
    - `query` (str): The query to be executed.
    - `pages` (int): Number of pages to fetch.
    - `plugin` (str): Plugins to use (e.g., "PulseConnectPlugin, ")
    - `fields` (str): Fields to extract from the JSON, comma-separated (e.g., "event_source, host, ip, port").

    Example:

    ```python
    results = scraper.execute(scope="leak", query='+country:"France"', pages=5, fields="event_source, host, ip, port", plugin="PulseConnectPlugin, SharePointPlugin")
    for result in results:
        print("Event Source:", result["event_source"])
        print("Host:", result["host"])
        print("IP:", result["ip"])
        print("Port:", result["port"])
        print("*" * 20)
    ```

## 🚫 Disclaimer

LeakPy is an unofficial tool and is not affiliated with leakix.net. The developers of LeakPy are not responsible for any misuse or potential damage from this tool. Use responsibly and ensure you have the necessary permissions when accessing data.
