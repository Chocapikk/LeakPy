# Changelog

All notable changes to LeakPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
    - Returns dictionary with 'Services' and 'Leaks' keys containing l9event objects
    - Supports field extraction and file output
  - **`get_domain(domain, fields="full", output=None)`**: Get detailed information about a domain
    - Returns dictionary with 'Services' and 'Leaks' keys containing l9event objects
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

