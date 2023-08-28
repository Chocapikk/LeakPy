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
[~] LeakPy x.x.x
usage: leakpy [-h] [-s {service,leak}] [-p PAGES] [-q QUERY] [-P PLUGINS] [-o OUTPUT] [-f FIELDS] [-b]
              [-i] [-r] [-lp] [-lf]

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
  -b, --bulk            Activate bulk mode.
  -i, --interactive     Activate interactive mode.
  -r, --reset-api       Reset the saved API key
  -lp, --list-plugins   List Available Plugins
  -lf, --list-fields    List all possible fields from a sample JSON.
  -v, --version         show program's version number and exit
```

### Interactive Mode:

When using the `-i` or `--interactive` option, LeakPy enters an interactive mode, allowing users to input commands directly:

```bash
$ leakpy -i
```

Once inside the interactive mode, users are greeted with:

```plaintext
Welcome to LeakPy interactive mode!
Type 'help' for available commands.
```

The available commands include:

```plaintext
Available Commands:
exit           : Exit the interactive mode.
help           : Display this help menu.
set            : Set a particular setting. Usage: set <setting_name> <value>
run            : Run the scraper with the current settings.
list-fields    : List all possible fields from a sample JSON.
list-plugins   : List available plugins.
show           : Display current settings.
```

## 📘 Library Documentation

### LeakixScraper

The `LeakixScraper` class offers a direct and user-friendly interface to the leakix.net API.

**Initialization:**

```python
from leakpy.scraper import LeakixScraper

scraper = LeakixScraper(api_key="Your_API_Key", verbose=False)
```

**Methods:**

- **execute(scope, query, pages, plugin, fields, bulk=False)**

    Conduct a search on leakix.net.

    Arguments:
    - `scope` (str): Type of information to search for, like "service" or "leak".
    - `query` (str): The specific search query.
    - `pages` (int): The number of pages to fetch.
    - `plugin` (str): Specify the plugins to use, for example "PulseConnectPlugin".
    - `fields` (str): Specify the fields to extract from the JSON data, separated by commas, like "event_source, host, ip, port".
    - `use_bulk` (bool): Activate bulk mode. Defaults to `False`.

    Example:

    ```python
    results = scraper.execute(scope="leak", query='+country:"France"', pages=5, plugin="PulseConnectPlugin", fields="event_source, host, ip, port", use_bulk=False)
    for result in results:
        print("Event Source:", result.get("event_source"))
        print("Host:", result.get("host"))
        print("IP:", result.get("ip"))
        print("Port:", result.get("port"))
        print("-" * 20)
    ```

## 🚫 Disclaimer

LeakPy is an independent tool and has no affiliation with leakix.net. The creators of LeakPy cannot be held responsible for any misuse or potential damage resulting from using this tool. Please use responsibly, and ensure you have the necessary permissions when accessing any data.
