Quick Start
===========

API Key Setup
-------------

When you run LeakPy for the first time without an API key, you'll be prompted to enter it:

.. code-block:: bash

   $ leakpy -lp
   [2024-01-15 14:30:45] INFO: LeakPy 2.0.0
   [2024-01-15 14:30:46] WARNING: API key is missing. Please enter your API key to continue.
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

   $ leakpy -lp

Search for leaks:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -p 5

Save results to file:

.. code-block:: bash

   $ leakpy -q '+country:"France"' -p 5 -o results.txt

Basic Python Usage
------------------

.. code-block:: python

   from leakpy import LeakIXScraper

   # Initialize scraper
   scraper = LeakIXScraper(verbose=True)

   # Check if API key is available
   if not scraper.has_api_key():
       scraper.save_api_key("your_48_character_api_key_here")

   # Search for leaks
   results = scraper.run(
       scope="leak",
       pages=5,
       query='+country:"France"',
       output="results.txt"
   )

   for result in results:
       print(result.get('url'))

