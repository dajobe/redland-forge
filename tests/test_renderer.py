#!/usr/bin/python3
"""
Tests for the Renderer module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from blessed import Terminal

from redland_forge.renderer import Renderer
from redland_forge.statistics_manager import StatisticsManager
from redland_forge.host_section import HostSection
from redland_forge.config import Config


def create_mock_terminal():
    """Create a properly mocked terminal for testing."""
    mock_terminal = Mock()
    mock_terminal.width = 80
    mock_terminal.height = 24
    # Mock the clear method
    mock_terminal.clear.return_value = ""
    # Mock the location context manager
    mock_location = Mock()
    mock_location.__enter__ = Mock(return_value=None)
    mock_location.__exit__ = Mock(return_value=None)
    mock_terminal.location.return_value = mock_location
    return mock_terminal


class TestRendererInitialization(unittest.TestCase):
    """Test Renderer initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_init_basic(self):
        """Test basic initialization."""
        self.assertEqual(self.renderer.term, self.mock_terminal)
        self.assertEqual(self.renderer.statistics_manager, self.mock_statistics_manager)
        self.assertEqual(self.renderer.last_clear, 0)
        self.assertEqual(self.renderer.last_render, 0)
        self.assertEqual(self.renderer.last_timer_update, 0)


class TestRendererTimerMethods(unittest.TestCase):
    """Test Renderer timer-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_update_timers(self):
        """Test updating timers for host sections."""
        # Create mock host sections with start times
        mock_section1 = Mock(spec=HostSection)
        mock_section1.start_time = time.time() - 10  # 10 seconds ago

        mock_section2 = Mock(spec=HostSection)
        mock_section2.start_time = time.time() - 5  # 5 seconds ago

        host_sections = {"host1": mock_section1, "host2": mock_section2}

        self.renderer.update_timers(host_sections)

        # Check that durations were updated
        self.assertAlmostEqual(mock_section1.duration, 10, delta=1)
        self.assertAlmostEqual(mock_section2.duration, 5, delta=1)

    def test_update_timers_no_start_time(self):
        """Test updating timers when sections have no start time."""
        mock_section = Mock(spec=HostSection)
        mock_section.start_time = None

        host_sections = {"host1": mock_section}

        # Should not raise an exception
        self.renderer.update_timers(host_sections)

        # Duration should not be set
        self.assertFalse(hasattr(mock_section, "duration"))

    def test_needs_timer_update_false(self):
        """Test timer update check when not needed."""
        self.renderer.last_timer_update = time.time()
        self.assertFalse(self.renderer.needs_timer_update())

    def test_needs_timer_update_true(self):
        """Test timer update check when needed."""
        self.renderer.last_timer_update = time.time() - (
            Config.TIMER_UPDATE_INTERVAL_SECONDS + 1
        )
        self.assertTrue(self.renderer.needs_timer_update())


class TestRendererRenderLogic(unittest.TestCase):
    """Test Renderer render logic methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_needs_render_first_time(self):
        """Test render check for first render."""
        self.assertTrue(self.renderer.needs_render(False, False))

    def test_needs_render_with_updates(self):
        """Test render check when there are updates."""
        self.renderer.last_clear = time.time()
        self.assertTrue(self.renderer.needs_render(True, False))

    def test_needs_render_with_timer_update(self):
        """Test render check when timer update is needed."""
        self.renderer.last_clear = time.time()
        self.assertTrue(self.renderer.needs_render(False, True))

    def test_needs_render_no_updates(self):
        """Test render check when no updates are needed."""
        self.renderer.last_clear = time.time()
        self.renderer.last_render = time.time()
        self.assertFalse(self.renderer.needs_render(False, False))

    def test_needs_render_min_interval(self):
        """Test render check respects minimum interval."""
        self.renderer.last_clear = time.time()
        self.renderer.last_render = time.time() - (
            Config.MIN_RENDER_INTERVAL_SECONDS - 0.1
        )
        self.assertFalse(self.renderer.needs_render(True, False))

    def test_needs_render_min_interval_with_timer(self):
        """Test render check allows timer updates even within min interval."""
        self.renderer.last_clear = time.time()
        self.renderer.last_render = time.time() - (
            Config.MIN_RENDER_INTERVAL_SECONDS - 0.1
        )
        self.assertTrue(self.renderer.needs_render(False, True))


class TestRendererHostSectionRendering(unittest.TestCase):
    """Test Renderer host section rendering."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_render_host_sections_building(self):
        """Test rendering host sections with building status."""
        mock_section = Mock(spec=HostSection)
        mock_section.last_update = time.time()

        host_sections = {"host1": mock_section}
        ssh_results = {"host1": {"status": "BUILDING"}}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 1)
        mock_section.render.assert_called_once_with(self.mock_terminal, False)

    def test_render_host_sections_success_recent(self):
        """Test rendering host sections with recent success."""
        mock_section = Mock(spec=HostSection)
        mock_section.last_update = time.time() - (
            Config.HOST_VISIBILITY_TIMEOUT_SECONDS - 1
        )

        host_sections = {"host1": mock_section}
        ssh_results = {"host1": {"status": "SUCCESS"}}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 1)
        mock_section.render.assert_called_once_with(self.mock_terminal, False)

    def test_render_host_sections_success_old(self):
        """Test rendering host sections with old success."""
        mock_section = Mock(spec=HostSection)
        mock_section.last_update = time.time() - (
            Config.HOST_VISIBILITY_TIMEOUT_SECONDS + 1
        )

        host_sections = {"host1": mock_section}
        ssh_results = {"host1": {"status": "SUCCESS"}}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 0)
        mock_section.render.assert_not_called()

    def test_render_host_sections_failed_recent(self):
        """Test rendering host sections with recent failure."""
        mock_section = Mock(spec=HostSection)
        mock_section.last_update = time.time() - (
            Config.HOST_VISIBILITY_TIMEOUT_SECONDS - 1
        )

        host_sections = {"host1": mock_section}
        ssh_results = {"host1": {"status": "FAILED"}}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 1)
        mock_section.render.assert_called_once_with(self.mock_terminal, False)

    def test_render_host_sections_failed_old(self):
        """Test rendering host sections with old failure."""
        mock_section = Mock(spec=HostSection)
        mock_section.last_update = time.time() - (
            Config.HOST_VISIBILITY_TIMEOUT_SECONDS + 1
        )

        host_sections = {"host1": mock_section}
        ssh_results = {"host1": {"status": "FAILED"}}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 0)
        mock_section.render.assert_not_called()

    def test_render_host_sections_no_results(self):
        """Test rendering host sections with no SSH results."""
        mock_section = Mock(spec=HostSection)
        host_sections = {"host1": mock_section}
        ssh_results = {}

        visible_count = self.renderer.render_host_sections(
            host_sections, ssh_results, None
        )

        self.assertEqual(visible_count, 0)
        mock_section.render.assert_not_called()


class TestRendererCompletionMessage(unittest.TestCase):
    """Test Renderer completion message rendering."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_render_completion_message_with_visible_hosts(self):
        """Test completion message when hosts are visible."""
        visible_hosts = ["host1"]
        ssh_results = {"host1": {"status": "BUILDING"}}
        connection_queue = []
        active_connections = {}

        # Should not call print when hosts are visible
        with patch("builtins.print") as mock_print:
            self.renderer.render_completion_message(
                visible_hosts, ssh_results, connection_queue, active_connections
            )
            mock_print.assert_not_called()

    def test_render_completion_message_all_completed(self):
        """Test completion message when all builds are completed."""
        visible_hosts = []
        ssh_results = {"host1": {"status": "SUCCESS"}}
        connection_queue = []
        active_connections = {}

        with patch("builtins.print") as mock_print:
            self.renderer.render_completion_message(
                visible_hosts, ssh_results, connection_queue, active_connections
            )
            # Should call print for the completion message
            self.assertGreater(mock_print.call_count, 0)

    def test_render_completion_message_processing(self):
        """Test completion message when builds are still processing."""
        visible_hosts = []
        ssh_results = {}
        connection_queue = []
        active_connections = {"host1": Mock()}

        with patch("builtins.print") as mock_print:
            self.renderer.render_completion_message(
                visible_hosts, ssh_results, connection_queue, active_connections
            )
            # Should call print for the processing message
            self.assertGreater(mock_print.call_count, 0)


class TestRendererUtilityMethods(unittest.TestCase):
    """Test Renderer utility methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_clear_screen(self):
        """Test screen clearing."""
        with patch("builtins.print") as mock_print:
            self.renderer.clear_screen()
            mock_print.assert_called_once()

    def test_flush_output(self):
        """Test output flushing."""
        with patch("sys.stdout.flush") as mock_flush:
            self.renderer.flush_output()
            mock_flush.assert_called_once()

    def test_update_timestamps(self):
        """Test timestamp updates."""
        current_time = time.time()
        self.renderer.update_timestamps(True)

        self.assertGreater(self.renderer.last_clear, 0)
        self.assertGreater(self.renderer.last_render, 0)
        self.assertGreater(self.renderer.last_timer_update, 0)

    def test_update_timestamps_no_timer_update(self):
        """Test timestamp updates without timer update."""
        current_time = time.time()
        self.renderer.update_timestamps(False)

        self.assertGreater(self.renderer.last_clear, 0)
        self.assertGreater(self.renderer.last_render, 0)
        # last_timer_update should remain unchanged
        self.assertEqual(self.renderer.last_timer_update, 0)


class TestRendererIntegration(unittest.TestCase):
    """Test Renderer integration scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_terminal = create_mock_terminal()
        self.mock_statistics_manager = Mock(spec=StatisticsManager)
        self.renderer = Renderer(self.mock_terminal, self.mock_statistics_manager)

    def test_render_full_ui_success(self):
        """Test successful full UI rendering."""
        tarball = "test.tar.gz"
        host_sections = {}
        ssh_results = {}
        connection_queue = []
        active_connections = {}

        # Mock the statistics manager
        self.mock_statistics_manager.calculate_statistics.return_value = {
            "visible_hosts": 0,
            "total_hosts": 0,
            "active": 0,
            "completed": 0,
            "failed": 0,
            "overall_progress": 0.0,
            "total_completed": 0,
        }

        with patch("builtins.print") as mock_print:
            self.renderer.render_full_ui(
                tarball,
                host_sections,
                ssh_results,
                connection_queue,
                active_connections,
                focused_host=None,
            )
            # Should call print multiple times for the UI
            self.assertGreater(mock_print.call_count, 0)

    def test_render_full_ui_exception_fallback(self):
        """Test fallback to simple output mode on exception."""
        tarball = "test.tar.gz"
        host_sections = {}
        ssh_results = {}
        connection_queue = []
        active_connections = {}

        # Mock terminal to raise exception
        self.mock_terminal.clear.side_effect = Exception("Terminal error")

        with patch("builtins.print") as mock_print:
            self.renderer.render_full_ui(
                tarball,
                host_sections,
                ssh_results,
                connection_queue,
                active_connections,
                focused_host=None,
            )
            # Should call print for error message and fallback
            self.assertGreater(mock_print.call_count, 0)

    def test_simple_output_mode(self):
        """Test simple output mode fallback."""
        host_sections = {"host1": Mock()}
        ssh_results = {"host1": {"status": "SUCCESS", "output": ["line1", "line2"]}}

        with patch("builtins.print") as mock_print:
            self.renderer._simple_output_mode(host_sections, ssh_results)
            # Should call print for the simple output
            self.assertGreater(mock_print.call_count, 0)


if __name__ == "__main__":
    unittest.main()
