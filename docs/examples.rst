Examples
========

CLI Examples
------------

.. code-block:: bash

   # Search
   $ leakpy search -q '+country:"France"' -p 5
   $ leakpy search -q 'plugin:TraccarPlugin' -b -o results.txt

   # Raw JSON output (for scripting/piping)
   $ leakpy --raw search -q '+country:"France"' -p 5
   $ leakpy --raw lookup host 157.90.211.37
   $ leakpy --raw list plugins

   # Lookup
   $ leakpy lookup host 157.90.211.37
   $ leakpy lookup domain leakix.net
   $ leakpy lookup subdomains leakix.net

   # List
   $ leakpy list plugins
   $ leakpy list fields

   # Example output (for search):
   # http://192.168.1.1:80
   # https://10.0.0.1:443
   # ssh://172.16.0.1:22

Python Examples
---------------

Search (with HTTP Streaming):

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Events are streamed page by page in real-time
   # By default, all fields are returned (fields="full")
   # You can process them as they arrive, no need to wait for all pages
   events = client.search(
       scope="leak",
       query='+country:"France"',
       pages=5
   )

   for event in events:
       # Events are processed immediately as they stream from the API
       # All fields are available by default (geoip, http, etc.)
       if event.ip and event.port:
           print(f"{event.protocol}://{event.ip}:{event.port}")
       
       # Access nested fields (available because fields="full" by default)
       if event.geoip:
           print(f"  Country: {event.geoip.country_name}")

   # Example output:
   # http://192.168.1.1:80
   #   Country: France
   # ssh://10.0.0.1:22
   #   Country: United States

Bulk Mode with HTTP Streaming (Pro API):

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Bulk mode uses HTTP streaming - events arrive line by line in real-time
   events = client.search(
       scope="leak",
       query='plugin:TraccarPlugin',
       use_bulk=True
   )

   # Events are streamed directly from the HTTP response
   for event in events:
       print(f"{event.ip}:{event.port}")

   # Example output:
   # 192.168.1.1:8082
   # 10.0.0.1:8082
   # 172.16.0.1:8082

Lookup:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Host details
   host_info = client.get_host("157.90.211.37")
   if host_info.services:
       for service in host_info.services:
           if service.ip and service.port:
               print(f"{service.protocol}://{service.ip}:{service.port}")

   # Example output:
   # http://157.90.211.37:80
   # https://157.90.211.37:443
   # ssh://157.90.211.37:22

   # Domain details
   domain_info = client.get_domain("leakix.net")
   if domain_info.services:
       for service in domain_info.services:
           if service.host and service.port:
               print(f"{service.protocol}://{service.host}:{service.port}")

   # Example output:
   # https://leakix.net:443
   # http://leakix.net:80

   # Subdomains
   subdomains = client.get_subdomains("leakix.net")
   for subdomain in subdomains:
       print(subdomain.subdomain)

   # Example output:
   # www.leakix.net
   # staging.leakix.net
   # blog.leakix.net

List Available Fields:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # Get all available fields from schema (no API call needed)
   fields = client.get_all_fields()
   for field in sorted(fields):
       print(field)

   # Example output:
   # event_fingerprint
   # event_type
   # geoip.city_name
   # geoip.country_name
   # http.status
   # ip
   # port
   # protocol

Statistics:

.. code-block:: python

   from leakpy import LeakIX
   client = LeakIX()

   # analyze_query_stats() accepts generators directly
   events = client.search(scope="leak", query='+country:"France"', pages=5)
   stats = client.analyze_query_stats(events, fields='protocol,geoip.country_name')
   
   print(f"Total: {stats.total}")
   print(f"France: {stats.fields.geoip.country_name.France}")
   print(f"HTTP: {stats.fields.protocol.http}")

   # Example output:
   # Total: 150
   # France: 45
   # HTTP: 30

Large Queries with Early Stopping:

.. code-block:: python

   from leakpy import LeakIX
   import time

   client = LeakIX()

   start_time = time.time()
   count = 0

   events = client.search(scope="leak", query="country:France", use_bulk=True)

   for event in events:
       count += 1
       if event.ip and event.port:
           print(f"{count}. {event.protocol}://{event.ip}:{event.port}")
       if count >= 2000:
           break

   elapsed = time.time() - start_time
   print(f"Processed {count} results in {elapsed:.2f} seconds")
   print(f"Speed: {count/elapsed:.1f} results/second")

   # Example output:
   # 1. https://192.168.1.1:443
   # 2. http://10.0.0.1:80
   # 3. https://172.16.0.1:443
   # ...
   # Processed 2000 results in 5.29 seconds
   # Speed: 378.4 results/second

See :doc:`api` for complete API reference.
