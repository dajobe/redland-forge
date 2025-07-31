#!/usr/bin/python3
"""
Tests for InputHandler module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from input_handler import InputHandler


class TestInputHandlerInitialization(unittest.TestCase):
    """Test InputHandler initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        mock_terminal = Mock()
        handler = InputHandler(mock_terminal)

        self.assertEqual(handler.term, mock_terminal)
        self.assertFalse(handler.help_visible)

    def test_init_with_terminal(self):
        """Test initialization with terminal object."""
        mock_terminal = Mock()
        mock_terminal.width = 80
        mock_terminal.height = 24

        handler = InputHandler(mock_terminal)

        self.assertEqual(handler.term, mock_terminal)
        self.assertFalse(handler.help_visible)


class TestInputHandlerHelpManagement(unittest.TestCase):
    """Test help screen management."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.handler = InputHandler(self.mock_terminal)

    def test_is_help_visible_default(self):
        """Test help visibility default state."""
        self.assertFalse(self.handler.is_help_visible())

    def test_set_help_visible_true(self):
        """Test setting help visible to True."""
        self.handler.set_help_visible(True)
        self.assertTrue(self.handler.is_help_visible())

    def test_set_help_visible_false(self):
        """Test setting help visible to False."""
        self.handler.set_help_visible(True)  # Set to True first
        self.handler.set_help_visible(False)  # Then set to False
        self.assertFalse(self.handler.is_help_visible())

    def test_show_help_basic(self):
        """Test show_help method calls."""
        with patch("input_handler.logging") as mock_logging:
            self.handler.show_help()
            mock_logging.debug.assert_called_with(
                "Help screen requested (not yet fully implemented)"
            )


class TestInputHandlerInputProcessing(unittest.TestCase):
    """Test input processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.handler = InputHandler(self.mock_terminal)

        # Mock callbacks
        self.mock_on_quit = Mock()
        self.mock_on_navigate_up = Mock()
        self.mock_on_navigate_down = Mock()
        self.mock_on_show_help = Mock()

    def test_handle_input_no_key(self):
        """Test input handling when no key is pressed."""
        mock_inkey = Mock(return_value=None)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        self.handler.handle_input(
            self.mock_on_quit,
            self.mock_on_navigate_up,
            self.mock_on_navigate_down,
            self.mock_on_show_help,
        )

        # Verify no callbacks were called
        self.mock_on_quit.assert_not_called()
        self.mock_on_navigate_up.assert_not_called()
        self.mock_on_navigate_down.assert_not_called()
        self.mock_on_show_help.assert_not_called()

    def test_handle_input_quit_key(self):
        """Test input handling for quit key."""
        mock_key = Mock()
        # Make the key behave like a string when compared
        mock_key.__eq__ = Mock(side_effect=lambda x: x == "q")
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify quit callback was called
            self.mock_on_quit.assert_called_once()
            mock_logging.debug.assert_called_with("Quit requested via keyboard input")

    def test_handle_input_help_key(self):
        """Test input handling for help key."""
        mock_key = Mock()
        # Make the key behave like a string when compared
        mock_key.__eq__ = Mock(side_effect=lambda x: x == "h")
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify help callback was called
            self.mock_on_show_help.assert_called_once()
            mock_logging.debug.assert_called_with("Help requested via keyboard input")

    def test_handle_input_up_key(self):
        """Test input handling for up arrow key."""
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_UP
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify up navigation callback was called
            self.mock_on_navigate_up.assert_called_once()
            mock_logging.debug.assert_called_with(
                "Up navigation requested via keyboard input"
            )

    def test_handle_input_down_key(self):
        """Test input handling for down arrow key."""
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_DOWN
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify down navigation callback was called
            self.mock_on_navigate_down.assert_called_once()
            mock_logging.debug.assert_called_with(
                "Down navigation requested via keyboard input"
            )

    def test_handle_input_unknown_key(self):
        """Test input handling for unknown key."""
        mock_key = Mock()
        # Make the key behave like a string when compared, but not match any known keys
        mock_key.__eq__ = Mock(side_effect=lambda x: x == "x")
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        self.handler.handle_input(
            self.mock_on_quit,
            self.mock_on_navigate_up,
            self.mock_on_navigate_down,
            self.mock_on_show_help,
        )

        # Verify no callbacks were called for unknown key
        self.mock_on_quit.assert_not_called()
        self.mock_on_navigate_up.assert_not_called()
        self.mock_on_navigate_down.assert_not_called()
        self.mock_on_show_help.assert_not_called()

    def test_handle_input_custom_timeout(self):
        """Test input handling with custom timeout."""
        mock_inkey = Mock(return_value=None)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        self.handler.handle_input(
            self.mock_on_quit,
            self.mock_on_navigate_up,
            self.mock_on_navigate_down,
            self.mock_on_show_help,
            timeout=0.5,
        )

        # Verify timeout was passed to inkey
        mock_inkey.assert_called_with(timeout=0.5)


class TestInputHandlerIntegration(unittest.TestCase):
    """Test InputHandler integration scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.handler = InputHandler(self.mock_terminal)

        # Mock callbacks
        self.mock_on_quit = Mock()
        self.mock_on_navigate_up = Mock()
        self.mock_on_navigate_down = Mock()
        self.mock_on_show_help = Mock()

    def test_multiple_input_handling(self):
        """Test handling multiple input types in sequence."""
        # Mock different keys for different calls
        mock_keys = [
            Mock(__eq__=Mock(side_effect=lambda x: x == "q")),  # Quit
            Mock(__eq__=Mock(side_effect=lambda x: x == "h")),  # Help
            Mock(code=self.mock_terminal.KEY_UP),  # Up
            Mock(code=self.mock_terminal.KEY_DOWN),  # Down
        ]

        mock_inkey = Mock(side_effect=mock_keys)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        # Handle each input
        for _ in range(4):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

        # Verify all callbacks were called
        self.assertEqual(self.mock_on_quit.call_count, 1)
        self.assertEqual(self.mock_on_show_help.call_count, 1)
        self.assertEqual(self.mock_on_navigate_up.call_count, 1)
        self.assertEqual(self.mock_on_navigate_down.call_count, 1)

    def test_help_visibility_state_management(self):
        """Test help visibility state management."""
        # Initially not visible
        self.assertFalse(self.handler.is_help_visible())

        # Show help
        self.handler.set_help_visible(True)
        self.assertTrue(self.handler.is_help_visible())

        # Hide help
        self.handler.set_help_visible(False)
        self.assertFalse(self.handler.is_help_visible())

        # Show again
        self.handler.set_help_visible(True)
        self.assertTrue(self.handler.is_help_visible())


if __name__ == "__main__":
    unittest.main()
