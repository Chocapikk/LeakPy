Command Line Interface
=======================

LeakPy provides a comprehensive command-line interface for interacting with the LeakIX API.

Basic Usage
-----------

.. code-block:: bash

   leakpy [OPTIONS]

Options
-------

.. program:: leakpy

.. option:: -h, --help

   Show help message and exit.

.. option:: -s, --scope {service,leak}

   Type of information to search for. Default: ``leak``

.. option:: -p, --pages PAGES

   Number of pages to scrape. Default: ``2``

.. option:: -q, --query QUERY

   Specify the search query.

.. option:: -P, --plugins PLUGINS

   Specify the plugin(s) to use (comma-separated).

.. option:: -o, --output OUTPUT

   Output file path to save results.

.. option:: -f, --fields FIELDS

   Fields to extract from the JSON, comma-separated. Use ``full`` to get the complete JSON.

   Example: ``protocol,ip,port``

.. option:: -b, --bulk

   Activate bulk mode (requires Pro API key).

.. option:: -r, --reset-api

   Reset the saved API key.

.. option:: --clear-cache

   Clear the API response cache.

.. option:: -lp, --list-plugins

   List available plugins.

.. option:: -lf, --list-fields

   List all possible fields from a sample JSON.

.. option:: --silent

   Suppress all output (no logs, no progress bar). Useful for scripting.
   When used with ``--list-plugins`` or ``--list-fields``, outputs only the data (one item per line).

.. option:: -v, --version

   Show program's version number and exit.

Examples
--------

List available plugins:

.. code-block:: bash

   $ leakpy -lp

List available fields:

.. code-block:: bash

   $ leakpy -lf

Search with default fields:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -p 5

Search with custom fields:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -f protocol,ip,port,host -p 3

Get complete JSON:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -f full -o results.json

Use bulk mode:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -b -o results.txt

Save results to file:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -p 5 -o results.txt

Reset API key:

.. code-block:: bash

   $ leakpy -r

Clear cache:

.. code-block:: bash

   $ leakpy --clear-cache

Silent mode (for scripting):

.. code-block:: bash

   # Suppress all logs and progress bars
   $ leakpy --silent -q '+country:"France"' -p 5 -o results.txt

   # List plugins in silent mode (outputs only plugin names)
   $ leakpy --silent --list-plugins

   # List fields in silent mode (outputs only field names)
   $ leakpy --silent --list-fields -q '+country:"France"'

