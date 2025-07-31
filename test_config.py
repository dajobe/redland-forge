#!/usr/bin/python3
"""
Unit tests for Config class.
"""

import unittest
import logging

from config import Config
from color_manager import ColorManager


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""

    def test_build_settings(self):
        """Test build process settings."""
        settings = Config.get_build_settings()

        self.assertIn("BUILD_TIMEOUT_SECONDS", settings)
        self.assertIn("BUILD_DIRECTORY", settings)
        self.assertIn("BUILD_SCRIPT_NAME", settings)

        self.assertEqual(settings["BUILD_TIMEOUT_SECONDS"], 7200)
        self.assertEqual(settings["BUILD_DIRECTORY"], "/tmp/build")
        self.assertEqual(settings["BUILD_SCRIPT_NAME"], "build-redland.py")

    def test_ui_settings(self):
        """Test UI rendering settings."""
        settings = Config.get_ui_settings()

        self.assertIn("MIN_RENDER_INTERVAL_SECONDS", settings)
        self.assertIn("TIMER_UPDATE_INTERVAL_SECONDS", settings)
        self.assertIn("HOST_VISIBILITY_TIMEOUT_SECONDS", settings)
        self.assertIn("HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS", settings)

        self.assertEqual(settings["MIN_RENDER_INTERVAL_SECONDS"], 0.2)
        self.assertEqual(settings["TIMER_UPDATE_INTERVAL_SECONDS"], 1.0)
        self.assertEqual(settings["HOST_VISIBILITY_TIMEOUT_SECONDS"], 10.0)
        self.assertEqual(settings["HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS"], 0.5)

    def test_layout_settings(self):
        """Test terminal layout settings."""
        settings = Config.get_layout_settings()

        self.assertIn("MIN_TERMINAL_HEIGHT", settings)
        self.assertIn("MIN_HOST_HEIGHT", settings)
        self.assertIn("HEADER_HEIGHT", settings)
        self.assertIn("FOOTER_HEIGHT", settings)
        self.assertIn("TERMINAL_MARGIN", settings)
        self.assertIn("BORDER_PADDING", settings)

        self.assertEqual(settings["MIN_TERMINAL_HEIGHT"], 10)
        self.assertEqual(settings["MIN_HOST_HEIGHT"], 8)
        self.assertEqual(settings["HEADER_HEIGHT"], 4)
        self.assertEqual(settings["FOOTER_HEIGHT"], 4)
        self.assertEqual(settings["TERMINAL_MARGIN"], 2)
        self.assertEqual(settings["BORDER_PADDING"], 4)

    def test_ssh_settings(self):
        """Test SSH connection settings."""
        settings = Config.get_ssh_settings()

        self.assertIn("SSH_TIMEOUT_SECONDS", settings)
        self.assertIn("SSH_CONNECTION_RETRIES", settings)

        self.assertEqual(settings["SSH_TIMEOUT_SECONDS"], 30)
        self.assertEqual(settings["SSH_CONNECTION_RETRIES"], 3)

    def test_output_settings(self):
        """Test output buffering settings."""
        settings = Config.get_output_settings()

        self.assertIn("MAX_OUTPUT_LINES_PER_HOST", settings)
        self.assertIn("OUTPUT_BUFFER_OVERFLOW_MARGIN", settings)

        self.assertEqual(settings["MAX_OUTPUT_LINES_PER_HOST"], 100)
        self.assertEqual(settings["OUTPUT_BUFFER_OVERFLOW_MARGIN"], 3)

    def test_logging_settings(self):
        """Test logging settings."""
        settings = Config.get_logging_settings()

        self.assertIn("DEFAULT_LOG_LEVEL", settings)
        self.assertIn("DEBUG_LOG_LEVEL", settings)
        self.assertIn("LOG_FILE", settings)

        self.assertEqual(settings["DEFAULT_LOG_LEVEL"], logging.INFO)
        self.assertEqual(settings["DEBUG_LOG_LEVEL"], logging.DEBUG)
        self.assertEqual(settings["LOG_FILE"], "debug.log")

    def test_color_settings(self):
        """Test color and formatting settings."""
        settings = ColorManager.get_color_settings()

        # DEFAULT_BORDER_COLOR is now in ColorManager, not Config
        # self.assertIn("DEFAULT_BORDER_COLOR", settings)
        # STATUS_COLORS and STATUS_SYMBOLS are now in ColorManager
        # self.assertIn("STATUS_COLORS", settings)
        # self.assertIn("STATUS_SYMBOLS", settings)

        # DEFAULT_BORDER_COLOR is now in ColorManager
        self.assertEqual(settings["DEFAULT_BORDER_COLOR"], "WHITE")
        self.assertIsInstance(settings["STATUS_COLORS"], dict)
        self.assertIsInstance(settings["STATUS_SYMBOLS"], dict)

        # Test that we get copies, not references
        self.assertIsNot(settings["STATUS_COLORS"], ColorManager.STATUS_COLORS)
        self.assertIsNot(settings["STATUS_SYMBOLS"], ColorManager.STATUS_SYMBOLS)

    def test_get_status_color(self):
        """Test get_status_color method."""
        # Test valid statuses
        self.assertEqual(ColorManager.get_status_color("SUCCESS"), "BRIGHT_GREEN")
        self.assertEqual(ColorManager.get_status_color("FAILED"), "BRIGHT_RED")
        self.assertEqual(ColorManager.get_status_color("BUILDING"), "BRIGHT_YELLOW")
        self.assertEqual(ColorManager.get_status_color("IDLE"), "DIM")

        # Test invalid status (should return default)
        self.assertEqual(ColorManager.get_status_color("INVALID_STATUS"), "WHITE")
        self.assertEqual(ColorManager.get_status_color(""), "WHITE")

    def test_get_status_symbol(self):
        """Test get_status_symbol method."""
        # Test valid statuses
        self.assertEqual(ColorManager.get_status_symbol("SUCCESS"), "✓")
        self.assertEqual(ColorManager.get_status_symbol("FAILED"), "✗")
        self.assertEqual(ColorManager.get_status_symbol("BUILDING"), "🔨")
        self.assertEqual(ColorManager.get_status_symbol("IDLE"), "⏳")

        # Test invalid status (should return empty string)
        self.assertEqual(ColorManager.get_status_symbol("INVALID_STATUS"), "")
        self.assertEqual(ColorManager.get_status_symbol(""), "")

    def test_get_all_settings(self):
        """Test get_all_settings method."""
        all_settings = Config.get_all_settings()

        self.assertIn("build", all_settings)
        self.assertIn("ui", all_settings)
        self.assertIn("layout", all_settings)
        self.assertIn("ssh", all_settings)
        self.assertIn("output", all_settings)
        self.assertIn("logging", all_settings)
        self.assertIn("colors", all_settings)

        # Test that each category contains the expected settings
        self.assertIn("BUILD_TIMEOUT_SECONDS", all_settings["build"])
        self.assertIn("MIN_RENDER_INTERVAL_SECONDS", all_settings["ui"])
        self.assertIn("MIN_TERMINAL_HEIGHT", all_settings["layout"])
        self.assertIn("SSH_TIMEOUT_SECONDS", all_settings["ssh"])
        self.assertIn("MAX_OUTPUT_LINES_PER_HOST", all_settings["output"])
        self.assertIn("DEFAULT_LOG_LEVEL", all_settings["logging"])
        self.assertIn("DEFAULT_BORDER_COLOR", all_settings["colors"])

    def test_validate_settings(self):
        """Test validate_settings method."""
        # Test that current settings are valid
        self.assertTrue(Config.validate_settings())

    def test_get_setting(self):
        """Test get_setting method."""
        # Test valid settings
        self.assertEqual(Config.get_setting("BUILD_TIMEOUT_SECONDS"), 7200)
        self.assertEqual(Config.get_setting("BUILD_DIRECTORY"), "/tmp/build")
        self.assertEqual(Config.get_setting("SSH_TIMEOUT_SECONDS"), 30)
        # DEFAULT_BORDER_COLOR is now in ColorManager
        # self.assertEqual(Config.get_setting("DEFAULT_BORDER_COLOR"), "WHITE")

        # Test invalid setting
        with self.assertRaises(AttributeError):
            Config.get_setting("INVALID_SETTING")

        with self.assertRaises(AttributeError):
            Config.get_setting("")

    def test_list_settings(self):
        """Test list_settings method."""
        settings = Config.list_settings()

        # Test that it returns a list
        self.assertIsInstance(settings, list)

        # Test that it contains expected settings
        self.assertIn("BUILD_TIMEOUT_SECONDS", settings)
        self.assertIn("BUILD_DIRECTORY", settings)
        self.assertIn("SSH_TIMEOUT_SECONDS", settings)
        # DEFAULT_BORDER_COLOR is now in ColorManager
        # self.assertIn("DEFAULT_BORDER_COLOR", settings)
        # STATUS_COLORS is now in ColorManager
        # self.assertIn("STATUS_COLORS", settings)
        # STATUS_SYMBOLS is now in ColorManager
        # self.assertIn("STATUS_SYMBOLS", settings)

        # Test that it doesn't contain method names
        self.assertNotIn("get_build_settings", settings)
        self.assertNotIn("validate_settings", settings)
        self.assertNotIn("get_setting", settings)

        # Test that it doesn't contain private attributes
        self.assertNotIn("_private", settings)

    def test_status_colors_completeness(self):
        """Test that STATUS_COLORS contains all expected statuses."""
        expected_statuses = [
            "IDLE",
            "CONNECTING",
            "PREPARING",
            "BUILDING",
            "SUCCESS",
            "FAILED",
            "WARNING",
        ]

        for status in expected_statuses:
            self.assertIn(status, ColorManager.STATUS_COLORS)
            self.assertIsInstance(ColorManager.STATUS_COLORS[status], str)
            self.assertGreater(len(ColorManager.STATUS_COLORS[status]), 0)

    def test_status_symbols_completeness(self):
        """Test that STATUS_SYMBOLS contains all expected statuses."""
        expected_statuses = [
            "IDLE",
            "CONNECTING",
            "PREPARING",
            "BUILDING",
            "SUCCESS",
            "FAILED",
            "WARNING",
        ]

        for status in expected_statuses:
            self.assertIn(status, ColorManager.STATUS_SYMBOLS)
            self.assertIsInstance(ColorManager.STATUS_SYMBOLS[status], str)
            self.assertGreater(len(ColorManager.STATUS_SYMBOLS[status]), 0)

    def test_status_colors_symbols_consistency(self):
        """Test that STATUS_COLORS and STATUS_SYMBOLS have the same keys."""
        color_keys = set(ColorManager.STATUS_COLORS.keys())
        symbol_keys = set(ColorManager.STATUS_SYMBOLS.keys())

        self.assertEqual(color_keys, symbol_keys)

    def test_setting_types(self):
        """Test that settings have the expected types."""
        # Test numeric settings
        self.assertIsInstance(Config.BUILD_TIMEOUT_SECONDS, int)
        self.assertIsInstance(Config.MIN_RENDER_INTERVAL_SECONDS, float)
        self.assertIsInstance(Config.SSH_TIMEOUT_SECONDS, int)
        self.assertIsInstance(Config.MAX_OUTPUT_LINES_PER_HOST, int)

        # Test string settings
        self.assertIsInstance(Config.BUILD_DIRECTORY, str)
        self.assertIsInstance(Config.BUILD_SCRIPT_NAME, str)
        self.assertIsInstance(Config.LOG_FILE, str)
        self.assertIsInstance(ColorManager.DEFAULT_BORDER_COLOR, str)

        # Test dictionary settings - now in ColorManager
        self.assertIsInstance(ColorManager.STATUS_COLORS, dict)
        self.assertIsInstance(ColorManager.STATUS_SYMBOLS, dict)

        # Test logging level settings
        self.assertIsInstance(Config.DEFAULT_LOG_LEVEL, int)
        self.assertIsInstance(Config.DEBUG_LOG_LEVEL, int)

    def test_setting_values(self):
        """Test that settings have reasonable values."""
        # Test timeouts are positive
        self.assertGreater(Config.BUILD_TIMEOUT_SECONDS, 0)
        self.assertGreater(Config.SSH_TIMEOUT_SECONDS, 0)
        self.assertGreater(Config.MIN_RENDER_INTERVAL_SECONDS, 0)
        self.assertGreater(Config.TIMER_UPDATE_INTERVAL_SECONDS, 0)

        # Test dimensions are positive
        self.assertGreater(Config.MIN_TERMINAL_HEIGHT, 0)
        self.assertGreater(Config.MIN_HOST_HEIGHT, 0)
        self.assertGreater(Config.HEADER_HEIGHT, 0)
        self.assertGreater(Config.FOOTER_HEIGHT, 0)
        self.assertGreater(Config.TERMINAL_MARGIN, 0)
        self.assertGreater(Config.BORDER_PADDING, 0)

        # Test buffer settings are reasonable
        self.assertGreater(Config.MAX_OUTPUT_LINES_PER_HOST, 0)
        self.assertGreaterEqual(Config.OUTPUT_BUFFER_OVERFLOW_MARGIN, 0)

        # Test retry count is positive
        self.assertGreater(Config.SSH_CONNECTION_RETRIES, 0)

        # Test file transfer settings are reasonable
        self.assertGreater(Config.SFTP_CHUNK_SIZE, 0)

    def test_logging_levels(self):
        """Test that logging levels are valid."""
        valid_levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]

        self.assertIn(Config.DEFAULT_LOG_LEVEL, valid_levels)
        self.assertIn(Config.DEBUG_LOG_LEVEL, valid_levels)

        # Debug level should be lower than or equal to default level
        self.assertLessEqual(Config.DEBUG_LOG_LEVEL, Config.DEFAULT_LOG_LEVEL)


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for Config class."""

    def test_settings_consistency(self):
        """Test that all settings are consistent and complete."""
        all_settings = Config.get_all_settings()

        # Test that all categories are present
        expected_categories = [
            "build",
            "ui",
            "layout",
            "ssh",
            "output",
            "logging",
            "colors",
        ]
        for category in expected_categories:
            self.assertIn(category, all_settings)
            self.assertIsInstance(all_settings[category], dict)
            self.assertGreater(len(all_settings[category]), 0)

    def test_settings_accessibility(self):
        """Test that all settings can be accessed through different methods."""
        # Test direct access
        direct_settings = {
            "BUILD_TIMEOUT_SECONDS": Config.BUILD_TIMEOUT_SECONDS,
            "SSH_TIMEOUT_SECONDS": Config.SSH_TIMEOUT_SECONDS,
            "DEFAULT_BORDER_COLOR": ColorManager.DEFAULT_BORDER_COLOR,
        }

        # Test get_setting method
        for name, value in direct_settings.items():
            if name == "DEFAULT_BORDER_COLOR":
                # Skip this as it's now in ColorManager
                continue
            self.assertEqual(Config.get_setting(name), value)

        # Test category methods
        build_settings = Config.get_build_settings()
        self.assertEqual(
            build_settings["BUILD_TIMEOUT_SECONDS"], Config.BUILD_TIMEOUT_SECONDS
        )

        ssh_settings = Config.get_ssh_settings()
        self.assertEqual(
            ssh_settings["SSH_TIMEOUT_SECONDS"], Config.SSH_TIMEOUT_SECONDS
        )

    def test_status_mapping_consistency(self):
        """Test that status colors and symbols are consistent."""
        # Test that all status colors have corresponding symbols
        for status in ColorManager.STATUS_COLORS:
            self.assertIn(status, ColorManager.STATUS_SYMBOLS)
            color = ColorManager.get_status_color(status)
            symbol = ColorManager.get_status_symbol(status)

            # Color should be a string
            self.assertIsInstance(color, str)
            self.assertGreater(len(color), 0)

            # Symbol should be a string
            self.assertIsInstance(symbol, str)
            self.assertGreater(len(symbol), 0)


if __name__ == "__main__":
    unittest.main()
