#!/usr/bin/python3
"""
Unit tests for ProgressDisplayManager
"""

import unittest
import time
from unittest.mock import Mock, MagicMock
from redland_forge.progress_display_manager import ProgressDisplayManager


class TestProgressDisplayManager(unittest.TestCase):
    """Test cases for ProgressDisplayManager"""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_timing_cache = Mock()
        self.progress_manager = ProgressDisplayManager(self.mock_timing_cache)

    def test_initialization(self):
        """Test ProgressDisplayManager initialization."""
        self.assertEqual(self.progress_manager.timing_cache, self.mock_timing_cache)
        self.assertEqual(self.progress_manager.build_start_times, {})
        self.assertEqual(self.progress_manager.build_steps, {})

    def test_start_build_tracking(self):
        """Test starting build tracking for a host."""
        host_name = "test-host"

        # Mock time.time to return a fixed timestamp
        with unittest.mock.patch("time.time", return_value=1000.0):
            self.progress_manager.start_build_tracking(host_name)

        self.assertIn(host_name, self.progress_manager.build_start_times)
        self.assertEqual(self.progress_manager.build_start_times[host_name], 1000.0)
        self.assertIn(host_name, self.progress_manager.build_steps)
        self.assertEqual(self.progress_manager.build_steps[host_name], "extract")

    def test_update_build_step(self):
        """Test updating build step for a host."""
        host_name = "test-host"
        self.progress_manager.build_steps[host_name] = "extract"

        self.progress_manager.update_build_step(host_name, "configure")
        self.assertEqual(self.progress_manager.build_steps[host_name], "configure")

    def test_update_build_step_unknown_host(self):
        """Test updating build step for unknown host."""
        host_name = "unknown-host"

        # Should not raise an error
        self.progress_manager.update_build_step(host_name, "configure")
        self.assertNotIn(host_name, self.progress_manager.build_steps)

    def test_get_progress_display_no_tracking(self):
        """Test getting progress display for untracked host."""
        host_name = "untracked-host"
        result = self.progress_manager.get_progress_display(host_name)
        self.assertIsNone(result)

    def test_get_progress_display_with_progress(self):
        """Test getting progress display with available progress."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 10.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache to return progress
        self.mock_timing_cache.get_progress_estimate.return_value = "25.5%"

        result = self.progress_manager.get_progress_display(host_name)
        self.assertEqual(result, "Progress: 25.5%")

        # Verify timing cache was called correctly
        self.mock_timing_cache.get_progress_estimate.assert_called_once()
        call_args = self.mock_timing_cache.get_progress_estimate.call_args
        self.assertEqual(call_args[0][0], host_name)  # host_name
        self.assertEqual(call_args[0][1], "configure")  # current_step

    def test_get_progress_display_no_progress(self):
        """Test getting progress display when no progress available."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 10.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache to return None
        self.mock_timing_cache.get_progress_estimate.return_value = None

        result = self.progress_manager.get_progress_display(host_name)
        self.assertIsNone(result)

    def test_get_time_estimate_no_tracking(self):
        """Test getting time estimate for untracked host."""
        host_name = "untracked-host"
        result = self.progress_manager.get_time_estimate(host_name)
        self.assertIsNone(result)

    def test_get_time_estimate_extract_step(self):
        """Test getting time estimate for extract step."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 2.0
        self.progress_manager.build_steps[host_name] = "extract"

        # Mock host statistics for extract step
        mock_stats = {
            "average_times": {"configure": 10.0, "make": 30.0, "make_check": 60.0}
        }
        self.mock_timing_cache.get_host_statistics.return_value = mock_stats

        result = self.progress_manager.get_time_estimate(host_name)
        self.assertEqual(result, "ETA: 5s")

    def test_get_time_estimate_configure_step(self):
        """Test getting time estimate for configure step."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 5.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock host statistics
        mock_stats = {
            "average_times": {"configure": 10.0, "make": 30.0, "make_check": 60.0}
        }
        self.mock_timing_cache.get_host_statistics.return_value = mock_stats

        result = self.progress_manager.get_time_estimate(host_name)
        self.assertEqual(result, "ETA: 1m35s")  # 30 + 60 + (10 - 5) = 95s

    def test_get_time_estimate_make_step(self):
        """Test getting time estimate for make step."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 35.0
        self.progress_manager.build_steps[host_name] = "make"

        # Mock host statistics
        mock_stats = {
            "average_times": {"configure": 10.0, "make": 30.0, "make_check": 60.0}
        }
        self.mock_timing_cache.get_host_statistics.return_value = mock_stats

        result = self.progress_manager.get_time_estimate(host_name)
        self.assertEqual(
            result, "ETA: 1m"
        )  # 60 (make_check only, since we're past make time)

    def test_get_time_estimate_check_step(self):
        """Test getting time estimate for check step."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 100.0
        self.progress_manager.build_steps[host_name] = "check"

        # Mock host statistics for check step
        mock_stats = {
            "average_times": {"configure": 10.0, "make": 30.0, "make_check": 60.0}
        }
        self.mock_timing_cache.get_host_statistics.return_value = mock_stats

        result = self.progress_manager.get_time_estimate(host_name)
        self.assertIsNone(result)  # Check is last step

    def test_get_time_estimate_no_statistics(self):
        """Test getting time estimate when no statistics available."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 5.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache to return None
        self.mock_timing_cache.get_host_statistics.return_value = None

        result = self.progress_manager.get_time_estimate(host_name)
        self.assertIsNone(result)

    def test_get_detailed_progress(self):
        """Test getting detailed progress information."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 15.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache responses
        self.mock_timing_cache.get_progress_estimate.return_value = "30.2%"

        mock_stats = {
            "average_times": {"configure": 20.0, "make": 40.0, "make_check": 80.0}
        }
        self.mock_timing_cache.get_host_statistics.return_value = mock_stats

        result = self.progress_manager.get_detailed_progress(host_name)

        # Should contain step, progress, ETA, and elapsed time
        self.assertIn("Step: configure", result)
        self.assertIn("Progress: 30.2%", result)
        self.assertIn("ETA:", result)
        self.assertIn("Elapsed: 15s", result)

    def test_get_detailed_progress_no_progress(self):
        """Test getting detailed progress when no progress available."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 15.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache to return None for progress
        self.mock_timing_cache.get_progress_estimate.return_value = None
        self.mock_timing_cache.get_host_statistics.return_value = None

        result = self.progress_manager.get_detailed_progress(host_name)

        # Should only contain step and elapsed time
        self.assertIn("Step: configure", result)
        self.assertIn("Elapsed: 15s", result)
        self.assertNotIn("Progress:", result)
        self.assertNotIn("ETA:", result)

    def test_complete_build_tracking(self):
        """Test completing build tracking for a host."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time()
        self.progress_manager.build_steps[host_name] = "configure"

        self.progress_manager.complete_build_tracking(host_name)

        self.assertNotIn(host_name, self.progress_manager.build_start_times)
        self.assertNotIn(host_name, self.progress_manager.build_steps)

    def test_get_active_builds(self):
        """Test getting information about active builds."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time() - 10.0
        self.progress_manager.build_steps[host_name] = "configure"

        # Mock timing cache responses
        self.mock_timing_cache.get_progress_estimate.return_value = "25.0%"
        self.mock_timing_cache.get_host_statistics.return_value = {
            "average_times": {"configure": 20.0, "make": 40.0, "make_check": 80.0}
        }

        active_builds = self.progress_manager.get_active_builds()

        self.assertIn(host_name, active_builds)
        build_info = active_builds[host_name]

        self.assertEqual(build_info["step"], "configure")
        self.assertAlmostEqual(build_info["elapsed_time"], 10.0, places=1)
        self.assertEqual(build_info["progress"], "Progress: 25.0%")
        self.assertIsNotNone(build_info["time_estimate"])
        self.assertIsNotNone(build_info["detailed_progress"])

    def test_get_active_builds_empty(self):
        """Test getting active builds when none are tracked."""
        active_builds = self.progress_manager.get_active_builds()
        self.assertEqual(active_builds, {})

    def test_cleanup(self):
        """Test cleanup method."""
        host_name = "test-host"
        self.progress_manager.build_start_times[host_name] = time.time()
        self.progress_manager.build_steps[host_name] = "configure"

        self.progress_manager.cleanup()

        self.assertEqual(self.progress_manager.build_start_times, {})
        self.assertEqual(self.progress_manager.build_steps, {})

    def test_multiple_hosts_tracking(self):
        """Test tracking multiple hosts simultaneously."""
        host1 = "host1"
        host2 = "host2"

        # Start tracking both hosts
        with unittest.mock.patch("time.time", return_value=1000.0):
            self.progress_manager.start_build_tracking(host1)
            self.progress_manager.start_build_tracking(host2)

        # Update steps for both hosts
        self.progress_manager.update_build_step(host1, "configure")
        self.progress_manager.update_build_step(host2, "make")

        # Verify both are tracked
        self.assertIn(host1, self.progress_manager.build_start_times)
        self.assertIn(host2, self.progress_manager.build_start_times)
        self.assertEqual(self.progress_manager.build_steps[host1], "configure")
        self.assertEqual(self.progress_manager.build_steps[host2], "make")

        # Complete one host
        self.progress_manager.complete_build_tracking(host1)

        # Verify host1 is removed but host2 remains
        self.assertNotIn(host1, self.progress_manager.build_start_times)
        self.assertIn(host2, self.progress_manager.build_start_times)


if __name__ == "__main__":
    unittest.main()
