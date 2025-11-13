# Changelog

All notable changes to LeakPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

