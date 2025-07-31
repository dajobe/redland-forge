#!/usr/bin/python3
"""
Unit tests for ParallelSSHManager module.
"""

import threading
import unittest
from unittest.mock import Mock, patch

from parallel_ssh_manager import ParallelSSHManager


class TestParallelSSHManagerInitialization(unittest.TestCase):
    """Test ParallelSSHManager initialization."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        manager = ParallelSSHManager()
        self.assertEqual(manager.max_concurrent, 4)
        self.assertEqual(manager.active_connections, {})
        self.assertEqual(manager.connection_queue, [])
        self.assertEqual(manager.results, {})
        self.assertIsInstance(manager.lock, type(threading.Lock()))
        self.assertIsNone(manager.build_script_path)

    def test_init_custom_concurrency(self):
        """Test initialization with custom concurrency limit."""
        manager = ParallelSSHManager(max_concurrent=8)
        self.assertEqual(manager.max_concurrent, 8)


class TestParallelSSHManagerHostManagement(unittest.TestCase):
    """Test host management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ParallelSSHManager()

    def test_add_host_basic(self):
        """Test adding a host to the queue."""
        self.manager.add_host("user@host1", "test.tar.gz")
        self.assertEqual(len(self.manager.connection_queue), 1)
        self.assertEqual(
            self.manager.connection_queue[0], ("user@host1", "test.tar.gz")
        )

    def test_add_host_multiple(self):
        """Test adding multiple hosts to the queue."""
        hosts = [
            ("user1@host1", "test1.tar.gz"),
            ("user2@host2", "test2.tar.gz"),
            ("user3@host3", "test3.tar.gz"),
        ]

        for hostname, tarball in hosts:
            self.manager.add_host(hostname, tarball)

        self.assertEqual(len(self.manager.connection_queue), 3)
        self.assertEqual(self.manager.connection_queue, hosts)

    def test_set_build_script_path(self):
        """Test setting build script path."""
        script_path = "/path/to/build-redland.py"
        self.manager.set_build_script_path(script_path)
        self.assertEqual(self.manager.build_script_path, script_path)


class TestParallelSSHManagerBuildOrchestration(unittest.TestCase):
    """Test build orchestration methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ParallelSSHManager(max_concurrent=2)

    @patch("parallel_ssh_manager.threading.Thread")
    def test_start_builds_empty_queue(self, mock_thread):
        """Test starting builds with empty queue."""
        self.manager.start_builds()
        mock_thread.assert_not_called()

    @patch("parallel_ssh_manager.threading.Thread")
    def test_start_builds_single_host(self, mock_thread):
        """Test starting builds with single host."""
        self.manager.add_host("user@host1", "test.tar.gz")
        self.manager.start_builds()

        mock_thread.assert_called_once()
        # Check that Thread was called with the correct arguments
        args, kwargs = mock_thread.call_args
        self.assertEqual(kwargs["target"], self.manager._build_worker)
        self.assertEqual(kwargs["args"], ("user@host1", "test.tar.gz"))

    @patch("parallel_ssh_manager.threading.Thread")
    def test_start_builds_respects_concurrency_limit(self, mock_thread):
        """Test that start_builds respects concurrency limit."""
        # Add more hosts than concurrency limit
        for i in range(5):
            self.manager.add_host(f"user@host{i}", f"test{i}.tar.gz")

        self.manager.start_builds()

        # Should only start 2 builds (max_concurrent)
        self.assertEqual(mock_thread.call_count, 2)
        self.assertEqual(len(self.manager.connection_queue), 3)


class TestParallelSSHManagerStatusTracking(unittest.TestCase):
    """Test status tracking and query methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ParallelSSHManager()

    def test_get_results_empty(self):
        """Test getting results when empty."""
        results = self.manager.get_results()
        self.assertEqual(results, {})

    def test_get_results_with_data(self):
        """Test getting results with data."""
        self.manager.results = {
            "host1": {"status": "SUCCESS", "output": ["line1", "line2"]},
            "host2": {"status": "FAILED", "output": ["error"]},
        }

        results = self.manager.get_results()
        self.assertEqual(results, self.manager.results)

    def test_is_build_complete_empty(self):
        """Test build completion check when empty."""
        self.assertTrue(self.manager.is_build_complete())

    def test_is_build_complete_with_active_connections(self):
        """Test build completion check with active connections."""
        self.manager.active_connections["host1"] = Mock()
        self.assertFalse(self.manager.is_build_complete())

    def test_get_build_status_summary_empty(self):
        """Test getting build status summary when empty."""
        summary = self.manager.get_build_status_summary()
        expected = {
            "CONNECTING": 0,
            "PREPARING": 0,
            "BUILDING": 0,
            "SUCCESS": 0,
            "FAILED": 0,
        }
        self.assertEqual(summary, expected)

    def test_get_build_status_summary_with_results(self):
        """Test getting build status summary with results."""
        self.manager.results = {
            "host1": {"status": "SUCCESS", "output": []},
            "host2": {"status": "FAILED", "output": []},
            "host3": {"status": "BUILDING", "output": []},
        }

        summary = self.manager.get_build_status_summary()
        expected = {
            "CONNECTING": 0,
            "PREPARING": 0,
            "BUILDING": 1,
            "SUCCESS": 1,
            "FAILED": 1,
        }
        self.assertEqual(summary, expected)


if __name__ == "__main__":
    unittest.main()
