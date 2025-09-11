# Build TUI - Parallel Build Monitor

A sophisticated text-based user interface for monitoring parallel Redland builds across multiple remote hosts.

## Overview

Build TUI provides real-time monitoring of parallel build processes with a clean, organized terminal interface. It displays build progress, status updates, and output from multiple hosts simultaneously.

** Documentation**

- **[Architecture Guide](architecture.md)**: Detailed system architecture and design
- **[Testing Guide](testing.md)**: Testing strategies and infrastructure

## Features

- **Real-time Monitoring**: Live updates of build progress across multiple hosts
- **Parallel Execution**: Concurrent builds with configurable limits
- **Status Tracking**: Visual indicators for different build stages (connecting, preparing, building, success/failure)
- **Output Buffering**: Intelligent output management with configurable limits
- **Terminal UI**: Responsive interface that adapts to terminal size
- **SSH Integration**: Secure remote execution with comprehensive error handling
- **Build Step Detection**: Automatic detection of build phases (configure, make, install, etc.)
- **Build Timing Cache**: Persistent storage of build timing data for progress estimates
- **Auto-Exit**: Automatically exits after builds complete with configurable delay
- **Build Summary**: Comprehensive build result summaries with success/failure reporting

## Quick Start

```bash
# Basic usage
cd build-tui
./build-redland-tui.py redland-1.1.0.tar.gz user@host1 user@host2

# With host file
./build-redland-tui.py redland-1.1.0.tar.gz -f hosts.txt

# Limit concurrent builds
./build-redland-tui.py redland-1.1.0.tar.gz --max-concurrent 4 user@host1 user@host2

# Auto-exit after 10 minutes (default: 5 minutes)
./build-redland-tui.py redland-1.1.0.tar.gz --auto-exit-delay 600 user@host1 user@host2

# Disable auto-exit
./build-redland-tui.py redland-1.1.0.tar.gz --no-auto-exit user@host1 user@host2
```

## Auto-Exit and Build Summary Features

### Auto-Exit Functionality

The application automatically exits after a configurable delay once all builds complete, providing hands-free operation for automated build monitoring.

**Key Benefits:**

- **Hands-free operation**: Perfect for CI/CD pipelines and scheduled builds
- **Configurable timing**: Adjustable delay from 1 second to any duration
- **Smart timer management**: Timer resets on each new build completion
- **Visual countdown**: Real-time countdown display in the UI header
- **Override capability**: Users can still manually exit before auto-exit triggers

**Configuration Options:**

```bash
--auto-exit-delay SECONDS    # Custom delay (default: 300 = 5 minutes)
--no-auto-exit               # Disable auto-exit entirely
```

## Command Line Options

### Build and Host Configuration

```bash
tarball                      # The Redland package tarball (e.g., redland-1.1.0.tar.gz)
hosts                        # One or more username@hostname pairs (can be comma-separated)
-f, --hosts-file FILE        # Read hosts from file, one per line
--max-concurrent N           # Maximum concurrent builds (default: auto-detect based on screen size)
```

### Auto-Exit Configuration

```bash
--auto-exit-delay SECONDS    # Auto-exit delay in seconds (default: 300 = 5 minutes)
--no-auto-exit               # Disable auto-exit functionality
```

### Build Timing Cache Configuration

```bash
--cache-file PATH            # Custom cache file location (default: ~/.config/build-tui/timing-cache.json)
--cache-retention DAYS       # Cache retention period in days (default: 30)
--cache-keep-builds N        # Number of recent builds to keep in cache (default: 5)
--no-cache                   # Disable timing cache functionality
--no-progress                # Disable progress display
```

### Output and Debug Options

```bash
--color MODE                 # Control color output: auto (default), always, or never
--debug                      # Enable debug logging to debug.log file
```

### Cache Management

```bash
--cleanup-demo-hosts         # Clean up demo/test host data from timing cache and exit
--remove-testing-hosts       # Remove specific testing hosts from timing cache and exit
```

## Build Timing Cache

The Build Timing Cache system provides intelligent progress estimation by storing historical build timing data. This enables accurate progress estimates for ongoing builds based on previous performance data from the same hosts.

### Key Features

- **Progress Estimation**: Real-time progress estimates based on historical data
- **Host-Specific Data**: Separate timing statistics for each remote host
- **Global Build Retention**: Configurable limit on the number of recent builds to keep
- **Time-Based Cleanup**: Automatic removal of data older than the retention period
- **Demo Host Management**: Special handling for temporary/testing hosts with shorter retention

### Cache Configuration

The cache system supports both count-based and time-based retention:

- **Count-Based**: Keep only the last N builds globally (default: 5)
- **Time-Based**: Remove data older than X days (default: 30 days)
- **Demo Hosts**: Automatically cleaned after 1 hour

### Cache Usage Examples

```bash
# Default cache settings (5 builds, 30 days retention)
./build-redland-tui.py redland-1.1.0.tar.gz user@host1

# Keep more build history
./build-redland-tui.py redland-1.1.0.tar.gz --cache-keep-builds 10 user@host1

# Longer retention period
./build-redland-tui.py redland-1.1.0.tar.gz --cache-retention 90 user@host1

# Custom cache location
./build-redland-tui.py redland-1.1.0.tar.gz --cache-file ~/.my-build-cache.json user@host1

# Disable caching entirely
./build-redland-tui.py redland-1.1.0.tar.gz --no-cache user@host1
```

### Build Summary Output

When the application exits (either manually or via auto-exit), it prints a comprehensive summary of all build results to stdout.

**Summary Includes:**

- **Total build time**: Overall duration from start to completion
- **Success/failure counts**: Clear breakdown of build outcomes
- **Per-host timing**: Individual build durations for each host
- **Error details**: Specific error messages for failed builds
- **Success rates**: Percentage and ratio of successful builds

**Example Output:**

```
============================================================
BUILD SUMMARY
============================================================
Total time: 12m 34s

SUCCESSFUL BUILDS:
  ✓ dajobe@berlin (3m 12s)
  ✓ dajobe@fedora (4m 45s)

FAILED BUILDS:
  ✗ dajobe@gentoo (1m 23s)
    Error: Build failed during make step

Overall: 2/3 builds successful (66.7%)
============================================================
```

### Use Cases

- **Automated builds**: Set up unattended build monitoring
- **CI/CD integration**: Perfect for continuous integration workflows
- **Batch processing**: Handle large-scale multi-host builds
- **Scheduled builds**: Run builds during off-hours with automatic cleanup
- **Reporting**: Generate build summaries for documentation and analysis

## Architecture

Build TUI uses a modular architecture with clear separation of concerns, designed for monitoring parallel build processes across multiple remote hosts. The application provides real-time monitoring, progress tracking, and comprehensive build management capabilities.

For detailed architectural information, design patterns, and technical implementation details, see the **[Architecture Guide](architecture.md)**.

## Configuration

All settings are centralized in `config.py`. For detailed configuration options including build timeouts, SSH settings, UI preferences, and advanced features, see the **[Architecture Guide](architecture.md)**.

## Testing

Build TUI includes a comprehensive test suite with 408+ unit tests covering all major components and functionality.

### Running Tests

```bash
cd build-tui
python3 -m pytest test_*.py -v
```

All tests should pass, covering unit tests, integration tests, edge cases, and configuration flexibility.

### Test Categories

- **Unit Tests**: Individual module functionality with mocked dependencies
- **Integration Tests**: Component interaction and data flow validation
- **UI Tests**: Rendering and display functionality
- **Error Handling Tests**: Exception scenarios and recovery mechanisms

For detailed information about the testing architecture, strategies, and infrastructure, see the **[Testing Guide](testing.md)**.

## Dependencies

- Python 3.6+
- blessed (terminal UI)
- paramiko (SSH connections)

Install with:

```bash
cd build-tui
pip install -r requirements.txt
```

## Usage Examples

### Basic Build

```bash
cd build-tui
./build-redland-tui.py redland-1.1.0.tar.gz user@build-server1 user@build-server2
```

### Large Scale Build

```bash
cd build-tui
./build-redland-tui.py redland-1.1.0.tar.gz -f production-hosts.txt --max-concurrent 8
```

### Debug Mode

```bash
cd build-tui
./build-redland-tui.py redland-1.1.0.tar.gz --debug user@host1 user@host2
```

### Automated Build Monitoring

```bash
cd build-tui
# Auto-exit after 10 minutes with comprehensive logging
./build-redland-tui.py redland-1.1.0.tar.gz \
  --auto-exit-delay 600 \
  --debug \
  -f production-hosts.txt \
  --max-concurrent 6
```

### CI/CD Integration

```bash
cd build-tui
# Perfect for automated pipelines - exits automatically
./build-redland-tui.py redland-1.1.0.tar.gz \
  --auto-exit-delay 300 \
  -f ci-hosts.txt \
  --max-concurrent 4
```

## Key Features

- **Adaptive Layout**: Automatically adjusts to terminal size
- **Real-time Updates**: Live status and progress monitoring
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance**: Efficient parallel execution with resource management
- **Extensibility**: Modular design for easy feature additions
- **Auto-Exit**: Hands-free operation with configurable timing
- **Build Summaries**: Comprehensive result reporting and analysis
- **CI/CD Ready**: Perfect for automated build pipelines

## Project Structure

```
build-tui/
├── 📄 Documentation
│   ├── README.md                 # Quick start and usage guide
│   ├── architecture.md           # System architecture and design
│   ├── testing.md                # Testing strategies and infrastructure
│   └── TODO.md                   # Future enhancements roadmap
│
├── 🚀 Core Application
│   ├── build-redland-tui.py      # Main application entry point
│   └── app.py                    # Main BuildTUI class and orchestration
│
├── 🔧 Core Components
│   ├── layout_manager.py         # Terminal layout and positioning
│   ├── host_section.py           # Individual host display logic
│   ├── statistics_manager.py     # Build statistics and progress tracking
│   ├── renderer.py               # UI rendering and display management
│   ├── input_handler.py          # Keyboard input processing and navigation
│   └── config.py                 # Centralized configuration management
│
├── 🌐 SSH and Networking
│   ├── parallel_ssh_manager.py   # Parallel SSH connection management
│   └── ssh_connection.py         # SSH connection and file transfer
│
├── 📊 Data Processing
│   ├── build_step_detector.py    # Build phase detection
│   ├── output_buffer.py          # Output buffering and management
│   ├── text_formatter.py         # Text formatting utilities
│   ├── build_timing_cache.py     # Build timing data persistence
│   ├── auto_exit_manager.py      # Auto-exit timing and countdown
│   └── build_summary_collector.py # Build result collection
│
├── 🧪 Testing Infrastructure
│   ├── test_*.py                 # Comprehensive test suite (19+ files)
│   └── test.tar.gz               # Test data archive
│
├── ⚙️ Utilities and Configuration
│   ├── color_manager.py          # ANSI color scheme management
│   ├── exception_handler.py      # Centralized exception handling
│   ├── host_visibility_manager.py # Host display visibility management
│   ├── progress_display_manager.py # Progress display utilities
│   └── requirements.txt          # Python dependencies
│
└── 🔨 Build Scripts
    └── build-agent.py            # Remote build execution script
```

## Documentation

Build TUI provides comprehensive documentation to help users and developers understand and work with the project:

### 📖 Documentation Files

| Document | Description |
|----------|-------------|
| **[Architecture Guide](architecture.md)** | Detailed system architecture, design patterns, and component interactions |
| **[Testing Guide](testing.md)** | Testing strategies, infrastructure, and development practices |
| **[README.md](README.md)** | This file - quick start, features, and usage examples |
| **[TODO.md](TODO.md)** | Future enhancements and development roadmap |

### Key Topics Covered

#### Architecture Guide (`architecture.md`)

- Core system components and their responsibilities
- Data flow and component interaction patterns
- Design patterns and architectural decisions
- Performance considerations and error handling
- Future extensibility and plugin architecture

#### Testing Guide (`testing.md`)

- Testing strategy and approach
- Test infrastructure and utilities
- Test categories and coverage
- Development testing workflow
- Mocking strategies and best practices

#### This README

- Quick start guide and basic usage
- Feature overview and command-line options
- Configuration examples and use cases
- Installation and dependency information

## Contributing

The codebase follows clean architecture principles with comprehensive test coverage, clear separation of concerns, well-documented APIs, and consistent coding standards. Each module contains its own documentation in docstrings.

### Getting Started for Contributors

1. Review the **[Architecture Guide](architecture.md)** to understand the system design
2. Familiarize yourself with the **[Testing Guide](testing.md)** for testing practices
3. Run the test suite: `python3 -m pytest test_*.py -v`
4. Check **[TODO.md](TODO.md)** for current development priorities
