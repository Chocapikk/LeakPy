Available Fields
=================

LeakPy supports 71+ fields organized by category. All results are returned as ``l9event`` objects that support dot notation access.

.. note::
   The field structure follows the official `l9format schema <https://docs.leakix.net/docs/api/l9format/>`_ from LeakIX. 
   For the complete official documentation of the l9event format, see the `LeakIX API documentation <https://docs.leakix.net/docs/api/l9format/>`_.

Accessing Fields
----------------

Use ``search()`` to get results as ``l9event`` objects:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()  # silent=True par défaut

   # Get results
   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="full"  # Get all fields
   )

   # Access fields using dot notation
   for leak in results:
       # Root fields
       ip = leak.ip
       port = leak.port
       
       # Nested fields
       if leak.geoip:
           country = leak.geoip.country_name
       
       if leak.http:
           status = leak.http.status

Field Categories
----------------

Root Fields
~~~~~~~~~~

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

**Example:**

.. code-block:: python

   for leak in results:
       print(f"{leak.protocol}://{leak.ip}:{leak.port}")
       print(f"Host: {leak.host}")
       print(f"Event Type: {leak.event_type}")

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

**Example:**

.. code-block:: python

   for leak in results:
       if leak.geoip:
           print(f"Country: {leak.geoip.country_name}")
           print(f"City: {leak.geoip.city_name}")
           if leak.geoip.location:
               print(f"Coordinates: {leak.geoip.location.lat}, {leak.geoip.location.lon}")

HTTP Fields
~~~~~~~~~~~

HTTP-specific information (access via ``leak.http.field``):

- ``http.favicon_hash`` - Favicon hash
- ``http.header.content-type`` - Content-Type header (access via ``leak.http.header.content_type`` or ``leak.get('http.header.content-type')``)
- ``http.header.server`` - Server header (access via ``leak.http.header.server``)
- ``http.length`` - Response length
- ``http.root`` - Root path
- ``http.status`` - HTTP status code
- ``http.title`` - Page title
- ``http.url`` - Full URL

**Example:**

.. code-block:: python

   for leak in results:
       if leak.http:
           print(f"HTTP Status: {leak.http.status}")
           print(f"HTTP Title: {leak.http.title}")
           if leak.http.header:
               print(f"Server: {leak.http.header.server}")
               # For headers with dashes, use get() or access via attribute
               content_type = leak.http.header.get('content-type') or getattr(leak.http.header, 'content_type', None)

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

**Example:**

.. code-block:: python

   for leak in results:
       if leak.leak:
           print(f"Leak Type: {leak.leak.type}")
           print(f"Severity: {leak.leak.severity}")
           if leak.leak.dataset:
               print(f"Dataset Size: {leak.leak.dataset.size}")

Network Fields
~~~~~~~~~~~~~~

Network information (access via ``leak.network.field``):

- ``network.asn`` - Autonomous System Number
- ``network.network`` - Network information
- ``network.organization_name`` - Organization name

**Example:**

.. code-block:: python

   for leak in results:
       if leak.network:
           print(f"ASN: {leak.network.asn}")
           print(f"Organization: {leak.network.organization_name}")

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

**Example:**

.. code-block:: python

   for leak in results:
       if leak.service:
           if leak.service.software:
               print(f"Software: {leak.service.software.name} {leak.service.software.version}")
           if leak.service.credentials:
               print(f"Username: {leak.service.credentials.username}")

SSH Fields
~~~~~~~~~~

SSH-specific information (access via ``leak.ssh.field``):

- ``ssh.banner`` - SSH banner
- ``ssh.fingerprint`` - SSH fingerprint
- ``ssh.motd`` - Message of the day
- ``ssh.version`` - SSH version

**Example:**

.. code-block:: python

   for leak in results:
       if leak.ssh:
           print(f"SSH Version: {leak.ssh.version}")
           print(f"SSH Banner: {leak.ssh.banner}")

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

**Example:**

.. code-block:: python

   for leak in results:
       if leak.ssl:
           print(f"SSL Version: {leak.ssl.version}")
           if leak.ssl.certificate:
               print(f"SSL CN: {leak.ssl.certificate.cn}")
               print(f"SSL Valid: {leak.ssl.certificate.valid}")
               print(f"Expires: {leak.ssl.certificate.not_after}")

Complete Example
----------------

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()  # silent=True par défaut

   results = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="full"
   )

   for leak in results:
       # Root fields
       print(f"Target: {leak.protocol}://{leak.ip}:{leak.port}")
       print(f"Host: {leak.host}")
       
       # GeoIP
       if leak.geoip:
           print(f"Location: {leak.geoip.country_name}, {leak.geoip.city_name}")
       
       # HTTP
       if leak.http:
           print(f"HTTP {leak.http.status}: {leak.http.title}")
       
       # SSL
       if leak.ssl and leak.ssl.certificate:
           print(f"SSL CN: {leak.ssl.certificate.cn}")
       
       # Leak info
       if leak.leak:
           print(f"Leak Type: {leak.leak.type}, Severity: {leak.leak.severity}")

