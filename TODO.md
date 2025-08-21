# Build TUI Enhancement Roadmap

## Overview

This document outlines the design for significant enhancements to the Build TUI application, focusing on improved navigation, user experience, and build monitoring capabilities.

## Current State Analysis

### Existing Features

- Basic up/down navigation between visible hosts
- Help screen toggle (h key) - **✅ IMPLEMENTED (debug logging only)**
- Quit functionality (q key) - **✅ FULLY WORKING**
- Automatic host visibility management (completed hosts auto-hide after timeout)
- Auto-exit functionality after build completion
- Build summary output on exit
- Build timing cache system for progress estimates
- **✅ Enhanced Input Handler with Navigation Modes (Phases 1-2 COMPLETED)**

### **Input Handler Technical Debt - COMPLETED PHASES**

#### **Phase 1: Extended Key Support ✅ COMPLETED**
- **✅ LEFT/RIGHT keys**: Navigate between ALL hosts (including completed ones)
- **✅ ENTER key**: Full-screen toggle for current host
- **✅ TAB key**: Menu toggle
- **✅ ESC key**: Escape functionality
- **✅ PAGE_UP/DOWN keys**: Log scrolling support
- **✅ HOME/END keys**: Log navigation support

#### **Phase 2: Navigation Modes ✅ COMPLETED**
- **✅ NavigationMode enum**: HOST_NAVIGATION, LOG_SCROLLING, FULL_SCREEN, MENU
- **✅ Mode-specific key handling**: Keys behave differently based on current mode
- **✅ Global key support**: q (quit) and h (help) work in all modes
- **✅ Comprehensive testing**: 33 input handler tests passing

#### **Current Status: Input System 100% Functional**
- **✅ All keys detected correctly** (confirmed via debug logs)
- **✅ All callbacks working properly** (navigation, help, menu, full-screen)
- **✅ No input lag or missed keystrokes**
- **✅ Terminal mode conflicts resolved**

### **Phase 3: Full-Screen Toggle Implementation ✅ COMPLETED**
- **Status**: ✅ COMPLETED
- **Priority**: HIGH (immediate user value)
- **Dependencies**: Input system foundation complete

#### **What Was Implemented:**
- **✅ Full-screen state management**: `full_screen_mode` and `full_screen_host` in app
- **✅ Full-screen toggle**: ENTER key toggles full-screen mode for focused host
- **✅ Escape functionality**: ESC key exits full-screen mode
- **✅ Navigation mode switching**: Input handler switches between HOST_NAVIGATION and FULL_SCREEN modes
- **✅ Full-screen rendering**: Renderer shows single host with enhanced output display
- **✅ Enhanced output display**: Shows last 30 lines with scroll indicators

#### **How It Works:**
1. **Enter full-screen**: Press ENTER on any host to enter full-screen mode
2. **Full-screen display**: Shows focused host with enhanced output (last 30 lines)
3. **Exit full-screen**: Press ESC or ENTER again to return to normal view
4. **Mode switching**: Input handler automatically switches navigation modes

### **Next Phase: Phase 4 - Menu Activation System**
- **Status**: READY TO START
- **Priority**: MEDIUM (enhances navigation)
- **Dependencies**: Full-screen functionality complete

### Current Limitations

- No log scrolling within host sections
- No full-screen mode for focused hosts
- No persistent access to completed builds
- Limited keyboard shortcuts
- No host selection menu
- Navigation only works with visible hosts

## Proposed Enhancements

### 1. Enhanced Navigation System

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

#### Focus Management

- **Normal Focus**: Host section highlighted with border color change
- **Full-Screen Focus**: Host takes entire terminal, other hosts hidden
- **Scroll Mode**: Within full-screen mode, user can scroll through log history
- **Visual Indicators**: Border color changes, status line updates, cursor positioning

#### Log Scrolling System

```python
class ScrollState:
    def __init__(self):
        self.scroll_offset = 0          # Lines scrolled up from bottom
        self.max_scroll_offset = 0      # Maximum possible scroll offset
        self.scroll_mode = False        # Whether currently in scroll mode
        self.scroll_speed = 1           # Lines per scroll action
```

- **Auto-scroll**: When not in scroll mode, always show latest output
- **Manual scroll**: When in scroll mode, maintain scroll position
- **Scroll limits**: Prevent scrolling beyond available log content
- **Scroll indicators**: Show scroll position (e.g., "Line 45 of 200")

### 2. Full-Screen Mode

#### Implementation

- **Enter**: Switch focused host to full-screen
- **Exit**: ESC key or ENTER again to return to normal view
- **Layout**: Full-screen host uses entire terminal minus minimal header/footer
- **Other hosts**: Continue running in background, not visible

#### Features

- **Enhanced log display**: More lines visible, better formatting
- **Scroll controls**: Full scrolling capabilities
- **Status overlay**: Minimal status info in corner
- **Quick exit**: ESC key always exits full-screen

### 3. Host Selection Menu

#### Menu Design

```terminal
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

#### Features

- **Numbered selection**: Quick access with number keys (1-9)
- **Status indicators**: Show current status for each host
- **Completion times**: Show when completed builds finished
- **Filtering**: Option to filter by status (all, active, completed, failed)
- **Search**: Type to filter hosts by name

### 4. Completed Build Management

#### Minimized State

- **Auto-minimize**: Completed builds automatically minimize after timeout
- **Minimized indicator**: Show small status bar instead of full section
- **Access methods**:
  - Host selection menu
  - LEFT/RIGHT navigation
  - 'm' key to toggle minimized view

#### Minimized Display

```terminal
┌─ Completed Builds ────────────────────────────────────┐
│ dajobe@berlin [SUCCESS] ✓ dajobe@fedora [BUILDING] 🔨 │
│ dajobe@gentoo [FAILED]  ✗ dajobe@stable [SUCCESS] ✓   │
└───────────────────────────────────────────────────────┘
```

### 5. Enhanced Layout Management

#### Dynamic Layout Adjustments

- **Normal mode**: Multiple hosts visible, adaptive sizing
- **Full-screen mode**: Single host uses all available space
- **Menu mode**: Overlay menu with semi-transparent background
- **Minimized mode**: Compact status bars for completed builds

#### Layout Transitions

- **Smooth transitions**: Animate layout changes when possible
- **State preservation**: Remember scroll positions and focus states
- **Responsive design**: Adapt to terminal size changes

## Implementation Architecture

### New Classes

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

### Enhanced Existing Classes

```python
class InputHandler:
    """Enhanced with new keyboard shortcuts and menu handling"""
    
class HostSection:
    """Enhanced with scroll state and focus indicators"""
    
class LayoutManager:
    """Enhanced with full-screen and minimized layouts"""
```

## Configuration Options

### User Preferences

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

## User Experience Considerations

### Visual Feedback

- **Focus indicators**: Clear visual indication of focused host
- **Scroll indicators**: Show scroll position and available content
- **Status overlays**: Minimal status info in full-screen mode
- **Transition animations**: Smooth visual transitions

### Accessibility

- **Keyboard navigation**: All features accessible via keyboard
- **Clear indicators**: Visual and textual status information
- **Consistent shortcuts**: Logical and memorable key mappings
- **Help system**: Comprehensive help with examples

### Performance

- **Efficient rendering**: Only redraw changed sections
- **Scroll optimization**: Virtual scrolling for large logs
- **Memory management**: Limit log buffer sizes
- **Background processing**: Non-blocking UI updates

## Testing Strategy

### Unit Tests

- Navigation state management
- Scroll position calculations
- Menu selection logic
- Focus state transitions

### Integration Tests

- Full navigation workflow
- Layout transitions
- Input handling scenarios
- Performance under load

### User Acceptance Tests

- Real-world usage scenarios
- Keyboard shortcut memorability
- Visual clarity and feedback
- Performance with large logs

## Success Metrics

### Usability

- Time to navigate between hosts
- Ease of log exploration
- User satisfaction with interface

### Performance

- Responsiveness of navigation
- Memory usage with large logs
- CPU usage during scrolling

### Reliability

- No navigation state corruption
- Proper cleanup of resources
- Graceful handling of edge cases

## Code-Focused Analysis and Implementation Priority

### Current Codebase Assessment

Based on my analysis of the existing code and the proposed navigation features, here's my assessment of the current state and recommendations for implementation priority:

#### **HIGH PRIORITY - Foundation Work (Addresses Technical Debt)**

1. **Enhanced Input Handler** ⭐⭐⭐⭐⭐
   - **Why**: The current `InputHandler` is only 100 lines and handles basic navigation. This is the foundation for all other features.
   - **Risk**: Low
   - **Impact**: High - enables all other navigation features
   - **Current State**: `input_handler.py` is clean and focused, easy to extend
   - **Navigation Connections**:
     - Currently only handles UP/DOWN navigation between visible hosts
     - Needs LEFT/RIGHT navigation between all hosts (including completed)
     - Must add ENTER/ESC for full-screen toggle
     - Requires TAB for menu activation
     - Needs PAGE_UP/PAGE_DOWN, HOME/END for log scrolling

2. **Focus Management System** ⭐⭐⭐⭐⭐
   - **Why**: Required for all navigation features. The current focus system is basic.
   - **Risk**: Low
   - **Impact**: High - core navigation functionality
   - **Current State**: Focus logic is scattered across multiple classes, needs centralization
   - **Navigation Connections**:
     - `HostSection` currently has no focus state management
     - `LayoutManager` handles positioning but not focus
     - `app.py` has basic focus tracking but no visual indicators
     - Need centralized focus state for normal, full-screen, and scroll modes

3. **Scroll State Management** ⭐⭐⭐⭐⭐
   - **Why**: Foundation for log exploration. The current `OutputBuffer` is simple and ready for enhancement.
   - **Risk**: Low
   - **Impact**: High - major UX improvement
   - **Current State**: `output_buffer.py` is only 97 lines, clean architecture ready for extension
   - **Navigation Connections**:
     - `OutputBuffer` in `HostSection` needs scroll offset tracking
     - Must integrate with focus management for scroll mode
     - Requires scroll indicators and position display
     - Needs to preserve scroll state during layout transitions

#### **MEDIUM PRIORITY - Core Features (Major UX Improvements)**

4. **Enhanced HostSection with Scroll Support** ⭐⭐⭐⭐
   - **Why**: Enables log exploration within existing UI. Current `HostSection` is 672 lines and could benefit from refactoring.
   - **Risk**: Medium
   - **Impact**: High - log scrolling is a major feature
   - **Current State**: `HostSection` is large but well-structured, needs scroll integration
   - **Navigation Connections**:
     - `BorderRenderer` class needs focus-aware border coloring
     - `OutputBuffer` integration with scroll state
     - Focus indicators and visual feedback
     - Scroll-aware rendering methods

5. **Layout Manager Enhancements** ⭐⭐⭐⭐
   - **Why**: Required for full-screen and minimized modes. Current `LayoutManager` is 441 lines and handles basic layouts well.
   - **Risk**: Medium
   - **Impact**: High - enables full-screen mode
   - **Current State**: Good foundation, needs full-screen and minimized layout support
   - **Navigation Connections**:
     - Currently only handles normal multi-host layout
     - Must add full-screen layout calculation
     - Needs minimized layout for completed builds
     - Layout transitions and state preservation
     - Responsive design for different terminal sizes

6. **Basic Full-Screen Mode** ⭐⭐⭐⭐
   - **Why**: Major UX improvement that builds on layout enhancements.
   - **Risk**: Medium
   - **Impact**: High - full-screen viewing is highly requested
   - **Current State**: Requires layout manager enhancements first
   - **Navigation Connections**:
     - ENTER key integration with focus management
     - ESC key handling for exit
     - Full-screen rendering in `Renderer` class
     - Background host management during full-screen

#### **LOWER PRIORITY - Advanced Features (Polish and Optimization)**

7. **Host Selection Menu** ⭐⭐⭐
   - **Why**: Provides access to all hosts including completed ones. Nice-to-have feature.
   - **Risk**: Low
   - **Impact**: Medium - improves host access
   - **Current State**: New functionality, no existing code to modify
   - **Navigation Connections**:
     - TAB key integration with `InputHandler`
     - Menu overlay rendering in `Renderer`
     - Host status integration with existing status tracking
     - Numbered selection (1-9 keys) implementation

8. **Completed Build Management** ⭐⭐⭐
   - **Why**: Solves the "lost completed builds" problem. Good UX improvement.
   - **Risk**: Low
   - **Impact**: Medium - better build history access
   - **Current State**: Builds on existing visibility management
   - **Navigation Connections**:
     - LEFT/RIGHT navigation between all hosts
     - Minimized display mode in `LayoutManager`
     - 'm' key toggle integration
     - Persistent access to completed builds

9. **Enhanced Navigation (LEFT/RIGHT between all hosts)** ⭐⭐⭐
   - **Why**: Polishes the navigation experience. Nice-to-have feature.
   - **Risk**: Low
   - **Impact**: Medium - smoother navigation
   - **Current State**: Requires focus management system first
   - **Navigation Connections**:
     - Extends current UP/DOWN navigation logic
     - Integrates with host visibility management
     - Smooth focus transitions
     - Visual feedback improvements

#### **OPTIMIZATION PRIORITY - Performance and Polish**

10. **Performance Optimization** ⭐⭐
    - **Why**: Ensures good performance with large builds. Important for production use.
    - **Risk**: Low
    - **Impact**: Medium - performance improvements
    - **Current State**: Current performance is adequate, optimization can wait
    - **Navigation Connections**:
      - Virtual scrolling for large logs
      - Efficient rendering for frequent updates
      - Memory management for log buffers
      - Background processing optimization

11. **User Experience Refinements** ⭐⭐
    - **Why**: Improves overall user experience. Polish features.
    - **Risk**: Low
    - **Impact**: Low - cosmetic improvements
    - **Current State**: Current UX is functional, refinements are nice-to-have
    - **Navigation Connections**:
      - Smooth transitions and animations
      - Comprehensive help system
      - Visual indicators and feedback
      - Keyboard shortcut consistency

### Key Code Integration Points

#### **Input Handler Integration**

- **Current**: Basic UP/DOWN navigation in `app.py` main loop
- **Needed**: Extended keyboard handling for all new shortcuts
- **Impact**: Low risk, high value - enables all navigation features

#### **Focus System Integration**

- **Current**: Basic focus tracking in `app.py` with `focused_host` index
- **Needed**: Centralized focus state management across all components
- **Impact**: Medium risk, high value - required for all navigation features

#### **Layout System Integration**

- **Current**: `LayoutManager` handles basic multi-host layouts
- **Needed**: Full-screen, minimized, and menu layout modes
- **Impact**: Medium risk, high value - enables major UX improvements

#### **Rendering System Integration**

- **Current**: `Renderer` class handles basic UI rendering
- **Needed**: Focus indicators, scroll indicators, menu overlays
- **Impact**: Low risk, medium value - visual polish and feedback

### Implementation Strategy Recommendations

#### **Phase 1: Foundation**

- Enhanced Input Handler
- Focus Management System  
- Scroll State Management

#### **Phase 2: Core Features**

- Enhanced HostSection with Scroll Support
- Layout Manager Enhancements
- Basic Full-Screen Mode

#### **Phase 3: Advanced Features**

- Host Selection Menu
- Completed Build Management
- Enhanced Navigation

#### **Phase 4: Optimization**

- Performance Optimization
- User Experience Refinements
- Testing & Documentation

### Risk Assessment

- **Low Risk**: Input handler, focus management, scroll state
- **Medium Risk**: Layout enhancements, full-screen mode, host section modifications
- **High Risk**: None identified - all features build incrementally

### Success Criteria

- **Phase 1**: All new keyboard shortcuts work, focus system functional
- **Phase 2**: Full-screen mode works, log scrolling functional  
- **Phase 3**: Menu system works, completed builds accessible
- **Phase 4**: Performance optimized, user experience polished

### Code Refactoring Requirements

#### **File Size Reduction**

- **`app.py` (753 lines)**: Extract navigation logic, focus management, and input handling
- **`host_section.py` (672 lines)**: Separate scroll logic, focus indicators, and rendering
- **`renderer.py` (583 lines)**: Split into focused rendering components
- **`layout_manager.py` (441 lines)**: Add new layout modes without increasing size

#### **Architecture Improvements**

- **Centralized Focus Management**: New `FocusManager` class to coordinate focus across components
- **Enhanced Input Handling**: Extend `InputHandler` with all new keyboard shortcuts
- **Scroll State Integration**: Integrate scroll state with existing `OutputBuffer` and `HostSection`
- **Layout Mode Support**: Add full-screen and minimized layouts to `LayoutManager`

#### **Integration Points**

- **Focus System**: Must integrate with `app.py`, `HostSection`, `LayoutManager`, and `Renderer`
- **Input Handling**: Must integrate with main app loop and all navigation features
- **Layout Management**: Must preserve existing functionality while adding new modes
- **Rendering**: Must maintain performance while adding visual feedback and indicators

## Conclusion

This enhanced navigation system will transform the Build TUI from a passive monitoring tool into an interactive build exploration platform. The design prioritizes usability, performance, and maintainability while building upon the existing solid architecture.

The implementation will be incremental, allowing for testing and refinement at each stage while maintaining backward compatibility with existing functionality.

Based on my code analysis, the foundation work (Phases 1-2) should be prioritized as it addresses technical debt and provides the most immediate user value with the lowest risk. The advanced features can be implemented incrementally once the foundation is solid.

The proposed navigation features have significant implications for the current codebase architecture. The existing code is well-structured but will require careful refactoring to integrate the new navigation capabilities while maintaining the current functionality and addressing the file size concerns identified in the initial assessment.

## Future Enhancement: Build Script Integration

### Current Architecture Decision

After careful analysis, the decision has been made to **maintain separation** between `build-tui` and `../build-redland.py` rather than integrating them into a single ownership model.

#### **Why Keep Separation**

1. **Architectural Purity**: Maintains clear separation of concerns between build tool and monitoring tool
2. **Reusability**: `build-redland.py` remains independent and usable outside of TUI context
3. **Maintainability**: Each component can evolve independently without affecting the other
4. **Testing**: Components can be tested in isolation
5. **Risk Management**: Changes to one component don't cascade to the other

#### **Current Integration Point**

```python
# From app.py - current well-architected integration
script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "build-redland.py")
)
```

The build script is **used** by build-tui (scp-ed to remote hosts) but not **owned** by it, maintaining proper separation.

### Future Enhancement Opportunities

#### **Interface Contract Improvements**

Instead of full integration, focus on enhancing the interface between components:

1. **Structured Output Format**
   - Define clear output format standards for build script
   - Add optional TUI-friendly output modes
   - Create parsing utilities in the TUI

2. **Optional TUI Mode**
   - Build script could support `--tui-mode` flag
   - Enable structured progress reporting
   - Add clear step boundary markers
   - Provide detailed timing data

3. **Configuration-Driven Cooperation**
   - Build script reads TUI configuration if present
   - Falls back to normal behavior if not
   - No hard coupling required

#### **TUI Enhancement Areas**

1. **Improved Parsing**
   - Better step detection from existing output
   - More robust error parsing and categorization
   - Enhanced timing extraction and analysis

2. **Configuration Integration**
   - TUI could configure build script behavior
   - Build script could read TUI preferences
   - Maintain independence while improving coordination

### Implementation Priority

This enhancement is **low priority** and should be considered only after:
- Core navigation features are implemented
- Current code refactoring is complete
- User feedback indicates interface improvements are needed

### Success Criteria

- **Maintain Independence**: Both components remain independently usable
- **Improved Coordination**: Better data flow between build script and TUI
- **Enhanced User Experience**: More reliable progress tracking and error reporting
- **No Performance Impact**: Integration doesn't slow down either component
