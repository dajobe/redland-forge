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

## Conclusion

This enhanced navigation system will transform the Build TUI from a passive monitoring tool into an interactive build exploration platform. The design prioritizes usability, performance, and maintainability while building upon the existing solid architecture.

The implementation will be incremental, allowing for testing and refinement at each phase while maintaining backward compatibility with existing functionality.
