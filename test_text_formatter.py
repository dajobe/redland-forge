#!/usr/bin/python3
"""
Unit tests for text_formatter.py
"""

import unittest

from text_formatter import visual_length, TextFormatter, format_duration


class TestFormatDuration(unittest.TestCase):
    """Test format_duration function."""

    def test_seconds_only(self):
        """Test formatting seconds only."""
        self.assertEqual(format_duration(5), "5s")
        self.assertEqual(format_duration(30.4), "30s")
        self.assertEqual(format_duration(59.4), "59s")  # Rounds down
        self.assertEqual(format_duration(59.6), "1m")  # Rounds up to 60s = 1m

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        self.assertEqual(format_duration(90), "1m30s")
        self.assertEqual(format_duration(125.3), "2m5s")
        self.assertEqual(format_duration(120), "2m")  # No remaining seconds
        self.assertEqual(format_duration(3599), "59m59s")

    def test_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        self.assertEqual(format_duration(3600), "1h")  # Exactly 1 hour
        self.assertEqual(format_duration(3661), "1h1m")  # 1 hour 1 minute 1 second
        self.assertEqual(format_duration(7200), "2h")  # Exactly 2 hours
        self.assertEqual(format_duration(7320), "2h2m")  # 2 hours 2 minutes

    def test_rounding(self):
        """Test proper rounding of time values."""
        self.assertEqual(format_duration(29.4), "29s")
        self.assertEqual(format_duration(29.6), "30s")
        self.assertEqual(format_duration(119.4), "1m59s")
        self.assertEqual(format_duration(119.6), "2m")

    def test_edge_cases(self):
        """Test edge cases."""
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(0.4), "0s")
        self.assertEqual(format_duration(0.6), "1s")


if __name__ == "__main__":
    unittest.main()
