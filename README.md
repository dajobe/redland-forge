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

## Quick Start

```bash
# Basic usage
cd build-tui
./build-redland-tui.py redland-1.1.0.tar.gz user@host1 user@host2

# With host file
./build-redland-tui.py redland-1.1.0.tar.gz -f hosts.txt

# Limit concurrent builds
./build-redland-tui.py redland-1.1.0.tar.gz --max-concurrent 4 user@host1 user@host2
```

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

## Configuration

All settings are centralized in `config.py` and include:

- Build timeouts and retries
- Terminal layout parameters
- SSH connection settings
- Output buffering limits
- Color and formatting options

## Testing

Run the comprehensive test suite:

```bash
cd build-tui
python3 -m pytest test_*.py -v
```

All 252 tests should pass, covering unit tests, integration tests, edge cases, and configuration flexibility.

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

## Key Features

- **Adaptive Layout**: Automatically adjusts to terminal size
- **Real-time Updates**: Live status and progress monitoring
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance**: Efficient parallel execution with resource management
- **Extensibility**: Modular design for easy feature additions

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
├── test_*.py                     # Comprehensive test suite
└── requirements.txt              # Python dependencies
```

## Contributing

The codebase follows clean architecture principles with comprehensive test coverage, clear separation of concerns, well-documented APIs, and consistent coding standards. Each module contains its own documentation in docstrings. 