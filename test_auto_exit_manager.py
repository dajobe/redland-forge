#!/usr/bin/python3
"""
Tests for AutoExitManager class.
"""

import time
import unittest
from unittest.mock import Mock, patch
from auto_exit_manager import AutoExitManager


class TestAutoExitManager(unittest.TestCase):
    """Test cases for AutoExitManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.auto_exit_manager = AutoExitManager(exit_delay_seconds=10, enabled=True)

    def test_initialization(self):
        """Test AutoExitManager initialization."""
        self.assertEqual(self.auto_exit_manager.exit_delay_seconds, 10)
        self.assertTrue(self.auto_exit_manager.enabled)
        self.assertIsNone(self.auto_exit_manager.last_build_completion_time)
        self.assertIsNone(self.auto_exit_manager.exit_timer)
        self.assertFalse(self.auto_exit_manager.is_exiting)

    def test_disabled_auto_exit(self):
        """Test that disabled auto-exit doesn't schedule exit."""
        disabled_manager = AutoExitManager(exit_delay_seconds=1, enabled=False)
        disabled_manager.on_build_completed("test-host", True)
        self.assertIsNone(disabled_manager.exit_timer)

    def test_build_completion_schedules_exit(self):
        """Test that build completion schedules auto-exit."""
        self.auto_exit_manager.on_build_completed("test-host", True)
        self.assertIsNotNone(self.auto_exit_manager.exit_timer)
        self.assertIsNotNone(self.auto_exit_manager.last_build_completion_time)

    def test_multiple_builds_reset_timer(self):
        """Test that multiple build completions reset the timer."""
        self.auto_exit_manager.on_build_completed("host1", True)
        first_timer = self.auto_exit_manager.exit_timer

        time.sleep(0.1)  # Small delay

        self.auto_exit_manager.on_build_completed("host2", False)
        second_timer = self.auto_exit_manager.exit_timer

        # Should be different timer objects
        self.assertIsNot(first_timer, second_timer)

    def test_cancel_exit(self):
        """Test canceling the scheduled exit."""
        self.auto_exit_manager.on_build_completed("test-host", True)
        self.assertIsNotNone(self.auto_exit_manager.exit_timer)

        self.auto_exit_manager.cancel_exit()
        self.assertIsNone(self.auto_exit_manager.exit_timer)

    def test_get_remaining_time(self):
        """Test getting remaining time until exit."""
        self.auto_exit_manager.on_build_completed("test-host", True)
        remaining = self.auto_exit_manager.get_remaining_time()
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, 10)

    def test_get_countdown_display(self):
        """Test countdown display formatting."""
        self.auto_exit_manager.on_build_completed("test-host", True)
        countdown = self.auto_exit_manager.get_countdown_display()
        self.assertIsNotNone(countdown)
        self.assertIn("Auto-exit in", countdown)

    def test_is_countdown_active(self):
        """Test countdown active state."""
        self.assertFalse(self.auto_exit_manager.is_countdown_active())

        self.auto_exit_manager.on_build_completed("test-host", True)
        self.assertTrue(self.auto_exit_manager.is_countdown_active())

    def test_exit_callback(self):
        """Test that exit callback is called."""
        mock_callback = Mock()
        self.auto_exit_manager.set_exit_callback(mock_callback)

        # Manually trigger exit
        self.auto_exit_manager._perform_exit()
        mock_callback.assert_called_once()

    def test_cleanup(self):
        """Test cleanup method."""
        self.auto_exit_manager.on_build_completed("test-host", True)
        self.assertIsNotNone(self.auto_exit_manager.exit_timer)

        self.auto_exit_manager.cleanup()
        self.assertIsNone(self.auto_exit_manager.exit_timer)

    def test_exit_callback_error_handling(self):
        """Test error handling in exit callback."""

        def failing_callback():
            raise Exception("Test error")

        self.auto_exit_manager.set_exit_callback(failing_callback)

        # Should not raise exception
        self.auto_exit_manager._perform_exit()
        self.assertTrue(self.auto_exit_manager.is_exiting)


if __name__ == "__main__":
    unittest.main()
