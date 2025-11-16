Command Line Interface
=======================

Basic Usage
-----------

.. code-block:: bash

   leakpy [OPTIONS] COMMAND [ARGS...]

Global Options
--------------

.. option:: --silent

   Suppress all output (useful for scripting)

Commands
--------

Search
~~~~~~

.. code-block:: bash

   leakpy search [OPTIONS]

Options:

.. option:: -q, --query QUERY

   Search query string

.. option:: -p, --pages PAGES

   Number of pages to fetch (default: 2)

.. option:: -s, --scope {service,leak}

   Search scope (default: leak)

.. option:: -P, --plugins PLUGINS

   Plugin(s) to use (comma-separated)

.. option:: -f, --fields FIELDS

   Fields to extract (comma-separated). Use ``full`` for complete JSON.

.. option:: -b, --bulk

   Activate bulk mode (requires Pro API)

.. option:: -o, --output OUTPUT

   Output file path

Examples:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5
   $ leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

Lookup
~~~~~~

.. code-block:: bash

   leakpy lookup {host,domain,subdomains} [OPTIONS]

Options:

.. option:: -i, --input INPUT

   Input file for batch processing

.. option:: -o, --output OUTPUT

   Output file path

.. option:: -f, --fields FIELDS

   Fields to extract (comma-separated)

Examples:

.. code-block:: bash

   $ leakpy lookup host 157.90.211.37
   $ leakpy lookup domain leakix.net
   $ leakpy lookup subdomains leakix.net

List
~~~~

.. code-block:: bash

   leakpy list {plugins,fields} [OPTIONS]

Examples:

.. code-block:: bash

   $ leakpy list plugins
   $ leakpy list fields

Config & Cache
~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy config set
   $ leakpy cache clear
   $ leakpy cache set-ttl 10

Stats
~~~~~

.. code-block:: bash

   $ leakpy stats query -q '+country:"France"' -p 5
   $ leakpy stats query -f results.json --fields "geoip.country_name,protocol"

For complete help, use ``leakpy COMMAND --help``.
