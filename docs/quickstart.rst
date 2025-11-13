Quick Start
===========

CLI vs Library
--------------

**All CLI functionalities are available via the Python library!**

The CLI commands are wrappers around library methods. You can use either:

* **CLI**: For quick commands and scripting (e.g., ``leakpy search -q '+country:"France"'`` or ``leakpy lookup host 157.90.211.37``)
* **Library**: For programmatic access and integration (e.g., ``client.search(query='+country:"France"')`` or ``client.get_host("157.90.211.37")``)

See the :doc:`api` documentation for the complete CLI-to-library mapping.

API Key Setup
-------------

When you run LeakPy for the first time without an API key, you'll be prompted to enter it:

.. code-block:: bash

   $ leakpy list plugins
   
      __            _   _____     
     |  |   ___ ___| |_|  _  |_ _ 
     |  |__| -_| .'| '_|   __| | | 
     |_____|___|__,|_,_|__|  |_  |
                             |___|
            (v2.0.5)
   
   Coded by Chocapikk | Non-official LeakIX API client
   
   WARNING: API key is missing. Please enter your API key to continue.
   API Key: [hidden input]

The API key is stored securely using your system's keychain:

* **macOS**: Keychain
* **Windows**: Credential Manager
* **Linux**: Secret Service (via keyring)

If keyring is not available, it falls back to file storage with restrictive permissions (600):

* **Linux/macOS**: ``~/.config/LeakPy/api_key.txt``
* **Windows**: ``%LOCALAPPDATA%\\LeakPy\\api_key.txt``

Requirements
------------

* API key must be exactly **48 characters** long
* Get your API key from `LeakIX <https://leakix.net/>`_

Basic CLI Usage
---------------

List available plugins:

.. code-block:: bash

   $ leakpy list plugins

Search for leaks:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5

Save results to file:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5 -o results.txt

Basic Python Usage
------------------

.. code-block:: python

   from leakpy import LeakIX

   # Initialize client (silent by default - no logs, no progress bars)
   client = LeakIX()

   # Check if API key is available
   if not client.has_api_key():
       client.save_api_key("your_48_character_api_key_here")

   # Get results using search() - returns l9event objects
   # search() is the main method - it always returns results, even if output is specified
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="protocol,ip,port,host"
   )

   # Access fields using dot notation (much cleaner!)
   for leak in results:
       # Direct access with dot notation
       print(f"{leak.protocol}://{leak.ip}:{leak.port}")
       print(f"Host: {leak.host}")

   # Write to file AND get results (search() always returns results)
   results = client.search(
       scope="leak",
       pages=5,
       query='+country:"France"',
       output="results.txt"  # Writes to file, but results are still returned
   )
   
   # You can still use the results even after writing to file
   print(f"Found {len(results)} results")

