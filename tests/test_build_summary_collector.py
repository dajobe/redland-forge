#!/usr/bin/python3
"""
Tests for BuildSummaryCollector class.
"""

import time
import unittest
from unittest.mock import patch
from redland_forge.build_summary_collector import BuildSummaryCollector, BuildResult


class TestBuildSummaryCollector(unittest.TestCase):
    """Test cases for BuildSummaryCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = BuildSummaryCollector()

    def test_initialization(self):
        """Test BuildSummaryCollector initialization."""
        self.assertEqual(len(self.collector.host_results), 0)
        self.assertEqual(len(self.collector.host_start_times), 0)
        self.assertGreater(self.collector.build_start_time, 0)

    def test_start_build_tracking(self):
        """Test starting build tracking for a host."""
        self.collector.start_build_tracking("test-host")
        self.assertIn("test-host", self.collector.host_start_times)
        self.assertGreater(self.collector.host_start_times["test-host"], 0)

    def test_stop_build_tracking(self):
        """Test stopping build tracking for a host."""
        self.collector.start_build_tracking("test-host")
        self.assertIn("test-host", self.collector.host_start_times)

        self.collector.stop_build_tracking("test-host")
        self.assertNotIn("test-host", self.collector.host_start_times)

        # Test stopping non-existent host (should not crash)
        self.collector.stop_build_tracking("non-existent-host")

    def test_record_build_result_success(self):
        """Test recording a successful build result."""
        self.collector.start_build_tracking("test-host")
        time.sleep(0.1)  # Small delay to ensure different timestamps

        self.collector.record_build_result(
            host_name="test-host", success=True, configure_time=10.5, make_time=45.2
        )

        result = self.collector.get_build_result("test-host")
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.configure_time, 10.5)
        self.assertEqual(result.make_time, 45.2)
        self.assertIsNotNone(result.total_time)
        self.assertGreater(result.total_time, 0)

    def test_record_build_result_failure(self):
        """Test recording a failed build result."""
        self.collector.start_build_tracking("test-host")

        self.collector.record_build_result(
            host_name="test-host",
            success=False,
            error_message="Build failed during make step",
        )

        result = self.collector.get_build_result("test-host")
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Build failed during make step")

    def test_get_all_results(self):
        """Test getting all build results."""
        self.collector.start_build_tracking("host1")
        self.collector.record_build_result("host1", True)

        self.collector.start_build_tracking("host2")
        self.collector.record_build_result("host2", False)

        all_results = self.collector.get_all_results()
        self.assertEqual(len(all_results), 2)
        self.assertIn("host1", all_results)
        self.assertIn("host2", all_results)

    def test_get_successful_builds(self):
        """Test getting only successful builds."""
        self.collector.start_build_tracking("host1")
        self.collector.record_build_result("host1", True)

        self.collector.start_build_tracking("host2")
        self.collector.record_build_result("host2", False)

        successful = self.collector.get_successful_builds()
        self.assertEqual(len(successful), 1)
        self.assertEqual(successful[0].host_name, "host1")

    def test_get_failed_builds(self):
        """Test getting only failed builds."""
        self.collector.start_build_tracking("host1")
        self.collector.record_build_result("host1", True)

        self.collector.start_build_tracking("host2")
        self.collector.record_build_result("host2", False)

        failed = self.collector.get_failed_builds()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].host_name, "host2")

    def test_get_total_build_time(self):
        """Test getting total build time."""
        initial_time = self.collector.get_total_build_time()
        self.assertGreaterEqual(initial_time, 0)

        time.sleep(0.1)
        later_time = self.collector.get_total_build_time()
        self.assertGreater(later_time, initial_time)

    def test_format_duration(self):
        """Test duration formatting."""
        # Test None case
        self.assertEqual(self.collector._format_duration(None), "unknown")

        # Test seconds (now using whole seconds)
        self.assertEqual(self.collector._format_duration(30.6), "31s")

        # Test minutes (now without spaces)
        self.assertEqual(self.collector._format_duration(90), "1m30s")
        self.assertEqual(self.collector._format_duration(120), "2m")

        # Test hours (now without spaces)
        self.assertEqual(self.collector._format_duration(3661), "1h1m")
        self.assertEqual(self.collector._format_duration(7200), "2h")

    def test_generate_summary_no_builds(self):
        """Test summary generation with no builds."""
        summary = self.collector.generate_summary()
        self.assertIn("BUILD SUMMARY", summary)
        self.assertIn("No builds completed", summary)

    def test_generate_summary_with_builds(self):
        """Test summary generation with builds."""
        self.collector.start_build_tracking("host1")
        self.collector.record_build_result("host1", True)

        self.collector.start_build_tracking("host2")
        self.collector.record_build_result("host2", False, error_message="Test error")

        summary = self.collector.generate_summary()
        self.assertIn("BUILD SUMMARY", summary)
        self.assertIn("host1", summary)
        self.assertIn("host2", summary)
        self.assertIn("SUCCESS", summary)
        self.assertIn("FAILED", summary)
        self.assertIn("Overall: 1/2 builds successful", summary)

    def test_get_statistics_summary(self):
        """Test getting statistics summary."""
        self.collector.start_build_tracking("host1")
        self.collector.record_build_result("host1", True)

        self.collector.start_build_tracking("host2")
        self.collector.record_build_result("host2", False)

        stats = self.collector.get_statistics_summary()
        self.assertEqual(stats["total_builds"], 2)
        self.assertEqual(stats["successful_builds"], 1)
        self.assertEqual(stats["failed_builds"], 1)
        self.assertEqual(stats["success_rate"], 50.0)
        self.assertIn("host1", stats["hosts"])
        self.assertIn("host2", stats["hosts"])

    def test_print_summary(self):
        """Test printing summary to stdout."""
        self.collector.start_build_tracking("test-host")
        self.collector.record_build_result("test-host", True)

        # Mock print to capture output
        with patch("builtins.print") as mock_print:
            self.collector.print_summary()
            mock_print.assert_called_once()
            # Verify the summary content
            summary_arg = mock_print.call_args[0][0]
            self.assertIn("BUILD SUMMARY", summary_arg)
            self.assertIn("test-host", summary_arg)
            self.assertIn("SUCCESS", summary_arg)


if __name__ == "__main__":
    unittest.main()
