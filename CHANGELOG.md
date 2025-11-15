# Changelog

All notable changes to LeakPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 2025-11-15

### Added
- **Improved `get_all_fields()` method**: Can now be called without parameters to get all fields from l9format schema (no API call needed)
  - When called without data: returns all 82+ fields from the schema
  - When called with data: extracts fields from that specific event (backward compatible)
  - No API key required when called without data

### Changed
- **Documentation updates**: Updated README, EXAMPLES.md, and RTD documentation to show the simplified usage of `get_all_fields()`

## [2.2.0] - 2025-11-15

### Changed
- **Major code refactoring**: Refactored `helpers.py` into modular `helpers/` directory structure
  - Separated helper functions into logical modules by theme (batch, bulk, cache, CLI execution, config, data, display, fetch, fields, files, logging, lookup, schema, etc.)
  - Reduced code duplication through extensive DRY (Don't Repeat Yourself) refactoring
  - Applied decorators for error handling, file operations, and API key requirements
  - Replaced custom parsing functions with Python built-ins (`int()`, `json.loads()`, `getattr()`)
  - Optimized list comprehensions and processing loops for better performance
  - Inlined single-use helper functions into their callers
  - Consolidated related functions into appropriate modules (e.g., statistics utilities, file operations)
- **Code organization improvements**:
  - Moved CLI execution functions to `cli_execution.py`
  - Moved display functions to `display.py`
  - Moved file operations to `file_operations.py`
  - Moved statistics processing to `data_utils.py`
  - Removed empty and redundant files (`formatting.py`, `http.py`, `api_parsing.py`, `statistics_utils.py`, `stats_command.py`)
- **Import optimization**: Simplified imports in `helpers/__init__.py` using `from .module import *`
- **Documentation improvements**: Fixed code examples to be self-contained and executable
- **Test improvements**: Moved `test_commands.sh` to `tests/` directory and fixed mock paths

### Fixed
- **Import errors**: Fixed circular imports and missing constant imports by using direct imports from `helpers.constants`
- **Mock paths**: Corrected mock targets in unit tests (`leakpy.helpers.fetch.make_api_request`, `leakpy.helpers.lookup.Console`)
- **Documentation examples**: Fixed `NameError` in documentation by adding necessary imports and client initialization
- **Output formatting**: Fixed SSH URLs being displayed as URLs in documentation examples (now shown as `PROTOCOL IP:PORT`)
- **Empty L9Event display**: Fixed `L9Event(None)` being printed by returning empty string in `_EmptyL9Event.__str__` and `__repr__`
- **HTTP status codes**: Replaced hardcoded status codes (429, 400) with `requests.codes` constants
- **CLI flags**: Ensured `--raw` and `--silent` flags are correctly placed before subcommands in all examples
- **Dependencies**: Fixed `emoji-country-flag` version requirement (changed from `>=2.1.0` to `>=1.3.2` for Python 3.9 compatibility)

### Removed
- **Backward compatibility**: Removed `helpers.py` compatibility file (direct imports to `helpers/` package now required)
- **Redundant files**: Removed empty and single-function files after inlining and consolidation
- **Unused functions**: Removed `display_stat_bar` and other unused helper functions
- **Test result files**: Removed unnecessary test output files from project root

## [2.1.0] - 2025-11-15

### Added
- **New `helpers.py` module**: Centralized helper functions for API operations, HTTP requests, caching, and CLI utilities
- **New `events.py` module**: Renamed from `parser.py` for better clarity (contains `L9Event` data models)
- **Documentation testing**: New test scripts `doc_examples_test.py` and `examples_md_test.py` to validate Python code examples in documentation (not executed by CI)

### Changed
- **Major DRY refactoring**: Consolidated repetitive code in `api.py` by extracting common patterns into helper functions
- **Helper migration**: All helper methods from `LeakIXAPI` class moved to standalone functions in `helpers.py` module
- **Rate limiting improvement**: Rate limit wait time now retrieved from `x-limited-for` header instead of defaulting to 60 seconds
- **Error handling**: Removed all `try/except` blocks in favor of conditional checks and dedicated helper functions for safe parsing
- **Code organization**: Reorganized `api.py` methods into logical sections (INITIALIZATION, HTTP HELPERS, PARSING HELPERS, CACHE HELPERS, BULK PROCESSING, PUBLIC API METHODS)
- **CLI consolidation**: Merged all CLI subcommands from `leakpy/cli/commands/` into single `cli.py` file for better maintainability
- **Module renaming**: `parser.py` → `events.py` for better semantic clarity (internal change, no API impact)
- **Documentation examples**: Simplified all examples in `EXAMPLES.md` and documentation to be more direct and concise
- **Bulk mode examples**: Updated all bulk mode examples to use `plugin:TraccarPlugin` instead of `country:"France"` and removed `pages` parameter (bulk mode retrieves all results automatically)

### Fixed
- **Import cleanup**: Removed unused imports and minimized import statements in `leakix.py`
- **Documentation consistency**: Fixed bulk mode examples to not specify `pages` parameter when using bulk mode
- **CLI output handling**: Fixed stdout redirection and output file handling in lookup commands
- **Argument parsing**: Used `getattr` for safe access to `args.ip` and `args.domain` to prevent `AttributeError` in CLI

### Removed
- **CLI subdirectory structure**: Removed `leakpy/cli/commands/` directory structure, consolidated into `cli.py`
- **Redundant example file**: Removed `example.py` as its purpose is covered by `EXAMPLES.md` and documentation
- **Unused imports**: Cleaned up unused imports across the codebase

## [2.0.5] - 2025-11-13

### Added
- **Stats Query**: Added bulk mode support (`-b/--bulk`) to `stats query` command for faster queries (requires Pro API)

### Fixed
- **Stats Query**: Removed broken deduplication logic that was incorrectly filtering results, causing `stats query` to return only 1 result instead of all results
- **Display**: Improved alignment of statistics output using Rich Table instead of text bars

### Removed
- **Deduplication**: Removed all deduplication functionality as it was not working correctly and causing issues with query results
- **API Breaking Change**: Removed `deduplicate` parameter from `LeakIX.search()` and `LeakIX.query()` methods (this parameter never worked correctly)

## [2.0.4] - 2025-11-13

### Fixed
- **CI Workflow**: Fixed import test to use correct module names (`leakpy.leakix.LeakIX` instead of deprecated `leakpy.scraper.LeakIXScraper`)
- **Test Suite**: Fixed `test_api_key_manager_read_nonexistent` to properly mock keyring and prevent reading from system keychain

## [2.0.3] - 2025-11-13

### Added
- **Complete CLI Refactoring**: Major overhaul of the command-line interface with git-like subcommand structure
  - **New Command Structure**: All commands now follow hierarchical subcommand pattern (`leakpy <command> <subcommand> [options]`)
  - **`search` Command**: Search LeakIX for leaks or services
    - Supports query strings, field extraction, bulk mode, and file output
  - **`lookup` Command with Subcommands**: Lookup information about specific IPs, domains, or subdomains
    - `leakpy lookup host <IP>` - Get detailed information about a specific IP address
    - `leakpy lookup domain <domain>` - Get detailed information about a domain and its subdomains
    - `leakpy lookup subdomains <domain>` - Get list of subdomains for a specific domain
  - **`list` Command with Subcommands**: List available plugins or fields
    - `leakpy list plugins` - List all available LeakIX plugins
    - `leakpy list fields` - List all available fields from sample queries
  - **`config` Command with Subcommands**: Manage API key configuration
    - `leakpy config set [API_KEY]` - Set or update API key (interactive or direct)
    - `leakpy config reset` - Delete stored API key
  - **`cache` Command with Subcommands**: Manage API response cache
    - `leakpy cache clear` - Clear all cached API responses
    - `leakpy cache set-ttl <MINUTES>` - Set cache TTL in minutes
    - `leakpy cache show-ttl` - Display current cache TTL setting
  - **`stats` Command with Subcommands**: Display statistics and metrics with visualizations
    - `leakpy stats cache` - Display cache statistics with visualizations
    - `leakpy stats overview` - Display overview of all statistics
    - `leakpy stats query` - Analyze and display statistics from search queries (by country, protocol, port, etc.)
  - **Enhanced Help Display**: ASCII banner now automatically displays when showing help messages (`--help` or `-h`)
    - Banner appears in README.md and documentation homepage for better brand recognition
    - Banner is automatically suppressed in `--silent` mode for scripting compatibility
  - **Batch Processing Support**: All lookup commands now support batch processing via `-i/--input` option
    - Process multiple IPs or domains from a file (one per line)
    - Progress bars and summary statistics for batch operations
    - JSON output format for batch results
  - **Improved Display Options**: New options for controlling output display
    - `--limit` option to control number of services/leaks displayed (default: 50)
    - `--all` option to display all results without limit
    - Better formatted tables with consistent styling across all lookup types
- **New Library Methods**: Expanded Python library API with new functionality
  - **`get_host(ip, fields="full", output=None)`**: Get detailed information about a specific IP address
    - Returns dictionary with 'Services' and 'Leaks' keys containing L9Event objects
    - Supports field extraction and file output
  - **`get_domain(domain, fields="full", output=None)`**: Get detailed information about a domain
    - Returns dictionary with 'Services' and 'Leaks' keys containing L9Event objects
    - Includes subdomain information and associated services
  - **`get_subdomains(domain, output=None)`**: Get list of subdomains for a specific domain
    - Returns list of dictionaries with subdomain, distinct_ips, and last_seen information
    - Supports file output for easy integration
  - **`get_plugins()`**: Get list of available LeakIX plugins
    - Returns list of plugin names
  - **`get_all_fields(data, current_path=None)`**: Extract all available fields from a data object
    - Returns set of all field paths (e.g., "protocol", "geoip.country_name", "service.software.name")
    - Supports nested field discovery
  - **`get_cache_stats()`**: Get comprehensive cache statistics
    - Returns dictionary with total_entries, active_entries, expired_entries, TTL information, and cache file details
  - **`get_cache_ttl()`**: Get current cache TTL in minutes
  - **`set_cache_ttl(minutes)`**: Configure cache TTL programmatically
  - **`clear_cache()`**: Clear all cached API responses programmatically
  - **`delete_api_key()`**: Delete stored API key from secure storage
  - **`analyze_query_stats(results, fields=None, top=10, all_fields=False)`**: Analyze query results and extract statistics
    - Returns QueryStats object with dot notation access (e.g., `stats.total`, `stats.fields.protocol.http`)
    - Supports object-oriented field extraction with callables
    - Flexible field specification (string, list, dict, or callable)
    - Can analyze from live queries or JSON files

### Changed
- **CLI Architecture**: Complete restructuring from flat commands to hierarchical subcommand system (similar to git)
  - Commands now follow pattern: `leakpy <command> <subcommand> [options]`
  - Better organization and discoverability of available operations
  - Consistent argument patterns across related commands
- **Lookup Commands**: Unified behavior and error handling across all lookup subcommands
  - Consistent progress bar display and formatting in batch mode operations
  - Unified error messages and validation across `lookup host`, `lookup domain`, and `lookup subdomains`
  - Improved table formatting for services and leaks display with better alignment
- **API Consistency**: Complete parity between CLI and library - all CLI commands have direct library method equivalents
  - `leakpy search` → `client.search()`
  - `leakpy lookup host` → `client.get_host()`
  - `leakpy lookup domain` → `client.get_domain()`
  - `leakpy lookup subdomains` → `client.get_subdomains()`
  - `leakpy list plugins` → `client.get_plugins()`
  - `leakpy list fields` → `client.get_all_fields()` + `client.search()`
  - `leakpy config set` → `client.save_api_key()`
  - `leakpy config reset` → `client.delete_api_key()`
  - `leakpy cache clear` → `client.clear_cache()`
  - `leakpy cache set-ttl` → `client.set_cache_ttl()`
  - `leakpy cache show-ttl` → `client.get_cache_ttl()`
  - `leakpy stats cache` → `client.get_cache_stats()`
  - `leakpy stats query` → `client.analyze_query_stats()`
- **Library Output Support**: All lookup methods now support file output
  - `get_host()`, `get_domain()`, and `get_subdomains()` accept `output` parameter
  - Can write directly to file path or file object
  - Results are still returned even when writing to file
- **Enhanced Query Statistics**: Improved `analyze_query_stats()` method
  - Object-oriented field extraction with callable functions
  - Support for nested field access (e.g., `leak.geoip.country_name`)
  - QueryStats objects with dot notation for clean, Pythonic API
  - No KeyError exceptions - missing fields return None

## [2.0.2] - 2025-11-13

### Fixed
- **Cache Support for Bulk Queries**: Fixed missing cache support for bulk mode queries, which was causing unnecessary API calls even when data was already cached
- **Cache Performance**: Improved cache performance by removing unused HTTP header parsing code (LeakIX doesn't send cache headers)

### Changed
- **Code Cleanup**: Removed unused `_get_cache_ttl_from_response()` method and simplified cache implementation
- **Documentation**: Updated documentation to accurately reflect cache behavior (default TTL of 5 minutes, no HTTP header support)

## [2.0.1] - 2025-11-13

### Fixed
- **Cache Support for Bulk Queries**: Fixed missing cache support for bulk mode queries, which was causing unnecessary API calls even when data was already cached
- **Cache Performance**: Improved cache performance by removing unused HTTP header parsing code (LeakIX doesn't send cache headers)

### Changed
- **Code Cleanup**: Removed unused `_get_cache_ttl_from_response()` method and simplified cache implementation
- **Documentation**: Updated documentation to accurately reflect cache behavior (default TTL of 5 minutes, no HTTP header support)

## [2.0.0] - 2025-11-13

### Added
- **API Response Caching**: Automatic caching of API responses to reduce unnecessary API calls
  - Default TTL of 5 minutes
  - New `--clear-cache` CLI option to clear the cache
- **Silent Mode**: New `--silent` flag for scripting that suppresses all output
- **Enhanced CLI**: Improved banner with ASCII art and better formatting
- **Better Error Handling**: More descriptive error messages and traceback information
- **Comprehensive Documentation**: Full Sphinx documentation with examples
- **Test Suite**: Complete unit test coverage for core functionality
- **CI/CD Pipeline**: Automated testing across multiple Python versions and operating systems

### Changed
- **Python Version Requirement**: Minimum Python version raised to 3.9 (from 3.6)
- **API Key Storage**: Enhanced secure storage using system keychain (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)
- **CLI Options**: Updated and standardized CLI options documentation
- **Code Structure**: Refactored codebase for better maintainability and modularity

### Fixed
- Documentation inconsistencies between README and actual CLI options
- Missing `--clear-cache` option in documentation
- Removed deprecated `-i/--interactive` option from documentation

### Security
- Improved API key storage security with keyring integration
- Fallback to secure file storage with restrictive permissions (600) when keyring is unavailable

## [1.0.0] - Previous Release

Initial release of LeakPy.

