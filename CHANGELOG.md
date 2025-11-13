# Changelog

All notable changes to LeakPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-13

### Added
- **API Response Caching**: Automatic caching of API responses to reduce unnecessary API calls
  - Respects HTTP headers (`Cache-Control: max-age` or `Expires`) when available
  - Default TTL of 5 minutes when headers are not available
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

