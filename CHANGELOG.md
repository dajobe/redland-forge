# Changelog

All notable changes to Redland Forge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-12

### Added

- Complete terminal user interface (TUI) for monitoring parallel builds across remote hosts
- Real-time progress tracking with live updates every 100ms
- Build timing cache system with persistent JSON storage and intelligent ETA calculation
- Auto-exit functionality with configurable countdown and build completion detection
- Enhanced navigation system with full-screen mode, interactive menus, and log scrolling
- Comprehensive test suite with 408 unit tests covering all major components
- Modular architecture with clear separation of concerns (SSH, UI, data management)
- Host visibility management for large-scale deployments
- Automatic build step detection (extract → configure → make → check → install)
- Color-coded status indicators and progress bars with adaptive terminal layouts
- Centralized configuration system with command-line options for all features

### Changed

- Migrated from shell scripts to modern Python 3 with type hints and proper error handling
- Implemented observer pattern for build state changes and strategy pattern for layouts
- Enhanced SSH connection management with parallel execution and connection pooling
- Added structured logging with debug/info separation and comprehensive error classification

### Technical Details

- Blessed-based terminal interface with responsive updates and keyboard input handling
- Output buffer limits and memory management for large-scale operations
- Mock-based testing for external dependencies (SSH, filesystem)
- Cross-platform compatibility from macOS to Linux variants
- Security features including input validation, connection timeouts, and SSH key management

## [0.5.0] - 2025-08

### Added

- Build timing cache with configurable retention (30 days, 5 builds per host default)
- Auto-exit manager with visual countdown display and build summary reporting
- Enhanced navigation with full-screen mode and interactive menu system
- Log scrolling support with PAGE UP/DOWN and HOME/END keys
- Visual focus indicators with colored borders for selected hosts

### Changed

- Improved cache key normalization using user@hostname format
- Enhanced progress estimation based on historical timing data
- Added build completion callbacks and result collection

## [0.4.0] - 2025-07

### Added

- Complete terminal user interface foundation with blessed library
- Modular architecture with dedicated SSH, UI, and data management modules
- Real-time build monitoring across multiple hosts
- Adaptive terminal layouts that respond to window resizing
- Build step detection and statistics tracking
- Keyboard navigation and input handling

### Changed

- Migrated core functionality from shell scripts to Python classes
- Implemented proper error handling and connection recovery
- Added output buffering and truncation for performance

## [0.3.0] - 2024-07

### Added

- Python 3 rewrite with type hints and modern features
- Real-time streaming output from remote builds
- Intelligent color support with terminal detection
- Host file support with comment parsing
- Enhanced build summaries with success/failure statistics
- Structured logging and return code tracking

### Changed

- Replaced manual option parsing with argparse
- Adopted pathlib for cross-platform file operations
- Improved error handling and user feedback

## [0.2.0] - 2006-2023

### Added

- Enhanced error detection and build artifact cleanup
- Build time calculation and performance monitoring
- Dynamic library path management for different architectures
- Berkeley DB version detection (versions 2, 3, 4)
- CPU core detection for parallel make execution (`make -j$ncpus`)
- Compiler output integration into build summaries

### Changed

- Improved cross-platform compatibility for various Unix systems
- Enhanced GNU make detection across different environments
- Added config.guess location discovery for architecture detection

## [0.1.0] - 2003-2005

### Added

- Initial remote build execution framework using SSH
- Basic time tracking and build status reporting
- Support for autoconf build sequence (configure, make, make check, make install)
- JDK detection and path management for Java language bindings
- Architecture-specific handling for macOS and various Unix variants
- Language binding support for C#, TCL, Python, and others
- Basic build artifact cleanup and remote directory management

### Changed

- Established foundation for cross-platform build testing
- Implemented core SSH-based remote execution patterns
