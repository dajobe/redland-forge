#!/usr/bin/python3
"""
Unit tests for StatisticsManager class.
"""

import unittest
from unittest.mock import Mock

from statistics_manager import StatisticsManager


class TestStatisticsManagerInitialization(unittest.TestCase):
    """Test StatisticsManager initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        hosts = ["host1", "host2", "host3"]
        manager = StatisticsManager(hosts)
        self.assertEqual(manager.all_hosts, hosts)

    def test_init_empty_hosts(self):
        """Test initialization with empty hosts list."""
        manager = StatisticsManager([])
        self.assertEqual(manager.all_hosts, [])

    def test_init_single_host(self):
        """Test initialization with single host."""
        hosts = ["single-host"]
        manager = StatisticsManager(hosts)
        self.assertEqual(manager.all_hosts, hosts)


class TestStatisticsManagerBasicStatistics(unittest.TestCase):
    """Test basic statistics calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3", "host4"]
        self.manager = StatisticsManager(self.hosts)

    def test_calculate_statistics_empty_results(self):
        """Test statistics calculation with empty results."""
        host_sections = {"host1": Mock(), "host2": Mock()}
        ssh_results = {}

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["total_completed"], 0)
        self.assertEqual(stats["overall_progress"], 0.0)
        self.assertEqual(stats["total_hosts"], 4)
        self.assertEqual(stats["visible_hosts"], 2)
        self.assertEqual(stats["processed_hosts"], 0)

    def test_calculate_statistics_all_success(self):
        """Test statistics calculation with all hosts successful."""
        host_sections = {
            "host1": Mock(),
            "host2": Mock(),
            "host3": Mock(),
            "host4": Mock(),
        }
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "SUCCESS"},
            "host3": {"status": "SUCCESS"},
            "host4": {"status": "SUCCESS"},
        }

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["completed"], 4)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["total_completed"], 4)
        self.assertEqual(stats["overall_progress"], 100.0)
        self.assertEqual(stats["total_hosts"], 4)
        self.assertEqual(stats["visible_hosts"], 4)
        self.assertEqual(stats["processed_hosts"], 4)

    def test_calculate_statistics_mixed_statuses(self):
        """Test statistics calculation with mixed statuses."""
        host_sections = {"host1": Mock(), "host2": Mock(), "host3": Mock()}
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "FAILED"},
            "host3": {"status": "BUILDING"},
        }

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 1)  # host3 is BUILDING
        self.assertEqual(stats["completed"], 1)  # host1
        self.assertEqual(stats["failed"], 1)  # host2
        self.assertEqual(stats["total_completed"], 2)
        self.assertEqual(stats["overall_progress"], 50.0)  # 2/4 hosts completed
        self.assertEqual(stats["total_hosts"], 4)
        self.assertEqual(stats["visible_hosts"], 3)
        self.assertEqual(stats["processed_hosts"], 3)

    def test_calculate_statistics_partial_visibility(self):
        """Test statistics calculation with partial host visibility."""
        host_sections = {"host1": Mock(), "host2": Mock()}  # Only 2 visible
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "BUILDING"},
            "host3": {"status": "FAILED"},  # Not visible
            "host4": {"status": "SUCCESS"},  # Not visible
        }

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 1)  # Only host2 (visible and BUILDING)
        self.assertEqual(stats["completed"], 2)  # host1 and host4
        self.assertEqual(stats["failed"], 1)  # host3
        self.assertEqual(stats["total_completed"], 3)
        self.assertEqual(stats["overall_progress"], 75.0)  # 3/4 hosts completed
        self.assertEqual(stats["total_hosts"], 4)
        self.assertEqual(stats["visible_hosts"], 2)
        self.assertEqual(stats["processed_hosts"], 4)

    def test_calculate_statistics_active_statuses(self):
        """Test statistics calculation with various active statuses."""
        host_sections = {"host1": Mock(), "host2": Mock(), "host3": Mock()}
        ssh_results = {
            "host1": {"status": "CONNECTING"},
            "host2": {"status": "PREPARING"},
            "host3": {"status": "BUILDING"},
        }

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 3)  # All three are active
        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["total_completed"], 0)
        self.assertEqual(stats["overall_progress"], 0.0)
        self.assertEqual(stats["total_hosts"], 4)
        self.assertEqual(stats["visible_hosts"], 3)
        self.assertEqual(stats["processed_hosts"], 3)

    def test_calculate_statistics_zero_total_hosts(self):
        """Test statistics calculation with zero total hosts."""
        manager = StatisticsManager([])
        host_sections = {}
        ssh_results = {}

        stats = manager.calculate_statistics(host_sections, ssh_results)

        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["total_completed"], 0)
        self.assertEqual(
            stats["overall_progress"], 0.0
        )  # Should handle division by zero
        self.assertEqual(stats["total_hosts"], 0)
        self.assertEqual(stats["visible_hosts"], 0)
        self.assertEqual(stats["processed_hosts"], 0)


class TestStatisticsManagerUtilityMethods(unittest.TestCase):
    """Test utility methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3"]
        self.manager = StatisticsManager(self.hosts)

    def test_get_status_summary(self):
        """Test status summary generation."""
        stats = {"active": 1, "completed": 2, "failed": 0}

        summary = self.manager.get_status_summary(stats)
        expected = "Global Status: 1 active, 2 completed, 0 failed"
        self.assertEqual(summary, expected)

    def test_get_progress_summary(self):
        """Test progress summary generation."""
        stats = {"overall_progress": 66.666666, "total_completed": 2, "total_hosts": 3}

        summary = self.manager.get_progress_summary(stats)
        expected = "Visible Progress: 66.7% (2/3)"
        self.assertEqual(summary, expected)

    def test_get_host_status_breakdown(self):
        """Test host status breakdown."""
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "FAILED"},
            "host3": {"status": "BUILDING"},
            "host4": {"status": "SUCCESS"},
        }

        breakdown = self.manager.get_host_status_breakdown(ssh_results)

        expected = {"SUCCESS": 2, "FAILED": 1, "BUILDING": 1}
        self.assertEqual(breakdown, expected)

    def test_get_host_status_breakdown_with_unknown(self):
        """Test host status breakdown with unknown status."""
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "UNKNOWN_STATUS"},
            "host3": {},  # No status key
        }

        breakdown = self.manager.get_host_status_breakdown(ssh_results)

        expected = {"SUCCESS": 1, "UNKNOWN_STATUS": 1, "UNKNOWN": 1}
        self.assertEqual(breakdown, expected)

    def test_get_visible_host_status_breakdown(self):
        """Test visible host status breakdown."""
        host_sections = {"host1": Mock(), "host2": Mock()}
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "BUILDING"},
            "host3": {"status": "FAILED"},  # Not visible
        }

        breakdown = self.manager.get_visible_host_status_breakdown(
            host_sections, ssh_results
        )

        expected = {"SUCCESS": 1, "BUILDING": 1}
        self.assertEqual(breakdown, expected)

    def test_get_visible_host_status_breakdown_with_missing_results(self):
        """Test visible host status breakdown with missing results."""
        host_sections = {"host1": Mock(), "host2": Mock()}
        ssh_results = {
            "host1": {"status": "SUCCESS"}
            # host2 not in results
        }

        breakdown = self.manager.get_visible_host_status_breakdown(
            host_sections, ssh_results
        )

        expected = {"SUCCESS": 1, "UNKNOWN": 1}
        self.assertEqual(breakdown, expected)


class TestStatisticsManagerCompletionMethods(unittest.TestCase):
    """Test completion-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3"]
        self.manager = StatisticsManager(self.hosts)

    def test_is_build_complete_true(self):
        """Test build completion check when complete."""
        stats = {"total_completed": 3, "total_hosts": 3}

        self.assertTrue(self.manager.is_build_complete(stats))

    def test_is_build_complete_false(self):
        """Test build completion check when not complete."""
        stats = {"total_completed": 2, "total_hosts": 3}

        self.assertFalse(self.manager.is_build_complete(stats))

    def test_is_build_complete_over_complete(self):
        """Test build completion check when over complete."""
        stats = {"total_completed": 4, "total_hosts": 3}

        self.assertTrue(self.manager.is_build_complete(stats))

    def test_get_completion_percentage(self):
        """Test completion percentage calculation."""
        stats = {"overall_progress": 75.5}

        self.assertEqual(self.manager.get_completion_percentage(stats), 75.5)

    def test_get_remaining_hosts(self):
        """Test remaining hosts calculation."""
        stats = {"total_hosts": 5, "total_completed": 3}

        self.assertEqual(self.manager.get_remaining_hosts(stats), 2)

    def test_get_remaining_hosts_zero(self):
        """Test remaining hosts calculation when complete."""
        stats = {"total_hosts": 3, "total_completed": 3}

        self.assertEqual(self.manager.get_remaining_hosts(stats), 0)

    def test_get_remaining_hosts_negative(self):
        """Test remaining hosts calculation when over complete."""
        stats = {"total_hosts": 3, "total_completed": 5}

        self.assertEqual(self.manager.get_remaining_hosts(stats), -2)


class TestStatisticsManagerRateCalculations(unittest.TestCase):
    """Test rate calculation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3"]
        self.manager = StatisticsManager(self.hosts)

    def test_get_success_rate(self):
        """Test success rate calculation."""
        stats = {"completed": 8, "total_completed": 10}

        self.assertEqual(self.manager.get_success_rate(stats), 80.0)

    def test_get_success_rate_zero_completed(self):
        """Test success rate calculation with zero completed."""
        stats = {"completed": 0, "total_completed": 0}

        self.assertEqual(self.manager.get_success_rate(stats), 0.0)

    def test_get_success_rate_perfect(self):
        """Test success rate calculation with perfect success."""
        stats = {"completed": 5, "total_completed": 5}

        self.assertEqual(self.manager.get_success_rate(stats), 100.0)

    def test_get_failure_rate(self):
        """Test failure rate calculation."""
        stats = {"failed": 2, "total_completed": 10}

        self.assertEqual(self.manager.get_failure_rate(stats), 20.0)

    def test_get_failure_rate_zero_completed(self):
        """Test failure rate calculation with zero completed."""
        stats = {"failed": 0, "total_completed": 0}

        self.assertEqual(self.manager.get_failure_rate(stats), 0.0)

    def test_get_failure_rate_all_failed(self):
        """Test failure rate calculation with all failed."""
        stats = {"failed": 3, "total_completed": 3}

        self.assertEqual(self.manager.get_failure_rate(stats), 100.0)


class TestStatisticsManagerDetailedStatistics(unittest.TestCase):
    """Test detailed statistics method."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3"]
        self.manager = StatisticsManager(self.hosts)

    def test_get_detailed_statistics(self):
        """Test detailed statistics generation."""
        host_sections = {"host1": Mock(), "host2": Mock()}
        ssh_results = {"host1": {"status": "SUCCESS"}, "host2": {"status": "BUILDING"}}

        detailed_stats = self.manager.get_detailed_statistics(
            host_sections, ssh_results
        )

        # Check basic stats are included
        self.assertIn("active", detailed_stats)
        self.assertIn("completed", detailed_stats)
        self.assertIn("failed", detailed_stats)
        self.assertIn("total_completed", detailed_stats)
        self.assertIn("overall_progress", detailed_stats)
        self.assertIn("total_hosts", detailed_stats)
        self.assertIn("visible_hosts", detailed_stats)
        self.assertIn("processed_hosts", detailed_stats)

        # Check additional detailed stats
        self.assertIn("host_status_breakdown", detailed_stats)
        self.assertIn("visible_host_status_breakdown", detailed_stats)
        self.assertIn("is_complete", detailed_stats)
        self.assertIn("remaining_hosts", detailed_stats)
        self.assertIn("success_rate", detailed_stats)
        self.assertIn("failure_rate", detailed_stats)
        self.assertIn("status_summary", detailed_stats)
        self.assertIn("progress_summary", detailed_stats)

        # Verify some specific values
        self.assertEqual(detailed_stats["active"], 1)
        self.assertEqual(detailed_stats["completed"], 1)
        self.assertEqual(detailed_stats["total_hosts"], 3)
        self.assertEqual(detailed_stats["visible_hosts"], 2)
        self.assertFalse(detailed_stats["is_complete"])
        self.assertEqual(
            detailed_stats["remaining_hosts"], 2
        )  # 3 total - 1 completed = 2 remaining

    def test_get_detailed_statistics_complete_build(self):
        """Test detailed statistics for complete build."""
        host_sections = {"host1": Mock(), "host2": Mock(), "host3": Mock()}
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "SUCCESS"},
            "host3": {"status": "FAILED"},
        }

        detailed_stats = self.manager.get_detailed_statistics(
            host_sections, ssh_results
        )

        self.assertTrue(detailed_stats["is_complete"])
        self.assertEqual(detailed_stats["remaining_hosts"], 0)
        self.assertEqual(detailed_stats["success_rate"], 66.66666666666666)
        self.assertEqual(detailed_stats["failure_rate"], 33.33333333333333)


class TestStatisticsManagerIntegration(unittest.TestCase):
    """Integration tests for StatisticsManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.hosts = ["host1", "host2", "host3", "host4", "host5"]
        self.manager = StatisticsManager(self.hosts)

    def test_full_build_cycle_statistics(self):
        """Test statistics through a full build cycle."""
        host_sections = {"host1": Mock(), "host2": Mock(), "host3": Mock()}

        # Initial state - no results
        ssh_results = {}
        stats = self.manager.calculate_statistics(host_sections, ssh_results)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["overall_progress"], 0.0)

        # Some hosts start building
        ssh_results = {
            "host1": {"status": "CONNECTING"},
            "host2": {"status": "BUILDING"},
        }
        stats = self.manager.calculate_statistics(host_sections, ssh_results)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["overall_progress"], 0.0)

        # Some hosts complete
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "FAILED"},
            "host3": {"status": "BUILDING"},
        }
        stats = self.manager.calculate_statistics(host_sections, ssh_results)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["overall_progress"], 40.0)  # 2/5 hosts completed

        # All hosts complete
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "FAILED"},
            "host3": {"status": "SUCCESS"},
            "host4": {"status": "SUCCESS"},
            "host5": {"status": "FAILED"},
        }
        stats = self.manager.calculate_statistics(host_sections, ssh_results)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["completed"], 3)
        self.assertEqual(stats["failed"], 2)
        self.assertEqual(stats["overall_progress"], 100.0)
        self.assertTrue(self.manager.is_build_complete(stats))

    def test_statistics_consistency(self):
        """Test that statistics are internally consistent."""
        host_sections = {"host1": Mock(), "host2": Mock(), "host3": Mock()}
        ssh_results = {
            "host1": {"status": "SUCCESS"},
            "host2": {"status": "BUILDING"},
            "host3": {"status": "FAILED"},
        }

        stats = self.manager.calculate_statistics(host_sections, ssh_results)

        # Check that total_completed equals completed + failed
        self.assertEqual(stats["total_completed"], stats["completed"] + stats["failed"])

        # Check that progress percentage is calculated correctly
        expected_progress = (stats["total_completed"] / stats["total_hosts"]) * 100
        self.assertEqual(stats["overall_progress"], expected_progress)

        # Check that visible_hosts equals the number of host sections
        self.assertEqual(stats["visible_hosts"], len(host_sections))

        # Check that processed_hosts equals the number of SSH results
        self.assertEqual(stats["processed_hosts"], len(ssh_results))


if __name__ == "__main__":
    unittest.main()
