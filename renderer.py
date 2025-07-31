#!/usr/bin/python3
"""
Renderer Module

A module for handling all UI rendering logic in the TUI.
"""

import logging
import time
from typing import Dict, Any

from blessed import Terminal

from config import Config
from color_manager import ColorManager
from host_section import Colors
from text_formatter import visual_length
from statistics_manager import StatisticsManager


class Renderer:
    """Handles all UI rendering logic for the TUI."""

    def __init__(self, terminal: Terminal, statistics_manager: StatisticsManager):
        """
        Initialize the renderer.

        Args:
            terminal: Blessed terminal object
            statistics_manager: Statistics manager for build data
        """
        self.term = terminal
        self.statistics_manager = statistics_manager
        self.last_clear = 0
        self.last_render = 0
        self.last_timer_update = 0

    def render_header(
        self,
        tarball: str,
        host_sections: Dict[str, Any],
        ssh_results: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Render the header with a nice border.

        Args:
            tarball: Name of the tarball being built
            host_sections: Dictionary of host sections
            ssh_results: Dictionary of SSH results
        """
        logging.debug(
            f"Terminal dimensions: width={self.term.width}, height={self.term.height}"
        )

        header = "Build Redland - Parallel Build Monitor"
        tarball_info = f"Tarball: {tarball}"

        # Get statistics using the statistics manager
        stats = self.statistics_manager.calculate_statistics(host_sections, ssh_results)
        host_info = f"Hosts: {stats['visible_hosts']}/{stats['total_hosts']} | Active: {stats['active']}"
        subtitle = f"{tarball_info} | {host_info}"

        # Use consistent border color (white) for all borders
        border_color = ColorManager.get_ansi_color(ColorManager.DEFAULT_BORDER_COLOR)

        # Handle small terminals
        if self.term.height < 10:
            # Simple header for small terminals
            with self.term.location(0, 0):
                print(
                    ColorManager.get_ansi_color("BRIGHT_CYAN")
                    + header
                    + ColorManager.get_ansi_color("RESET")
                )
            with self.term.location(0, 1):
                print(
                    ColorManager.get_ansi_color("DIM")
                    + subtitle
                    + ColorManager.get_ansi_color("RESET")
                )
        else:
            # Full bordered header - use proper cursor positioning
            # Top border
            top_border = (
                border_color
                + "┌"
                + "─" * (self.term.width - 2)
                + "┐"
                + ColorManager.get_ansi_color("RESET")
            )
            with self.term.location(0, 0):
                print(top_border)

            # Title line - manually center the content
            title_content = (
                ColorManager.get_ansi_color("BRIGHT_CYAN")
                + header
                + ColorManager.get_ansi_color("RESET")
            )
            title_width = visual_length(title_content)
            available_width = self.term.width - 4  # Account for borders and padding
            left_padding = (available_width - title_width) // 2
            right_padding = available_width - title_width - left_padding
            title_line = (
                border_color
                + "│ "
                + ColorManager.get_ansi_color("RESET")
                + (" " * left_padding)
                + title_content
                + (" " * right_padding)
                + border_color
                + " │"
                + ColorManager.get_ansi_color("RESET")
            )
            with self.term.location(0, 1):
                print(title_line)

            # Subtitle line - manually center the content
            subtitle_content = (
                ColorManager.get_ansi_color("DIM") + subtitle + ColorManager.get_ansi_color("RESET")
            )
            subtitle_width = visual_length(subtitle_content)
            left_padding = (available_width - subtitle_width) // 2
            right_padding = available_width - subtitle_width - left_padding
            subtitle_line = (
                border_color
                + "│ "
                + ColorManager.get_ansi_color("RESET")
                + (" " * left_padding)
                + subtitle_content
                + (" " * right_padding)
                + border_color
                + " │"
                + ColorManager.get_ansi_color("RESET")
            )
            with self.term.location(0, 2):
                print(subtitle_line)

            # Bottom border
            bottom_border = (
                border_color
                + "└"
                + "─" * (self.term.width - 2)
                + "┘"
                + ColorManager.get_ansi_color("RESET")
            )
            with self.term.location(0, 3):
                print(bottom_border)

    def render_footer(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Render the footer with a nice border.

        Args:
            host_sections: Dictionary of host sections
            ssh_results: Dictionary of SSH results
        """
        footer_y = self.term.height - 4  # Leave space for border

        # Get statistics using the statistics manager
        stats = self.statistics_manager.calculate_statistics(host_sections, ssh_results)

        status_line = f"Global Status: {stats['active']} active, {stats['completed']} completed, {stats['failed']} failed"
        progress_line = f"Visible Progress: {stats['overall_progress']:.1f}% ({stats['total_completed']}/{stats['total_hosts']})"

        # Use consistent border color (white) for all borders
        border_color = ColorManager.get_ansi_color(ColorManager.DEFAULT_BORDER_COLOR)

        # Top border
        top_border = (
            border_color
            + "┌"
            + "─" * (self.term.width - 2)
            + "┐"
            + ColorManager.get_ansi_color("RESET")
        )
        with self.term.location(0, footer_y):
            print(top_border)

        # Status line - manually center the content
        status_content = (
            ColorManager.get_ansi_color("BRIGHT_CYAN")
            + status_line
            + ColorManager.get_ansi_color("RESET")
        )
        status_width = visual_length(status_content)
        available_width = self.term.width - 4  # Account for borders and padding
        left_padding = (available_width - status_width) // 2
        right_padding = available_width - status_width - left_padding
        status_line_formatted = (
            border_color
            + "│ "
            + ColorManager.get_ansi_color("RESET")
            + (" " * left_padding)
            + status_content
            + (" " * right_padding)
            + border_color
            + " │"
            + ColorManager.get_ansi_color("RESET")
        )
        with self.term.location(0, footer_y + 1):
            print(status_line_formatted)

        # Progress line - manually center the content
        progress_content = (
            ColorManager.get_ansi_color("BRIGHT_CYAN")
            + progress_line
            + ColorManager.get_ansi_color("RESET")
        )
        progress_width = visual_length(progress_content)
        left_padding = (available_width - progress_width) // 2
        right_padding = available_width - progress_width - left_padding
        progress_line_formatted = (
            border_color
            + "│ "
            + ColorManager.get_ansi_color("RESET")
            + (" " * left_padding)
            + progress_content
            + (" " * right_padding)
            + border_color
            + " │"
            + ColorManager.get_ansi_color("RESET")
        )
        with self.term.location(0, footer_y + 2):
            print(progress_line_formatted)

        # Bottom border
        bottom_border = (
            border_color
            + "└"
            + "─" * (self.term.width - 2)
            + "┘"
            + ColorManager.get_ansi_color("RESET")
        )
        with self.term.location(0, footer_y + 3):
            print(bottom_border)

    def render_completion_message(
        self,
        visible_hosts: int,
        ssh_results: Dict[str, Dict[str, Any]],
        connection_queue: list,
        active_connections: Dict[str, Any],
    ) -> None:
        """
        Render completion message when no hosts are visible.

        Args:
            visible_hosts: List of currently visible hosts
            ssh_results: Dictionary of SSH results
            connection_queue: List of hosts in queue
            active_connections: Dictionary of active connections
        """
        if visible_hosts:
            return  # Don't show completion message if hosts are visible

        # Check if all builds are completed
        total_processed = len(ssh_results)
        queue_size = len(connection_queue)
        active_count = len(active_connections)

        logging.debug(
            f"Build status: processed={total_processed}, queue={queue_size}, active={active_count}, visible_hosts={visible_hosts}"
        )

        # All builds are completed if:
        # 1. No hosts are visible (all completed and hidden)
        # 2. No hosts are in the queue waiting to start
        # 3. No hosts are currently building
        all_completed = visible_hosts == 0 and queue_size == 0 and active_count == 0

        if all_completed:
            msg = "All visible builds completed!"
        else:
            # This shouldn't happen since we only process visible hosts
            msg = f"Processing {active_count} hosts"

        msg_pad = max(0, (self.term.width - visual_length(msg) - 4) // 2)
        msg_line = f"│ {msg_pad * ' '}{ColorManager.get_ansi_color('BRIGHT_GREEN')}{msg}"
        remaining_space = self.term.width - visual_length(msg_line) - 1
        if remaining_space > 0:
            msg_line += " " * remaining_space
        msg_line += " │"

        # Draw completion message box using proper terminal methods
        top_border = "┌" + "─" * (self.term.width - 2) + "┐"
        bottom_border = "└" + "─" * (self.term.width - 2) + "┘"

        with self.term.location(0, 5):
            print(top_border)
        with self.term.location(0, 6):
            print(msg_line)
        with self.term.location(0, 7):
            print(bottom_border)

    def render_host_sections(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> int:
        """
        Render all host sections.

        Args:
            host_sections: Dictionary of host sections
            ssh_results: Dictionary of SSH results

        Returns:
            Number of visible hosts rendered
        """
        visible_hosts = 0
        for host, section in host_sections.items():
            if host in ssh_results:
                result = ssh_results[host]

                # Show if building or completed within timeout
                if result["status"] == "BUILDING":
                    section.render(self.term)
                    visible_hosts += 1
                elif result["status"] == "SUCCESS":
                    time_since_update = time.time() - section.last_update
                    if time_since_update < Config.HOST_VISIBILITY_TIMEOUT_SECONDS:
                        section.render(self.term)
                        visible_hosts += 1
                    else:
                        logging.debug(
                            f"Host {host} completed {time_since_update:.1f}s ago, hiding from display"
                        )
                elif result["status"] == "FAILED":
                    time_since_update = time.time() - section.last_update
                    if time_since_update < Config.HOST_VISIBILITY_TIMEOUT_SECONDS:
                        section.render(self.term)
                        visible_hosts += 1
                    else:
                        logging.debug(
                            f"Host {host} failed {time_since_update:.1f}s ago, hiding from display"
                        )

        return visible_hosts

    def update_timers(self, host_sections: Dict[str, Any]) -> None:
        """
        Update duration timers for all host sections.

        Args:
            host_sections: Dictionary of host sections
        """
        current_time = time.time()
        for host, section in host_sections.items():
            if section.start_time:
                section.duration = current_time - section.start_time

    def needs_timer_update(self) -> bool:
        """
        Check if timer update is needed.

        Returns:
            True if timer update is needed, False otherwise
        """
        current_time = time.time()
        return (
            current_time - self.last_timer_update
            >= Config.TIMER_UPDATE_INTERVAL_SECONDS
        )

    def needs_render(self, has_updates: bool, needs_timer_update: bool) -> bool:
        """
        Check if a render is needed.

        Args:
            has_updates: Whether there are content updates
            needs_timer_update: Whether timer update is needed

        Returns:
            True if render is needed, False otherwise
        """
        needs_full_render = self.last_clear == 0
        current_time = time.time()

        # Only render if there are updates, timer updates, or it's the first render
        if not needs_full_render and not has_updates and not needs_timer_update:
            return False

        # Also add a minimum interval between renders to prevent flickering
        min_render_interval = Config.MIN_RENDER_INTERVAL_SECONDS
        if (
            not needs_full_render
            and not needs_timer_update
            and current_time - self.last_render < min_render_interval
        ):
            return False

        return True

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        print(self.term.clear())
        # No need to move cursor after clear() - it already positions at (0,0)

    def flush_output(self) -> None:
        """Flush output buffer."""
        import sys

        sys.stdout.flush()

    def update_timestamps(self, needs_timer_update: bool) -> None:
        """
        Update render timestamps.

        Args:
            needs_timer_update: Whether timer update was performed
        """
        current_time = time.time()
        if self.last_clear == 0:
            self.last_clear = current_time
        self.last_render = current_time
        if needs_timer_update:
            self.last_timer_update = current_time

    def render_full_ui(
        self,
        tarball: str,
        host_sections: Dict[str, Any],
        ssh_results: Dict[str, Dict[str, Any]],
        connection_queue: list,
        active_connections: Dict[str, Any],
        has_updates: bool = False,
    ) -> None:
        """
        Render the complete UI.

        Args:
            tarball: Name of the tarball being built
            host_sections: Dictionary of host sections
            ssh_results: Dictionary of SSH results
            connection_queue: List of hosts in queue
            active_connections: Dictionary of active connections
            has_updates: Whether there are content updates
        """
        try:
            # Update timers for all sections
            self.update_timers(host_sections)

            # Check if timer update is needed
            needs_timer_update = self.needs_timer_update()

            # Check if render is needed
            if not self.needs_render(has_updates, needs_timer_update):
                return

            # Always do a full render to prevent corruption
            self.clear_screen()

            # Render header
            self.render_header(tarball, host_sections, ssh_results)

            # Render host sections
            visible_hosts = self.render_host_sections(host_sections, ssh_results)

            # Render completion message if no hosts visible
            self.render_completion_message(
                visible_hosts, ssh_results, connection_queue, active_connections
            )

            # Render footer
            self.render_footer(host_sections, ssh_results)

            # Flush output
            self.flush_output()

            # Update timestamps
            self.update_timestamps(needs_timer_update)

        except Exception as e:
            # Fallback to simple output if blessed fails
            import traceback

            print(f"TUI Error: {e}")
            print("Full traceback:")
            traceback.print_exc()
            print("Falling back to simple output mode...")
            self._simple_output_mode(host_sections, ssh_results)

    def _simple_output_mode(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Fallback simple output mode when blessed fails.

        Args:
            host_sections: Dictionary of host sections
            ssh_results: Dictionary of SSH results
        """
        print("\n" + "=" * 80)
        print("Build Redland - Simple Output Mode")
        print("=" * 80)

        for host in host_sections:
            status = "IDLE"
            if host in ssh_results:
                status = ssh_results[host]["status"]

            print(f"{host}: {status}")

            if host in ssh_results:
                result = ssh_results[host]
                for line in result["output"][-5:]:  # Show last 5 lines
                    print(f"  {line}")
            print()
