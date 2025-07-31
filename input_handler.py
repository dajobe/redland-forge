#!/usr/bin/python3
"""
Input Handler Module

A module for handling keyboard input and help display in the TUI.
"""

import logging
from typing import Callable, Optional

from blessed import Terminal


class InputHandler:
    """Handles keyboard input and help display for the TUI."""

    def __init__(self, terminal: Terminal):
        """
        Initialize the input handler.

        Args:
            terminal: Blessed terminal object
        """
        self.term = terminal
        self.help_visible = False

    def handle_input(
        self,
        on_quit: Callable[[], None],
        on_navigate_up: Callable[[], None],
        on_navigate_down: Callable[[], None],
        on_show_help: Callable[[], None],
        timeout: float = 0.1,
    ) -> None:
        """
        Handle keyboard input.

        Args:
            on_quit: Callback function to call when quit is requested
            on_navigate_up: Callback function to call when up navigation is requested
            on_navigate_down: Callback function to call when down navigation is requested
            on_show_help: Callback function to call when help is requested
            timeout: Timeout for input reading in seconds
        """
        with self.term.cbreak():
            key = self.term.inkey(timeout=timeout)
            if key:
                if key == "q":
                    logging.debug("Quit requested via keyboard input")
                    on_quit()
                elif key == "h":
                    logging.debug("Help requested via keyboard input")
                    on_show_help()
                elif key.code == self.term.KEY_UP:
                    logging.debug("Up navigation requested via keyboard input")
                    on_navigate_up()
                elif key.code == self.term.KEY_DOWN:
                    logging.debug("Down navigation requested via keyboard input")
                    on_navigate_down()

    def show_help(self) -> None:
        """Show help screen."""
        help_text = [
            "Keyboard Controls:",
            "  q - Quit",
            "  h - Show/hide this help",
            "  UP/DOWN - Navigate between hosts",
            "  SPACE - Pause/resume updates",
            "",
            "Press any key to continue...",
        ]

        # Save current screen
        # Show help overlay
        # Wait for key press
        # Restore screen

        # TODO: Implement full help screen functionality
        # For now, just log that help was requested
        logging.debug("Help screen requested (not yet fully implemented)")

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
