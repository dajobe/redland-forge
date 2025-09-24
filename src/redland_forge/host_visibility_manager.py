#!/usr/bin/python3
"""
Host Visibility Manager Module

A module for managing host visibility, dynamic host section creation,
and timeout-based host hiding/showing in the TUI.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable

from blessed import Terminal

from .config import Config
from .host_section import HostSection
from .layout_manager import LayoutManager


class HostVisibilityManager:
    """Manages host visibility and dynamic host section creation."""

    def __init__(
        self,
        terminal: Terminal,
        layout_manager: LayoutManager,
        all_hosts: List[str],
        step_change_callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the host visibility manager.

        Args:
            terminal: Blessed terminal object
            layout_manager: Layout manager for calculating positions
            all_hosts: List of all hosts to manage
            step_change_callback: Optional callback function for step changes
        """
        self.term = terminal
        self.layout_manager = layout_manager
        self.all_hosts = all_hosts
        self.step_change_callback = step_change_callback
        self.host_sections: Dict[str, HostSection] = {}

    def update_host_visibility(
        self,
        ssh_results: Dict[str, Dict[str, Any]],
        connection_queue: List[tuple],
        active_connections: Dict[str, Any],
    ) -> None:
        """
        Update which hosts are visible based on completion status and screen space.

        Args:
            ssh_results: Dictionary of SSH results for each host
            connection_queue: List of hosts in queue
            active_connections: Dictionary of active connections
        """
        current_time = time.time()

        # Get all hosts that have results (are being processed or completed)
        active_hosts = list(ssh_results.keys())

        # Debug: log current state
        logging.debug(f"Current visible hosts: {list(self.host_sections.keys())}")
        logging.debug(f"Queue hosts: {[h for h, _ in connection_queue]}")
        logging.debug(f"Active connections: {list(active_connections.keys())}")
        logging.debug(f"Results hosts: {list(ssh_results.keys())}")

        for host in self.host_sections:
            if host in ssh_results:
                status = ssh_results[host]["status"]
                completion_time = getattr(
                    self.host_sections[host], "completion_time", None
                )
                logging.debug(
                    f"  {host}: status={status}, completion_time={completion_time}"
                )

        # Hide completed hosts that have timed out
        self._hide_completed_hosts(active_hosts, ssh_results, current_time)

        # Show new hosts that should be visible
        self._show_new_hosts(
            ssh_results, connection_queue, active_connections, current_time
        )

    def _hide_completed_hosts(
        self,
        active_hosts: List[str],
        ssh_results: Dict[str, Dict[str, Any]],
        current_time: float,
    ) -> None:
        """
        Hide hosts that are completed and have been visible for more than the timeout period.

        Args:
            active_hosts: List of hosts with results
            ssh_results: Dictionary of SSH results
            current_time: Current timestamp
        """
        completed_hosts_to_hide = []

        for host in active_hosts:
            if host in self.host_sections and ssh_results[host]["status"] in [
                "SUCCESS",
                "FAILED",
            ]:
                # Check if this host has been completed for more than the timeout
                if (
                    hasattr(self.host_sections[host], "completion_time")
                    and self.host_sections[host].completion_time is not None
                ):
                    completion_time = self.host_sections[host].completion_time
                    assert completion_time is not None  # Help mypy understand this can't be None
                    time_since_completion = current_time - completion_time
                    logging.debug(
                        f"Host {host} completed {time_since_completion:.1f}s ago (timeout: {Config.HOST_VISIBILITY_TIMEOUT_SECONDS}s)"
                    )
                    if time_since_completion > Config.HOST_VISIBILITY_TIMEOUT_SECONDS:
                        completed_hosts_to_hide.append(host)
                        logging.debug(
                            f"Marking {host} for hiding after {time_since_completion:.1f}s"
                        )
                else:
                    # Mark the completion time if not already set
                    self.host_sections[host].completion_time = current_time
                    logging.debug(
                        f"Setting completion time for {host} to {current_time}"
                    )

        # Hide hosts that have been completed for more than the timeout
        for host in completed_hosts_to_hide:
            del self.host_sections[host]
            logging.debug(
                f"Hiding completed host {host} after {Config.HOST_VISIBILITY_TIMEOUT_SECONDS}s timeout"
            )

    def _show_new_hosts(
        self,
        ssh_results: Dict[str, Dict[str, Any]],
        connection_queue: List[tuple],
        active_connections: Dict[str, Any],
        current_time: float,
    ) -> None:
        """
        Show new hosts that should be visible but aren't yet.

        Args:
            ssh_results: Dictionary of SSH results
            connection_queue: List of hosts in queue
            active_connections: Dictionary of active connections
            current_time: Current timestamp
        """
        # Find hosts that are not yet visible but should be shown
        invisible_hosts = []

        for host in self.all_hosts:
            if host not in self.host_sections:
                # Check if host is active (in results with active status)
                if host in ssh_results and ssh_results[host]["status"] in [
                    "CONNECTING",
                    "PREPARING",
                    "BUILDING",
                ]:
                    invisible_hosts.append(host)
                    logging.debug(
                        f"Found active host {host} (status: {ssh_results[host]['status']}) that should be made visible"
                    )
                # Check if host is in queue but not yet started (not in results)
                elif host not in ssh_results:
                    # Check if this host is in the connection queue
                    queue_hosts = [h for h, _ in connection_queue]
                    if host in queue_hosts:
                        invisible_hosts.append(host)
                        logging.debug(
                            f"Found queued host {host} that should be made visible"
                        )
                    # Check if host is in active_connections but not yet in results (just started)
                    elif host in active_connections:
                        invisible_hosts.append(host)
                        logging.debug(
                            f"Found active connection host {host} that should be made visible"
                        )
                    else:
                        logging.debug(
                            f"Host {host} not in results, queue, or active_connections - may be completed"
                        )

        logging.debug(
            f"Found {len(invisible_hosts)} invisible hosts that should be shown: {invisible_hosts}"
        )

        # Show new hosts if there's space
        for host in invisible_hosts:
            if len(self.host_sections) < self._get_max_visible_hosts():
                # Create a new host section for this host
                self._add_host_section(host)

                # If this host is in queue but not yet started, initialize it with appropriate status
                if host not in ssh_results:
                    # Check if it's in active_connections (just started) or queue (waiting)
                    if host in active_connections:
                        # Host just started but not yet in results - initialize with CONNECTING
                        ssh_results[host] = {
                            "status": "CONNECTING",
                            "output": [],
                        }
                        logging.debug(
                            f"Initialized active connection host {host} with CONNECTING status"
                        )
                    else:
                        # Host is in queue - initialize with IDLE status
                        ssh_results[host] = {
                            "status": "IDLE",
                            "output": [],
                        }
                        logging.debug(
                            f"Initialized queued host {host} with IDLE status"
                        )

                logging.debug(f"Showing new host {host}")
            else:
                break  # No more space available

    def _add_host_section(self, host: str) -> None:
        """
        Add a host section using layout manager logic.

        Args:
            host: Hostname to add
        """
        max_visible_hosts = self._get_max_visible_hosts()

        if len(self.host_sections) >= max_visible_hosts:
            return  # No space available

        # Calculate section height using the same logic as setup_layout
        available_height = self.term.height - (
            Config.HEADER_HEIGHT + Config.FOOTER_HEIGHT
        )
        min_host_height = Config.MIN_HOST_HEIGHT
        section_height = max(min_host_height, available_height // max_visible_hosts)

        # Find the first available slot
        slot_index = 0
        start_y = Config.HEADER_HEIGHT + (slot_index * section_height)

        # Check if this slot is available (no existing host at this position)
        while slot_index < max_visible_hosts:
            start_y = Config.HEADER_HEIGHT + (slot_index * section_height)
            if start_y + section_height > self.term.height - Config.FOOTER_HEIGHT:
                break  # Would exceed bounds

            # Check if this slot is occupied
            slot_occupied = False
            for existing_host, existing_section in self.host_sections.items():
                if existing_section.start_y == start_y:
                    slot_occupied = True
                    break

            if not slot_occupied:
                break  # Found available slot
            else:
                slot_index += 1  # Try next slot

        logging.debug(
            f"Adding host {host}: slot_index={slot_index}, start_y={start_y}, current_host_sections={list(self.host_sections.keys())}"
        )

        # Check if this would render outside bounds
        if start_y + section_height > self.term.height - Config.FOOTER_HEIGHT:
            logging.debug(
                f"Skipping host {host} - would render outside bounds (start_y={start_y}, height={section_height}, term_height={self.term.height})"
            )
            return

        # Create the host section
        self.host_sections[host] = HostSection(
            host, start_y, section_height, self.step_change_callback
        )
        logging.debug(
            f"Created host section for {host}: start_y={start_y}, height={section_height}, end_y={start_y + section_height}, callback={self.step_change_callback is not None}"
        )

    def _get_max_visible_hosts(self) -> int:
        """
        Calculate the maximum number of visible hosts based on terminal height.

        Returns:
            Maximum number of hosts that can be displayed
        """
        return self.layout_manager.get_max_visible_hosts()

    def get_host_sections(self) -> Dict[str, HostSection]:
        """
        Get the current host sections.

        Returns:
            Dictionary of host sections
        """
        return self.host_sections

    def get_visible_hosts(self) -> List[str]:
        """
        Get list of currently visible hosts.

        Returns:
            List of visible hostnames
        """
        return list(self.host_sections.keys())

    def is_host_visible(self, host: str) -> bool:
        """
        Check if a host is currently visible.

        Args:
            host: Hostname to check

        Returns:
            True if host is visible, False otherwise
        """
        return host in self.host_sections

    def get_host_section(self, host: str) -> Optional[HostSection]:
        """
        Get the host section for a specific host.

        Args:
            host: Hostname to get section for

        Returns:
            HostSection if host is visible, None otherwise
        """
        return self.host_sections.get(host)

    def remove_host_section(self, host: str) -> bool:
        """
        Remove a host section.

        Args:
            host: Hostname to remove

        Returns:
            True if host was removed, False if not found
        """
        if host in self.host_sections:
            del self.host_sections[host]
            logging.debug(f"Removed host section for {host}")
            return True
        return False

    def clear_all_sections(self) -> None:
        """Clear all host sections."""
        self.host_sections.clear()
        logging.debug("Cleared all host sections")
