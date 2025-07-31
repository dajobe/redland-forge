#!/usr/bin/python3
"""
Unit tests for HostSection class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from host_section import HostSection, BorderRenderer
from color_manager import ColorManager
from config import Config


class TestHostSectionInitialization(unittest.TestCase):
    """Test HostSection initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        section = HostSection("testhost", 5, 10)
        self.assertEqual(section.hostname, "testhost")
        self.assertEqual(section.start_y, 5)
        self.assertEqual(section.height, 10)
        self.assertEqual(section.status, "IDLE")
        self.assertEqual(section.current_step, "")
        self.assertEqual(section.duration, 0)
        self.assertEqual(section.total_lines_processed, 0)
        self.assertEqual(section.processed_lines, 0)
        self.assertEqual(section.step_trigger_line, "")
        self.assertIsNone(section.start_time)
        self.assertIsNone(section.completion_time)
        self.assertIsNotNone(section.last_update)

    def test_init_with_at_symbol(self):
        """Test initialization with hostname containing @."""
        section = HostSection("user@testhost", 5, 10)
        self.assertEqual(section.hostname, "user@testhost")
        self.assertEqual(section.get_display_hostname(), "testhost")

    def test_init_without_at_symbol(self):
        """Test initialization with hostname without @."""
        section = HostSection("testhost", 5, 10)
        self.assertEqual(section.hostname, "testhost")
        self.assertEqual(section.get_display_hostname(), "testhost")


class TestHostSectionOutputManagement(unittest.TestCase):
    """Test output management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    def test_add_output_basic(self):
        """Test adding output lines."""
        self.section.add_output("test line 1")
        self.assertEqual(self.section.total_lines_processed, 1)
        self.assertEqual(len(self.section.output_buffer), 1)

        self.section.add_output("test line 2")
        self.assertEqual(self.section.total_lines_processed, 2)
        self.assertEqual(len(self.section.output_buffer), 2)

    def test_add_output_updates_last_update(self):
        """Test that add_output updates last_update."""
        old_time = self.section.last_update
        time.sleep(0.001)  # Ensure time difference
        self.section.add_output("test line")
        self.assertGreater(self.section.last_update, old_time)

    def test_add_output_clears_buffer_when_full(self):
        """Test that buffer is cleared when it exceeds height limit."""
        # Add more lines than the height allows
        for i in range(20):
            self.section.add_output(f"line {i}")

        # Buffer should be cleared when it exceeds height - 4
        self.assertLessEqual(len(self.section.output_buffer), self.section.height - 4)


class TestHostSectionStatusManagement(unittest.TestCase):
    """Test status management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    @patch("time.time")
    def test_update_status_basic(self, mock_time):
        """Test basic status update."""
        mock_time.return_value = 100.0
        self.section.update_status("BUILDING", "configure")

        self.assertEqual(self.section.status, "BUILDING")
        self.assertEqual(self.section.current_step, "configure")
        self.assertEqual(self.section.start_time, 100.0)

    @patch("time.time")
    def test_update_status_without_step(self, mock_time):
        """Test status update without step."""
        mock_time.return_value = 100.0
        self.section.current_step = "existing_step"
        self.section.update_status("BUILDING")

        self.assertEqual(self.section.status, "BUILDING")
        self.assertEqual(
            self.section.current_step, "existing_step"
        )  # Should not change

    @patch("time.time")
    def test_update_status_sets_start_time(self, mock_time):
        """Test that start_time is set when status becomes BUILDING."""
        mock_time.return_value = 100.0
        self.section.update_status("BUILDING")

        self.assertEqual(self.section.start_time, 100.0)

    @patch("time.time")
    def test_update_status_calculates_duration(self, mock_time):
        """Test duration calculation."""
        mock_time.side_effect = [100.0, 105.0, 105.0]

        self.section.update_status("BUILDING")
        self.section.update_status("BUILDING")  # Update again

        self.assertEqual(self.section.duration, 5.0)

    @patch("time.time")
    def test_update_status_sets_completion_time(self, mock_time):
        """Test that completion_time is set for SUCCESS/FAILED."""
        mock_time.side_effect = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]

        self.section.update_status("SUCCESS")
        self.assertEqual(self.section.completion_time, 100.0)

        # Reset status and completion_time to test FAILED
        self.section.status = "BUILDING"
        self.section.completion_time = None
        self.section.update_status("FAILED")
        self.assertEqual(self.section.completion_time, 100.0)

    @patch("time.time")
    def test_update_status_updates_last_update_on_completion(self, mock_time):
        """Test that last_update is updated when status becomes SUCCESS/FAILED."""
        mock_time.side_effect = [100.0, 105.0, 105.0, 105.0, 105.0, 105.0]

        self.section.update_status("BUILDING")
        old_update = self.section.last_update
        self.section.update_status("SUCCESS")

        self.assertEqual(self.section.last_update, 105.0)


class TestHostSectionStepDetection(unittest.TestCase):
    """Test step detection methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    @patch("host_section.detect_build_step")
    def test_detect_step_from_output_new_step(self, mock_detect):
        """Test step detection when new step is found."""
        mock_detect.return_value = "configure"

        self.section.detect_step_from_output("configuring...")

        self.assertEqual(self.section.current_step, "configure")
        self.assertEqual(self.section.step_trigger_line, "configuring...")

    @patch("host_section.detect_build_step")
    def test_detect_step_from_output_no_new_step(self, mock_detect):
        """Test step detection when no new step is found."""
        mock_detect.return_value = None

        self.section.detect_step_from_output("some output")

        self.assertEqual(self.section.current_step, "")  # Should not change

    @patch("host_section.detect_build_step")
    @patch("host_section.logging")
    def test_detect_step_from_output_debug_logging(self, mock_logging, mock_detect):
        """Test debug logging for step detection."""
        mock_detect.return_value = "configure"

        self.section.detect_step_from_output("configuring...")

        mock_logging.debug.assert_called_with(
            "Step updated to 'configure' for testhost from line: 'configuring...' (was: '')"
        )


class TestHostSectionStatusColors(unittest.TestCase):
    """Test status color and symbol methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    def test_get_status_color_idle(self):
        """Test status color for IDLE."""
        self.section.status = "IDLE"
        color = self.section.get_status_color()
        self.assertEqual(color, ColorManager.get_status_ansi_color("IDLE"))

    def test_get_status_color_building(self):
        """Test status color for BUILDING."""
        self.section.status = "BUILDING"
        color = self.section.get_status_color()
        self.assertEqual(color, ColorManager.get_status_ansi_color("BUILDING"))

    def test_get_status_color_success(self):
        """Test status color for SUCCESS."""
        self.section.status = "SUCCESS"
        color = self.section.get_status_color()
        self.assertEqual(color, ColorManager.get_status_ansi_color("SUCCESS"))

    def test_get_status_color_failed(self):
        """Test status color for FAILED."""
        self.section.status = "FAILED"
        color = self.section.get_status_color()
        self.assertEqual(color, ColorManager.get_status_ansi_color("FAILED"))

    def test_get_status_color_unknown(self):
        """Test status color for unknown status."""
        self.section.status = "UNKNOWN_STATUS"
        color = self.section.get_status_color()
        self.assertEqual(color, ColorManager.get_status_ansi_color("UNKNOWN_STATUS"))

    def test_get_status_symbol_idle(self):
        """Test status symbol for IDLE."""
        self.section.status = "IDLE"
        symbol = self.section.get_status_symbol()
        self.assertEqual(symbol, "⏳")

    def test_get_status_symbol_building(self):
        """Test status symbol for BUILDING."""
        self.section.status = "BUILDING"
        symbol = self.section.get_status_symbol()
        self.assertEqual(symbol, "🔨")

    def test_get_status_symbol_success(self):
        """Test status symbol for SUCCESS."""
        self.section.status = "SUCCESS"
        symbol = self.section.get_status_symbol()
        self.assertEqual(symbol, "✓")

    def test_get_status_symbol_failed(self):
        """Test status symbol for FAILED."""
        self.section.status = "FAILED"
        symbol = self.section.get_status_symbol()
        self.assertEqual(symbol, "✗")

    def test_get_status_symbol_unknown(self):
        """Test status symbol for unknown status."""
        self.section.status = "UNKNOWN_STATUS"
        symbol = self.section.get_status_symbol()
        self.assertEqual(symbol, "")


class TestHostSectionRendering(unittest.TestCase):
    """Test rendering methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)
        self.mock_term = Mock()
        self.mock_term.width = 80
        self.mock_term.height = 24

    def test_should_render_within_bounds(self):
        """Test _should_render when section is within bounds."""
        result = self.section._should_render(self.mock_term)
        self.assertTrue(result)

    def test_should_render_outside_bounds(self):
        """Test _should_render when section would render outside bounds."""
        self.section.start_y = 20  # Would render outside bounds
        result = self.section._should_render(self.mock_term)
        self.assertFalse(result)

    @patch("host_section.BorderRenderer")
    def test_draw_borders(self, mock_border_renderer):
        """Test border drawing."""
        self.section._draw_borders(self.mock_term, 70)

        # Check that all border methods were called
        mock_border_renderer.draw_top_border.assert_called_once_with(
            self.mock_term, 5, 70
        )
        mock_border_renderer.draw_middle_border.assert_called_once_with(
            self.mock_term, 7, 70
        )
        mock_border_renderer.draw_bottom_border.assert_called_once_with(
            self.mock_term, 14, 70
        )

    @patch("host_section.BorderRenderer")
    @patch("host_section.TextFormatter")
    def test_render_header_basic(self, mock_text_formatter, mock_border_renderer):
        """Test header rendering."""
        mock_text_formatter.truncate_text.return_value = "truncated"
        mock_text_formatter.center_text.return_value = "centered"
        self.mock_term.move.return_value = ""

        self.section._render_header(self.mock_term, 70)

        mock_border_renderer.draw_content_line.assert_called_once()

    @patch("host_section.BorderRenderer")
    def test_render_header_with_duration_and_step(self, mock_border_renderer):
        """Test header rendering with duration and step."""
        self.section.status = "BUILDING"
        self.section.duration = 5.5
        self.section.current_step = "configure"
        self.mock_term.move.return_value = ""

        with patch("time.time", return_value=105.5):
            self.section.start_time = 100.0

        self.section._render_header(self.mock_term, 70)

        mock_border_renderer.draw_content_line.assert_called_once()

    @patch("host_section.BorderRenderer")
    def test_render_output_lines(self, mock_border_renderer):
        """Test output lines rendering."""
        # Add some output
        self.section.add_output("line 1")
        self.section.add_output("line 2")

        self.section._render_output_lines(self.mock_term, 70)

        # Should call draw_content_line for each output line
        self.assertGreater(mock_border_renderer.draw_content_line.call_count, 0)

    def test_prepare_display_lines_basic(self):
        """Test preparing display lines without step trigger."""
        recent_lines = ["line 1", "line 2", "line 3"]
        result = self.section._prepare_display_lines(recent_lines, 5)
        self.assertEqual(result, recent_lines)

    def test_prepare_display_lines_with_step_trigger(self):
        """Test preparing display lines with step trigger."""
        self.section.step_trigger_line = "step line"
        self.section.current_step = "configure"
        recent_lines = ["line 1", "line 2", "line 3"]

        result = self.section._prepare_display_lines(recent_lines, 5)

        # Should include step trigger line first
        self.assertIn("step line", result[0])
        self.assertIn("configure", result[0])

    def test_format_output_line_short(self):
        """Test formatting short output line."""
        line = "short line"
        result = self.section._format_output_line(line, 20)
        self.assertIn(line, result)

    def test_format_output_line_long(self):
        """Test formatting long output line."""
        line = "this is a very long line that should be truncated"
        result = self.section._format_output_line(line, 20)
        self.assertLessEqual(len(result), 20)

    @patch("host_section.BorderRenderer")
    def test_fill_remaining_lines(self, mock_border_renderer):
        """Test filling remaining lines."""
        self.section._fill_remaining_lines(self.mock_term, 8, 2, 5, 70)

        # Should call draw_empty_line for remaining lines
        self.assertEqual(mock_border_renderer.draw_empty_line.call_count, 3)

    @patch("host_section.BorderRenderer")
    def test_render_footer(self, mock_border_renderer):
        """Test footer rendering."""
        self.section.total_lines_processed = 10
        self.section.current_step = "configure"

        self.section._render_footer(self.mock_term, 70)

        mock_border_renderer.draw_content_line.assert_called_once()


class TestHostSectionUtilityMethods(unittest.TestCase):
    """Test utility methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    def test_get_display_hostname_with_at(self):
        """Test get_display_hostname with @ symbol."""
        self.section.hostname = "user@testhost"
        result = self.section.get_display_hostname()
        self.assertEqual(result, "testhost")

    def test_get_display_hostname_without_at(self):
        """Test get_display_hostname without @ symbol."""
        self.section.hostname = "testhost"
        result = self.section.get_display_hostname()
        self.assertEqual(result, "testhost")

    def test_is_completed_false(self):
        """Test is_completed when not completed."""
        self.section.status = "BUILDING"
        self.assertFalse(self.section.is_completed())

    def test_is_completed_success(self):
        """Test is_completed when SUCCESS."""
        self.section.status = "SUCCESS"
        self.assertTrue(self.section.is_completed())

    def test_is_completed_failed(self):
        """Test is_completed when FAILED."""
        self.section.status = "FAILED"
        self.assertTrue(self.section.is_completed())

    def test_get_completion_time_none(self):
        """Test get_completion_time when not completed."""
        self.assertIsNone(self.section.get_completion_time())

    def test_get_completion_time_set(self):
        """Test get_completion_time when completed."""
        self.section.completion_time = 100.0
        self.assertEqual(self.section.get_completion_time(), 100.0)

    @patch("time.time")
    def test_get_duration_with_start_time(self, mock_time):
        """Test get_duration with start time."""
        mock_time.side_effect = [100.0, 105.0]
        self.section.start_time = 100.0
        self.section.update_status("BUILDING")

        result = self.section.get_duration()
        self.assertEqual(result, 5.0)

    def test_get_duration_without_start_time(self):
        """Test get_duration without start time."""
        result = self.section.get_duration()
        self.assertEqual(result, 0.0)

    def test_reset(self):
        """Test reset method."""
        # Set some values
        self.section.status = "BUILDING"
        self.section.current_step = "configure"
        self.section.add_output("test line")
        self.section.start_time = 100.0
        self.section.completion_time = 105.0

        # Reset
        self.section.reset()

        # Check reset values
        self.assertEqual(self.section.status, "IDLE")
        self.assertEqual(self.section.current_step, "")
        self.assertEqual(len(self.section.output_buffer), 0)
        self.assertEqual(self.section.total_lines_processed, 0)
        self.assertEqual(self.section.processed_lines, 0)
        self.assertEqual(self.section.step_trigger_line, "")
        self.assertIsNone(self.section.start_time)
        self.assertIsNone(self.section.completion_time)
        self.assertEqual(self.section.duration, 0)


class TestHostSectionIntegration(unittest.TestCase):
    """Integration tests for HostSection."""

    def setUp(self):
        """Set up test fixtures."""
        self.section = HostSection("testhost", 5, 10)

    @patch("host_section.BorderRenderer")
    def test_full_render_cycle(self, mock_border_renderer):
        """Test a full render cycle."""
        mock_term = Mock()
        mock_term.width = 80
        mock_term.height = 24
        mock_term.move.return_value = ""

        # Add some output and update status
        self.section.add_output("configuring...")
        self.section.update_status("BUILDING", "configure")

        # Render
        self.section.render(mock_term)

        # Verify all rendering methods were called
        self.assertTrue(mock_border_renderer.draw_top_border.called)
        self.assertTrue(mock_border_renderer.draw_content_line.called)
        self.assertTrue(mock_border_renderer.draw_bottom_border.called)

    def test_output_buffer_integration(self):
        """Test integration with output buffer."""
        # Add multiple lines
        for i in range(5):
            self.section.add_output(f"line {i}")

        # Check buffer state
        self.assertEqual(len(self.section.output_buffer), 5)
        self.assertEqual(self.section.total_lines_processed, 5)

        # Get recent lines
        recent_lines = self.section.output_buffer.get_recent_lines(3)
        self.assertEqual(len(recent_lines), 3)
        self.assertEqual(recent_lines[-1], "line 4")

    @patch("host_section.detect_build_step")
    def test_step_detection_integration(self, mock_detect):
        """Test integration with step detection."""
        mock_detect.return_value = "configure"

        # Add output that triggers step detection
        self.section.add_output("configuring...")
        self.section.detect_step_from_output("configuring...")

        # Check step was updated
        self.assertEqual(self.section.current_step, "configure")
        self.assertEqual(self.section.step_trigger_line, "configuring...")


if __name__ == "__main__":
    unittest.main()
