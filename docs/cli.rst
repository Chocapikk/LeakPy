Command Line Interface
=======================

LeakPy provides a comprehensive command-line interface for interacting with the LeakIX API using a subcommand-based structure (similar to git).

Basic Usage
-----------

.. code-block:: bash

   leakpy [OPTIONS] COMMAND [ARGS...]

Global Options
--------------

.. program:: leakpy

.. option:: -h, --help

   Show help message and exit.

.. option:: -v, --version

   Show program's version number and exit.

.. option:: --silent

   Suppress all output (no logs, no progress bar). Useful for scripting.
   When used with list commands, outputs only the data (one item per line).

Commands
--------

Lookup Command
~~~~~~~~~~~~~~

Lookup information about specific IPs, domains, or subdomains:

.. code-block:: bash

   leakpy lookup {host,domain,subdomains} [OPTIONS]

Lookup Host
~~~~~~~~~~~

Get detailed information about a specific IP address:

.. code-block:: bash

   leakpy lookup host IP [OPTIONS]

Options for lookup host:

.. option:: IP

   IP address to lookup (optional if using batch mode with ``-i/--input``)

.. option:: -i, --input INPUT

   Input file containing IP addresses (one per line). Enables batch mode.
   Empty lines and lines starting with ``#`` are ignored.

.. option:: -o, --output OUTPUT

   Output file path to save results. In batch mode, saves JSON array with all results.

.. option:: -f, --fields FIELDS

   Fields to extract from the JSON, comma-separated. Use ``full`` to get the complete JSON.

   Example: ``protocol,ip,port,host``

.. option:: --silent

   Suppress all output (useful for scripting). In batch mode, disables progress bar.

.. option:: --limit LIMIT

   Maximum number of services/leaks to display (default: 50, use 0 for all)

.. option:: --all

   Display all services and leaks (equivalent to ``--limit 0``)

Examples:

.. code-block:: bash

   # Get host details (shows up to 50 services and 50 leaks by default)
   $ leakpy lookup host 157.90.211.37

   # Save to file
   $ leakpy lookup host 157.90.211.37 -o host_details.json

   # Extract specific fields
   $ leakpy lookup host 157.90.211.37 -f protocol,ip,port,host

   # Display all services and leaks
   $ leakpy lookup host 157.90.211.37 --all

   # Display only first 20 services and leaks
   $ leakpy lookup host 157.90.211.37 --limit 20

   # Batch mode: process multiple IPs from file
   $ leakpy lookup host -i ips.txt -o results.json

   # Batch mode with progress bar (default)
   $ leakpy lookup host -i ips.txt

   # Batch mode in silent mode (no progress bar)
   $ leakpy --silent lookup host -i ips.txt -o results.json

Lookup Domain
~~~~~~~~~~~~~

Get detailed information about a specific domain and its subdomains:

.. code-block:: bash

   leakpy lookup domain DOMAIN [OPTIONS]

Options for lookup domain:

.. option:: DOMAIN

   Domain to lookup (optional if using batch mode with ``-i/--input``)

.. option:: -i, --input INPUT

   Input file containing domains (one per line). Enables batch mode.
   Empty lines and lines starting with ``#`` are ignored.

.. option:: -o, --output OUTPUT

   Output file path to save results. In batch mode, saves JSON array with all results.

.. option:: -f, --fields FIELDS

   Fields to extract from the JSON, comma-separated. Use ``full`` to get the complete JSON.

   Example: ``protocol,host,port,ip``

.. option:: --silent

   Suppress all output (useful for scripting). In batch mode, disables progress bar.

.. option:: --limit LIMIT

   Maximum number of services/leaks to display (default: 50, use 0 for all)

.. option:: --all

   Display all services and leaks (equivalent to ``--limit 0``)

Examples:

.. code-block:: bash

   # Get domain details (shows up to 50 services and 50 leaks by default)
   $ leakpy lookup domain leakix.net

   # Save to file
   $ leakpy lookup domain leakix.net -o domain_details.json

   # Extract specific fields
   $ leakpy lookup domain leakix.net -f protocol,host,port,ip

   # Display all services and leaks
   $ leakpy lookup domain leakix.net --all

   # Display only first 20 services and leaks
   $ leakpy lookup domain leakix.net --limit 20

   # Batch mode: process multiple domains from file
   $ leakpy lookup domain -i domains.txt -o results.json

Lookup Subdomains
~~~~~~~~~~~~~~~~~

Get list of subdomains for a specific domain:

.. code-block:: bash

   leakpy lookup subdomains DOMAIN [OPTIONS]

Options for lookup subdomains:

.. option:: DOMAIN

   Domain to lookup subdomains for (optional if using batch mode with ``-i/--input``)

.. option:: -i, --input INPUT

   Input file containing domains (one per line). Enables batch mode.
   Empty lines and lines starting with ``#`` are ignored.

.. option:: -o, --output OUTPUT

   Output file path to save results. In batch mode, saves JSON array with all subdomains.

.. option:: --silent

   Suppress all output (useful for scripting). In batch mode, disables progress bar.

Examples:

.. code-block:: bash

   # Get subdomains for a domain
   $ leakpy lookup subdomains leakix.net

   # Save to file
   $ leakpy lookup subdomains leakix.net -o subdomains.json

   # Silent mode for scripting (outputs one subdomain per line)
   $ leakpy --silent lookup subdomains leakix.net

   # Batch mode: process multiple domains from file
   $ leakpy lookup subdomains -i domains.txt -o subdomains.json

Search Command
~~~~~~~~~~~~~~

Search LeakIX for leaks or services:

.. code-block:: bash

   leakpy search [OPTIONS]

Options for search:

.. option:: -s, --scope {service,leak}

   Search scope: 'leak' or 'service' (default: leak)

.. option:: -p, --pages PAGES

   Number of pages to fetch (default: 2)

.. option:: -q, --query QUERY

   Search query string

.. option:: -P, --plugins PLUGINS

   Plugin(s) to use (comma-separated)

.. option:: -o, --output OUTPUT

   Output file path to save results

.. option:: -f, --fields FIELDS

   Fields to extract from the JSON, comma-separated. Use ``full`` to get the complete JSON.

   Example: ``protocol,ip,port``

.. option:: -b, --bulk

   Activate bulk mode (requires Pro API key)

.. option:: --silent

   Suppress all output (useful for scripting)

List Command
~~~~~~~~~~~~

List available plugins or fields:

.. code-block:: bash

   leakpy list {plugins,fields} [OPTIONS]

Subcommands:

- ``plugins``: List available plugins
- ``fields``: List all possible fields from a sample query

Options for ``list fields``:

.. option:: -s, --scope {service,leak}

   Search scope: 'leak' or 'service' (default: leak)

.. option:: -q, --query QUERY

   Query string to fetch sample data

.. option:: -P, --plugins PLUGINS

   Plugin(s) to use (comma-separated)

.. option:: --silent

   Output only field names (one per line)

Config Command
~~~~~~~~~~~~~~

Manage API key configuration:

.. code-block:: bash

   leakpy config {set,reset} [OPTIONS]

Subcommands:

- ``set [API_KEY]``: Set or update your API key. If API_KEY is not provided, will prompt interactively.
- ``reset``: Reset/delete saved API key

Cache Command
~~~~~~~~~~~~~

Manage API response cache:

.. code-block:: bash

   leakpy cache {clear,set-ttl,show-ttl} [OPTIONS]

Subcommands:

- ``clear``: Clear all cached API responses
- ``set-ttl MINUTES``: Set cache TTL (Time To Live) in minutes
- ``show-ttl``: Show current cache TTL setting

Stats Command
~~~~~~~~~~~~~

Display statistics and metrics with visualizations:

.. code-block:: bash

   leakpy stats {cache,overview,query} [OPTIONS]

Subcommands:

- ``cache``: Display cache statistics with visualizations
- ``overview``: Display overview of all statistics
- ``query``: Analyze and display statistics from search queries

Options for ``stats query``:

.. option:: -f, --file FILE

   JSON file containing query results to analyze

.. option:: -q, --query QUERY

   Query string to search (if no file provided)

.. option:: -p, --pages PAGES

   Number of pages to fetch (default: 2)

.. option:: -s, --scope {service,leak}

   Search scope (default: leak)

.. option:: --top TOP

   Number of top items to display (default: 10)

.. option:: --fields FIELDS

   Comma-separated list of fields to analyze (e.g. "country,protocol,port")

.. option:: --all-fields

   Analyze all available fields in the results

Examples
--------

List available plugins:

.. code-block:: bash

   $ leakpy list plugins

List available fields:

.. code-block:: bash

   $ leakpy list fields

Search with default fields:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5

Search with custom fields:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -f protocol,ip,port,host -p 3

Get complete JSON:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -f full -o results.json

Use bulk mode:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -b -o results.txt

Configure API key:

.. code-block:: bash

   $ leakpy config set

Reset API key:

.. code-block:: bash

   $ leakpy config reset

Clear cache:

.. code-block:: bash

   $ leakpy cache clear

Set cache TTL:

.. code-block:: bash

   $ leakpy cache set-ttl 10

Show cache TTL:

.. code-block:: bash

   $ leakpy cache show-ttl

Display cache statistics:

.. code-block:: bash

   $ leakpy stats cache

Analyze query statistics:

.. code-block:: bash

   $ leakpy stats query -q '+country:"France"' -p 5

Analyze statistics from a file:

.. code-block:: bash

   $ leakpy stats query -f results.json

Analyze specific fields:

.. code-block:: bash

   $ leakpy stats query -f results.json --fields "geoip.country_name,protocol,port"

Analyze all fields:

.. code-block:: bash

   $ leakpy stats query -f results.json --all-fields

Silent mode (for scripting):

.. code-block:: bash

   # Suppress all logs and progress bars
   $ leakpy --silent search -q '+country:"France"' -p 5 -o results.txt

   # List plugins in silent mode (outputs only plugin names)
   $ leakpy --silent list plugins

   # List fields in silent mode (outputs only field names)
   $ leakpy --silent list fields -q '+country:"France"'

   # Get cache stats in silent mode
   $ leakpy --silent stats cache

Batch Processing
~~~~~~~~~~~~~~~

All lookup commands support batch processing from an input file. Rate limiting is handled automatically by the API:

.. code-block:: bash

   # Process multiple IPs from file
   $ leakpy lookup host -i ips.txt -o results.json

   # Process multiple domains from file
   $ leakpy lookup domain -i domains.txt -o results.json

   # Process multiple domains for subdomain discovery
   $ leakpy lookup subdomains -i domains.txt -o subdomains.json

   # Batch mode with progress bar (shows processing status)
   $ leakpy lookup host -i ips.txt

   # Batch mode in silent mode (no progress bar, JSON output)
   $ leakpy --silent lookup host -i ips.txt -o results.json

**Note:** Rate limiting (HTTP 429) is automatically handled by the API layer. The batch processing will automatically respect rate limits without manual intervention.
