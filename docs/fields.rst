Available Fields
=================

LeakPy supports 70 fields organized by category. All events are returned as ``L9Event`` objects that support dot notation access.

.. note::
   The field structure follows the official `l9format schema <https://docs.leakix.net/docs/api/l9format/>`_ from LeakIX. 
   For the complete official documentation of the L9Event format, see the `LeakIX API documentation <https://docs.leakix.net/docs/api/l9format/>`_.

Accessing Fields
----------------

Use ``search()`` to get events as ``L9Event`` objects:

.. code-block:: python

   from leakpy import LeakIX

   client = LeakIX()
   events = client.search(
       scope="leak",
       query='+country:"France"',
       pages=2,
       fields="full"
   )

   for event in events:
       print(event.ip, event.port, event.protocol)

Field Reference
---------------

+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| Category         | Fields                                                                                                                                 |
+==================+==================================================================================================================================+
| Root             | ``event_fingerprint``, ``event_pipeline``, ``event_source``, ``event_type``, ``host``, ``ip``, ``mac``, ``port``, ``protocol``, |
|                  | ``reverse``, ``summary``, ``tags``, ``time``, ``transport``, ``vendor``                                                         |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| GeoIP            | ``geoip.city_name``, ``geoip.continent_name``, ``geoip.country_iso_code``, ``geoip.country_name``, ``geoip.location.lat``,        |
|                  | ``geoip.location.lon``, ``geoip.region_iso_code``, ``geoip.region_name``                                                         |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| HTTP             | ``http.favicon_hash``, ``http.length``, ``http.root``, ``http.status``, ``http.title``, ``http.url``                             |
|                  | **Note:** HTTP headers via ``event.http.header.get('header_name')``                                                              |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| Leak             | ``leak.dataset.collections``, ``leak.dataset.files``, ``leak.dataset.infected``, ``leak.dataset.ransom_notes``,                  |
|                  | ``leak.dataset.rows``, ``leak.dataset.size``, ``leak.severity``, ``leak.stage``, ``leak.type``                                   |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| Network          | ``network.asn``, ``network.network``, ``network.organization_name``                                                               |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| Service          | ``service.credentials.key``, ``service.credentials.noauth``, ``service.credentials.password``, ``service.credentials.raw``,        |
|                  | ``service.credentials.username``, ``service.software.fingerprint``, ``service.software.modules``, ``service.software.name``,     |
|                  | ``service.software.os``, ``service.software.version``                                                                              |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| SSH              | ``ssh.banner``, ``ssh.fingerprint``, ``ssh.motd``, ``ssh.version``                                                                |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+
| SSL              | ``ssl.certificate.cn``, ``ssl.certificate.domain``, ``ssl.certificate.fingerprint``, ``ssl.certificate.issuer_name``,             |
|                  | ``ssl.certificate.key_algo``, ``ssl.certificate.key_size``, ``ssl.certificate.not_after``, ``ssl.certificate.not_before``,        |
|                  | ``ssl.certificate.valid``, ``ssl.cypher_suite``, ``ssl.detected``, ``ssl.enabled``, ``ssl.jarm``, ``ssl.version``                 |
+------------------+----------------------------------------------------------------------------------------------------------------------------------+

Complete Example
----------------

See :doc:`examples` for complete usage examples.
