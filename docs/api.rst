API Reference
=============

This section provides detailed documentation for the LeakPy API.

Main Classes
------------

LeakIXScraper
~~~~~~~~~~~~~

.. autoclass:: leakpy.scraper.LeakIXScraper
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

LeakIXAPI
~~~~~~~~~

.. autoclass:: leakpy.api.LeakIXAPI
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

APIKeyManager
~~~~~~~~~~~~~

.. autoclass:: leakpy.config.APIKeyManager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Functions
---------

Parser Functions
~~~~~~~~~~~~~~~~

.. autofunction:: leakpy.parser.extract_data_from_json

.. autofunction:: leakpy.parser.get_all_fields

.. autofunction:: leakpy.parser.process_and_format_data

Logger Functions
~~~~~~~~~~~~~~~~

.. autofunction:: leakpy.logger.setup_logger

Config Functions
~~~~~~~~~~~~~~~~

.. autofunction:: leakpy.config.get_config_dir

Cache
~~~~~

.. autoclass:: leakpy.cache.APICache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

