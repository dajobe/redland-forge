#!/usr/bin/env python3
"""
Test the new config-based color system.
"""

import unittest
from color_manager import ColorManager


class TestColorSystem(unittest.TestCase):
    """Test the new config-based color system."""

    def test_ansi_colors_exist(self):
        """Test that all expected ANSI colors are defined."""
        expected_colors = [
            "RESET",
            "BLACK",
            "RED",
            "GREEN",
            "YELLOW",
            "BLUE",
            "MAGENTA",
            "CYAN",
            "WHITE",
            "BRIGHT_RED",
            "BRIGHT_GREEN",
            "BRIGHT_YELLOW",
            "BRIGHT_BLUE",
            "BRIGHT_MAGENTA",
            "BRIGHT_CYAN",
            "BG_RED",
            "BG_GREEN",
            "BG_YELLOW",
            "BG_BLUE",
            "BOLD",
            "DIM",
            "ITALIC",
            "UNDERLINE",
        ]

        for color in expected_colors:
            self.assertIn(color, ColorManager.ANSI_COLORS)
            self.assertIsInstance(ColorManager.ANSI_COLORS[color], str)
            self.assertTrue(ColorManager.ANSI_COLORS[color].startswith("\033["))

    def test_get_ansi_color(self):
        """Test get_ansi_color method."""
                # Test valid colors
        self.assertEqual(ColorManager.get_ansi_color("RED"), "\033[31m")
        self.assertEqual(ColorManager.get_ansi_color("BRIGHT_GREEN"), "\033[92m")
        self.assertEqual(ColorManager.get_ansi_color("RESET"), "\033[0m")
        
        # Test invalid color (should return RESET)
        self.assertEqual(ColorManager.get_ansi_color("INVALID_COLOR"), "\033[0m")

    def test_get_status_ansi_color(self):
        """Test get_status_ansi_color method."""
        # Test valid statuses
        self.assertEqual(
            ColorManager.get_status_ansi_color("SUCCESS"), "\033[92m"
        )  # BRIGHT_GREEN
        self.assertEqual(
            ColorManager.get_status_ansi_color("FAILED"), "\033[91m"
        )  # BRIGHT_RED
        self.assertEqual(ColorManager.get_status_ansi_color("IDLE"), "\033[2m")  # DIM

        # Test invalid status (should return default border color)
        self.assertEqual(
            ColorManager.get_status_ansi_color("INVALID_STATUS"), "\033[37m"
        )  # WHITE

    def test_colorize(self):
        """Test colorize method."""
        # Force color mode for testing
        ColorManager.set_color_mode("always")
        
        # Test basic colorization
        result = ColorManager.colorize("Hello", "RED")
        self.assertEqual(result, "\033[31mHello\033[0m")
        
        # Test with bright color
        result = ColorManager.colorize("World", "BRIGHT_CYAN")
        self.assertEqual(result, "\033[96mWorld\033[0m")
        
        # Test with invalid color (should use RESET)
        result = ColorManager.colorize("Test", "INVALID")
        self.assertEqual(result, "\033[0mTest\033[0m")
        
        # Reset to auto mode
        ColorManager.set_color_mode("auto")

    def test_status_colors_consistency(self):
        """Test that status colors are consistent."""
        # All status colors should map to valid ANSI colors
        for status, color_name in ColorManager.STATUS_COLORS.items():
            self.assertIn(color_name, ColorManager.ANSI_COLORS)
            ansi_code = ColorManager.get_ansi_color(color_name)
            self.assertTrue(ansi_code.startswith("\033["))

    def test_color_settings_inclusion(self):
        """Test that color settings include ANSI_COLORS."""
        color_settings = ColorManager.get_color_settings()
        self.assertIn("ANSI_COLORS", color_settings)
        self.assertIsInstance(color_settings["ANSI_COLORS"], dict)
        self.assertEqual(len(color_settings["ANSI_COLORS"]), len(ColorManager.ANSI_COLORS))


if __name__ == "__main__":
    unittest.main()
