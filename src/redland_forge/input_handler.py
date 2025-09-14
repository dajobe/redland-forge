#!/usr/bin/python3
"""
Input Handler Module

A module for handling keyboard input and help display in the TUI.
"""

import logging
from typing import Callable, Optional
from enum import Enum

from blessed import Terminal


class NavigationMode(Enum):
    """Navigation modes for the input handler."""

    HOST_NAVIGATION = "host_navigation"
    LOG_SCROLLING = "log_scrolling"
    FULL_SCREEN = "full_screen"
    MENU = "menu"


class InputHandler:
    """Handles keyboard input and help display for the TUI."""

    def __init__(self, terminal: Terminal) -> None:
        """
        Initialize the input handler.

        Args:
            terminal: Blessed terminal object
        """
        self.term = terminal
        self.help_visible = False
        self.navigation_mode = NavigationMode.HOST_NAVIGATION
        self.full_screen_active = False
        self.menu_active = False

    def handle_input(
        self,
        on_quit: Callable[[], None],
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_show_help: Callable[[], None],
        on_navigate_left: Optional[Callable[[], None]] = None,
        on_navigate_right: Optional[Callable[[], None]] = None,
        on_toggle_fullscreen: Optional[Callable[[], None]] = None,
        on_escape: Optional[Callable[[], None]] = None,
        on_toggle_menu: Optional[Callable[[], None]] = None,
        on_page_up: Optional[Callable[[], None]] = None,
        on_page_down: Optional[Callable[[], None]] = None,
        on_home: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None,
        timeout: float = 0.1,
    ) -> None:
        """
        Handle keyboard input.

        Args:
            on_quit: Callback function to call when quit is requested
            on_navigate_up: Callback function to call when up navigation is requested
            on_navigate_down: Callback function to call when down navigation is requested
            on_show_help: Callback function to call when help is requested
            on_navigate_left: Callback function to call when left navigation is requested
            on_navigate_right: Callback function to call when right navigation is requested
            on_toggle_fullscreen: Callback function to call when full-screen toggle is requested
            on_escape: Callback function to call when escape is pressed
            on_toggle_menu: Callback function to call when menu toggle is requested
            on_page_up: Callback function to call when page up is requested
            on_page_down: Callback function to call when page down is requested
            on_home: Callback function to call when home key is pressed
            on_end: Callback function to call when end key is pressed
            timeout: Timeout for input reading in seconds
        """
        # Use non-blocking input with proper terminal mode
        key = self.term.inkey(timeout=0.0)  # Always non-blocking
        if key:
            self._handle_key(
                key,
                on_quit=on_quit,
                on_navigate_up=on_navigate_up,
                on_navigate_down=on_navigate_down,
                on_show_help=on_show_help,
                on_navigate_left=on_navigate_left,
                on_navigate_right=on_navigate_right,
                on_toggle_fullscreen=on_toggle_fullscreen,
                on_escape=on_escape,
                on_toggle_menu=on_toggle_menu,
                on_page_up=on_page_up,
                on_page_down=on_page_down,
                on_home=on_home,
                on_end=on_end,
            )

    def _handle_key(
        self,
        key,
        on_quit: Callable[[], None],
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_show_help: Callable[[], None],
        on_navigate_left: Optional[Callable[[], None]] = None,
        on_navigate_right: Optional[Callable[[], None]] = None,
        on_toggle_fullscreen: Optional[Callable[[], None]] = None,
        on_escape: Optional[Callable[[], None]] = None,
        on_toggle_menu: Optional[Callable[[], None]] = None,
        on_menu_select: Optional[Callable[[], None]] = None,
        on_page_up: Optional[Callable[[], None]] = None,
        on_page_down: Optional[Callable[[], None]] = None,
        on_home: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Handle a specific key press based on the current navigation mode.

        Args:
            key: The key that was pressed
            on_*: Various callback functions for different actions
        """
        # Global keys that work in all modes
        if key == "q":
            logging.debug("Quit requested via keyboard input")
            on_quit()
        elif key in ("h", "?"):
            logging.debug("Help requested via keyboard input")
            on_show_help()

        # Mode-specific handling
        if self.navigation_mode == NavigationMode.HOST_NAVIGATION:
            self._handle_host_navigation_key(
                key,
                on_navigate_up,
                on_navigate_down,
                on_navigate_left,
                on_navigate_right,
                on_toggle_fullscreen,
                on_toggle_menu,
                on_escape,
            )
        elif self.navigation_mode == NavigationMode.LOG_SCROLLING:
            self._handle_log_scrolling_key(
                key,
                on_navigate_up,
                on_navigate_down,
                on_page_up,
                on_page_down,
                on_home,
                on_end,
                on_escape,
            )
        elif self.navigation_mode == NavigationMode.FULL_SCREEN:
            self._handle_full_screen_key(
                key,
                on_navigate_up,
                on_navigate_down,
                on_page_up,
                on_page_down,
                on_home,
                on_end,
                on_escape,
                on_toggle_fullscreen,
            )
        elif self.navigation_mode == NavigationMode.MENU:
            self._handle_menu_key(
                key,
                on_navigate_up,
                on_navigate_down,
                on_toggle_menu,
                on_escape,
                on_menu_select,
            )

    def show_help(self) -> None:
        """Show help screen."""
        help_text = [
            "Keyboard Controls:",
            "",
            "Basic Navigation:",
            "  q - Quit",
            "  h, ? - Show/hide this help",
            "  UP/DOWN - Navigate between visible hosts",
            "  LEFT/RIGHT - Navigate between all hosts (including completed)",
            "",
            "Display Controls:",
            "  ENTER - Toggle full-screen mode for current host",
            "  ESC - Exit full-screen or menu mode",
            "  TAB - Toggle menu/options",
            "",
            "Log Scrolling (in full-screen mode):",
            "  PAGE UP/DOWN - Scroll log by page",
            "  HOME - Go to beginning of log",
            "  END - Go to end of log",
            "",
            "Press any key to continue...",
        ]

        # Save current screen
        # Show help overlay
        # Wait for key press
        # Restore screen

        # Help screen functionality is fully implemented in the main app
        logging.debug("Help screen requested")

    def is_help_visible(self) -> bool:
        """
        Check if help screen is currently visible.

        Returns:
            True if help is visible, False otherwise
        """
        return self.help_visible

    def set_help_visible(self, visible: bool) -> None:
        """
        Set help screen visibility.

        Args:
            visible: Whether help should be visible
        """
        self.help_visible = visible
        logging.debug(f"Help visibility set to: {visible}")

    def get_navigation_mode(self) -> NavigationMode:
        """
        Get the current navigation mode.

        Returns:
            Current navigation mode
        """
        return self.navigation_mode

    def set_navigation_mode(self, mode: NavigationMode) -> None:
        """
        Set the navigation mode.

        Args:
            mode: Navigation mode to set
        """
        self.navigation_mode = mode
        logging.debug(f"Navigation mode set to: {mode.value}")

    def is_full_screen_active(self) -> bool:
        """
        Check if full-screen mode is active.

        Returns:
            True if full-screen is active, False otherwise
        """
        return self.full_screen_active

    def set_full_screen_active(self, active: bool) -> None:
        """
        Set full-screen mode state.

        Args:
            active: Whether full-screen should be active
        """
        self.full_screen_active = active
        logging.debug(f"Full-screen mode set to: {active}")

    def is_menu_active(self) -> bool:
        """
        Check if menu is active.

        Returns:
            True if menu is active, False otherwise
        """
        return self.menu_active

    def set_menu_active(self, active: bool) -> None:
        """
        Set menu active state.

        Args:
            active: Whether menu should be active
        """
        self.menu_active = active
        logging.debug(f"Menu active set to: {active}")

    def _handle_host_navigation_key(
        self,
        key,
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_navigate_left: Optional[Callable[[], None]],
        on_navigate_right: Optional[Callable[[], None]],
        on_toggle_fullscreen: Optional[Callable[[], None]],
        on_toggle_menu: Optional[Callable[[], None]],
        on_escape: Optional[Callable[[], None]],
    ) -> None:
        """Handle key presses in host navigation mode."""
        if key.code == self.term.KEY_UP:
            on_navigate_up()
        elif key.code == self.term.KEY_DOWN:
            on_navigate_down()
        elif key.code == self.term.KEY_LEFT:
            if on_navigate_left:
                on_navigate_left()
        elif key.code == self.term.KEY_RIGHT:
            if on_navigate_right:
                on_navigate_right()
        elif key.code == self.term.KEY_ENTER or key == "\r" or key == "\n":
            if on_toggle_fullscreen:
                on_toggle_fullscreen()
        elif key == "\t":  # Tab key
            if on_toggle_menu:
                on_toggle_menu()

    def _handle_log_scrolling_key(
        self,
        key,
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_page_up: Optional[Callable[[], None]],
        on_page_down: Optional[Callable[[], None]],
        on_home: Optional[Callable[[], None]],
        on_end: Optional[Callable[[], None]],
        on_escape: Optional[Callable[[], None]],
    ) -> None:
        """Handle key presses in log scrolling mode."""
        if key.code == self.term.KEY_UP:
            logging.debug("Scroll up one line")
            on_navigate_up()
        elif key.code == self.term.KEY_DOWN:
            logging.debug("Scroll down one line")
            on_navigate_down()
        elif key.code == self.term.KEY_PGUP:
            logging.debug("Scroll up one page")
            if on_page_up:
                on_page_up()
        elif key.code == self.term.KEY_PGDN or key.code == 338:
            logging.debug("Scroll down one page")
            if on_page_down:
                on_page_down()
        elif key.code == self.term.KEY_HOME:
            logging.debug("Go to beginning of log")
            if on_home:
                on_home()
        elif key.code == self.term.KEY_END:
            logging.debug("Go to end of log")
            if on_end:
                on_end()
        elif key.code == self.term.KEY_ESCAPE:
            logging.debug("Exit log scrolling mode")
            if on_escape:
                on_escape()

    def _handle_full_screen_key(
        self,
        key,
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_page_up: Optional[Callable[[], None]],
        on_page_down: Optional[Callable[[], None]],
        on_home: Optional[Callable[[], None]],
        on_end: Optional[Callable[[], None]],
        on_escape: Optional[Callable[[], None]],
        on_toggle_fullscreen: Optional[Callable[[], None]],
    ) -> None:
        """Handle key presses in full-screen mode."""
        if key.code == self.term.KEY_UP:
            logging.debug("Scroll up one line (full-screen)")
            if on_navigate_up:
                on_navigate_up()
        elif key.code == self.term.KEY_DOWN:
            logging.debug("Scroll down one line (full-screen)")
            if on_navigate_down:
                on_navigate_down()
        elif key.code == self.term.KEY_PGUP:
            logging.debug("Scroll up one page (full-screen)")
            if on_page_up:
                on_page_up()
        elif key.code == self.term.KEY_PGDN or key.code == 338:
            logging.debug("Scroll down one page (full-screen)")
            if on_page_down:
                on_page_down()
        elif key.code == self.term.KEY_HOME:
            logging.debug("Go to beginning of log (full-screen)")
            if on_home:
                on_home()
        elif key.code == self.term.KEY_END:
            logging.debug("Go to end of log (full-screen)")
            if on_end:
                on_end()
        elif (
            key.code == self.term.KEY_ESCAPE
            or key.code == self.term.KEY_ENTER
            or key == "\r"
            or key == "\n"
        ):
            logging.debug("Exit full-screen mode")
            if on_escape or on_toggle_fullscreen:
                (on_escape or on_toggle_fullscreen)()

    def _handle_menu_key(
        self,
        key,
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_toggle_menu: Optional[Callable[[], None]],
        on_escape: Optional[Callable[[], None]],
        on_menu_select: Optional[Callable[[], None]],
    ) -> None:
        """Handle key presses in menu mode."""
        if key.code == self.term.KEY_UP:
            logging.debug("Navigate up in menu")
            on_navigate_up()
        elif key.code == self.term.KEY_DOWN:
            logging.debug("Navigate down in menu")
            on_navigate_down()
        elif key.code == self.term.KEY_ENTER or key == "\r" or key == "\n":
            logging.debug("Select menu option")
            # In menu mode, ENTER should select the current option
            if on_menu_select:
                on_menu_select()
        elif key == "\t" or key.code == self.term.KEY_ESCAPE:
            logging.debug("Exit menu mode")
            if on_toggle_menu or on_escape:
                (on_toggle_menu or on_escape)()
