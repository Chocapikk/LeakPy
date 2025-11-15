API Reference
=============

This section provides documentation for the main public API of LeakPy.

CLI vs Library
--------------

**All CLI functionalities are available via the Python library!**

The CLI is essentially a wrapper around the library methods. Here's the complete mapping:

+--------------------------------+------------------------------------------+
| CLI Command                    | Library Method                           |
+================================+==========================================+
| ``leakpy search``              | ``client.search()``                      |
+--------------------------------+------------------------------------------+
| ``leakpy lookup host``         | ``client.get_host()``                    |
+--------------------------------+------------------------------------------+
| ``leakpy lookup domain``       | ``client.get_domain()``                  |
+--------------------------------+------------------------------------------+
| ``leakpy lookup subdomains``   | ``client.get_subdomains()``              |
+--------------------------------+------------------------------------------+
| ``leakpy list plugins``        | ``client.get_plugins()``                 |
+--------------------------------+------------------------------------------+
| ``leakpy list fields``         | ``client.get_all_fields()`` +            |
|                                | ``client.search()``                      |
+--------------------------------+------------------------------------------+
| ``leakpy config set``          | ``client.save_api_key()``                |
+--------------------------------+------------------------------------------+
| ``leakpy cache clear``         | ``client.clear_cache()``                 |
+--------------------------------+------------------------------------------+
| ``leakpy cache set-ttl``       | ``client.set_cache_ttl(minutes)``        |
+--------------------------------+------------------------------------------+
| ``leakpy cache show-ttl``      | ``client.get_cache_ttl()``               |
+--------------------------------+------------------------------------------+
| ``leakpy stats cache``         | ``client.get_cache_stats()``             |
+--------------------------------+------------------------------------------+
| ``leakpy stats query``         | ``client.analyze_query_stats()``         |
+--------------------------------+------------------------------------------+

**Example:** To get available fields like ``leakpy list fields``:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=1,
       fields="full"
   )
   if results:
       fields = client.get_all_fields(results[0])
       for field in sorted(fields):
           print(field)

LeakIX
------

The main class for interacting with the LeakIX API.

Initialization
~~~~~~~~~~~~~~~

.. autoclass:: leakpy.leakix.LeakIX
   :members:
   :exclude-members: log, process_and_print_data, get_all_fields, query
   :noindex:

Public Methods
~~~~~~~~~~~~~~

The following methods are the main entry points for using LeakPy:

**search()** - Search LeakIX and return results as ``L9Event`` objects. 
              Optionally write results to a file if ``output`` is specified.

.. automethod:: leakpy.leakix.LeakIX.search

**get_plugins()** - Get list of available plugins

.. automethod:: leakpy.leakix.LeakIX.get_plugins

**has_api_key()** - Check if API key is available and valid

.. automethod:: leakpy.leakix.LeakIX.has_api_key

**save_api_key()** - Save API key securely

.. automethod:: leakpy.leakix.LeakIX.save_api_key

**delete_api_key()** - Delete stored API key

.. automethod:: leakpy.leakix.LeakIX.delete_api_key

**get_cache_stats()** - Get cache statistics

.. automethod:: leakpy.leakix.LeakIX.get_cache_stats

**clear_cache()** - Clear all cache entries

.. automethod:: leakpy.leakix.LeakIX.clear_cache

**get_cache_ttl()** - Get current cache TTL

.. automethod:: leakpy.leakix.LeakIX.get_cache_ttl

**set_cache_ttl()** - Set cache TTL

.. automethod:: leakpy.leakix.LeakIX.set_cache_ttl

**analyze_query_stats()** - Analyze query results and extract statistics

Returns a ``QueryStats`` object with dot notation access (e.g., ``stats.total``, ``stats.fields.protocol.http``).

.. automethod:: leakpy.leakix.LeakIX.analyze_query_stats

**get_host()** - Get host details for a specific IP address

Returns a dictionary with 'Services' and 'Leaks' keys, each containing a list of L9Event objects.

.. automethod:: leakpy.leakix.LeakIX.get_host

**get_domain()** - Get domain details for a specific domain name

Returns a dictionary with 'Services' and 'Leaks' keys, each containing a list of L9Event objects.

.. automethod:: leakpy.leakix.LeakIX.get_domain

**get_subdomains()** - Get subdomains for a specific domain name

Returns a list of dictionaries containing subdomain information (subdomain, distinct_ips, last_seen).

.. automethod:: leakpy.leakix.LeakIX.get_subdomains

QueryStats Objects
------------------

Statistics are returned as ``QueryStats`` objects that support dot notation access, similar to ``L9Event`` objects.

**Benefits of QueryStats objects:**

* **Dot notation**: ``stats.total`` instead of ``stats['total']``
* **Nested access**: ``stats.fields.protocol.http`` for nested statistics
* **No KeyError**: Missing fields return ``None`` instead of raising errors
* **Object-oriented**: Clean, Pythonic API

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()
   
   # First, get some results
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2
   )
   
   # Then analyze the statistics
   stats = client.analyze_query_stats(results, fields='geoip.country_name,protocol')
   
   # Access with dot notation
   print(stats.total)  # Total number of results
   print(stats.fields.geoip.country_name.France)  # Number of leaks in France
   print(stats.fields.protocol.http)  # Number of HTTP services
   
   # Convert to dict if needed for iteration
   stats_dict = stats.fields.protocol.to_dict()
   for protocol, count in stats_dict.items():
       print(f"{protocol}: {count}")

L9Event Objects
---------------

Results are returned as ``L9Event`` objects that support dot notation access. **Simple and direct** - no if checks needed!

**Benefits of L9Event objects:**

* **Simple and direct**: Direct access, no ``if`` checks needed - ``leak.geoip.country_name`` works even if ``geoip`` doesn't exist
* **Dot notation only**: ``leak.ip`` - exclusive use of dot notation for field access
* **No KeyError**: Missing fields return ``None`` instead of raising errors
* **Nested access**: ``leak.geoip.country_name`` for nested fields - works directly!
* **Uses official l9format library**: Built on top of the official ``l9format.L9Event``

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()
   
   # Get results first
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2
   )
   
   # Then iterate over them
   for leak in results:
       # Simple and direct - no if checks needed!
       ip = leak.ip
       port = leak.port
       protocol = leak.protocol
       
       # Nested fields - works directly, no if checks needed!
       country = leak.geoip.country_name  # None if doesn't exist, no error!
       city = leak.geoip.city_name
       http_status = leak.http.status
       leak_type = leak.leak.type
       
       # Use with 'or' for defaults
       country = leak.geoip.country_name or "Unknown"
       status = leak.http.status or 0
       
       # Convert to dict if needed
       data = leak.to_dict()

For the complete list of available fields, see the :doc:`fields` page or the official `LeakIX l9format documentation <https://docs.leakix.net/docs/api/l9format/>`_.

