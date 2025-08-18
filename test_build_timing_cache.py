"""
Unit tests for BuildTimingCache class.
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, mock_open
from build_timing_cache import BuildTimingCache, BuildTimingRecord


class TestBuildTimingCache(unittest.TestCase):
    """Test cases for BuildTimingCache class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test cache files
        self.test_dir = tempfile.mkdtemp()
        self.test_cache_file = os.path.join(self.test_dir, "test_cache.json")

        # Create a cache instance for testing
        self.cache = BuildTimingCache(
            cache_file_path=self.test_cache_file, retention_days=1
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_initialization(self):
        """Test cache initialization."""
        self.assertEqual(self.cache.cache_file_path, self.test_cache_file)
        self.assertEqual(self.cache.retention_days, 1)
        self.assertIn("version", self.cache.cache_data)
        self.assertIn("hosts", self.cache.cache_data)
        self.assertEqual(self.cache.cache_data["version"], "1.0")

    def test_load_cache_new_file(self):
        """Test loading cache when file doesn't exist."""
        # Remove the test file
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

        # Create new cache instance
        new_cache = BuildTimingCache(cache_file_path=self.test_cache_file)

        # Should create default structure
        self.assertEqual(new_cache.cache_data["version"], "1.0")
        self.assertEqual(new_cache.cache_data["hosts"], {})

    def test_load_cache_existing_file(self):
        """Test loading cache from existing file."""
        # Create test cache data
        test_data = {
            "version": "1.0",
            "cache_retention_days": 1,
            "hosts": {
                "test-host": {
                    "last_updated": time.time(),
                    "total_builds": 5,
                    "average_times": {
                        "configure": 10.0,
                        "make": 20.0,
                        "make_check": 5.0,
                        "total": 35.0,
                    },
                    "recent_builds": [],
                }
            },
        }

        # Write test data to file
        with open(self.test_cache_file, "w") as f:
            json.dump(test_data, f)

        # Load cache from file
        loaded_cache = BuildTimingCache(cache_file_path=self.test_cache_file)

        # Verify data was loaded correctly
        self.assertIn("test-host", loaded_cache.cache_data["hosts"])
        self.assertEqual(
            loaded_cache.cache_data["hosts"]["test-host"]["total_builds"], 5
        )

    def test_load_cache_version_mismatch(self):
        """Test loading cache with version mismatch."""
        # Create test cache data with wrong version
        test_data = {"version": "0.9", "cache_retention_days": 1, "hosts": {}}

        # Write test data to file
        with open(self.test_cache_file, "w") as f:
            json.dump(test_data, f)

        # Load cache from file - should create new default structure
        loaded_cache = BuildTimingCache(cache_file_path=self.test_cache_file)

        # Should have default structure, not old data
        self.assertEqual(loaded_cache.cache_data["version"], "1.0")
        self.assertEqual(loaded_cache.cache_data["hosts"], {})

    def test_record_build_timing_new_host(self):
        """Test recording timing for a new host."""
        self.cache.record_build_timing(
            host_name="new-host",
            configure_time=15.0,
            make_time=25.0,
            make_check_time=8.0,
            total_time=48.0,
            success=True,
        )

        # Verify host was added
        self.assertIn("new-host", self.cache.cache_data["hosts"])
        host_data = self.cache.cache_data["hosts"]["new-host"]

        # Verify statistics
        self.assertEqual(host_data["total_builds"], 1)
        self.assertEqual(host_data["average_times"]["configure"], 15.0)
        self.assertEqual(host_data["average_times"]["make"], 25.0)
        self.assertEqual(host_data["average_times"]["make_check"], 8.0)
        self.assertEqual(host_data["average_times"]["total"], 48.0)

        # Verify recent builds
        self.assertEqual(len(host_data["recent_builds"]), 1)
        recent_build = host_data["recent_builds"][0]
        self.assertEqual(recent_build["configure_time"], 15.0)
        self.assertEqual(recent_build["make_time"], 25.0)
        self.assertEqual(recent_build["make_check_time"], 8.0)
        self.assertEqual(recent_build["total_time"], 48.0)
        self.assertEqual(recent_build["success"], True)

    def test_record_build_timing_existing_host(self):
        """Test recording timing for an existing host."""
        # Record first build
        self.cache.record_build_timing(
            host_name="existing-host",
            configure_time=10.0,
            make_time=20.0,
            make_check_time=5.0,
            total_time=35.0,
            success=True,
        )

        # Record second build
        self.cache.record_build_timing(
            host_name="existing-host",
            configure_time=20.0,
            make_time=40.0,
            make_check_time=10.0,
            total_time=70.0,
            success=False,
        )

        # Verify statistics
        host_data = self.cache.cache_data["hosts"]["existing-host"]
        self.assertEqual(host_data["total_builds"], 2)

        # Verify averages (should be 15.0, 30.0, 7.5, 52.5)
        self.assertEqual(host_data["average_times"]["configure"], 15.0)
        self.assertEqual(host_data["average_times"]["make"], 30.0)
        self.assertEqual(host_data["average_times"]["make_check"], 7.5)
        self.assertEqual(host_data["average_times"]["total"], 52.5)

        # Verify recent builds (should have 2)
        self.assertEqual(len(host_data["recent_builds"]), 2)

    def test_recent_builds_limit(self):
        """Test that recent builds are limited to 10."""
        # Record 12 builds
        for i in range(12):
            self.cache.record_build_timing(
                host_name="limit-test-host",
                configure_time=float(i),
                make_time=float(i * 2),
                make_check_time=float(i * 0.5),
                total_time=float(i * 3.5),
                success=True,
            )

        # Should only keep last 10
        host_data = self.cache.cache_data["hosts"]["limit-test-host"]
        self.assertEqual(len(host_data["recent_builds"]), 10)

        # Last build should be the 12th one (index 11)
        last_build = host_data["recent_builds"][-1]
        self.assertEqual(last_build["configure_time"], 11.0)

    def test_get_progress_estimate_configure(self):
        """Test progress estimate for configure step."""
        # Record some timing data
        self.cache.record_build_timing(
            host_name="progress-host",
            configure_time=100.0,
            make_time=200.0,
            make_check_time=50.0,
            total_time=350.0,
            success=True,
        )

        # Test progress at 50 seconds (should be 50%)
        progress = self.cache.get_progress_estimate("progress-host", "configure", 50.0)
        self.assertEqual(progress, "50.0%")

        # Test progress at 100 seconds (should be 100%)
        progress = self.cache.get_progress_estimate("progress-host", "configure", 100.0)
        self.assertEqual(progress, "100.0%")

        # Test progress beyond 100% (should be capped at 100%)
        progress = self.cache.get_progress_estimate("progress-host", "configure", 150.0)
        self.assertEqual(progress, "100.0%")

    def test_get_progress_estimate_make(self):
        """Test progress estimate for make step."""
        # Record some timing data
        self.cache.record_build_timing(
            host_name="progress-host",
            configure_time=100.0,
            make_time=200.0,
            make_check_time=50.0,
            total_time=350.0,
            success=True,
        )

        # Test progress at 50 seconds into make (should be 50% of total)
        # Total elapsed = 100 (configure) + 50 (make) = 150
        # Progress = 150/350 = 42.9%
        progress = self.cache.get_progress_estimate("progress-host", "make", 50.0)
        self.assertEqual(progress, "42.9%")

        # Test progress at 100 seconds into make (should be 57.1% of total)
        # Total elapsed = 100 (configure) + 100 (make) = 200
        # Progress = 200/350 = 57.1%
        progress = self.cache.get_progress_estimate("progress-host", "make", 100.0)
        self.assertEqual(progress, "57.1%")

    def test_get_progress_estimate_no_data(self):
        """Test progress estimate when no timing data exists."""
        # Should return None for unknown host
        progress = self.cache.get_progress_estimate("unknown-host", "configure", 50.0)
        self.assertIsNone(progress)

        # Should return None for unknown step
        progress = self.cache.get_progress_estimate(
            "progress-host", "unknown-step", 50.0
        )
        self.assertIsNone(progress)

    def test_get_host_statistics(self):
        """Test getting host statistics."""
        # Record some timing data
        self.cache.record_build_timing(
            host_name="stats-host",
            configure_time=10.0,
            make_time=20.0,
            make_check_time=5.0,
            total_time=35.0,
            success=True,
        )

        # Get statistics
        stats = self.cache.get_host_statistics("stats-host")

        # Verify statistics
        self.assertIsNotNone(stats)
        self.assertEqual(stats["total_builds"], 1)
        self.assertIn("last_updated", stats)
        self.assertIn("average_times", stats)
        self.assertIn("recent_builds", stats)

        # Verify average times
        avg_times = stats["average_times"]
        self.assertEqual(avg_times["configure"], 10.0)
        self.assertEqual(avg_times["make"], 20.0)
        self.assertEqual(avg_times["make_check"], 5.0)
        self.assertEqual(avg_times["total"], 35.0)

    def test_get_host_statistics_unknown_host(self):
        """Test getting statistics for unknown host."""
        stats = self.cache.get_host_statistics("unknown-host")
        self.assertIsNone(stats)

    def test_get_all_hosts(self):
        """Test getting list of all hosts."""
        # Initially should be empty
        hosts = self.cache.get_all_hosts()
        self.assertEqual(hosts, [])

        # Add some hosts
        self.cache.record_build_timing("host1", 10.0, 20.0, 5.0, 35.0, True)
        self.cache.record_build_timing("host2", 15.0, 25.0, 8.0, 48.0, False)

        # Should have both hosts
        hosts = self.cache.get_all_hosts()
        self.assertIn("host1", hosts)
        self.assertIn("host2", hosts)
        self.assertEqual(len(hosts), 2)

    def test_clear_host_data(self):
        """Test clearing data for a specific host."""
        # Add a host
        self.cache.record_build_timing("clear-test-host", 10.0, 20.0, 5.0, 35.0, True)

        # Verify host exists
        self.assertIn("clear-test-host", self.cache.cache_data["hosts"])

        # Clear host data
        result = self.cache.clear_host_data("clear-test-host")
        self.assertTrue(result)

        # Verify host was removed
        self.assertNotIn("clear-test-host", self.cache.cache_data["hosts"])

    def test_clear_host_data_unknown_host(self):
        """Test clearing data for unknown host."""
        result = self.cache.clear_host_data("unknown-host")
        self.assertFalse(result)

    def test_clear_all_data(self):
        """Test clearing all data."""
        # Add some hosts
        self.cache.record_build_timing("host1", 10.0, 20.0, 5.0, 35.0, True)
        self.cache.record_build_timing("host2", 15.0, 25.0, 8.0, 48.0, False)

        # Verify hosts exist
        self.assertEqual(len(self.cache.cache_data["hosts"]), 2)

        # Clear all data
        self.cache.clear_all_data()

        # Verify all hosts were removed
        self.assertEqual(len(self.cache.cache_data["hosts"]), 0)

    def test_get_cache_info(self):
        """Test getting cache information."""
        # Add some hosts
        self.cache.record_build_timing("host1", 10.0, 20.0, 5.0, 35.0, True)
        self.cache.record_build_timing("host2", 15.0, 25.0, 8.0, 48.0, False)

        # Get cache info
        info = self.cache.get_cache_info()

        # Verify info
        self.assertEqual(info["version"], "1.0")
        self.assertEqual(info["cache_file"], self.test_cache_file)
        self.assertEqual(info["retention_days"], 1)
        self.assertEqual(info["total_hosts"], 2)
        self.assertEqual(info["total_builds"], 2)
        self.assertGreater(info["cache_size_bytes"], 0)

    def test_cleanup_old_data(self):
        """Test cleanup of old data."""
        # Add a host with old timestamp
        old_time = time.time() - (2 * 24 * 3600)  # 2 days ago
        self.cache.cache_data["hosts"]["old-host"] = {
            "last_updated": old_time,
            "total_builds": 1,
            "average_times": {
                "configure": 10.0,
                "make": 20.0,
                "make_check": 5.0,
                "total": 35.0,
            },
            "recent_builds": [],
        }

        # Add a host with recent timestamp
        recent_time = time.time() - (12 * 3600)  # 12 hours ago
        self.cache.cache_data["hosts"]["recent-host"] = {
            "last_updated": recent_time,
            "total_builds": 1,
            "average_times": {
                "configure": 15.0,
                "make": 25.0,
                "make_check": 8.0,
                "total": 48.0,
            },
            "recent_builds": [],
        }

        # Verify both hosts exist
        self.assertEqual(len(self.cache.cache_data["hosts"]), 2)

        # Clean up old data
        self.cache._cleanup_old_data()

        # Old host should be removed, recent host should remain
        self.assertNotIn("old-host", self.cache.cache_data["hosts"])
        self.assertIn("recent-host", self.cache.cache_data["hosts"])
        self.assertEqual(len(self.cache.cache_data["hosts"]), 1)

    def test_save_cache_error_handling(self):
        """Test error handling during cache save."""
        # Create cache with invalid file path
        invalid_cache = BuildTimingCache(cache_file_path="/invalid/path/cache.json")

        # Try to save - should handle error gracefully
        invalid_cache.record_build_timing("test-host", 10.0, 20.0, 5.0, 35.0, True)
        # Should not raise exception, just log error

    def test_load_cache_error_handling(self):
        """Test error handling during cache load."""
        # Create invalid JSON file
        with open(self.test_cache_file, "w") as f:
            f.write("invalid json content")

        # Try to load - should handle error gracefully and create default structure
        cache = BuildTimingCache(cache_file_path=self.test_cache_file)
        self.assertEqual(cache.cache_data["version"], "1.0")
        self.assertEqual(cache.cache_data["hosts"], {})


class TestBuildTimingRecord(unittest.TestCase):
    """Test cases for BuildTimingRecord dataclass."""

    def test_build_timing_record_creation(self):
        """Test creating BuildTimingRecord instances."""
        record = BuildTimingRecord(
            timestamp=1234567890.0,
            configure_time=10.5,
            make_time=20.7,
            make_check_time=5.2,
            total_time=36.4,
            success=True,
        )

        self.assertEqual(record.timestamp, 1234567890.0)
        self.assertEqual(record.configure_time, 10.5)
        self.assertEqual(record.make_time, 20.7)
        self.assertEqual(record.make_check_time, 5.2)
        self.assertEqual(record.total_time, 36.4)
        self.assertTrue(record.success)

    def test_build_timing_record_equality(self):
        """Test BuildTimingRecord equality comparison."""
        record1 = BuildTimingRecord(1.0, 10.0, 20.0, 5.0, 35.0, True)
        record2 = BuildTimingRecord(1.0, 10.0, 20.0, 5.0, 35.0, True)
        record3 = BuildTimingRecord(2.0, 15.0, 25.0, 8.0, 48.0, False)

        self.assertEqual(record1, record2)
        self.assertNotEqual(record1, record3)


if __name__ == "__main__":
    unittest.main()
