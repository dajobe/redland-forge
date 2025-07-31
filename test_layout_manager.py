#!/usr/bin/python3
"""
Unit tests for LayoutManager class.
"""

import unittest
from unittest.mock import Mock, patch

from layout_manager import LayoutManager
from host_section import HostSection


# Test configuration constants
class TestConfig:
    """Test configuration values for consistent testing."""

    MIN_TERMINAL_HEIGHT = 10
    MIN_HOST_HEIGHT = 8
    HEADER_HEIGHT = 4
    FOOTER_HEIGHT = 4

    # Small terminal layout settings
    SMALL_TERMINAL_HEADER_FOOTER = 2  # Minimal header/footer space for small terminals
    SMALL_TERMINAL_MIN_HOST_HEIGHT = 3  # Minimum host height for small terminals
    SMALL_TERMINAL_MAX_VISIBLE_HOSTS = 1  # Maximum visible hosts for small terminals
    HOST_SECTION_START_Y = 3  # Starting Y position for host sections
    SMALL_TERMINAL_FOOTER_SPACE = 1  # Footer space for small terminals


class TestLayoutManagerInitialization(unittest.TestCase):
    """Test LayoutManager initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        mock_terminal = Mock()
        mock_terminal.width = 80
        mock_terminal.height = 24

        hosts = ["host1", "host2", "host3"]
        manager = LayoutManager(mock_terminal, hosts)

        self.assertEqual(manager.term, mock_terminal)
        self.assertEqual(manager.hosts, hosts)
        self.assertEqual(manager.host_sections, {})

    def test_init_empty_hosts(self):
        """Test initialization with empty hosts list."""
        mock_terminal = Mock()
        mock_terminal.width = 80
        mock_terminal.height = 24

        manager = LayoutManager(mock_terminal, [])

        self.assertEqual(manager.hosts, [])
        self.assertEqual(manager.host_sections, {})

    def test_init_single_host(self):
        """Test initialization with single host."""
        mock_terminal = Mock()
        mock_terminal.width = 80
        mock_terminal.height = 24

        hosts = ["single-host"]
        manager = LayoutManager(mock_terminal, hosts)

        self.assertEqual(manager.hosts, hosts)


class TestLayoutManagerSmallTerminalLayout(unittest.TestCase):
    """Test layout calculations for small terminals."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = TestConfig.MIN_TERMINAL_HEIGHT - 1  # Small terminal
        self.hosts = ["host1", "host2", "host3"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_calculate_small_terminal_layout(self):
        """Test small terminal layout calculation."""
        layout_info = self.manager._calculate_small_terminal_layout()

        # Test relative calculations instead of hardcoded values
        expected_available_height = (
            self.mock_terminal.height - 2
        )  # Minimal header/footer
        expected_max_section_height = (
            self.mock_terminal.height - 3 - 1
        )  # start_y - footer_space
        expected_section_height = max(
            1, min(expected_available_height, expected_max_section_height)
        )

        self.assertEqual(layout_info["available_height"], expected_available_height)
        self.assertEqual(layout_info["min_host_height"], 3)  # Fixed for small terminals
        self.assertEqual(
            layout_info["max_visible_hosts"], 1
        )  # Always 1 for small terminals
        self.assertEqual(layout_info["section_height"], expected_section_height)

    def test_setup_layout_small_terminal(self):
        """Test complete layout setup for small terminal."""
        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            host_sections = self.manager.setup_layout()

        # Should only have one host section for small terminals
        self.assertEqual(len(host_sections), 1)
        self.assertIn("host1", host_sections)

        # Check the section properties
        section = host_sections["host1"]
        self.assertEqual(section.start_y, 3)  # Fixed start position
        self.assertGreater(section.height, 0)  # Should have positive height

    def test_get_available_height_small_terminal(self):
        """Test available height calculation for small terminal."""
        height = self.manager.get_available_height()
        expected_height = self.mock_terminal.height - 2  # Minimal header/footer
        self.assertEqual(height, expected_height)

    def test_get_section_height_small_terminal(self):
        """Test section height calculation for small terminal."""
        height = self.manager.get_section_height()
        # Should be positive and fit within terminal bounds
        self.assertGreater(height, 0)
        self.assertLessEqual(height, self.mock_terminal.height - 2)


class TestLayoutManagerNormalTerminalLayout(unittest.TestCase):
    """Test layout calculations for normal terminals."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3", "host4"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_calculate_normal_terminal_layout(self):
        """Test normal terminal layout calculation."""
        layout_info = self.manager._calculate_normal_terminal_layout()

        # Test relative calculations instead of hardcoded values
        expected_available_height = self.mock_terminal.height - (
            TestConfig.HEADER_HEIGHT + TestConfig.FOOTER_HEIGHT
        )
        expected_max_visible_hosts = min(
            len(self.hosts), expected_available_height // TestConfig.MIN_HOST_HEIGHT
        )

        self.assertEqual(layout_info["available_height"], expected_available_height)
        self.assertEqual(layout_info["min_host_height"], TestConfig.MIN_HOST_HEIGHT)
        self.assertEqual(layout_info["max_visible_hosts"], expected_max_visible_hosts)
        self.assertGreater(layout_info["section_height"], 0)

    def test_setup_layout_normal_terminal(self):
        """Test complete layout setup for normal terminal."""
        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            host_sections = self.manager.setup_layout()

        # Should have multiple host sections for normal terminals
        self.assertGreater(len(host_sections), 1)

        # Check that sections are positioned correctly
        sections = list(host_sections.values())
        for i, section in enumerate(sections):
            expected_start_y = 3 + (i * section.height)
            self.assertEqual(section.start_y, expected_start_y)

    def test_get_available_height_normal_terminal(self):
        """Test available height calculation for normal terminal."""
        height = self.manager.get_available_height()
        expected_height = self.mock_terminal.height - (
            TestConfig.HEADER_HEIGHT + TestConfig.FOOTER_HEIGHT
        )
        self.assertEqual(height, expected_height)

    def test_get_max_visible_hosts(self):
        """Test maximum visible hosts calculation."""
        max_hosts = self.manager.get_max_visible_hosts()
        available_height = self.mock_terminal.height - (
            TestConfig.HEADER_HEIGHT + TestConfig.FOOTER_HEIGHT
        )
        expected_max = min(
            len(self.hosts), available_height // TestConfig.MIN_HOST_HEIGHT
        )
        self.assertEqual(max_hosts, expected_max)

    def test_get_section_height_normal_terminal(self):
        """Test section height calculation for normal terminal."""
        height = self.manager.get_section_height()
        self.assertGreaterEqual(height, TestConfig.MIN_HOST_HEIGHT)


class TestLayoutManagerHostSectionManagement(unittest.TestCase):
    """Test host section management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_add_host_section(self):
        """Test adding a host section."""
        self.manager.add_host_section("host1", 5, 10)

        self.assertIn("host1", self.manager.host_sections)
        section = self.manager.host_sections["host1"]
        self.assertEqual(section.start_y, 5)
        self.assertEqual(section.height, 10)

    def test_remove_host_section(self):
        """Test removing a host section."""
        self.manager.add_host_section("host1", 5, 10)
        self.assertIn("host1", self.manager.host_sections)

        self.manager.remove_host_section("host1")
        self.assertNotIn("host1", self.manager.host_sections)

    def test_remove_nonexistent_host_section(self):
        """Test removing a host section that doesn't exist."""
        # Should not raise an exception
        self.manager.remove_host_section("nonexistent")

    def test_get_host_section(self):
        """Test getting a host section."""
        self.manager.add_host_section("host1", 5, 10)

        section = self.manager.get_host_section("host1")
        self.assertIsNotNone(section)
        self.assertEqual(section.start_y, 5)
        self.assertEqual(section.height, 10)

    def test_get_nonexistent_host_section(self):
        """Test getting a host section that doesn't exist."""
        section = self.manager.get_host_section("nonexistent")
        self.assertIsNone(section)

    def test_get_all_host_sections(self):
        """Test getting all host sections."""
        self.manager.add_host_section("host1", 5, 10)
        self.manager.add_host_section("host2", 15, 8)

        sections = self.manager.get_all_host_sections()
        self.assertEqual(len(sections), 2)
        self.assertIn("host1", sections)
        self.assertIn("host2", sections)

        # Should return a copy, not the original
        sections["host3"] = Mock()
        self.assertNotIn("host3", self.manager.host_sections)

    def test_get_visible_hosts(self):
        """Test getting visible hostnames."""
        self.manager.add_host_section("host1", 5, 10)
        self.manager.add_host_section("host2", 15, 8)

        visible_hosts = self.manager.get_visible_hosts()
        self.assertEqual(set(visible_hosts), {"host1", "host2"})

    def test_get_hidden_hosts(self):
        """Test getting hidden hostnames."""
        self.manager.add_host_section("host1", 5, 10)

        hidden_hosts = self.manager.get_hidden_hosts()
        self.assertEqual(set(hidden_hosts), {"host2", "host3"})

    def test_is_host_visible(self):
        """Test checking if a host is visible."""
        self.manager.add_host_section("host1", 5, 10)

        self.assertTrue(self.manager.is_host_visible("host1"))
        self.assertFalse(self.manager.is_host_visible("host2"))

    def test_get_section_position(self):
        """Test getting section position."""
        self.manager.add_host_section("host1", 5, 10)

        position = self.manager.get_section_position("host1")
        self.assertEqual(position, (5, 10))

    def test_get_section_position_nonexistent(self):
        """Test getting position of nonexistent section."""
        position = self.manager.get_section_position("nonexistent")
        self.assertIsNone(position)


class TestLayoutManagerValidation(unittest.TestCase):
    """Test layout validation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_validate_layout_valid(self):
        """Test validation of valid layout."""
        self.manager.add_host_section(
            "host1", 3, TestConfig.MIN_HOST_HEIGHT + 2
        )  # Height >= MIN_HOST_HEIGHT
        self.manager.add_host_section(
            "host2", 13, TestConfig.MIN_HOST_HEIGHT + 2
        )  # Height >= MIN_HOST_HEIGHT

        self.assertTrue(self.manager.validate_layout())

    def test_validate_layout_negative_start_y(self):
        """Test validation with negative start Y."""
        self.manager.add_host_section("host1", -1, 5)

        self.assertFalse(self.manager.validate_layout())

    def test_validate_layout_beyond_terminal_height(self):
        """Test validation with section beyond terminal height."""
        self.manager.add_host_section("host1", 20, 10)  # 20 + 10 = 30 > 24

        self.assertFalse(self.manager.validate_layout())

    def test_validate_layout_small_height(self):
        """Test validation with section height too small."""
        self.manager.add_host_section(
            "host1", 3, TestConfig.MIN_HOST_HEIGHT - 3
        )  # Too small

        self.assertFalse(self.manager.validate_layout())

    def test_validate_layout_overlapping_sections(self):
        """Test validation with overlapping sections."""
        self.manager.add_host_section("host1", 3, 5)
        self.manager.add_host_section("host2", 5, 5)  # Overlaps with host1

        self.assertFalse(self.manager.validate_layout())

    def test_sections_overlap(self):
        """Test section overlap detection."""
        section1 = HostSection("host1", 3, 5)
        section2 = HostSection("host2", 5, 5)  # Overlaps
        section3 = HostSection("host3", 10, 5)  # No overlap

        self.assertTrue(self.manager._sections_overlap(section1, section2))
        self.assertFalse(self.manager._sections_overlap(section1, section3))
        self.assertFalse(self.manager._sections_overlap(section2, section3))

    def test_sections_overlap_edge_cases(self):
        """Test section overlap edge cases."""
        section1 = HostSection("host1", 3, 5)  # 3-8
        section2 = HostSection("host2", 8, 5)  # 8-13 (touches but doesn't overlap)
        section3 = HostSection("host3", 7, 5)  # 7-12 (overlaps with section1)

        self.assertFalse(self.manager._sections_overlap(section1, section2))
        self.assertTrue(self.manager._sections_overlap(section1, section3))


class TestLayoutManagerLayoutInfo(unittest.TestCase):
    """Test layout information methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_get_layout_info(self):
        """Test getting comprehensive layout information."""
        self.manager.add_host_section("host1", 3, 5)
        self.manager.add_host_section("host2", 8, 5)

        info = self.manager.get_layout_info()

        self.assertEqual(info["terminal_width"], 80)
        self.assertEqual(info["terminal_height"], 24)
        self.assertEqual(info["total_hosts"], 3)
        self.assertEqual(info["visible_hosts"], 2)
        self.assertEqual(info["hidden_hosts"], 1)
        self.assertIn("max_visible_hosts", info)
        self.assertIn("available_height", info)
        self.assertIn("section_height", info)
        self.assertIn("is_small_terminal", info)
        self.assertIn("layout_valid", info)

    def test_get_layout_info_empty(self):
        """Test getting layout info with no sections."""
        info = self.manager.get_layout_info()

        self.assertEqual(info["visible_hosts"], 0)
        self.assertEqual(info["hidden_hosts"], 3)
        self.assertTrue(info["layout_valid"])  # Empty layout is valid


class TestLayoutManagerResize(unittest.TestCase):
    """Test layout resize functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_resize_layout(self):
        """Test resizing layout."""
        # Add some sections first
        self.manager.add_host_section("host1", 3, 10)
        self.manager.add_host_section("host2", 13, 10)

        # Resize layout
        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            new_sections = self.manager.resize_layout()

        # Should have recalculated sections (may be same number but different positions/sizes)
        self.assertIsInstance(new_sections, dict)
        # Verify that the sections were recalculated by checking the new sections are different
        self.assertNotEqual(len(new_sections), 0)  # Should have some sections


class TestLayoutManagerIntegration(unittest.TestCase):
    """Integration tests for LayoutManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = Mock()
        self.mock_terminal.width = 80
        self.mock_terminal.height = (
            TestConfig.MIN_TERMINAL_HEIGHT + 14
        )  # Normal terminal (24)
        self.hosts = ["host1", "host2", "host3", "host4", "host5"]

        # Mock Config class for consistent testing
        self.config_patcher = patch("layout_manager.Config", TestConfig)
        self.mock_config = self.config_patcher.start()

        self.manager = LayoutManager(self.mock_terminal, self.hosts)

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    def test_full_layout_cycle(self):
        """Test complete layout cycle."""
        # Setup layout
        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            host_sections = self.manager.setup_layout()

        # Verify layout is valid
        self.assertTrue(self.manager.validate_layout())

        # Check that sections don't overlap
        sections = list(host_sections.values())
        for i, section1 in enumerate(sections):
            for section2 in sections[i + 1 :]:
                self.assertFalse(self.manager._sections_overlap(section1, section2))

        # Check that all sections fit within terminal bounds
        for section in sections:
            self.assertGreaterEqual(section.start_y, 0)
            self.assertLessEqual(
                section.start_y + section.height, self.mock_terminal.height
            )

    def test_layout_consistency(self):
        """Test that layout information is consistent."""
        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            host_sections = self.manager.setup_layout()

        info = self.manager.get_layout_info()

        # Check consistency
        self.assertEqual(info["visible_hosts"], len(host_sections))
        self.assertEqual(info["hidden_hosts"], len(self.hosts) - len(host_sections))
        self.assertEqual(info["total_hosts"], len(self.hosts))

        # Check that visible hosts match
        visible_hosts = self.manager.get_visible_hosts()
        self.assertEqual(set(visible_hosts), set(host_sections.keys()))

    def test_small_terminal_integration(self):
        """Test integration with small terminal."""
        self.mock_terminal.height = TestConfig.MIN_TERMINAL_HEIGHT - 1  # Small terminal

        with patch.object(self.manager, "_warn_about_hidden_hosts"):
            host_sections = self.manager.setup_layout()

        # Should only show one host in small terminal
        self.assertEqual(len(host_sections), 1)
        self.assertTrue(self.manager.validate_layout())

        info = self.manager.get_layout_info()
        self.assertTrue(info["is_small_terminal"])


if __name__ == "__main__":
    unittest.main()
