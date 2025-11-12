Examples
========

This section provides comprehensive examples of using LeakPy.

CLI Examples
------------

Basic Search
~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy -q '+country:"France"' -p 5

Search with Plugin
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy -q '+country:"France"' -P PulseConnectPlugin -p 3

Extract Specific Fields
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy -q '+country:"France"' -f protocol,ip,port,host

Get Complete JSON
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy -q '+country:"France"' -f full -o results.json

Bulk Mode
~~~~~~~~~

.. code-block:: bash

   $ leakpy -q '+country:"France"' -b -o results.txt

Silent Mode (Scripting)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Suppress all logs and progress bars (useful for scripting)
   $ leakpy --silent -q '+country:"France"' -p 5 -o results.txt

   # List plugins in silent mode (outputs only plugin names, one per line)
   $ leakpy --silent --list-plugins

   # List fields in silent mode (outputs only field names, one per line)
   $ leakpy --silent --list-fields -q '+country:"France"'

Python Library Examples
-----------------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   # Basic initialization
   scraper = LeakIXScraper(verbose=True)

   # Silent mode (no logs, no progress bar) - useful for scripting
   scraper = LeakIXScraper(verbose=False, silent=True)

   if not scraper.has_api_key():
       scraper.save_api_key("your_api_key_here")

   results = scraper.run(
       scope="leak",
       pages=5,
       query='+country:"France"',
       output="results.txt"
   )


Search with Custom Fields
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(verbose=True)

   results = scraper.run(
       scope="leak",
       pages=3,
       query='+country:"France"',
       fields="protocol,ip,port,host,event_source",
       output="results.json"
   )

   for result in results:
       print(f"IP: {result.get('ip')}, Port: {result.get('port')}")

Get Complete JSON
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(verbose=True)

   results = scraper.run(
       scope="leak",
       pages=2,
       query='+country:"France"',
       fields="full",
       output="full_results.json"
   )

   # Each result contains the complete JSON object
   for result in results:
       print(result)

Using execute() Method
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(verbose=True)

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

List Plugins
~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(verbose=True)

   plugins = scraper.get_plugins()
   print(f"Available plugins: {len(plugins)}")
   for plugin in plugins:
       print(f"  - {plugin}")

Bulk Mode (Pro API)
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(verbose=True)

   # Use bulk mode for faster results (requires Pro API)
   # A spinner will be displayed showing:
   # - Downloading and processing...
   # - Processing results...
   # - ✓ Found X unique results
   results = scraper.run(
       scope="leak",
       pages=1,  # Not used in bulk mode
       query='+country:"France"',
       use_bulk=True,
       output="bulk_results.txt"
   )

Error Handling
--------------

Missing API Key
~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper()

   if not scraper.has_api_key():
       print("Please set your API key:")
       api_key = input("API Key: ")
       scraper.save_api_key(api_key)

Invalid API Key
~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIXScraper

   scraper = LeakIXScraper(api_key="invalid_key")

   if not scraper.has_api_key():
       print("API key is invalid. It must be 48 characters long.")

Query Errors
~~~~~~~~~~~~

.. code-block:: python

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

