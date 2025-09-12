#!/usr/bin/python3
"""
Tests for InputHandler module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from redland_forge.input_handler import InputHandler, NavigationMode


class TestInputHandlerInitialization(unittest.TestCase):
    """Test InputHandler initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        mock_terminal = Mock()
        handler = InputHandler(mock_terminal)

        self.assertEqual(handler.term, mock_terminal)
        self.assertFalse(handler.help_visible)
        self.assertEqual(handler.navigation_mode, NavigationMode.HOST_NAVIGATION)
        self.assertFalse(handler.full_screen_active)
        self.assertFalse(handler.menu_active)

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
        self.handler.show_help()


class TestInputHandlerStateManagement(unittest.TestCase):
    """Test state management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.handler = InputHandler(self.mock_terminal)

    def test_navigation_mode_management(self):
        """Test navigation mode getter and setter."""
        # Initial state should be HOST_NAVIGATION
        self.assertEqual(
            self.handler.get_navigation_mode(), NavigationMode.HOST_NAVIGATION
        )

        # Test setting different modes
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)
        self.assertEqual(
            self.handler.get_navigation_mode(), NavigationMode.LOG_SCROLLING
        )

        self.handler.set_navigation_mode(NavigationMode.FULL_SCREEN)
        self.assertEqual(self.handler.get_navigation_mode(), NavigationMode.FULL_SCREEN)

        self.handler.set_navigation_mode(NavigationMode.MENU)
        self.assertEqual(self.handler.get_navigation_mode(), NavigationMode.MENU)

    def test_full_screen_state_management(self):
        """Test full-screen state management."""
        # Initial state should be False
        self.assertFalse(self.handler.is_full_screen_active())

        # Test setting to True
        self.handler.set_full_screen_active(True)
        self.assertTrue(self.handler.is_full_screen_active())

        # Test setting back to False
        self.handler.set_full_screen_active(False)
        self.assertFalse(self.handler.is_full_screen_active())

    def test_menu_state_management(self):
        """Test menu state management."""
        # Initial state should be False
        self.assertFalse(self.handler.is_menu_active())

        # Test setting to True
        self.handler.set_menu_active(True)
        self.assertTrue(self.handler.is_menu_active())

        # Test setting back to False
        self.handler.set_menu_active(False)
        self.assertFalse(self.handler.is_menu_active())


class TestInputHandlerNavigationModes(unittest.TestCase):
    """Test navigation mode-specific behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.handler = InputHandler(self.mock_terminal)

        # Mock callbacks
        self.mock_on_quit = Mock()
        self.mock_on_navigate_up = Mock()
        self.mock_on_navigate_down = Mock()
        self.mock_on_show_help = Mock()
        self.mock_on_navigate_left = Mock()
        self.mock_on_navigate_right = Mock()
        self.mock_on_toggle_fullscreen = Mock()
        self.mock_on_escape = Mock()
        self.mock_on_toggle_menu = Mock()
        self.mock_on_page_up = Mock()
        self.mock_on_page_down = Mock()
        self.mock_on_home = Mock()
        self.mock_on_end = Mock()

    def test_host_navigation_mode_up_down(self):
        """Test UP/DOWN keys in host navigation mode."""
        self.handler.set_navigation_mode(NavigationMode.HOST_NAVIGATION)

        # Test UP key
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_UP
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging"):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

        self.mock_on_navigate_up.assert_called_once()

    def test_host_navigation_mode_left_right(self):
        """Test LEFT/RIGHT keys in host navigation mode."""
        self.handler.set_navigation_mode(NavigationMode.HOST_NAVIGATION)

        # Test LEFT key
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_LEFT
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging"):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

        self.mock_on_navigate_left.assert_called_once()

    def test_log_scrolling_mode_page_up_down(self):
        """Test PAGE_UP/PAGE_DOWN keys in log scrolling mode."""
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        # Test PAGE_UP key
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_PGUP
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging"):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

        self.mock_on_page_up.assert_called_once()

    def test_log_scrolling_mode_home_end(self):
        """Test HOME/END keys in log scrolling mode."""
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        # Test HOME key
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_HOME
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging"):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

        self.mock_on_home.assert_called_once()

    def test_menu_mode_navigation(self):
        """Test navigation in menu mode."""
        self.handler.set_navigation_mode(NavigationMode.MENU)

        # Test UP key in menu mode
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_UP
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging"):
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

        self.mock_on_navigate_up.assert_called_once()

    def test_global_keys_work_in_all_modes(self):
        """Test that global keys (q, h) work in all navigation modes."""
        for mode in NavigationMode:
            with self.subTest(mode=mode):
                self.handler.set_navigation_mode(mode)

                # Test 'q' key
                mock_key = Mock()
                mock_key.__eq__ = Mock(side_effect=lambda x: x == "q")
                mock_inkey = Mock(return_value=mock_key)
                mock_cbreak = Mock()
                mock_cbreak.__enter__ = Mock(return_value=None)
                mock_cbreak.__exit__ = Mock(return_value=None)

                self.mock_terminal.cbreak.return_value = mock_cbreak
                self.mock_terminal.inkey = mock_inkey

                # Reset mocks
                self.mock_on_quit.reset_mock()

                with patch("redland_forge.input_handler.logging"):
                    self.handler.handle_input(
                        self.mock_on_quit,
                        self.mock_on_navigate_up,
                        self.mock_on_navigate_down,
                        self.mock_on_show_help,
                        on_navigate_left=self.mock_on_navigate_left,
                        on_navigate_right=self.mock_on_navigate_right,
                        on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                        on_escape=self.mock_on_escape,
                        on_toggle_menu=self.mock_on_toggle_menu,
                        on_page_up=self.mock_on_page_up,
                        on_page_down=self.mock_on_page_down,
                        on_home=self.mock_on_home,
                        on_end=self.mock_on_end,
                    )

                self.mock_on_quit.assert_called_once()


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
        self.mock_on_navigate_left = Mock()
        self.mock_on_navigate_right = Mock()
        self.mock_on_toggle_fullscreen = Mock()
        self.mock_on_escape = Mock()
        self.mock_on_toggle_menu = Mock()
        self.mock_on_page_up = Mock()
        self.mock_on_page_down = Mock()
        self.mock_on_home = Mock()
        self.mock_on_end = Mock()

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
            on_navigate_left=self.mock_on_navigate_left,
            on_navigate_right=self.mock_on_navigate_right,
            on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
            on_escape=self.mock_on_escape,
            on_toggle_menu=self.mock_on_toggle_menu,
            on_page_up=self.mock_on_page_up,
            on_page_down=self.mock_on_page_down,
            on_home=self.mock_on_home,
            on_end=self.mock_on_end,
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

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify quit callback was called
            self.mock_on_quit.assert_called_once()

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

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify help callback was called
            self.mock_on_show_help.assert_called_once()

    def test_handle_input_question_mark_help_key(self):
        """Test input handling for question mark help key."""
        mock_key = Mock()
        # Make the key behave like a string when compared
        mock_key.__eq__ = Mock(side_effect=lambda x: x == "?")
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify help callback was called
            self.mock_on_show_help.assert_called_once()

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

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify up navigation callback was called
            self.mock_on_navigate_up.assert_called_once()

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

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
            )

            # Verify down navigation callback was called
            self.mock_on_navigate_down.assert_called_once()

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
            on_navigate_left=self.mock_on_navigate_left,
            on_navigate_right=self.mock_on_navigate_right,
            on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
            on_escape=self.mock_on_escape,
            on_toggle_menu=self.mock_on_toggle_menu,
            on_page_up=self.mock_on_page_up,
            on_page_down=self.mock_on_page_down,
            on_home=self.mock_on_home,
            on_end=self.mock_on_end,
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
            on_navigate_left=self.mock_on_navigate_left,
            on_navigate_right=self.mock_on_navigate_right,
            on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
            on_escape=self.mock_on_escape,
            on_toggle_menu=self.mock_on_toggle_menu,
            on_page_up=self.mock_on_page_up,
            on_page_down=self.mock_on_page_down,
            on_home=self.mock_on_home,
            on_end=self.mock_on_end,
            timeout=0.5,
        )

        # Verify timeout was passed to inkey (now always 0.0 for non-blocking)
        mock_inkey.assert_called_with(timeout=0.0)

    def test_handle_input_left_key(self):
        """Test input handling for left arrow key."""
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_LEFT
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify left navigation callback was called
            self.mock_on_navigate_left.assert_called_once()

    def test_handle_input_right_key(self):
        """Test input handling for right arrow key."""
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_RIGHT
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify right navigation callback was called
            self.mock_on_navigate_right.assert_called_once()

    def test_handle_input_enter_key(self):
        """Test input handling for enter key."""
        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_ENTER
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify fullscreen toggle callback was called
            self.mock_on_toggle_fullscreen.assert_called_once()

    def test_handle_input_escape_key(self):
        """Test input handling for escape key."""
        # Set to LOG_SCROLLING mode where escape works
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_ESCAPE
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify escape callback was called
            self.mock_on_escape.assert_called_once()

    def test_handle_input_tab_key(self):
        """Test input handling for tab key."""
        mock_key = Mock()
        # Tab key is "\t"
        mock_key.__eq__ = Mock(side_effect=lambda x: x == "\t")
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify menu toggle callback was called
            self.mock_on_toggle_menu.assert_called_once()

    def test_handle_input_page_up_key(self):
        """Test input handling for page up key."""
        # Set to LOG_SCROLLING mode where page up works
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_PGUP
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify page up callback was called
            self.mock_on_page_up.assert_called_once()

    def test_handle_input_page_down_key(self):
        """Test input handling for page down key."""
        # Set to LOG_SCROLLING mode where page down works
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_PGDN
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify page down callback was called
            self.mock_on_page_down.assert_called_once()

    def test_handle_input_home_key(self):
        """Test input handling for home key."""
        # Set to LOG_SCROLLING mode where home works
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_HOME
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify home callback was called
            self.mock_on_home.assert_called_once()

    def test_handle_input_end_key(self):
        """Test input handling for end key."""
        # Set to LOG_SCROLLING mode where end works
        self.handler.set_navigation_mode(NavigationMode.LOG_SCROLLING)

        mock_key = Mock()
        mock_key.code = self.mock_terminal.KEY_END
        mock_inkey = Mock(return_value=mock_key)
        mock_cbreak = Mock()
        mock_cbreak.__enter__ = Mock(return_value=None)
        mock_cbreak.__exit__ = Mock(return_value=None)

        self.mock_terminal.cbreak.return_value = mock_cbreak
        self.mock_terminal.inkey = mock_inkey

        with patch("redland_forge.input_handler.logging") as mock_logging:
            self.handler.handle_input(
                self.mock_on_quit,
                self.mock_on_navigate_up,
                self.mock_on_navigate_down,
                self.mock_on_show_help,
                on_navigate_left=self.mock_on_navigate_left,
                on_navigate_right=self.mock_on_navigate_right,
                on_toggle_fullscreen=self.mock_on_toggle_fullscreen,
                on_escape=self.mock_on_escape,
                on_toggle_menu=self.mock_on_toggle_menu,
                on_page_up=self.mock_on_page_up,
                on_page_down=self.mock_on_page_down,
                on_home=self.mock_on_home,
                on_end=self.mock_on_end,
            )

            # Verify end callback was called
            self.mock_on_end.assert_called_once()


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
