Examples
========

CLI Examples
------------

.. code-block:: bash

   # Search
   $ leakpy search -q '+country:"France"' -p 5
   $ leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

   # Lookup
   $ leakpy lookup host 157.90.211.37
   $ leakpy lookup domain leakix.net
   $ leakpy lookup subdomains leakix.net

   # List
   $ leakpy list plugins
   $ leakpy list fields

Python Examples
---------------

Search:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   events = client.search(
       scope="leak",
       query='+country:"France"',
       pages=5
   )

   for event in events:
       if event.protocol in ('http', 'https') and event.ip and event.port:
           print(f"{event.protocol}://{event.ip}:{event.port}")
       elif event.ip and event.port:
           print(f"{event.protocol} {event.ip}:{event.port}")

Lookup:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Host details
   host_info = client.get_host("157.90.211.37")
   if host_info.Services:
       for service in host_info.Services:
           if service.protocol in ('http', 'https') and service.ip and service.port:
               print(f"{service.protocol}://{service.ip}:{service.port}")
           elif service.ip and service.port:
               print(f"{service.protocol} {service.ip}:{service.port}")

   # Domain details
   domain_info = client.get_domain("leakix.net")
   if domain_info.Services:
       for service in domain_info.Services:
           if service.protocol in ('http', 'https') and service.host and service.port:
               print(f"{service.protocol}://{service.host}:{service.port}")
           elif service.host and service.port:
               print(f"{service.protocol} {service.host}:{service.port}")

   # Subdomains
   subdomains = client.get_subdomains("leakix.net")
   for subdomain in subdomains:
       print(subdomain.subdomain)

List Available Fields:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Get all available fields from schema (no API call needed)
   fields = client.get_all_fields()
   for field in sorted(fields):
       print(field)

Statistics:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   events = client.search(scope="leak", query='+country:"France"', pages=5)
   stats = client.analyze_query_stats(events, fields='protocol,geoip.country_name')
   
   print(f"Total: {stats.total}")
   print(f"France: {stats.fields.geoip.country_name.France}")
   print(f"HTTP: {stats.fields.protocol.http}")

See :doc:`api` for complete API reference.
