Examples
========

This section provides comprehensive examples of using LeakPy.

CLI Examples
------------

Basic Search
~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -p 5

Search with Plugin
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -P PulseConnectPlugin -p 3

Extract Specific Fields
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -f protocol,ip,port,host

Get Complete JSON
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -f full -o results.json

Bulk Mode
~~~~~~~~~

.. code-block:: bash

   $ leakpy search -q '+country:"France"' -b -o results.txt

Silent Mode (Scripting)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Suppress all logs and progress bars (useful for scripting)
   $ leakpy --silent search -q '+country:"France"' -p 5 -o results.txt

   # List plugins in silent mode (outputs only plugin names, one per line)
   $ leakpy --silent list plugins

   # List fields in silent mode (outputs only field names, one per line)
   $ leakpy --silent list fields -q '+country:"France"'

Python Library Examples
-----------------------

**Note:** All CLI functionalities are available via the Python library. The CLI is a wrapper around these library methods. See the :doc:`api` documentation for the complete CLI-to-library mapping.

**Note:** The ``host``, ``domain``, and ``subdomains`` commands have been moved under ``lookup`` (e.g., ``leakpy lookup host`` instead of ``leakpy host``).

Retrieving Results
~~~~~~~~~~~~~~~~~~

LeakPy returns results as ``l9event`` objects that support dot notation access. Use ``search()`` to get results. If you specify ``output``, results are written to a file but still returned.

**Key Concepts:**

* **``l9event`` objects**: Results are wrapped in ``l9event`` objects that allow dot notation access (e.g., ``leak.ip`` instead of ``leak.get('ip')``)
* **``search()`` method**: The main method to query LeakIX. Always returns a list of ``l9event`` objects, even when writing to a file
* **Silent by default**: The library is silent by default (no logs, no progress bars) - perfect for scripting
* **Dot notation**: Access fields directly with ``leak.field`` instead of dictionary-style access

.. code-block:: python

   from leakpy import LeakIX

   # Basic initialization (silent by default - perfect for scripts)
   client = LeakIX()

   # Enable logs and progress bars (optional, for interactive use)
   client = LeakIX(silent=False)

   # Check and set API key if needed
   if not client.has_api_key():
       client.save_api_key("your_48_character_api_key_here")

   # Use search() to get results as l9event objects
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=5,
       fields="protocol,ip,port,host"
   )

   # Access fields using dot notation (much cleaner than dict access!)
   for leak in results:
       protocol = leak.protocol  # "http" or "https"
       ip = leak.ip              # "1.2.3.4"
       port = leak.port          # 80
       host = leak.host          # "example.com"
       
       # Build URL from fields
       if protocol and ip and port:
           url = f"{protocol}://{ip}:{port}"
           print(f"Target: {url}")

Writing Results to File
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # search() writes to file AND returns results
   # This is useful when you want both: save to file and process in code
   results = client.search(
       scope="leak",
       pages=5,
       query='+country:"France"',
       output="results.txt"  # Writes to file
   )
   
   # Results are still available for processing
   print(f"Saved {len(results)} results to file")
   for leak in results:
       print(f"Found: {leak.ip}:{leak.port}")


Search with Custom Fields
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Use search() to get results
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=3,
       fields="protocol,ip,port,host,event_source"
   )

   # Access fields using dot notation (recommended)
   for leak in results:
       print(f"IP: {leak.ip}, Port: {leak.port}, Host: {leak.host}")
       print(f"Protocol: {leak.protocol}, Source: {leak.event_source}")

   # Note: Use dot notation for all field access (e.g., leak.ip, leak.port)

Get Complete JSON
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Get all fields with fields="full"
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="full"
   )

   # Access any field using dot notation
   for leak in results:
       # Root fields
       print(f"IP: {leak.ip}, Port: {leak.port}, Protocol: {leak.protocol}")
       
       # Nested fields with dot notation (l9event handles None automatically)
       if leak.geoip:
           print(f"Country: {leak.geoip.country_name}")
           print(f"City: {leak.geoip.city_name}")
       
       if leak.http:
           print(f"HTTP Status: {leak.http.status}")
           print(f"HTTP Title: {leak.http.title}")
       
       if leak.ssl and leak.ssl.certificate:
           print(f"SSL Version: {leak.ssl.version}")
           print(f"SSL CN: {leak.ssl.certificate.cn}")

Using search() Method with Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=5,
       plugin="PulseConnectPlugin",
       fields="protocol,ip,port,host",
       use_bulk=False
   )

   # Access fields with dot notation
   for leak in results:
       print(f"IP: {leak.ip}, Port: {leak.port}, Host: {leak.host}")

List Plugins
~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   plugins = client.get_plugins()
   print(f"Available plugins: {len(plugins)}")
   for plugin in plugins:
       print(f"  - {plugin}")

Bulk Mode (Pro API)
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Use bulk mode for faster results (requires Pro API)
   # A spinner will be displayed showing:
   # - Downloading and processing...
   # - Processing results...
   # - ✓ Found X unique results
   results = client.search(
       scope="leak",
       pages=1,  # Not used in bulk mode
       query='+country:"France"',
       use_bulk=True,
       output="bulk_results.txt"
   )

Available Fields
----------------

LeakPy supports 71+ fields organized by category. The field structure follows the official `l9format schema <https://docs.leakix.net/docs/api/l9format/>`_ from LeakIX.

Here are all available fields:

Root Fields
~~~~~~~~~~~

Basic information available at the root level:

- ``event_fingerprint`` - Unique identifier for the event
- ``event_pipeline`` - Event processing pipeline
- ``event_source`` - Source of the event
- ``event_type`` - Type of event
- ``host`` - Hostname
- ``ip`` - IP address
- ``mac`` - MAC address
- ``port`` - Port number
- ``protocol`` - Protocol (http, https, ssh, etc.)
- ``reverse`` - Reverse DNS
- ``summary`` - Event summary
- ``tags`` - Event tags
- ``time`` - Timestamp
- ``transport`` - Transport protocol
- ``vendor`` - Vendor information

GeoIP Fields
~~~~~~~~~~~~

Geographic information (access via ``leak.geoip.field``):

- ``geoip.city_name`` - City name
- ``geoip.continent_name`` - Continent name
- ``geoip.country_iso_code`` - Country ISO code
- ``geoip.country_name`` - Country name
- ``geoip.location.lat`` - Latitude
- ``geoip.location.lon`` - Longitude
- ``geoip.region_iso_code`` - Region ISO code
- ``geoip.region_name`` - Region name

HTTP Fields
~~~~~~~~~~~

HTTP-specific information (access via ``leak.http.field``):

- ``http.favicon_hash`` - Favicon hash
- ``http.header.content-type`` - Content-Type header
- ``http.header.server`` - Server header
- ``http.length`` - Response length
- ``http.root`` - Root path
- ``http.status`` - HTTP status code
- ``http.title`` - Page title
- ``http.url`` - Full URL

Leak Fields
~~~~~~~~~~~~

Leak-specific information (access via ``leak.leak.field``):

- ``leak.dataset.collections`` - Dataset collections
- ``leak.dataset.files`` - Dataset files
- ``leak.dataset.infected`` - Infected status
- ``leak.dataset.ransom_notes`` - Ransom notes
- ``leak.dataset.rows`` - Dataset rows
- ``leak.dataset.size`` - Dataset size
- ``leak.severity`` - Severity level
- ``leak.stage`` - Leak stage
- ``leak.type`` - Leak type

Network Fields
~~~~~~~~~~~~~~

Network information (access via ``leak.network.field``):

- ``network.asn`` - Autonomous System Number
- ``network.network`` - Network information
- ``network.organization_name`` - Organization name

Service Fields
~~~~~~~~~~~~~~

Service-specific information (access via ``leak.service.field``):

- ``service.credentials.key`` - Credential key
- ``service.credentials.noauth`` - No authentication required
- ``service.credentials.password`` - Password
- ``service.credentials.raw`` - Raw credentials
- ``service.credentials.username`` - Username
- ``service.software.fingerprint`` - Software fingerprint
- ``service.software.modules`` - Software modules
- ``service.software.name`` - Software name
- ``service.software.os`` - Operating system
- ``service.software.version`` - Software version

SSH Fields
~~~~~~~~~~

SSH-specific information (access via ``leak.ssh.field``):

- ``ssh.banner`` - SSH banner
- ``ssh.fingerprint`` - SSH fingerprint
- ``ssh.motd`` - Message of the day
- ``ssh.version`` - SSH version

SSL Fields
~~~~~~~~~~

SSL/TLS information (access via ``leak.ssl.field``):

- ``ssl.certificate.cn`` - Certificate Common Name
- ``ssl.certificate.domain`` - Certificate domain
- ``ssl.certificate.fingerprint`` - Certificate fingerprint
- ``ssl.certificate.issuer_name`` - Certificate issuer
- ``ssl.certificate.key_algo`` - Key algorithm
- ``ssl.certificate.key_size`` - Key size
- ``ssl.certificate.not_after`` - Certificate expiration date
- ``ssl.certificate.not_before`` - Certificate start date
- ``ssl.certificate.valid`` - Certificate validity
- ``ssl.cypher_suite`` - Cipher suite
- ``ssl.detected`` - SSL detected
- ``ssl.enabled`` - SSL enabled
- ``ssl.jarm`` - JARM fingerprint
- ``ssl.version`` - SSL/TLS version

Example: Accessing Nested Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()  # silent=True par défaut

   # Get full JSON to access all nested fields
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="full"
   )

   for leak in results:
       # Root fields
       print(f"IP: {leak.ip}, Port: {leak.port}")
       
       # GeoIP fields (nested access with dot notation)
       if leak.geoip:
           print(f"Country: {leak.geoip.country_name}")
           print(f"City: {leak.geoip.city_name}")
           if leak.geoip.location:
               print(f"Coordinates: {leak.geoip.location.lat}, {leak.geoip.location.lon}")
       
       # HTTP fields (nested access)
       if leak.http:
           print(f"HTTP Status: {leak.http.status}")
           print(f"HTTP Title: {leak.http.title}")
           if leak.http.header:
               print(f"Server: {leak.http.header.server}")
       
       # SSL fields (deeply nested access)
       if leak.ssl:
           print(f"SSL Version: {leak.ssl.version}")
           if leak.ssl.certificate:
               print(f"SSL CN: {leak.ssl.certificate.cn}")
               print(f"SSL Valid: {leak.ssl.certificate.valid}")
       
       # Leak fields (nested access)
       if leak.leak:
           print(f"Leak Type: {leak.leak.type}")
           print(f"Severity: {leak.leak.severity}")
           if leak.leak.dataset:
               print(f"Dataset Size: {leak.leak.dataset.size}")

Query Statistics
~~~~~~~~~~~~~~~~

Analyze query results using object-oriented approach with dot notation:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Search for results
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=5,
       fields="full"
   )

   # Object-oriented approach with callables (RECOMMENDED)
   # Use direct dot notation - clean and Pythonic!
   stats = client.analyze_query_stats(results, fields={
       'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
       'protocol': lambda leak: leak.protocol,
       'port': lambda leak: leak.port,
       'city': lambda leak: leak.geoip.city_name if leak.geoip else None
   }, top=10)

   # Use dot notation (no dict access!)
   print(f"Total results: {stats.total}")
   print(f"France: {stats.fields.country.France} leaks")
   print(f"HTTP: {stats.fields.protocol.http} services")
   print(f"HTTPS: {stats.fields.protocol.https} services")

   # Using named functions for complex logic
   def get_severity_level(leak):
       """Categorize leaks by port security level."""
       if not leak.port:
           return "Unknown"
       port = int(leak.port) if isinstance(leak.port, str) else leak.port
       
       # Common dangerous ports
       dangerous = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 5432, 6379, 27017]
       if port in dangerous:
           return "High Risk"
       elif port < 1024:
           return "System Port"
       else:
           return "User Port"

   def get_port_category(leak):
       """Categorize ports into ranges."""
       if not leak.port:
           return None
       port = int(leak.port) if isinstance(leak.port, str) else leak.port
       if port < 1024:
           return "Well-known (0-1023)"
       elif port < 49152:
           return "Registered (1024-49151)"
       else:
           return "Dynamic (49152-65535)"

   stats = client.analyze_query_stats(results, fields={
       'severity': get_severity_level,
       'port_category': get_port_category,
       'protocol': lambda leak: leak.protocol
   })

   # Access with dot notation
   # For simple values, use dot notation directly
   # For values with special characters, convert to dict first
   severity_dict = stats.fields.severity.to_dict()
   print(f"High Risk: {severity_dict.get('High Risk', 0)}")
   port_cat_dict = stats.fields.port_category.to_dict()
   print(f"System Ports: {port_cat_dict.get('Well-known (0-1023)', 0)}")

   # Real-world example: Find most common protocols
   stats = client.analyze_query_stats(results, fields={
       'protocol': lambda leak: leak.protocol
   }, top=5)

   # Convert to dict to iterate
   stats_dict = stats.fields.protocol.to_dict()
   for protocol, count in sorted(stats_dict.items(), key=lambda x: x[1], reverse=True):
       print(f"{protocol}: {count} leaks")

   # Fun Example: Security Dashboard
   def security_dashboard(results):
       """Create a fun security dashboard."""
       stats = client.analyze_query_stats(results, fields={
           'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
           'protocol': lambda leak: leak.protocol,
       })
       
       print("=" * 40)
       print("SECURITY DASHBOARD")
       print("=" * 40)
       print(f"Total: {stats.total} leaks found")
       print(f"Countries: {len(stats.fields.country.to_dict())}")
       print(f"Protocols: {len(stats.fields.protocol.to_dict())}")
       
       # Top country
       country_dict = stats.fields.country.to_dict()
       if country_dict:
           top_country = max(country_dict.items(), key=lambda x: x[1])
           print(f"Top Country: {top_country[0]} ({top_country[1]} leaks)")
       
       print("=" * 40)
   
   security_dashboard(results)

Host Details
~~~~~~~~~~~~~

Get detailed information about a specific IP address:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Get host details
   host_info = client.get_host("157.90.211.37")

   # Access services with dot notation
   if host_info['Services']:
       print(f"Found {len(host_info['Services'])} services:")
       for service in host_info['Services']:
           print(f"{service.protocol}://{service.ip}:{service.port}")
           if service.host:
               print(f"  Hostname: {service.host}")
           if service.http and service.http.status:
               print(f"  HTTP Status: {service.http.status}")

   # Access leaks
   if host_info['Leaks']:
       print(f"\nFound {len(host_info['Leaks'])} leaks:")
       for leak in host_info['Leaks']:
           if leak.leak:
               print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

   # Fun Example: Security Reconnaissance
   def recon_ip(ip):
       """Perform reconnaissance on an IP address."""
       host_info = client.get_host(ip)
       
       print(f"\nRECONNAISSANCE REPORT: {ip}")
       print("=" * 50)
       
       if host_info['Services']:
           print(f"\nServices ({len(host_info['Services'])}):")
           for service in host_info['Services']:
               url = f"{service.protocol}://{service.ip}:{service.port}"
               print(f"  • {url}")
               if service.host:
                   print(f"    └─ Host: {service.host}")
       
       if host_info['Leaks']:
           print(f"\nLeaks Found ({len(host_info['Leaks'])}):")
           for leak in host_info['Leaks']:
               if leak.leak:
                   print(f"  • {leak.leak.type} ({leak.leak.severity})")
       else:
           print("\nNo leaks found")
       
       print("=" * 50)
   
   recon_ip("157.90.211.37")

Domain Details
~~~~~~~~~~~~~~~

Get detailed information about a specific domain and its subdomains:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Get domain details
   domain_info = client.get_domain("leakix.net")

   # Access services with dot notation
   if domain_info['Services']:
       print(f"Found {len(domain_info['Services'])} services:")
       for service in domain_info['Services']:
           print(f"{service.protocol}://{service.host}:{service.port}")
           if service.ip:
               print(f"  IP: {service.ip}")
           if service.http and service.http.status:
               print(f"  HTTP Status: {service.http.status}")

   # Access leaks
   if domain_info['Leaks']:
       print(f"\nFound {len(domain_info['Leaks'])} leaks:")
       for leak in domain_info['Leaks']:
           if leak.leak:
               print(f"  Type: {leak.leak.type}, Severity: {leak.leak.severity}")

   # Fun Example: Domain Reconnaissance
   def recon_domain(domain):
       """Perform reconnaissance on a domain."""
       domain_info = client.get_domain(domain)
       
       print(f"\nDOMAIN RECONNAISSANCE: {domain}")
       print("=" * 50)
       
       if domain_info['Services']:
           print(f"\nServices ({len(domain_info['Services'])}):")
           # Group by subdomain
           subdomains = {}
           for service in domain_info['Services']:
               host = service.host or "N/A"
               if host not in subdomains:
                   subdomains[host] = []
               subdomains[host].append(service)
           
           for host, services in sorted(subdomains.items()):
               print(f"  {host}:")
               for service in services:
                   url = f"{service.protocol}://{host}:{service.port}"
                   print(f"    • {url}")
                   if service.ip:
                       print(f"      └─ IP: {service.ip}")
       
       if domain_info['Leaks']:
           print(f"\nLeaks Found ({len(domain_info['Leaks'])}):")
           for leak in domain_info['Leaks']:
               if leak.leak:
                   print(f"  • {leak.leak.type} ({leak.leak.severity})")
       else:
           print("\nNo leaks found")
       
       print("=" * 50)
   
   recon_domain("leakix.net")

Subdomains
~~~~~~~~~~

Get list of subdomains for a specific domain:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Get subdomains
   subdomains = client.get_subdomains("leakix.net")

   # Access subdomain details
   print(f"Found {len(subdomains)} subdomains:")
   for subdomain in subdomains:
       print(f"{subdomain['subdomain']} - {subdomain['distinct_ips']} IPs")
       print(f"  Last seen: {subdomain['last_seen']}")

   # Fun Example: Subdomain Discovery
   def discover_subdomains(domain):
       """Discover and analyze subdomains for a domain."""
       subdomains = client.get_subdomains(domain)
       
       print(f"\nSUBDOMAIN DISCOVERY: {domain}")
       print("=" * 50)
       
       if subdomains:
           print(f"\nFound {len(subdomains)} subdomains:\n")
           
           # Sort by last_seen (most recent first)
           sorted_subs = sorted(
               subdomains, 
               key=lambda x: x.get('last_seen', ''), 
               reverse=True
           )
           
           for i, subdomain in enumerate(sorted_subs, 1):
               subdomain_name = subdomain['subdomain']
               distinct_ips = subdomain.get('distinct_ips', 0)
               last_seen = subdomain.get('last_seen', 'N/A')
               
               print(f"  {i}. {subdomain_name}")
               print(f"     IPs: {distinct_ips} | Last seen: {last_seen}")
       else:
           print("\nNo subdomains found")
       
       print("=" * 50)
       
       return subdomains
   
   discover_subdomains("leakix.net")

Cache Management
~~~~~~~~~~~~~~~~

Manage cache and get statistics:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   # Get cache statistics
   stats = client.get_cache_stats()
   print(f"Total entries: {stats['total_entries']}")
   print(f"Active entries: {stats['active_entries']}")
   print(f"TTL: {stats['ttl_minutes']} minutes")

   # Get current TTL
   ttl = client.get_cache_ttl()
   print(f"Current TTL: {ttl} minutes")

   # Set cache TTL to 10 minutes
   client.set_cache_ttl(10)

   # Clear all cache entries
   client.clear_cache()

Error Handling
--------------

Missing API Key
~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   if not client.has_api_key():
       print("Please set your API key:")
       api_key = input("API Key: ")
       client.save_api_key(api_key)

Invalid API Key
~~~~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX(api_key="invalid_key")

   if not client.has_api_key():
       print("API key is invalid. It must be 48 characters long.")

Query Errors
~~~~~~~~~~~~

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()

   try:
       results = client.search(
           scope="leak",
           pages=5,
           query='invalid query syntax',
       )
       if not results:
           print("No results found. Check your query.")
   except ValueError as e:
       print(f"Error: {e}")

