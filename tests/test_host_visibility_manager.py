#!/usr/bin/python3
"""
Tests for HostVisibilityManager module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from redland_forge.host_visibility_manager import HostVisibilityManager
from redland_forge.host_section import HostSection


class TestHostVisibilityManagerInitialization(unittest.TestCase):
    """Test HostVisibilityManager initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        mock_terminal = Mock()
        mock_layout_manager = Mock()
        all_hosts = ["host1", "host2", "host3"]

        manager = HostVisibilityManager(mock_terminal, mock_layout_manager, all_hosts)

        self.assertEqual(manager.term, mock_terminal)
        self.assertEqual(manager.layout_manager, mock_layout_manager)
        self.assertEqual(manager.all_hosts, all_hosts)
        self.assertEqual(manager.host_sections, {})

    def test_init_empty_hosts(self):
        """Test initialization with empty host list."""
        mock_terminal = Mock()
        mock_layout_manager = Mock()
        all_hosts = []

        manager = HostVisibilityManager(mock_terminal, mock_layout_manager, all_hosts)

        self.assertEqual(manager.all_hosts, [])
        self.assertEqual(manager.host_sections, {})


class TestHostVisibilityManagerBasicOperations(unittest.TestCase):
    """Test basic host visibility operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = 24

        self.mock_layout_manager = Mock()
        self.mock_layout_manager.get_max_visible_hosts.return_value = 4

        self.all_hosts = ["host1", "host2", "host3", "host4", "host5"]
        self.manager = HostVisibilityManager(
            self.mock_terminal, self.mock_layout_manager, self.all_hosts
        )

    def test_get_host_sections_empty(self):
        """Test getting host sections when empty."""
        sections = self.manager.get_host_sections()
        self.assertEqual(sections, {})

    def test_get_visible_hosts_empty(self):
        """Test getting visible hosts when empty."""
        visible_hosts = self.manager.get_visible_hosts()
        self.assertEqual(visible_hosts, [])

    def test_is_host_visible_false(self):
        """Test checking visibility for non-existent host."""
        self.assertFalse(self.manager.is_host_visible("nonexistent"))

    def test_get_host_section_nonexistent(self):
        """Test getting host section for non-existent host."""
        section = self.manager.get_host_section("nonexistent")
        self.assertIsNone(section)

    def test_remove_host_section_nonexistent(self):
        """Test removing non-existent host section."""
        result = self.manager.remove_host_section("nonexistent")
        self.assertFalse(result)

    def test_clear_all_sections(self):
        """Test clearing all host sections."""
        # Add some mock sections
        self.manager.host_sections = {"host1": Mock(), "host2": Mock()}

        self.manager.clear_all_sections()

        self.assertEqual(self.manager.host_sections, {})


class TestHostVisibilityManagerHostSectionManagement(unittest.TestCase):
    """Test host section management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = 24

        self.mock_layout_manager = Mock()
        self.mock_layout_manager.get_max_visible_hosts.return_value = 4

        self.all_hosts = ["host1", "host2", "host3"]
        self.manager = HostVisibilityManager(
            self.mock_terminal, self.mock_layout_manager, self.all_hosts
        )

    def test_get_max_visible_hosts(self):
        """Test getting max visible hosts."""
        max_hosts = self.manager._get_max_visible_hosts()
        self.assertEqual(max_hosts, 4)
        self.mock_layout_manager.get_max_visible_hosts.assert_called_once()

    def test_add_host_section_basic(self):
        """Test adding a host section."""
        with patch("redland_forge.host_visibility_manager.HostSection") as mock_host_section_class:
            mock_section = Mock()
            mock_host_section_class.return_value = mock_section

            # Mock terminal properties
            self.mock_terminal.height = 24

            self.manager._add_host_section("host1")

            # Verify HostSection was created
            mock_host_section_class.assert_called_once()
            self.assertIn("host1", self.manager.host_sections)

    def test_add_host_section_at_capacity(self):
        """Test adding host section when at capacity."""
        # Fill up the sections
        self.manager.host_sections = {
            "host1": Mock(),
            "host2": Mock(),
            "host3": Mock(),
            "host4": Mock(),
        }

        with patch("redland_forge.host_visibility_manager.HostSection") as mock_host_section_class:
            self.manager._add_host_section("host5")

            # Should not create new section
            mock_host_section_class.assert_not_called()
            self.assertNotIn("host5", self.manager.host_sections)

    def test_remove_host_section_existing(self):
        """Test removing existing host section."""
        # Add a mock section
        mock_section = Mock()
        self.manager.host_sections["host1"] = mock_section

        result = self.manager.remove_host_section("host1")

        self.assertTrue(result)
        self.assertNotIn("host1", self.manager.host_sections)

    def test_get_host_section_existing(self):
        """Test getting existing host section."""
        mock_section = Mock()
        self.manager.host_sections["host1"] = mock_section

        section = self.manager.get_host_section("host1")

        self.assertEqual(section, mock_section)

    def test_is_host_visible_true(self):
        """Test checking visibility for existing host."""
        mock_section = Mock()
        self.manager.host_sections["host1"] = mock_section

        self.assertTrue(self.manager.is_host_visible("host1"))


class TestHostVisibilityManagerHideCompletedHosts(unittest.TestCase):
    """Test hiding completed hosts functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = 24

        self.mock_layout_manager = Mock()
        self.mock_layout_manager.get_max_visible_hosts.return_value = 4

        self.all_hosts = ["host1", "host2", "host3"]
        self.manager = HostVisibilityManager(
            self.mock_terminal, self.mock_layout_manager, self.all_hosts
        )

    def test_hide_completed_hosts_no_completed(self):
        """Test hiding completed hosts when none are completed."""
        # Add active hosts
        mock_section1 = Mock()
        mock_section1.completion_time = None
        self.manager.host_sections["host1"] = mock_section1

        mock_section2 = Mock()
        mock_section2.completion_time = None
        self.manager.host_sections["host2"] = mock_section2

        ssh_results = {
            "host1": {"status": "BUILDING"},
            "host2": {"status": "CONNECTING"},
        }

        current_time = time.time()

        self.manager._hide_completed_hosts(
            ["host1", "host2"], ssh_results, current_time
        )

        # Should not hide any hosts
        self.assertIn("host1", self.manager.host_sections)
        self.assertIn("host2", self.manager.host_sections)

    def test_hide_completed_hosts_with_timeout(self):
        """Test hiding completed hosts that have timed out."""
        current_time = time.time()

        # Add a completed host that has timed out
        mock_section = Mock()
        mock_section.completion_time = current_time - 15  # 15 seconds ago
        self.manager.host_sections["host1"] = mock_section

        ssh_results = {"host1": {"status": "SUCCESS"}}

        with patch("redland_forge.host_visibility_manager.Config") as mock_config:
            mock_config.HOST_VISIBILITY_TIMEOUT_SECONDS = 10

            self.manager._hide_completed_hosts(["host1"], ssh_results, current_time)

            # Should hide the host
            self.assertNotIn("host1", self.manager.host_sections)

    def test_hide_completed_hosts_not_timed_out(self):
        """Test not hiding completed hosts that haven't timed out."""
        current_time = time.time()

        # Add a completed host that hasn't timed out
        mock_section = Mock()
        mock_section.completion_time = current_time - 5  # 5 seconds ago
        self.manager.host_sections["host1"] = mock_section

        ssh_results = {"host1": {"status": "SUCCESS"}}

        with patch("redland_forge.host_visibility_manager.Config") as mock_config:
            mock_config.HOST_VISIBILITY_TIMEOUT_SECONDS = 10

            self.manager._hide_completed_hosts(["host1"], ssh_results, current_time)

            # Should not hide the host
            self.assertIn("host1", self.manager.host_sections)

    def test_hide_completed_hosts_set_completion_time(self):
        """Test setting completion time for newly completed hosts."""
        current_time = time.time()

        # Add a completed host without completion time
        mock_section = Mock()
        mock_section.completion_time = None
        self.manager.host_sections["host1"] = mock_section

        ssh_results = {"host1": {"status": "SUCCESS"}}

        self.manager._hide_completed_hosts(["host1"], ssh_results, current_time)

        # Should set completion time but not hide
        self.assertEqual(mock_section.completion_time, current_time)
        self.assertIn("host1", self.manager.host_sections)


class TestHostVisibilityManagerShowNewHosts(unittest.TestCase):
    """Test showing new hosts functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = 24

        self.mock_layout_manager = Mock()
        self.mock_layout_manager.get_max_visible_hosts.return_value = 4

        self.all_hosts = ["host1", "host2", "host3", "host4"]
        self.manager = HostVisibilityManager(
            self.mock_terminal, self.mock_layout_manager, self.all_hosts
        )

    def test_show_new_hosts_active_host(self):
        """Test showing new active host."""
        ssh_results = {"host1": {"status": "BUILDING"}}
        connection_queue = []
        active_connections = {}
        current_time = time.time()

        with patch.object(self.manager, "_add_host_section") as mock_add:
            self.manager._show_new_hosts(
                ssh_results, connection_queue, active_connections, current_time
            )

            # Should add the active host
            mock_add.assert_called_with("host1")

    def test_show_new_hosts_queued_host(self):
        """Test showing new queued host."""
        ssh_results = {}
        connection_queue = [("host1", "tarball")]
        active_connections = {}
        current_time = time.time()

        with patch.object(self.manager, "_add_host_section") as mock_add:
            self.manager._show_new_hosts(
                ssh_results, connection_queue, active_connections, current_time
            )

            # Should add the queued host and initialize it
            mock_add.assert_called_with("host1")
            self.assertIn("host1", ssh_results)
            self.assertEqual(ssh_results["host1"]["status"], "IDLE")

    def test_show_new_hosts_active_connection_host(self):
        """Test showing new host with active connection."""
        ssh_results = {}
        connection_queue = []
        active_connections = {"host1": Mock()}
        current_time = time.time()

        with patch.object(self.manager, "_add_host_section") as mock_add:
            self.manager._show_new_hosts(
                ssh_results, connection_queue, active_connections, current_time
            )

            # Should add the host and initialize it as CONNECTING
            mock_add.assert_called_with("host1")
            self.assertIn("host1", ssh_results)
            self.assertEqual(ssh_results["host1"]["status"], "CONNECTING")

    def test_show_new_hosts_at_capacity(self):
        """Test showing new hosts when at capacity."""
        # Fill up the sections
        self.manager.host_sections = {
            "host1": Mock(),
            "host2": Mock(),
            "host3": Mock(),
            "host4": Mock(),
        }

        ssh_results = {"host5": {"status": "BUILDING"}}
        connection_queue = []
        active_connections = {}
        current_time = time.time()

        with patch.object(self.manager, "_add_host_section") as mock_add:
            self.manager._show_new_hosts(
                ssh_results, connection_queue, active_connections, current_time
            )

            # Should not add new host due to capacity
            mock_add.assert_not_called()


class TestHostVisibilityManagerIntegration(unittest.TestCase):
    """Test HostVisibilityManager integration scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = 24

        self.mock_layout_manager = Mock()
        self.mock_layout_manager.get_max_visible_hosts.return_value = 3

        self.all_hosts = ["host1", "host2", "host3", "host4"]
        self.manager = HostVisibilityManager(
            self.mock_terminal, self.mock_layout_manager, self.all_hosts
        )

    def test_update_host_visibility_full_cycle(self):
        """Test full host visibility update cycle."""
        current_time = time.time()

        # Start with some hosts
        ssh_results = {
            "host1": {"status": "BUILDING"},
            "host2": {"status": "SUCCESS"},
            "host3": {"status": "CONNECTING"},
        }

        # Add completed host that should be hidden
        mock_section = Mock()
        mock_section.completion_time = current_time - 15  # 15 seconds ago
        self.manager.host_sections["host2"] = mock_section

        connection_queue = [("host4", "tarball")]
        active_connections = {}

        with patch("redland_forge.host_visibility_manager.Config") as mock_config:
            mock_config.HOST_VISIBILITY_TIMEOUT_SECONDS = 10
            mock_config.HEADER_HEIGHT = 4
            mock_config.FOOTER_HEIGHT = 4
            mock_config.MIN_HOST_HEIGHT = 3

            with patch.object(self.manager, "_add_host_section") as mock_add:
                self.manager.update_host_visibility(
                    ssh_results, connection_queue, active_connections
                )

                # Should hide completed host2
                self.assertNotIn("host2", self.manager.host_sections)

                # Should add new hosts
                mock_add.assert_any_call("host1")
                mock_add.assert_any_call("host3")
                mock_add.assert_any_call("host4")

    def test_visibility_state_consistency(self):
        """Test that visibility state remains consistent."""
        # Add some hosts
        mock_section1 = Mock()
        mock_section2 = Mock()
        self.manager.host_sections = {"host1": mock_section1, "host2": mock_section2}

        # Test consistency
        visible_hosts = self.manager.get_visible_hosts()
        self.assertEqual(set(visible_hosts), {"host1", "host2"})

        self.assertTrue(self.manager.is_host_visible("host1"))
        self.assertTrue(self.manager.is_host_visible("host2"))
        self.assertFalse(self.manager.is_host_visible("host3"))

        self.assertEqual(self.manager.get_host_section("host1"), mock_section1)
        self.assertEqual(self.manager.get_host_section("host2"), mock_section2)
        self.assertIsNone(self.manager.get_host_section("host3"))


if __name__ == "__main__":
    unittest.main()
