# Changelog

All notable changes to LeakPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.6] - 2025-11-16

### Added
- Custom LeakIX dark theme for documentation with Fira Code font support
- Event deduplication in search results display
- Unique event count tracking in progress bar

### Changed
- Improved statistics counting for list fields (more accurate percentages)
- Enhanced color scheme in CLI tables to match LeakIX branding
- Improved multi-column layout for plugins and fields listing
- Better display of long field values (automatic wrapping)

### Fixed
- Fixed percentage calculations in statistics for list fields

## [2.2.5] - 2025-11-16

### Fixed
- Fixed broken CLI search command - table display was corrupted and not showing results correctly
- Improved progress bar for search and stats query commands - now shows real-time progress as events are streamed, with accurate event count and rate (events/second)
- Fixed progress bar display when interrupting with Ctrl+C - now properly removes the progress bar and shows a clean message
- Cache now automatically removes expired entries on load - expired entries are no longer stored on disk

### Added
- Progress bar now available for `stats query` command when loading results from API
- Graceful handling of Ctrl+C interruption - statistics are displayed on partially collected results instead of exiting

### Changed
- Progress bar now updates at each streamed event for more accurate real-time feedback
- Improved `list plugins` command display - plugins are now organized in multiple columns based on terminal width for better readability

### Removed
- Removed `query()` method from LeakIX class (use `search()` instead, which returns a generator with streaming support)
- Removed `stats overview` command (duplicate of `stats cache`)
- Removed "expired entries" from cache statistics display (expired entries are now automatically removed)

### Validation
- Added validation to prevent using bulk mode with scope="service" (bulk mode only works with scope="leak" per LeakIX API limitations)

## [2.2.4] - 2025-11-16

### Fixed
- HTTP connection not being closed when stopping generator early (e.g., using `break` in loop), causing unnecessary bandwidth and API quota consumption

## [2.2.3] - 2025-11-16

### Fixed
- Fixed `--raw` mode not outputting JSON when using `search` command (generator was not being consumed)

## [2.2.2] - 2025-11-16

### Changed
- `search()` now returns a generator instead of a list. Use `list(client.search(...))` if you need a list.
- Default `fields` parameter changed from `"protocol,ip,port"` to `"full"` in library API (CLI unchanged).
- `get_host()` and `get_domain()` now return `services`/`leaks` (lowercase) instead of `Services`/`Leaks`.

## [2.2.1] - 2025-11-15

### Added
- `get_all_fields()` can now be called without parameters to get all fields from schema (no API call needed)

## [2.2.0] - 2025-11-15

### Fixed
- Fixed documentation examples and import errors
- Fixed dependency compatibility (Python 3.9)

## [2.1.0] - 2025-11-15

### Changed
- Rate limit wait time now retrieved from `x-limited-for` header instead of defaulting to 60 seconds

### Fixed
- Fixed CLI output handling and argument parsing

## [2.0.5] - 2025-11-13

### Added
- Added bulk mode support (`-b/--bulk`) to `stats query` command (requires Pro API)

### Fixed
- Fixed `stats query` returning only 1 result instead of all results
- Improved statistics output display

### Removed
- Removed `deduplicate` parameter from `LeakIX.search()` and `LeakIX.query()` methods (was not working correctly)

## [2.0.4] - 2025-11-13

### Fixed
- Fixed import errors and test suite issues

## [2.0.3] - 2025-11-13

### Added
- Complete CLI refactoring with git-like subcommand structure (`leakpy <command> <subcommand>`)
- New commands: `lookup`, `list`, `config`, `cache`, `stats` with subcommands
- Batch processing support for lookup commands (`-i/--input`)
- New library methods: `get_host()`, `get_domain()`, `get_subdomains()`, `get_plugins()`, `get_all_fields()`, `get_cache_stats()`, `set_cache_ttl()`, `clear_cache()`, `analyze_query_stats()`
- All lookup methods support file output via `output` parameter

## [2.0.2] - 2025-11-13

### Fixed
- Fixed missing cache support for bulk mode queries

## [2.0.1] - 2025-11-13

### Fixed
- Fixed missing cache support for bulk mode queries

## [2.0.0] - 2025-11-13

### Added
- API response caching (default TTL: 5 minutes)
- `--silent` flag for scripting
- Enhanced CLI with improved banner and formatting

### Changed
- Minimum Python version: 3.9 (from 3.6)
- Enhanced API key storage using system keychain

### Security
- Improved API key storage security with keyring integration

## [1.0.0] - Previous Release

Initial release of LeakPy.

