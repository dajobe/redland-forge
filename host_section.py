#!/usr/bin/python3
"""
Host Section Module

A module for managing and rendering individual host sections in the TUI.
"""

import logging
import time
from typing import List

from blessed import Terminal

from output_buffer import OutputBuffer
from text_formatter import TextFormatter, visual_length, format_duration
from config import Config
from build_step_detector import detect_build_step, detect_step_completion
from color_manager import ColorManager, Colors


class BorderRenderer:
    """Utility class for border drawing operations."""

    @staticmethod
    def draw_top_border(
        term: Terminal, y: int, width: int, border_color: str = None, is_focused: bool = False
    ) -> None:
        """Draw a top border line."""
        if border_color is None:
            border_color = ColorManager.get_ansi_color(
                ColorManager.DEFAULT_BORDER_COLOR
            )
        
        # Use bright color for focused host
        if is_focused:
            border_color = ColorManager.get_ansi_color("BRIGHT_YELLOW")
        
        border = (
            border_color
            + "┌"
            + "─" * (width - 2)
            + "┐"
            + ColorManager.get_ansi_color("RESET")
        )
        with term.location(1, y):
            print(border)

    @staticmethod
    def draw_bottom_border(
        term: Terminal, y: int, width: int, border_color: str = None, is_focused: bool = False
    ) -> None:
        """Draw a bottom border line."""
        if border_color is None:
            border_color = ColorManager.get_ansi_color(
                ColorManager.DEFAULT_BORDER_COLOR
            )
        
        # Use bright color for focused host
        if is_focused:
            border_color = ColorManager.get_ansi_color("BRIGHT_YELLOW")
        
        border = (
            border_color
            + "└"
            + "─" * (width - 2)
            + "┘"
            + ColorManager.get_ansi_color("RESET")
        )
        with term.location(1, y):
            print(border)

    @staticmethod
    def draw_middle_border(
        term: Terminal, y: int, width: int, border_color: str = None, is_focused: bool = False
    ) -> None:
        """Draw a middle border line."""
        if border_color is None:
            border_color = ColorManager.get_ansi_color(
                ColorManager.DEFAULT_BORDER_COLOR
            )
        
        # Use bright color for focused host
        if is_focused:
            border_color = ColorManager.get_ansi_color("BRIGHT_YELLOW")
        
        border = (
            border_color
            + "├"
            + "─" * (width - 2)
            + "┤"
            + ColorManager.get_ansi_color("RESET")
        )
        with term.location(1, y):
            print(border)

    @staticmethod
    def draw_content_line(
        term: Terminal, y: int, content: str, width: int, border_color: str = None
    ) -> None:
        """Draw a content line with borders."""
        if border_color is None:
            border_color = ColorManager.get_ansi_color(
                ColorManager.DEFAULT_BORDER_COLOR
            )
        line = TextFormatter.build_bordered_line(content, width, "│ ", " │")
        with term.location(1, y):
            print(border_color + line + ColorManager.get_ansi_color("RESET"))

    @staticmethod
    def draw_empty_line(
        term: Terminal, y: int, width: int, border_color: str = None
    ) -> None:
        """Draw an empty line with borders."""
        if border_color is None:
            border_color = ColorManager.get_ansi_color(
                ColorManager.DEFAULT_BORDER_COLOR
            )
        line = (
            border_color
            + "│"
            + " " * (width - 2)
            + "│"
            + ColorManager.get_ansi_color("RESET")
        )
        with term.location(1, y):
            print(line)


class HostSection:
    """Represents a host section in the TUI."""

    def __init__(
        self, hostname: str, start_y: int, height: int, step_change_callback=None
    ):
        """
        Initialize a host section.

        Args:
            hostname: Name of the host
            start_y: Starting Y position for rendering
            height: Height of the section
            step_change_callback: Optional callback function for step changes
        """
        self.hostname = hostname
        self.start_y = start_y
        self.height = height
        self.status = "IDLE"
        self.output_buffer = OutputBuffer(Config.MAX_OUTPUT_LINES_PER_HOST)
        self.processed_lines = 0  # Track how many lines we've processed from the result
        self.total_lines_processed = (
            0  # Track total lines processed (not just displayed)
        )
        self.step_trigger_line = ""  # Store the line that triggered the current step
        self.start_time = None
        self.current_step = ""
        self.duration = 0
        self.last_update = time.time()
        self.completion_time = None  # Added for 10-second timeout
        self.step_change_callback = step_change_callback
        logging.debug(
            f"HostSection created for {self.hostname} with step_change_callback: {step_change_callback is not None}"
        )
        self.progress_info = (
            {}
        )  # Store progress information from progress display manager

    def add_output(self, line: str) -> None:
        """
        Add a line of output to the buffer.

        Args:
            line: Output line to add
        """
        self.output_buffer.add_line(line)
        self.total_lines_processed += 1  # Track total lines processed
        self.last_update = time.time()

        # Keep only last N lines to fit in section height
        max_lines = self.height - 4  # -4 for header, separator, and bottom border
        if len(self.output_buffer) > max_lines:
            self.output_buffer.clear()  # Clear the buffer to keep only recent lines

    def update_status(self, status: str, step: str = "") -> None:
        """
        Update build status and current step.

        Args:
            status: New status
            step: New step (optional)
        """
        old_status = self.status
        self.status = status
        if step:
            self.current_step = step

        if self.start_time is None and status == "BUILDING":
            self.start_time = time.time()

        if self.start_time:
            self.duration = time.time() - self.start_time

        # Set completion time when status changes to SUCCESS or FAILED
        if status in ["SUCCESS", "FAILED"] and old_status not in ["SUCCESS", "FAILED"]:
            self.completion_time = time.time()
            logging.debug(f"Host {self.hostname} completed at {self.completion_time}")

        # Update last_update when status changes to SUCCESS or FAILED
        if status in ["SUCCESS", "FAILED"] and old_status != status:
            self.last_update = time.time()

    def detect_step_from_output(self, line: str) -> None:
        """
        Detect and update the current step based on output line.

        Args:
            line: Output line to analyze
        """
        # Debug: log the current state before step detection
        logging.debug(
            f"Step detection for {self.hostname}: line='{line.strip()}', current_step='{self.current_step}', callback_exists={self.step_change_callback is not None}"
        )

        new_step = detect_build_step(line, self.current_step)
        logging.debug(
            f"detect_build_step returned: '{new_step}' for {self.hostname} (current: '{self.current_step}')"
        )

        if new_step:
            old_step = self.current_step
            self.current_step = new_step
            self.step_trigger_line = line  # Store the line that triggered this step
            logging.debug(
                f"Step updated to '{new_step}' for {self.hostname} from line: '{line.strip()}' (was: '{old_step}')"
            )
            # Add additional debug info for step changes
            logging.info(
                f"STEP CHANGE: {self.hostname} '{old_step}' -> '{new_step}' from '{line.strip()}'"
            )

            # Call step change callback if provided
            if self.step_change_callback:
                try:
                    logging.debug(
                        f"Calling step change callback for {self.hostname}: {old_step} -> {new_step}"
                    )
                    self.step_change_callback(self.hostname, new_step)
                    logging.debug(f"Step change callback completed for {self.hostname}")
                except Exception as e:
                    logging.warning(
                        f"Error in step change callback for {self.hostname}: {e}"
                    )
            else:
                logging.debug(f"No step change callback available for {self.hostname}")
        else:
            # Check if the current step has completed
            if detect_step_completion(line, self.current_step):
                logging.debug(
                    f"Step '{self.current_step}' completed for {self.hostname} from line: '{line.strip()}'"
                )
                # Add additional debug info for step completions
                logging.info(
                    f"STEP COMPLETION: {self.hostname} '{self.current_step}' completed from '{line.strip()}'"
                )

                # Automatically advance to the next step
                next_step = self._get_next_step(self.current_step)
                if next_step:
                    old_step = self.current_step
                    self.current_step = next_step
                    logging.debug(
                        f"Auto-advanced step from '{old_step}' to '{next_step}' for {self.hostname}"
                    )
                    logging.info(
                        f"STEP AUTO-ADVANCE: {self.hostname} '{old_step}' -> '{next_step}' after completion"
                    )

                    # Call step change callback if provided
                    if self.step_change_callback:
                        try:
                            logging.debug(
                                f"Calling step change callback (auto-advance) for {self.hostname}: {old_step} -> {next_step}"
                            )
                            self.step_change_callback(self.hostname, next_step)
                            logging.debug(
                                f"Step change callback (auto-advance) completed for {self.hostname}"
                            )
                        except Exception as e:
                            logging.warning(
                                f"Error in step change callback (auto-advance) for {self.hostname}: {e}"
                            )
                    else:
                        logging.debug(
                            f"No step change callback available for {self.hostname} (auto-advance)"
                        )
            # Debug: log when we don't detect a step change
            elif "completed" in line or "succeeded" in line or "Total time" in line:
                logging.debug(
                    f"No step change detected for {self.hostname} from line: '{line.strip()}' (current step: {self.current_step})"
                )

    def get_status_color(self) -> str:
        """
        Get color for current status.

        Returns:
            ANSI color code for the current status
        """
        return ColorManager.get_status_ansi_color(self.status)

    def get_status_symbol(self) -> str:
        """
        Get symbol for current status.

        Returns:
            Symbol for the current status
        """
        return ColorManager.get_status_symbol(self.status)

    def _get_next_step(self, current_step: str) -> str:
        """
        Get the next step in the build sequence.

        Args:
            current_step: Current step name

        Returns:
            Next step name, or empty string if no next step
        """
        step_sequence = [
            "extract",
            "configure",
            "make",
            "check",
            "install",
            "completed",
        ]

        try:
            current_index = step_sequence.index(current_step)
            if current_index < len(step_sequence) - 1:
                return step_sequence[current_index + 1]
        except ValueError:
            # Current step not in sequence, return empty string
            pass

        return ""

    def render(self, term: Terminal, is_focused: bool = False) -> None:
        """
        Render the host section with a drawn box.

        Args:
            term: Terminal object for rendering
            is_focused: Whether this host is currently focused
        """
        if not self._should_render(term):
            return

        # Log state periodically for debugging (every 10 seconds)
        current_time = time.time()
        if (
            not hasattr(self, "_last_state_log")
            or current_time - getattr(self, "_last_state_log", 0) > 10
        ):
            self.log_current_state()
            self._last_state_log = current_time

        box_width = term.width - Config.TERMINAL_MARGIN
        self._draw_borders(term, box_width, is_focused)
        self._render_header(term, box_width, is_focused)
        self._render_output_lines(term, box_width)

    def _should_render(self, term: Terminal) -> bool:
        """
        Check if this section should be rendered.

        Args:
            term: Terminal object

        Returns:
            True if section should be rendered, False otherwise
        """
        if self.start_y + self.height > term.height - Config.FOOTER_HEIGHT:
            logging.debug(
                f"Host section {self.hostname} would render outside bounds "
                f"(y={self.start_y}, height={self.height}, term_height={term.height})"
            )
            return False
        return True

    def _draw_borders(self, term: Terminal, box_width: int, is_focused: bool = False) -> None:
        """
        Draw the border lines for this section.

        Args:
            term: Terminal object
            box_width: Width of the box
            is_focused: Whether this host is currently focused
        """
        # Top border
        BorderRenderer.draw_top_border(term, self.start_y, box_width, is_focused=is_focused)

        # Middle border
        BorderRenderer.draw_middle_border(term, self.start_y + 2, box_width, is_focused=is_focused)

        # Bottom border
        BorderRenderer.draw_bottom_border(
            term, self.start_y + self.height - 1, box_width, is_focused=is_focused
        )

    def _render_header(self, term: Terminal, box_width: int, is_focused: bool = False) -> None:
        """
        Render the header line with status information.

        Args:
            term: Terminal object
            box_width: Width of the box
            is_focused: Whether this host is currently focused
        """
        status_color = self.get_status_color()
        symbol = self.get_status_symbol()

        # Extract just the hostname part if it contains @
        display_hostname = (
            self.hostname.split("@")[-1] if "@" in self.hostname else self.hostname
        )
        
        # Add focus indicator
        focus_indicator = "▶ " if is_focused else "  "
        header = f"{focus_indicator}{symbol} {display_hostname} [{self.status}]"

        # Add duration and current step
        if self.duration > 0:
            header += f" ({format_duration(self.duration)})"
        if self.current_step:
            header += f" - {self.current_step}"
            # Add debug logging for step display
            logging.debug(
                f"Displaying step '{self.current_step}' in header for {self.hostname}"
            )
        else:
            logging.debug(f"No current step to display for {self.hostname}")

        # Add progress information if available
        if self.progress_info:
            progress_parts = []

            # Add progress percentage
            if self.progress_info.get("progress"):
                progress_parts.append(self.progress_info["progress"])

            # Add time estimate
            if self.progress_info.get("time_estimate"):
                progress_parts.append(self.progress_info["time_estimate"])

            if progress_parts:
                header += f" | {' | '.join(progress_parts)}"
                logging.debug(
                    f"Displaying progress info for {self.hostname}: {progress_parts}"
                )

        # Format header with proper coloring and centering
        header_content = status_color + header + ColorManager.get_ansi_color("RESET")
        available_width = box_width - Config.BORDER_PADDING

        # Truncate if too long
        if visual_length(header_content) > available_width:
            header_content = TextFormatter.truncate_text(
                header_content, available_width
            )

        # Center the header
        header_content = TextFormatter.center_text(header_content, available_width)

        # Draw the header line
        BorderRenderer.draw_content_line(
            term, self.start_y + 1, header_content, box_width
        )

    def _render_output_lines(self, term: Terminal, box_width: int) -> None:
        """
        Render the output lines section.

        Args:
            term: Terminal object
            box_width: Width of the box
        """
        output_start = self.start_y + 3
        max_lines = self.height - 3  # Leave room for header and bottom border
        available_width = box_width - Config.BORDER_PADDING

        # Get recent lines to display
        recent_lines = self.output_buffer.get_recent_lines(max_lines)
        display_lines = self._prepare_display_lines(recent_lines, max_lines)

        # Render each line
        for i, line in enumerate(display_lines):
            if (
                output_start + i >= self.start_y + self.height - 1
            ):  # Leave room for bottom border
                break

            # Format the line
            formatted_line = self._format_output_line(line, available_width)

            # Draw the line
            BorderRenderer.draw_content_line(
                term, output_start + i, formatted_line, box_width
            )

        # Fill remaining lines with empty space
        self._fill_remaining_lines(
            term, output_start, len(display_lines), max_lines, box_width
        )

    def _prepare_display_lines(
        self, recent_lines: List[str], max_lines: int
    ) -> List[str]:
        """
        Prepare lines for display, including step trigger line if needed.

        Args:
            recent_lines: Recent output lines
            max_lines: Maximum number of lines to display

        Returns:
            List of lines to display
        """
        display_lines = []

        # Always show the step trigger line if we have one and a current step
        if self.step_trigger_line and self.current_step:
            step_indicator = f"[STEP: {self.current_step}] "
            display_lines.append(
                ColorManager.get_ansi_color("BRIGHT_MAGENTA")
                + step_indicator
                + ColorManager.get_ansi_color("RESET")
                + self.step_trigger_line
            )
            # Add recent lines, but leave room for the step trigger line
            display_lines.extend(recent_lines[-(max_lines - 1) :])
            logging.debug(
                f"Showing step trigger line for {self.hostname}: '{self.step_trigger_line}' with step '{self.current_step}'"
            )
        else:
            display_lines = recent_lines
            if self.step_trigger_line:
                logging.debug(
                    f"Step trigger line already in recent lines for {self.hostname}: '{self.step_trigger_line}'"
                )
            else:
                logging.debug(f"No step trigger line for {self.hostname}")

        return display_lines

    def _format_output_line(self, line: str, available_width: int) -> str:
        """
        Format a single output line for display.

        Args:
            line: Line to format
            available_width: Available width for the line

        Returns:
            Formatted line
        """
        # Truncate line if too long
        if visual_length(line) > available_width:
            line = TextFormatter.truncate_text(line, available_width)

        # Pad the line to fill the available width
        return TextFormatter.pad_text(line, available_width, "left")

    def _fill_remaining_lines(
        self,
        term: Terminal,
        output_start: int,
        lines_rendered: int,
        max_lines: int,
        box_width: int,
    ) -> None:
        """
        Fill remaining lines with empty space.

        Args:
            term: Terminal object
            output_start: Starting Y position for output
            lines_rendered: Number of lines already rendered
            max_lines: Maximum number of lines
            box_width: Width of the box
        """
        for i in range(lines_rendered, max_lines):
            if (
                output_start + i >= self.start_y + self.height - 1
            ):  # Leave room for bottom border
                break
            BorderRenderer.draw_empty_line(term, output_start + i, box_width)


    def get_display_hostname(self) -> str:
        """
        Get the display hostname (without username if present).

        Returns:
            Display hostname
        """
        return self.hostname.split("@")[-1] if "@" in self.hostname else self.hostname

    def is_completed(self) -> bool:
        """
        Check if the host section is completed.

        Returns:
            True if completed, False otherwise
        """
        return self.status in ["SUCCESS", "FAILED"]

    def get_completion_time(self) -> float:
        """
        Get the completion time.

        Returns:
            Completion time or None if not completed
        """
        return self.completion_time

    def get_duration(self) -> float:
        """
        Get the current duration.

        Returns:
            Current duration in seconds
        """
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

    def reset(self) -> None:
        """Reset the host section to initial state."""
        self.status = "IDLE"
        self.output_buffer.clear()
        self.processed_lines = 0
        self.total_lines_processed = 0
        self.step_trigger_line = ""
        self.start_time = None
        self.current_step = ""
        self.duration = 0
        self.last_update = time.time()
        self.completion_time = None

    def log_current_state(self) -> None:
        """Log the current state for debugging."""
        logging.info(
            f"STATE: {self.hostname} status='{self.status}' step='{self.current_step}' "
            f"trigger_line='{self.step_trigger_line}' lines={self.total_lines_processed}"
        )
