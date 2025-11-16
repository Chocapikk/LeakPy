Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install leakpy

API Key Setup
-------------

Get your API key from `LeakIX <https://leakix.net/>`_ (48 characters).

.. code-block:: bash

   $ leakpy config set

Basic Usage
-----------

CLI:

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5
   $ leakpy lookup host 157.90.211.37

   # Raw JSON output (for scripting/piping)
   $ leakpy --raw search -q '+country:"France"' -p 5

   # Example output (for search):
   # http://192.168.1.1:80
   # https://10.0.0.1:443
   # ssh://172.16.0.1:22

Python:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()
   if not client.has_api_key():
       client.save_api_key("your_48_character_api_key_here")

   # Events are streamed page by page in real-time
   events = client.search(scope="leak", query='+country:"France"', pages=5)
   for event in events:
       # Events are processed as they arrive, no waiting for all pages
       if event.ip and event.port:
           print(f"{event.protocol}://{event.ip}:{event.port}")

   # Example output:
   # http://192.168.1.1:80
   # https://10.0.0.1:443
   # ssh://172.16.0.1:22

See :doc:`api` for all available methods.
