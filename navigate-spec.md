# Build TUI Navigation Enhancement Specification

## Overview

This document outlines the design for enhanced navigation capabilities in the Build TUI application, allowing users to interactively explore build logs, switch between host windows, and manage the display of completed builds.

## Current State Analysis

### Existing Navigation Features

- Basic up/down navigation between visible hosts
- Help screen toggle (h key)
- Quit functionality (q key)
- Automatic host visibility management (completed hosts auto-hide after timeout)

### Current Limitations

- No log scrolling within host sections
- No full-screen mode for focused hosts
- No persistent access to completed builds
- Limited keyboard shortcuts
- No host selection menu

## Proposed Navigation System

### 1. Enhanced Input Handling

#### New Keyboard Shortcuts

```
Navigation:
  UP/DOWN     - Navigate between visible hosts
  LEFT/RIGHT  - Navigate between all hosts (including completed)
  ENTER       - Toggle full-screen mode for focused host
  ESC         - Exit full-screen mode / Cancel current action
  
Log Scrolling (when host is focused):
  PAGE_UP     - Scroll log up by one page
  PAGE_DOWN   - Scroll log down by one page
  HOME        - Jump to beginning of log
  END         - Jump to end of log (latest output)
  UP/DOWN     - Scroll log line by line (when in scroll mode)
  
Host Management:
  TAB         - Open host selection menu
  SPACE       - Toggle pause/resume for focused host
  'c'         - Clear log for focused host
  'r'         - Restart build for focused host (if failed)
  
General:
  'h'         - Show/hide help screen
  'q'         - Quit application
  '?'         - Quick help overlay
  'm'         - Toggle minimized view for completed hosts
```

### 2. Host Focus Management

#### Focus States

1. **Normal Focus**: Host section highlighted with border color change
2. **Full-Screen Focus**: Host takes entire terminal, other hosts hidden
3. **Scroll Mode**: Within full-screen mode, user can scroll through log history

#### Focus Indicators

- **Visual**: Border color changes (bright cyan for focused, dim for others)
- **Status Line**: Show focused host info in header/footer
- **Cursor**: Position cursor at focused host section

### 3. Log Scrolling System

#### Scroll State Management

```python
class ScrollState:
    def __init__(self):
        self.scroll_offset = 0          # Lines scrolled up from bottom
        self.max_scroll_offset = 0      # Maximum possible scroll offset
        self.scroll_mode = False        # Whether currently in scroll mode
        self.scroll_speed = 1           # Lines per scroll action
```

#### Scroll Behavior

- **Auto-scroll**: When not in scroll mode, always show latest output
- **Manual scroll**: When in scroll mode, maintain scroll position
- **Scroll limits**: Prevent scrolling beyond available log content
- **Scroll indicators**: Show scroll position (e.g., "Line 45 of 200")

### 4. Full-Screen Mode

#### Implementation

- **Enter**: Switch focused host to full-screen
- **Exit**: ESC key or ENTER again to return to normal view
- **Layout**: Full-screen host uses entire terminal minus minimal header/footer
- **Other hosts**: Continue running in background, not visible

#### Full-Screen Features

- **Enhanced log display**: More lines visible, better formatting
- **Scroll controls**: Full scrolling capabilities
- **Status overlay**: Minimal status info in corner
- **Quick exit**: ESC key always exits full-screen

### 5. Host Selection Menu

#### Menu Design

```
┌─ Host Selection ──────────────────────────────────────┐
│ [1] dajobe@berlin     [SUCCESS] Completed 2m ago      │
│ [2] dajobe@fedora     [BUILDING] Configure step       │
│ [3] dajobe@gentoo     [FAILED] Build error            │
│ [4] dajobe@sid        [QUEUED] Waiting to start       │
│ [5] dajobe@stable     [SUCCESS] Completed 5m ago      │
│                                                       │
│ Navigation: UP/DOWN, ENTER to select, ESC to cancel   │
└───────────────────────────────────────────────────────┘
```

#### Menu Features

- **Numbered selection**: Quick access with number keys
- **Status indicators**: Show current status for each host
- **Completion times**: Show when completed builds finished
- **Filtering**: Option to filter by status (all, active, completed, failed)
- **Search**: Type to filter hosts by name

### 6. Completed Build Management

#### Minimized State

- **Auto-minimize**: Completed builds automatically minimize after timeout
- **Minimized indicator**: Show small status bar instead of full section
- **Access methods**:
  - Host selection menu
  - LEFT/RIGHT navigation
  - 'm' key to toggle minimized view

#### Minimized Display

```
┌─ Completed Builds ────────────────────────────────────┐
│ dajobe@berlin [SUCCESS] ✓ dajobe@fedora [BUILDING] 🔨 │
│ dajobe@gentoo [FAILED] ✗ dajobe@stable [SUCCESS] ✓   │
└───────────────────────────────────────────────────────┘
```

### 7. Enhanced Layout Management

#### Dynamic Layout Adjustments

- **Normal mode**: Multiple hosts visible, adaptive sizing
- **Full-screen mode**: Single host uses all available space
- **Menu mode**: Overlay menu with semi-transparent background
- **Minimized mode**: Compact status bars for completed builds

#### Layout Transitions

- **Smooth transitions**: Animate layout changes when possible
- **State preservation**: Remember scroll positions and focus states
- **Responsive design**: Adapt to terminal size changes

### 8. Implementation Architecture

#### New Classes

```python
class NavigationManager:
    """Manages focus, scrolling, and navigation state"""
    
class ScrollManager:
    """Handles log scrolling for individual hosts"""
    
class MenuManager:
    """Manages host selection and other menus"""
    
class FocusManager:
    """Manages host focus and full-screen states"""
```

#### Enhanced Existing Classes

```python
class InputHandler:
    """Enhanced with new keyboard shortcuts and menu handling"""
    
class HostSection:
    """Enhanced with scroll state and focus indicators"""
    
class LayoutManager:
    """Enhanced with full-screen and minimized layouts"""
```

### 9. User Experience Considerations

#### Visual Feedback

- **Focus indicators**: Clear visual indication of focused host
- **Scroll indicators**: Show scroll position and available content
- **Status overlays**: Minimal status info in full-screen mode
- **Transition animations**: Smooth visual transitions

#### Accessibility

- **Keyboard navigation**: All features accessible via keyboard
- **Clear indicators**: Visual and textual status information
- **Consistent shortcuts**: Logical and memorable key mappings
- **Help system**: Comprehensive help with examples

#### Performance

- **Efficient rendering**: Only redraw changed sections
- **Scroll optimization**: Virtual scrolling for large logs
- **Memory management**: Limit log buffer sizes
- **Background processing**: Non-blocking UI updates

### 10. Configuration Options

#### User Preferences

```python
# Navigation settings
NAVIGATION_SCROLL_SPEED = 1
NAVIGATION_AUTO_MINIMIZE_TIMEOUT = 30
NAVIGATION_FULL_SCREEN_HEADER_HEIGHT = 2
NAVIGATION_MENU_OVERLAY_OPACITY = 0.8

# Visual settings
NAVIGATION_FOCUS_BORDER_COLOR = "BRIGHT_CYAN"
NAVIGATION_SCROLL_INDICATOR_COLOR = "YELLOW"
NAVIGATION_MENU_BORDER_COLOR = "WHITE"
```

### 11. Testing Strategy

#### Unit Tests

- Navigation state management
- Scroll position calculations
- Menu selection logic
- Focus state transitions

#### Integration Tests

- Full navigation workflow
- Layout transitions
- Input handling scenarios
- Performance under load

#### User Acceptance Tests

- Real-world usage scenarios
- Keyboard shortcut memorability
- Visual clarity and feedback
- Performance with large logs

### 12. Implementation Order

#### Phase 1: Foundation (Week 1-2)

##### 1.1 Enhanced Input Handler

- Extend `InputHandler` with new keyboard shortcuts
- Add LEFT/RIGHT navigation between all hosts
- Implement ENTER/ESC for full-screen toggle
- Add TAB for menu activation
- **Why first**: Enables all other navigation features

##### 1.2 Focus Management System

- Create `FocusManager` class
- Add focus state tracking (normal, full-screen, scroll)
- Implement visual focus indicators (border color changes)
- Add focus status display in header/footer
- **Why second**: Required for all navigation features

##### 1.3 Scroll State Management

- Create `ScrollManager` class
- Add scroll state to `HostSection`
- Implement basic scroll position tracking
- Add scroll indicators (line numbers)
- **Why third**: Foundation for log exploration

#### Phase 2: Core Navigation (Week 3-4)

##### 2.1 Enhanced HostSection

- Integrate scroll state with existing output buffer
- Add scroll-aware rendering
- Implement PAGE_UP/PAGE_DOWN scrolling
- Add HOME/END jump functionality
- **Why first**: Enables log exploration within existing UI

##### 2.2 Layout Manager Enhancements

- Add full-screen layout calculation
- Implement minimized layout for completed hosts
- Add layout transition support
- Preserve layout state during transitions
- **Why second**: Required for full-screen and minimized modes

##### 2.3 Basic Full-Screen Mode

- Implement ENTER to toggle full-screen
- Add ESC to exit full-screen
- Show focused host in full terminal
- Hide other hosts during full-screen
- **Why third**: Major UX improvement, builds on layout enhancements

#### Phase 3: Advanced Features (Week 5-6)

##### 3.1 Host Selection Menu

- Create `MenuManager` class
- Implement TAB-activated host menu
- Add numbered selection (1-9 keys)
- Show host status and completion times
- **Why first**: Provides access to all hosts including completed ones

##### 3.2 Completed Build Management

- Implement auto-minimize for completed hosts
- Add minimized display mode
- Create persistent access to completed builds
- Add 'm' key toggle for minimized view
- **Why second**: Solves the "lost completed builds" problem

##### 3.3 Enhanced Navigation

- Implement LEFT/RIGHT navigation between all hosts
- Add smooth focus transitions
- Improve visual feedback
- Add keyboard shortcut help
- **Why third**: Polishes the navigation experience

#### Phase 4: Polish & Optimization (Week 7-8)

##### 4.1 Performance Optimization

- Implement virtual scrolling for large logs
- Optimize rendering for frequent updates
- Add memory management for log buffers
- Profile and optimize CPU usage
- **Why first**: Ensures good performance with large builds

##### 4.2 User Experience Refinements

- Add smooth transitions and animations
- Implement comprehensive help system
- Add configuration options
- Polish visual indicators and feedback
- **Why second**: Improves overall user experience

##### 4.3 Testing & Documentation

- Add comprehensive unit tests for new features
- Create integration tests for navigation workflows
- Update documentation and help text
- Add user acceptance testing
- **Why third**: Ensures reliability and usability

#### Implementation Strategy

##### Incremental Development

1. **Each phase builds on the previous** - no feature dependencies across phases
2. **Maintain backward compatibility** - existing functionality always works
3. **Test each component thoroughly** - don't move to next until current is solid
4. **User feedback integration** - test with real builds after each phase

##### Risk Mitigation

- **Phase 1**: Low risk, foundation work
- **Phase 2**: Medium risk, UI changes
- **Phase 3**: Medium risk, new features
- **Phase 4**: Low risk, optimization and polish

##### Success Criteria

- **Phase 1**: All new keyboard shortcuts work, focus system functional
- **Phase 2**: Full-screen mode works, log scrolling functional
- **Phase 3**: Menu system works, completed builds accessible
- **Phase 4**: Performance optimized, user experience polished

This order ensures that:

1. **Each phase delivers usable functionality**
2. **Dependencies are properly managed**
3. **Risk is minimized**
4. **User value is delivered incrementally**
5. **Testing can be comprehensive at each stage**

### 13. Success Metrics

#### Usability

- Time to navigate between hosts
- Ease of log exploration
- User satisfaction with interface

#### Performance

- Responsiveness of navigation
- Memory usage with large logs
- CPU usage during scrolling

#### Reliability

- No navigation state corruption
- Proper cleanup of resources
- Graceful handling of edge cases

## New Features Specification

### 14. Auto-Exit After Build Completion

#### Overview

The application will automatically exit 5 minutes after the last build finishes, providing a hands-free experience for automated build monitoring.

#### Implementation Details

##### Auto-Exit Timer Management

```python
class AutoExitManager:
    """Manages automatic exit after build completion"""
    
    def __init__(self, exit_delay_seconds=300):  # 5 minutes default
        self.exit_delay_seconds = exit_delay_seconds
        self.last_build_completion_time = None
        self.exit_timer = None
        self.is_exiting = False
    
    def on_build_completed(self, host_name, success):
        """Called when any build completes (success or failure)"""
        self.last_build_completion_time = time.time()
        self._schedule_exit()
    
    def _schedule_exit(self):
        """Schedule exit after configured delay"""
        if self.exit_timer:
            self.exit_timer.cancel()
        
        self.exit_timer = threading.Timer(
            self.exit_delay_seconds, 
            self._perform_exit
        )
        self.exit_timer.start()
    
    def _perform_exit(self):
        """Perform the actual exit"""
        self.is_exiting = True
        # Trigger exit sequence
```

##### Configuration Options

```python
# Auto-exit settings
AUTO_EXIT_DELAY_SECONDS = 300  # 5 minutes
AUTO_EXIT_ENABLED = True        # Can be disabled via config
AUTO_EXIT_SHOW_COUNTDOWN = True # Show countdown in UI
```

##### User Experience

- **Countdown display**: Show remaining time in header/footer
- **Override capability**: User can still manually exit before auto-exit
- **Configurable delay**: Adjustable via configuration file
- **Visual indication**: Clear indication that auto-exit is active

### 15. Build Summary Output

#### Overview

When the application terminates (either manually or via auto-exit), it will print a comprehensive summary of all build results to stdout, including success/failure states and total time taken.

#### Implementation Details

##### Summary Data Collection

```python
class BuildSummaryCollector:
    """Collects build results and timing data"""
    
    def __init__(self):
        self.build_start_time = time.time()
        self.host_results = {}  # host_name -> BuildResult
    
    def record_build_result(self, host_name, success, error_message=None, 
                          configure_time=None, make_time=None, total_time=None):
        """Record the result of a build for a specific host"""
        self.host_results[host_name] = BuildResult(
            host_name=host_name,
            success=success,
            error_message=error_message,
            configure_time=configure_time,
            make_time=make_time,
            total_time=total_time
        )
    
    def generate_summary(self):
        """Generate formatted summary for stdout output"""
        total_time = time.time() - self.build_start_time
        
        summary = []
        summary.append("=" * 60)
        summary.append("BUILD SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Total time: {self._format_duration(total_time)}")
        summary.append("")
        
        # Group by status
        successful = [r for r in self.host_results.values() if r.success]
        failed = [r for r in self.host_results.values() if not r.success]
        
        if successful:
            summary.append("SUCCESSFUL BUILDS:")
            for result in successful:
                summary.append(f"  ✓ {result.host_name} ({self._format_duration(result.total_time)})")
            summary.append("")
        
        if failed:
            summary.append("FAILED BUILDS:")
            for result in failed:
                summary.append(f"  ✗ {result.host_name} ({self._format_duration(result.total_time)})")
                if result.error_message:
                    summary.append(f"    Error: {result.error_message}")
            summary.append("")
        
        summary.append(f"Overall: {len(successful)}/{len(self.host_results)} builds successful")
        summary.append("=" * 60)
        
        return "\n".join(summary)
```

##### Summary Output Format

```
============================================================
BUILD SUMMARY
============================================================
Total time: 12m 34s

SUCCESSFUL BUILDS:
  ✓ dajobe@berlin (3m 12s)
  ✓ dajobe@fedora (4m 45s)
  ✓ dajobe@stable (2m 18s)

FAILED BUILDS:
  ✗ dajobe@gentoo (1m 23s)
    Error: Build failed during make step

Overall: 3/4 builds successful
============================================================
```

##### Integration Points

- **Exit sequence**: Called during both manual and auto-exit
- **Data collection**: Integrated with build monitoring system
- **Error handling**: Graceful handling of missing or incomplete data

### 16. Build Timing Cache System

#### Overview

The application will maintain a persistent cache of build timing data to provide progress estimates for ongoing builds, improving user experience with realistic time expectations.

#### Implementation Details

##### Cache File Structure

```json
{
  "version": "1.0",
  "cache_retention_days": 1,
  "hosts": {
    "dajobe@berlin": {
      "last_updated": 1703123456,
      "total_builds": 15,
      "average_times": {
        "configure": 45.2,
        "make": 187.3,
        "total": 232.5
      },
      "recent_builds": [
        {
          "timestamp": 1703123456,
          "configure_time": 42.1,
          "make_time": 185.2,
          "total_time": 227.3,
          "success": true
        }
      ]
    }
  }
}
```

##### Cache Management Class

```python
class BuildTimingCache:
    """Manages persistent build timing data"""
    
    def __init__(self, cache_file_path="~/.config/build-tui.json", 
                 retention_days=1):
        self.cache_file_path = os.path.expanduser(cache_file_path)
        self.retention_days = retention_days
        self.cache_data = self._load_cache()
        self._cleanup_old_data()
    
    def _load_cache(self):
        """Load cache from file, create if doesn't exist"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r') as f:
                    data = json.load(f)
                    # Validate version and structure
                    if data.get('version') == '1.0':
                        return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}")
        
        # Return default structure
        return {
            "version": "1.0",
            "cache_retention_days": self.retention_days,
            "hosts": {}
        }
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            with open(self.cache_file_path, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        
        for host_name in list(self.cache_data['hosts'].keys()):
            host_data = self.cache_data['hosts'][host_name]
            if host_data['last_updated'] < cutoff_time:
                del self.cache_data['hosts'][host_name]
        
        self._save_cache()
    
    def record_build_timing(self, host_name, configure_time, make_time, 
                          total_time, success):
        """Record timing data for a completed build"""
        if host_name not in self.cache_data['hosts']:
            self.cache_data['hosts'][host_name] = {
                "last_updated": time.time(),
                "total_builds": 0,
                "average_times": {"configure": 0, "make": 0, "total": 0},
                "recent_builds": []
            }
        
        host_data = self.cache_data['hosts'][host_name]
        host_data['last_updated'] = time.time()
        host_data['total_builds'] += 1
        
        # Update averages
        current_avg = host_data['average_times']
        total_builds = host_data['total_builds']
        
        current_avg['configure'] = (
            (current_avg['configure'] * (total_builds - 1) + configure_time) / total_builds
        )
        current_avg['make'] = (
            (current_avg['make'] * (total_builds - 1) + make_time) / total_builds
        )
        current_avg['total'] = (
            (current_avg['total'] * (total_builds - 1) + total_time) / total_builds
        )
        
        # Add to recent builds (keep last 10)
        recent_build = {
            "timestamp": time.time(),
            "configure_time": configure_time,
            "make_time": make_time,
            "total_time": total_time,
            "success": success
        }
        
        host_data['recent_builds'].append(recent_build)
        if len(host_data['recent_builds']) > 10:
            host_data['recent_builds'] = host_data['recent_builds'][-10:]
        
        self._save_cache()
    
    def get_progress_estimate(self, host_name, current_step, elapsed_time):
        """Get progress estimate for ongoing build"""
        if host_name not in self.cache_data['hosts']:
            return None
        
        host_data = self.cache_data['hosts'][host_name]
        avg_times = host_data['average_times']
        
        if current_step == "configure":
            if avg_times['configure'] > 0:
                progress = min(100, (elapsed_time / avg_times['configure']) * 100)
                return f"{progress:.1f}%"
        elif current_step == "make":
            if avg_times['total'] > 0:
                # Include configure time in total estimate
                total_elapsed = elapsed_time + avg_times['configure']
                progress = min(100, (total_elapsed / avg_times['total']) * 100)
                return f"{progress:.1f}%"
        
        return None
```

##### Progress Display Integration

```python
class ProgressDisplayManager:
    """Manages progress display for ongoing builds"""
    
    def __init__(self, timing_cache):
        self.timing_cache = timing_cache
        self.build_start_times = {}  # host_name -> start_time
    
    def start_build_tracking(self, host_name):
        """Start tracking build time for a host"""
        self.build_start_times[host_name] = time.time()
    
    def update_progress_display(self, host_name, current_step):
        """Update progress display for a host"""
        if host_name not in self.build_start_times:
            return None
        
        elapsed_time = time.time() - self.build_start_times[host_name]
        progress = self.timing_cache.get_progress_estimate(
            host_name, current_step, elapsed_time
        )
        
        if progress:
            return f"Progress: {progress}"
        return None
    
    def complete_build_tracking(self, host_name, configure_time, make_time, 
                              total_time, success):
        """Complete tracking and record timing data"""
        if host_name in self.build_start_times:
            del self.build_start_times[host_name]
        
        self.timing_cache.record_build_timing(
            host_name, configure_time, make_time, total_time, success
        )
```

##### Configuration Options

```python
# Timing cache settings
TIMING_CACHE_FILE = "~/.config/build-tui.json"
TIMING_CACHE_RETENTION_DAYS = 1
TIMING_CACHE_ENABLED = True
TIMING_CACHE_SHOW_PROGRESS = True

# Command line options
# --cache-file PATH          # Custom cache file location
# --cache-retention DAYS     # Custom retention period
# --no-cache                # Disable timing cache
# --no-progress             # Disable progress display
```

##### User Experience

- **Progress indicators**: Show percentage completion based on historical data
- **Time estimates**: Display expected completion times
- **Fallback behavior**: Gracefully handle missing historical data
- **Configuration**: Easy customization of cache behavior

### 17. Integration with Existing Architecture

#### New Class Relationships

```
Application
├── AutoExitManager          # Manages auto-exit timing
├── BuildSummaryCollector    # Collects build results
├── BuildTimingCache        # Manages timing data
├── ProgressDisplayManager   # Shows progress estimates
└── Existing classes...
```

#### Data Flow

1. **Build start**: `ProgressDisplayManager.start_build_tracking()`
2. **Build progress**: `ProgressDisplayManager.update_progress_display()`
3. **Build completion**:
   - `BuildSummaryCollector.record_build_result()`
   - `ProgressDisplayManager.complete_build_tracking()`
   - `AutoExitManager.on_build_completed()`
4. **Application exit**: `BuildSummaryCollector.generate_summary()`

#### Configuration Integration

- **Environment variables**: Override default settings
- **Command line options**: Runtime configuration
- **Config file**: Persistent user preferences
- **Fallback values**: Sensible defaults for all options

### 18. Implementation Priority for New Features

#### Phase 5: Auto-Exit and Summary (Week 9)

##### 5.1 Auto-Exit System

- Implement `AutoExitManager` class
- Integrate with build completion events
- Add countdown display in UI
- **Why first**: Provides hands-free operation capability

##### 5.2 Build Summary System

- Implement `BuildSummaryCollector` class
- Integrate with exit sequence
- Add stdout output formatting
- **Why second**: Essential for understanding build results

#### Phase 6: Timing Cache and Progress (Week 10)

##### 6.1 Timing Cache Foundation

- Implement `BuildTimingCache` class
- Add cache file management
- Implement data cleanup and retention
- **Why first**: Foundation for progress estimates

##### 6.2 Progress Display System

- Implement `ProgressDisplayManager` class
- Integrate with build monitoring
- Add progress percentage display
- **Why second**: Provides user value through progress estimates

#### Success Criteria for New Features

- **Phase 5**: Auto-exit works reliably, summary output is comprehensive
- **Phase 6**: Progress estimates are accurate, cache management is robust

## Conclusion

This enhanced navigation system will transform the Build TUI from a passive monitoring tool into an interactive build exploration platform. The design prioritizes usability, performance, and maintainability while building upon the existing solid architecture.

The implementation will be incremental, allowing for testing and refinement at each phase while maintaining backward compatibility with existing functionality.

The new features (auto-exit, build summary, and timing cache) provide additional value for automated build monitoring and user experience improvements, making the tool more suitable for both interactive and hands-free operation scenarios.
