# Redland Forge - Distributed Build Orchestrator

A distributed build orchestrator for monitoring and managing parallel
builds across multiple remote hosts.

This was created as part of the [Redland Project](https://librdf.org/)
for internal build testing.

## Overview

Redland Forge is a distributed build orchestrator that provides
comprehensive build management across multiple remote hosts. It
offers real-time monitoring through a clean terminal interface, and
intelligent build coordination with timing analytics and progress
estimation.

## Features

- **Distributed Orchestration**: Coordinate builds across multiple
  remote hosts with intelligent resource management.
- **Real-time Monitoring**: Live terminal interface with build
  progress tracking and status visualization.
- **Parallel Execution**: Concurrent builds with configurable
  concurrency limits.
- **Build Intelligence**: Automatic step detection, timing analytics,
  and progress estimation.
- **SSH Integration**: Secure remote execution with connection
  pooling and error recovery.
- **Output Management**: Intelligent buffering and display of build
  logs across hosts.
- **Auto-Exit & Summaries**: Automatic completion handling with
  comprehensive result reporting.
- **Timing Cache**: Persistent build performance data for accurate
  progress predictions.

## Quick Start

```bash
# Basic usage
cd redland-forge
./redland-forge redland-1.1.0.tar.gz user@host1 user@host2

# Or using Python directly
./redland-forge.py redland-1.1.0.tar.gz user@host1 user@host2

# With host file
./redland-forge redland-1.1.0.tar.gz -f hosts.txt

# Limit concurrent builds
./redland-forge redland-1.1.0.tar.gz --max-concurrent 4 user@host1 user@host2

# Auto-exit after 10 minutes (default: 5 minutes)
./redland-forge redland-1.1.0.tar.gz --auto-exit-delay 600 user@host1 user@host2

# Disable auto-exit
./redland-forge redland-1.1.0.tar.gz --no-auto-exit user@host1 user@host2
```

## Documentation

- **[Architecture Guide](architecture.md)**: Detailed system
  architecture and design.
- **[Testing Guide](testing.md)**: Testing strategies and infrastructure.
- **[TODO.md](TODO.md)** for current development priorities.

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
--cache-file PATH            # Custom cache file location (default: ~/.config/redland-forge/timing-cache.json)
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

This system provides intelligent progress estimation by storing
historical build timing data. This enables accurate progress
estimates for ongoing builds based on previous performance data from
the same hosts.

### Key Features

- **Progress Estimation**: Real-time progress estimates based on
  historical data.
- **Host-Specific Data**: Separate timing statistics for each remote
  host.
- **Global Build Retention**: Configurable limit on the number of
  recent builds to keep.
- **Time-Based Cleanup**: Automatic removal of data older than the
  retention period.
- **Demo Host Management**: Special handling for temporary/testing
  hosts with shorter retention.

### Cache Configuration

The cache system supports both count-based and time-based retention:

- **Count-Based**: Keep only the last N builds globally (default: 5)
- **Time-Based**: Remove data older than X days (default: 30 days)
- **Demo Hosts**: Automatically cleaned after 1 hour

### Cache Usage Examples

```bash
# Default cache settings (5 builds, 30 days retention)
./redland-forge.py redland-1.1.0.tar.gz user@host1

# Keep more build history
./redland-forge.py redland-1.1.0.tar.gz --cache-keep-builds 10 user@host1

# Longer retention period
./redland-forge.py redland-1.1.0.tar.gz --cache-retention 90 user@host1

# Custom cache location
./redland-forge.py redland-1.1.0.tar.gz --cache-file ~/.my-build-cache.json user@host1

# Disable caching entirely
./redland-forge.py redland-1.1.0.tar.gz --no-cache user@host1
```

### Build Summary Output

When the application exits (either manually or via auto-exit), it prints a comprehensive summary of all build results to stdout.

Summary Includes:

- **Total build time**: Overall duration from start to completion
- **Success/failure counts**: Clear breakdown of build outcomes
- **Per-host timing**: Individual build durations for each host
- **Error details**: Specific error messages for failed builds
- **Success rates**: Percentage and ratio of successful builds

Example Output:

```diagram
============================================================
BUILD SUMMARY
============================================================
Total time: 12m 34s

SUCCESSFUL BUILDS:
  ✓ dajobe@foo (3m 12s)
  ✓ dajobe@bar (4m 45s)

FAILED BUILDS:
  ✗ dajobe@baz (1m 23s)
    Error: Build failed during make step

Overall: 2/3 builds successful (66.7%)
============================================================
```

## Configuration

All settings are centralized in `config.py`. For detailed
configuration options including build timeouts, SSH settings, UI
preferences, and advanced features, see the
**[Architecture Guide](architecture.md)**.

## Testing

For detailed information about the testing architecture, strategies,
and infrastructure, see the **[Testing Guide](testing.md)**.

## Dependencies

- Python 3.6+
- blessed (terminal UI)
- paramiko (SSH connections)

## Try It Now (No Installation Required)

For the quickest way to try Redland Forge without installation, use
`uvx` (requires [uv](https://github.com/astral-sh/uv)):

```bash
# Install uv first (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run Redland Forge directly from GitHub
uvx git+https://github.com/dajobe/redland-forge.git --help

# Or run with your own local copy
uvx --from . redland-forge --help
```

For development with uv:

```bash
# Create a virtual environment and install dependencies
uv venv
uv pip install -e .

# Run the application
uv run redland-forge --help

# Or run with development dependencies
uv pip install -e ".[dev]"
uv run redland-forge --help
```

## Traditional Installation

Install with:

```bash
cd redland-forge

# Install the package
pip install .

# Or for development (recommended)
pip install -e .
```

For development dependencies:

```bash
cd redland-forge

# Install with development dependencies
pip install -e ".[dev]"

# Or install development tools separately
pip install -e . pytest black mypy flake8
```

## Usage Examples

### Basic Build

```bash
cd redland-forge
./redland-forge.py redland-1.1.0.tar.gz user@build-server1 user@build-server2
```

### Large Scale Build

```bash
cd redland-forge
./redland-forge.py redland-1.1.0.tar.gz -f production-hosts.txt --max-concurrent 8
```

### Debug Mode

```bash
cd redland-forge
./redland-forge.py redland-1.1.0.tar.gz --debug user@host1 user@host2
```

### Automated Build Monitoring

```bash
cd redland-forge
# Auto-exit after 10 minutes with comprehensive logging
./redland-forge.py redland-1.1.0.tar.gz \
  --auto-exit-delay 600 \
  --debug \
  -f production-hosts.txt \
  --max-concurrent 6
```

Key Features:

- **Adaptive Layout**: Automatically adjusts to terminal size
- **Real-time Updates**: Live status and progress monitoring
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance**: Efficient parallel execution with resource management
- **Extensibility**: Modular design for easy feature additions
- **Auto-Exit**: Hands-free operation with configurable timing
- **Build Summaries**: Comprehensive result reporting and analysis

## History

Where this all came from, thanks for the 20 years of service:

- `build-redland`: the shell script
- `build-redland-on`: the Perl script that called the shell script. Note the RCS / CVS Id in the source.  If you know what these are, I salute you.
