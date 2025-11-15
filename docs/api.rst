API Reference
=============

LeakIX Class
------------

.. autoclass:: leakpy.leakix.LeakIX
   :members: search, get_host, get_domain, get_subdomains, get_plugins, 
             get_all_fields, has_api_key, save_api_key, delete_api_key,
             get_cache_stats, clear_cache, get_cache_ttl, set_cache_ttl,
             analyze_query_stats
   :noindex:

CLI Mapping
-----------

+----------------------------+--------------------------+
| CLI Command                | Library Method           |
+============================+==========================+
| ``leakpy search``          | ``client.search()``      |
+----------------------------+--------------------------+
| ``leakpy lookup host``     | ``client.get_host()``    |
+----------------------------+--------------------------+
| ``leakpy lookup domain``   | ``client.get_domain()``  |
+----------------------------+--------------------------+
| ``leakpy lookup subdomains`` | ``client.get_subdomains()`` |
+----------------------------+--------------------------+
| ``leakpy list plugins``    | ``client.get_plugins()`` |
+----------------------------+--------------------------+
| ``leakpy config set``      | ``client.save_api_key()`` |
+----------------------------+--------------------------+
| ``leakpy cache clear``     | ``client.clear_cache()`` |
+----------------------------+--------------------------+
| ``leakpy stats query``     | ``client.analyze_query_stats()`` |
+----------------------------+--------------------------+

L9Event Objects
---------------

Results are returned as ``L9Event`` objects with dot notation access:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()
   events = client.search(scope="leak", query='+country:"France"', pages=1)

   for event in events:
       if event.ip and event.port and event.protocol:
           print(f"{event.protocol} {event.ip}:{event.port}")
       if event.geoip and event.geoip.country_name:
           print(f"  Country: {event.geoip.country_name}")

See :doc:`fields` for all available fields.
