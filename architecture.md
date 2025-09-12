# Redland Forge Architecture

## Overview

Redland Forge is a distributed build orchestrator for managing build
processes over tarballs constructed with autoconf suite (configure,
make, make check, make install steps). It coordinates builds across
multiple remote hosts in parallel, providing real-time monitoring,
progress tracking, and comprehensive build management capabilities.

**Note**: Testing architecture and practices are documented
separately in `testing.md`.

## Project Structure

```diagram
redland-forge/
├── 📄 Documentation
│   ├── README.md                 # Quick start and usage guide
│   ├── architecture.md           # System architecture and design
│   ├── testing.md                # Testing strategies and infrastructure
│   └── TODO.md                   # Future enhancements roadmap
│
├── 🚀 Application Entry
│   ├── redland-forge.py          # Main application entry point
│   └── build-agent.py            # Remote build execution script
│
├── 📦 Source Code (src/)
│   ├── app.py                    # Main BuildTUI class and orchestration
│   ├── config.py                 # Centralized configuration management
│   ├── layout_manager.py         # Terminal layout and positioning
│   ├── host_section.py           # Individual host display logic
│   ├── statistics_manager.py     # Build statistics and progress tracking
│   ├── renderer.py               # UI rendering and display management
│   ├── input_handler.py          # Keyboard input processing and navigation
│   ├── parallel_ssh_manager.py   # Parallel SSH connection management
│   ├── ssh_connection.py         # SSH connection and file transfer
│   ├── build_step_detector.py    # Build phase detection
│   ├── output_buffer.py          # Output buffering and management
│   ├── text_formatter.py         # Text formatting utilities
│   ├── build_timing_cache.py     # Build timing data persistence
│   ├── auto_exit_manager.py      # Auto-exit timing and countdown
│   ├── build_summary_collector.py # Build result collection
│   ├── color_manager.py          # ANSI color scheme management
│   ├── exception_handler.py      # Centralized exception handling
│   ├── host_visibility_manager.py # Host display visibility management
│   └── progress_display_manager.py # Progress display utilities
│
├── 🧪 Tests (tests/)
│   ├── test_app.py               # Main application tests
│   ├── test_auto_exit_manager.py # Auto-exit functionality tests
│   ├── test_build_step_detector.py # Build step detection tests
│   ├── test_build_summary_collector.py # Build summary tests
│   ├── test_build_timing_cache.py # Cache functionality tests
│   ├── test_color_system.py      # Color management tests
│   ├── test_config.py            # Configuration tests
│   ├── test_host_section.py      # Host section tests
│   ├── test_host_visibility_manager.py # Host visibility tests
│   ├── test_input_handler.py     # Input handling tests
│   ├── test_layout_manager.py    # Layout management tests
│   ├── test_output_buffer.py     # Output buffer tests
│   ├── test_parallel_ssh_manager.py # SSH manager tests
│   ├── test_progress_display_manager.py # Progress display tests
│   ├── test_renderer.py          # Renderer tests
│   ├── test_ssh_connection.py    # SSH connection tests
│   ├── test_statistics_manager.py # Statistics tests
│   ├── test_text_formatter.py    # Text formatting tests
│   └── test.tar.gz               # Test data archive
│
├── ⚙️ Configuration
│   ├── pyproject.toml            # Modern Python packaging and dependencies
│   └── build-redland-on.py       # Build script
│
└── 📋 Project Files
    ├── architecture.md           # Architecture documentation
    ├── testing.md                # Testing documentation
    ├── TODO.md                   # Future enhancements
    └── build-redland-spec.md     # Build specifications
```

## Core Architecture

### Application Entry Point

- **`redland-forge.py`** - Main entry point with argument parsing
  and application orchestration.
- Thin wrapper that creates and runs the `BuildTUI` instance
- **`build-agent.py`** - Remote build execution script for target hosts

### Main Application Controller

- **`src/app.py`** - `BuildTUI` class that orchestrates the entire application
  - Manages the main event loop and application state
  - Coordinates all subsystems (SSH, layout, rendering, input)
  - Handles application lifecycle (startup, shutdown, cleanup)

## Architectural Components

### 1. SSH and Build Management

- **`src/parallel_ssh_manager.py`** - Manages parallel SSH connections
  and build execution.
  - Handles concurrent build processes across multiple hosts
  - Manages connection queue and active connections
  - Transfers build scripts and tarballs to remote hosts
  - Monitors build output in real-time

- **`src/ssh_connection.py`** - Low-level SSH connection management.
  - Establishes and maintains SSH connections
  - Handles file transfers (SCP/SFTP)
  - Executes remote commands with output capture
  - Manages connection timeouts and error handling

### 2. User Interface System

#### Layout Management

- **`src/layout_manager.py`** - Terminal layout calculation and host positioning
  - Calculates optimal host section sizes based on terminal dimensions
  - Handles different layout modes (normal, small terminal, full-screen)
  - Manages host visibility and positioning
  - Adapts to terminal resizing

#### Rendering System

- **`src/renderer.py`** - UI rendering and display management
  - Renders the complete terminal interface
  - Handles header, footer, and host sections
  - Manages color schemes and visual indicators
  - Provides different rendering modes (normal, full-screen, menu)

#### Host Display

- **`src/host_section.py`** - Individual host display and state management
  - Renders individual host status and output
  - Manages host-specific data (status, timing, output buffer)
  - Handles focus indicators and visual feedback
  - Border rendering and status display

### 3. Input and Navigation

- **`src/input_handler.py`** - Keyboard input processing and navigation
  - Handles all keyboard shortcuts and navigation
  - Supports multiple navigation modes (host, full-screen, menu, scrolling)
  - Processes special keys (arrows, function keys, etc.)
  - Manages help system and menu navigation

### 4. Data Management

#### Build Progress Tracking

- **`src/statistics_manager.py`** - Build statistics calculation and tracking
  - Calculates completion percentages and success rates
  - Tracks build timing and performance metrics
  - Manages host status aggregation
  - Provides data for UI status displays

#### Build Timing Cache

- **`src/build_timing_cache.py`** - Persistent storage of build timing data
  - Stores historical build performance data
  - Enables progress estimation for ongoing builds
  - Manages cache retention and cleanup
  - Supports per-host timing statistics

### 5. Build Processing

#### Step Detection

- **`src/build_step_detector.py`** - Automatic build phase detection
  - Identifies build phases from output patterns
  - Supports configurable step definitions
  - Handles step priority and matching logic
  - Provides build progress indicators

#### Output Management

- **`src/output_buffer.py`** - Log output buffering and management
  - Manages output line storage with size limits
  - Provides scrolling and line access methods
  - Handles output formatting and display
  - Supports efficient memory usage

### 6. Utility and Configuration

#### Text Processing

- **`src/text_formatter.py`** - Text formatting and display utilities
  - Handles duration formatting and time display
  - Manages visual length calculations
  - Provides text alignment and formatting functions

#### Color Management

- **`src/color_manager.py`** - ANSI color scheme management
  - Provides consistent color definitions
  - Handles color mode detection and switching
  - Manages status color mapping
  - Supports different color schemes

#### Configuration

- **`src/config.py`** - Centralized application configuration
  - Defines all application settings and constants
  - Manages timeouts, limits, and default values
  - Provides configuration access methods

### 7. Advanced Features

#### Auto-Exit Management

- **`src/auto_exit_manager.py`** - Automatic application exit handling
  - Manages countdown timers for build completion
  - Provides visual countdown display
  - Handles exit callbacks and cleanup
  - Supports configurable exit delays

#### Build Summary

- **`src/build_summary_collector.py`** - Build result collection and reporting
  - Collects comprehensive build results
  - Generates formatted summary reports
  - Tracks timing and success/failure statistics
  - Provides post-build analysis

#### Exception Handling

- **`src/exception_handler.py`** - Centralized exception management
  - Categorizes exceptions by severity
  - Provides user-friendly error messages
  - Handles logging and error reporting
  - Manages exception display in UI

#### Host Visibility

- **`src/host_visibility_manager.py`** - Host display visibility management
  - Controls which hosts are currently visible
  - Manages host hiding/showing based on state
  - Handles completed build visibility
  - Optimizes display for large host counts

### Core Components Overview

The application uses a modular architecture with clear separation of concerns. The following core components work together to provide comprehensive build monitoring:

#### Core Orchestration

- **BuildTUI** (`src/app.py`): Main orchestrator and UI controller
- **LayoutManager** (`src/layout_manager.py`): Terminal layout and host section positioning
- **StatisticsManager** (`src/statistics_manager.py`): Build progress and statistics calculation

#### Host Management

- **HostSection** (`src/host_section.py`): Individual host display and state management
- **SSHConnection** (`src/ssh_connection.py`): Remote connection and command execution
- **OutputBuffer** (`src/output_buffer.py`): Output buffering and line management

#### Data Processing

- **TextFormatter** (`src/text_formatter.py`): Text formatting and display utilities
- **Config** (`src/config.py`): Centralized configuration management
- **BuildStepDetector** (`src/build_step_detector.py`): Build phase detection

#### Advanced Features

- **AutoExitManager** (`src/auto_exit_manager.py`): Auto-exit timing and countdown management
- **BuildSummaryCollector** (`src/build_summary_collector.py`): Build result collection and summary generation
- **ProgressDisplayManager** (`src/progress_display_manager.py`): Progress display utilities

## Data Flow Architecture

### 1. Initialization Phase

```diagram
Command Line Args → redland-forge.py → src/app.py::BuildTUI.__init__()
                                             ↓
Host List Validation → SSH Manager Setup → Layout Calculation
                                             ↓
Terminal Setup → Component Initialization → Event Loop Start
```

### 2. Build Execution Phase

```diagram
BuildTUI.run() → SSH Manager → Parallel Build Workers
                    ↓                    ↓
Input Processing ← Renderer ← Layout Manager
                    ↓                    ↓
Host Updates ← Statistics ← Output Processing
```

### 3. Rendering Pipeline

```diagram
Terminal State → Renderer.render_full_ui() → Layout Manager
                        ↓                           ↓
Statistics Calculation ← Host Section Rendering ← Position Calculation
                        ↓                           ↓
Header/Footer Render ← Color Management ← Text Formatting
```

## Component Interaction Diagram

```diagram
┌─────────────────────────────────────────────────────────────┐
│                    Redland Forge Application                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  BuildTUI   │────│ InputHandler│────│  Renderer   │      │
│  │  (Main)     │    │             │    │             │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │SSH Manager  │────│LayoutManager│────│Statistics   │      │
│  │             │    │             │    │Manager      │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │SSH          │    │Host Section │    │Output       │      │
│  │Connection   │    │             │    │Buffer       │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │Build Timing │    │Step Detector│    │Exception    │      │
│  │Cache        │    │             │    │Handler      │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │Text         │    │Color        │    │Configuration│      │
│  │Formatter    │    │Manager      │    │            │       │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. **Observer Pattern**

- SSH Manager notifies BuildTUI of build state changes
- Layout Manager observes terminal size changes
- Statistics Manager reacts to host status updates

### 2. **Strategy Pattern**

- Different layout strategies for different terminal sizes
- Multiple rendering strategies (normal, full-screen, menu)
- Configurable input handling modes

### 3. **Factory Pattern**

- Layout Manager creates appropriate layout based on terminal size
- Host Section factory creates host displays
- Connection factory manages SSH connection types

### 4. **Command Pattern**

- Input Handler processes keyboard commands
- Build steps are command-like operations
- Menu selections trigger specific actions

### 5. **Singleton Pattern**

- Configuration management (Config class)
- Color management (ColorManager)
- Terminal instance management

### 6. **Template Method Pattern**

- Build execution follows standardized autoconf workflow
- Step detection uses pattern matching templates
- Error handling follows consistent recovery procedures

### 7. **Decorator Pattern**

- Progress indicators wrap build operations
- Color formatting decorates text output
- Exception handling decorates component interactions

## Performance Considerations

### Memory Management

- Output buffers have configurable size limits
- Host sections are created only for visible hosts
- Cache data is periodically cleaned up
- Large log files are truncated for display

### Concurrency Management

- SSH connections are limited by max_concurrent setting
- Threading is used for parallel build execution
- Locks protect shared data structures
- Non-blocking input handling prevents UI freezing

### Rendering Optimization

- Only changed sections are re-rendered
- Terminal size changes trigger layout recalculation
- Color and formatting operations are cached
- Text formatting is optimized for performance

## Error Handling Architecture

### Exception Classification

- **Critical**: Application-terminating errors
- **High**: Serious errors affecting functionality
- **Medium**: Operational issues
- **Low**: Minor warnings and recoverable errors

### Error Propagation

- SSH errors are handled at connection level
- Build errors are captured and displayed per host
- UI errors are managed by exception handler
- Configuration errors are validated at startup

### Recovery Mechanisms

- Connection retry logic for transient failures
- Graceful degradation for terminal size issues
- Fallback rendering modes for display problems
- Automatic cleanup on application exit

## Configuration Management

### Centralized Configuration

- All settings managed through `Config` class
- Runtime configuration validation
- Environment-specific overrides
- User preference persistence

### Configuration Categories

- **Build Settings**: Timeouts, concurrency limits, script paths
- **UI Settings**: Colors, layout preferences, display options
- **SSH Settings**: Connection parameters, authentication methods
- **Cache Settings**: Timing data retention, cache file locations

## Future Extensibility

### Plugin Architecture

- SSH connection plugins for different protocols
- Build system plugins for different build tools
- UI theme plugins for customization
- Output parser plugins for different log formats

### Configuration Extensions

- User-defined build steps and patterns
- Custom color schemes and themes
- Host-specific configuration overrides
- Environment-specific settings

### Monitoring Extensions

- Additional build metrics and KPIs
- External monitoring system integration
- Alert and notification systems
- Historical trend analysis
