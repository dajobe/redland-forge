# Build TUI - Parallel Build Monitor

A sophisticated text-based user interface for monitoring parallel Redland builds across multiple remote hosts.

## Overview

Build TUI provides real-time monitoring of parallel build processes with a clean, organized terminal interface. It displays build progress, status updates, and output from multiple hosts simultaneously.

## Features

- **Real-time Monitoring**: Live updates of build progress across multiple hosts
- **Parallel Execution**: Concurrent builds with configurable limits
- **Status Tracking**: Visual indicators for different build stages (connecting, preparing, building, success/failure)
- **Output Buffering**: Intelligent output management with configurable limits
- **Terminal UI**: Responsive interface that adapts to terminal size
- **SSH Integration**: Secure remote execution with comprehensive error handling
- **Build Step Detection**: Automatic detection of build phases (configure, make, install, etc.)
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

The application uses a modular architecture with clear separation of concerns:

- **BuildTUI** (`build-redland-tui.py`): Main orchestrator and UI controller
- **LayoutManager** (`layout_manager.py`): Terminal layout and host section positioning
- **StatisticsManager** (`statistics_manager.py`): Build progress and statistics calculation
- **HostSection** (`host_section.py`): Individual host display and state management
- **SSHConnection** (`ssh_connection.py`): Remote connection and command execution
- **OutputBuffer** (`output_buffer.py`): Output buffering and line management
- **TextFormatter** (`text_formatter.py`): Text formatting and display utilities
- **Config** (`config.py`): Centralized configuration management
- **BuildStepDetector** (`build_step_detector.py`): Build phase detection
- **AutoExitManager** (`auto_exit_manager.py`): Auto-exit timing and countdown management
- **BuildSummaryCollector** (`build_summary_collector.py`): Build result collection and summary generation

## Configuration

All settings are centralized in `config.py` and include:

- Build timeouts and retries
- Terminal layout parameters
- SSH connection settings
- Output buffering limits
- Color and formatting options
- Auto-exit timing and behavior
- Build summary configuration

## Testing

Run the comprehensive test suite:

```bash
cd build-tui
python3 -m pytest test_*.py -v
```

All 366 tests should pass, covering unit tests, integration tests, edge cases, and configuration flexibility.

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
├── build-redland-tui.py          # Main application
├── config.py                     # Centralized configuration
├── layout_manager.py             # Terminal layout management
├── host_section.py               # Individual host display logic
├── statistics_manager.py         # Build statistics and progress tracking
├── ssh_connection.py             # SSH connection and file transfer
├── build_step_detector.py        # Build phase detection
├── output_buffer.py              # Output buffering and management
├── text_formatter.py             # Text formatting and display utilities
├── auto_exit_manager.py          # Auto-exit timing and countdown
├── build_summary_collector.py    # Build result collection and summaries
├── test_*.py                     # Comprehensive test suite
└── requirements.txt              # Python dependencies
```

## Contributing

The codebase follows clean architecture principles with comprehensive test coverage, clear separation of concerns, well-documented APIs, and consistent coding standards. Each module contains its own documentation in docstrings.
