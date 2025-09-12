# Redland Forge Overview

Redland Forge is a distributed build orchestrator for managing
parallel builds across multiple remote hosts. It orchestrates
autoconf-based builds (configure, make, make check, make install)
with real-time status updates, progress tracking and comprehensive
build management.

## Architecture

The project uses a modular architecture with clear separation of concerns:

### Main Entry Points

- **`redland-forge.py`**: Main CLI entry point with argument parsing
- **`build-agent.py`**: Remote build execution script deployed to target hosts

### Core Application (`src/redland_forge/`)

- **`app.py`**: Main `BuildTUI` class - orchestrates the entire application and main event loop
- **`config.py`**: Centralized configuration management with all application settings
- **`parallel_ssh_manager.py`**: Manages concurrent SSH connections and build execution
- **`ssh_connection.py`**: Low-level SSH connection management and file transfers

### UI System

- **`layout_manager.py`**: Terminal layout calculation and host positioning
- **`renderer.py`**: Complete UI rendering and display management
- **`host_section.py`**: Individual host display and state management
- **`input_handler.py`**: Keyboard input processing and navigation

### Data Management

- **`statistics_manager.py`**: Build progress calculation and tracking
- **`build_timing_cache.py`**: Persistent storage of historical build timing data
- **`output_buffer.py`**: Log output buffering with configurable size limits
- **`build_step_detector.py`**: Automatic detection of build phases from output patterns

### Utility Components  

- **`text_formatter.py`**: Text formatting and duration display utilities
- **`color_manager.py`**: ANSI color scheme management
- **`exception_handler.py`**: Centralized exception management
- **`auto_exit_manager.py`**: Auto-exit timing and countdown functionality
- **`build_summary_collector.py`**: Build result collection and summary reporting

## Development Environment

### Setup

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Using uv (recommended for development)
uv venv
uv pip install -e ".[dev]"

# Build package
python -m build
```

### Key Commands

#### Running Tests

```bash
# Run all tests using pytest
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_app.py -v

# Run tests matching pattern
python -m pytest tests/ -k "ssh" -v

# Run with debug output
python -m pytest tests/ -v -s
```

#### Code Quality

```bash
# Format code with black
black src/ tests/ *.py

# Type checking with mypy
mypy src/

# Linting with flake8
flake8 src/ tests/ *.py
```

#### Running the Application

```bash
# Basic usage
./redland-forge.py redland-1.1.0.tar.gz user@host1 user@host2

# With host file
./redland-forge.py redland-1.1.0.tar.gz -f hosts.txt

# Limit concurrent builds
./redland-forge.py redland-1.1.0.tar.gz --max-concurrent 4 user@host1 user@host2

# Debug mode with auto-exit
./redland-forge.py redland-1.1.0.tar.gz --debug --auto-exit-delay 300 user@host1

# Run using uv
uv run redland-forge --help
```

## Code Style Guidelines

- Follow PEP 8 with 88-character line length (Black formatting)
- Use type hints for all function parameters and return values
- Comprehensive docstrings for all modules, classes, and public functions
- Prefer composition over inheritance
- Use dataclasses for structured data where appropriate

## Architecture Guidelines

### Module Structure

- Source code is in `src/redland_forge/` package
- Tests are in `tests/` directory following `test_*.py` pattern  
- Entry scripts are in project root (`redland-forge.py`, `build-agent.py`)
- Documentation in markdown files (`README.md`, `architecture.md`, `testing.md`)

### Key Components

- `BuildTUI` (app.py) - Main orchestrator and event loop
- `ParallelSSHManager` - Concurrent SSH connection management  
- `LayoutManager` - Terminal layout and positioning
- `Renderer` - Complete UI rendering system
- `HostSection` - Individual host display logic

### Design Patterns Used

- Observer pattern for build state changes
- Strategy pattern for different layout modes
- Factory pattern for connection management
- Template method for build workflows

## Testing Requirements

### Testing Strategy

- Maintain 400+ unit test coverage
- Mock-based testing for external dependencies (SSH, filesystem)
- Component isolation with mocked dependencies
- Integration tests for component interaction
- Error scenario and edge case coverage
- Test files mirror source structure

### Key Technologies

- **Python 3.6+** with modern features (type hints, f-strings, dataclasses)
- **blessed>=1.20.0** for terminal UI and cross-platform input handling
- **paramiko>=3.3.1** for SSH/SFTP connections
- **pytest** for testing with 408+ unit tests covering all major components

## Configuration

All settings are centralized in `config.py` including:

- Build timeouts and SSH connection parameters
- UI preferences and color schemes  
- Cache settings and retention policies
- Debug and logging options

## Build System Integration

- Supports standard autoconf/automake workflow (configure, make, make check, make install)
- Automatic detection of build phases from output patterns
- Progress estimation based on historical timing data
- Comprehensive error handling and recovery mechanisms

## Security Considerations

- Never log SSH credentials or sensitive connection details
- Validate all user input for host specifications
- Use paramiko for secure SSH connections with proper error handling
- Sanitize output before display to prevent terminal injection
- Handle connection timeouts and authentication failures gracefully

## Common Development Tasks

### Adding New Components

1. Create module in `src/redland_forge/`
2. Add corresponding test file in `tests/`
3. Update imports in `__init__.py` if needed
4. Follow existing patterns for error handling and configuration

### Modifying UI Elements

1. UI changes typically involve `renderer.py`, `layout_manager.py`, or `host_section.py`
2. Test with different terminal sizes
3. Verify color schemes work in different terminal environments
4. Update input handling if adding interactive elements

### SSH/Build Logic Changes

1. Changes typically involve `parallel_ssh_manager.py` or `ssh_connection.py`
2. Mock SSH connections thoroughly in tests
3. Test connection failure scenarios
4. Verify build step detection works with changes

### Configuration Updates

1. Add new settings to `config.py`
2. Update argument parsing in `redland-forge.py`
3. Add corresponding tests
4. Update documentation

## Dependencies

### Core Dependencies

- `blessed>=1.20.0` - Terminal UI library
- `paramiko>=3.3.1` - SSH/SFTP client

### Development Dependencies

- `pytest>=7.0.0` - Testing framework
- `black>=22.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking
- `flake8>=5.0.0` - Linting

## Important Implementation Details

### Concurrency Model

- SSH connections limited by `--max-concurrent` setting
- Threading used for parallel build execution
- Non-blocking input handling prevents UI freezing
- Shared data structures protected by locks

### Memory Management

- Output buffers have configurable size limits
- Cache data periodically cleaned up
- Large log files truncated for display
- Host sections created only for visible hosts

### Performance Considerations

- Output buffers have configurable size limits to prevent memory issues
- SSH connections limited by `--max-concurrent` to avoid overwhelming systems
- Terminal rendering optimized to only update changed sections
- Historical timing data cleaned up automatically

## Error Handling

The application uses a four-tier exception classification:

- **Critical**: Application-terminating errors
- **High**: Serious functionality issues  
- **Medium**: Operational problems
- **Low**: Warnings and recoverable errors

All errors should be handled gracefully with user-friendly messages:

- SSH connection retry logic for transient failures
- Graceful degradation for terminal size issues
- Automatic cleanup on application exit

## Debugging

```bash
# Enable debug mode
./redland-forge.py --debug [other args]

# Check debug.log file for detailed logging
tail -f debug.log
```
