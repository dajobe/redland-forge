#!/usr/bin/python3
"""
Layout Manager Module

A module for managing terminal layout and host section positioning in the TUI.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from blessed import Terminal

from .config import Config
from .color_manager import ColorManager
from .host_section import HostSection


class LayoutManager:
    """Manages terminal layout and host section positioning."""

    def __init__(
        self, terminal: Terminal, hosts: List[str], step_change_callback: Optional[Callable] = None
    ) -> None:
        """
        Initialize the layout manager.

        Args:
            terminal: Blessed terminal object
            hosts: List of all hosts to be managed
            step_change_callback: Optional callback function for step changes
        """
        self.term = terminal
        self.hosts = hosts
        self.step_change_callback = step_change_callback
        self.host_sections: Dict[str, HostSection] = {}

    def setup_layout(self) -> Dict[str, HostSection]:
        """
        Calculate and create host sections based on terminal dimensions.

        Returns:
            Dictionary of host sections with their positions and dimensions
        """
        try:
            logging.debug(
                f"Setting up layout for {len(self.hosts)} hosts on terminal {self.term.width}x{self.term.height}"
            )

            # Handle very small terminals
            if self.term.height < Config.MIN_TERMINAL_HEIGHT:
                layout_info = self._calculate_small_terminal_layout()
            else:
                layout_info = self._calculate_normal_terminal_layout()

            # Create host sections
            self._create_host_sections(layout_info)

            return self.host_sections

        except Exception as e:
            import traceback

            logging.error(f"Error in setup_layout: {e}")
            logging.error("Full traceback:")
            logging.error(traceback.format_exc())
            print(f"Error in setup_layout: {e}")
            print("Full traceback:")
            traceback.print_exc()
            raise

    def _calculate_small_terminal_layout(self) -> Dict[str, Any]:
        """
        Calculate layout for very small terminals.

        Returns:
            Dictionary containing layout information
        """
        available_height = self.term.height - Config.SMALL_TERMINAL_HEADER_FOOTER
        min_host_height = Config.SMALL_TERMINAL_MIN_HOST_HEIGHT
        max_visible_hosts = Config.SMALL_TERMINAL_MAX_VISIBLE_HOSTS

        # Calculate maximum section height that would fit
        max_section_height = (
            self.term.height
            - Config.HOST_SECTION_START_Y
            - Config.SMALL_TERMINAL_FOOTER_SPACE
        )

        # For very small terminals, ensure we can display at least 1 host
        if max_section_height <= 0:
            # Terminal is extremely small, use minimal space
            section_height = 1
            max_visible_hosts = 1
        else:
            # Use the smaller of available_height or max_section_height, but ensure at least 1
            section_height = max(1, min(available_height, max_section_height))
            # Ensure we can display at least 1 host if there's any space
            if section_height >= 1:
                max_visible_hosts = 1
            else:
                max_visible_hosts = 0

        logging.debug(
            f"Small terminal mode: available_height={available_height}, section_height={section_height}, max_section_height={max_section_height}, max_visible_hosts={max_visible_hosts}"
        )

        return {
            "available_height": available_height,
            "min_host_height": min_host_height,
            "max_visible_hosts": max_visible_hosts,
            "section_height": section_height,
        }

    def _calculate_normal_terminal_layout(self) -> Dict[str, Any]:
        """
        Calculate layout for normal-sized terminals.

        Returns:
            Dictionary containing layout information
        """
        # Reserve space for header and footer
        available_height = self.term.height - (
            Config.HEADER_HEIGHT + Config.FOOTER_HEIGHT
        )
        min_host_height = Config.MIN_HOST_HEIGHT
        max_visible_hosts = min(len(self.hosts), available_height // min_host_height)

        # Ensure we have at least one visible host
        if max_visible_hosts < 1:
            max_visible_hosts = 1
            min_host_height = available_height

        section_height = max(min_host_height, available_height // max_visible_hosts)

        logging.debug(
            f"Normal terminal mode: available_height={available_height}, max_visible_hosts={max_visible_hosts}, section_height={section_height}"
        )

        return {
            "available_height": available_height,
            "min_host_height": min_host_height,
            "max_visible_hosts": max_visible_hosts,
            "section_height": section_height,
        }

    def _create_host_sections(self, layout_info: Dict[str, Any]) -> None:
        """
        Create host sections based on layout information.

        Args:
            layout_info: Layout calculation results
        """
        max_visible_hosts = layout_info["max_visible_hosts"]
        section_height = layout_info["section_height"]

        # Determine footer space based on terminal size
        footer_space = (
            Config.SMALL_TERMINAL_FOOTER_SPACE
            if self.term.height < Config.MIN_TERMINAL_HEIGHT
            else Config.FOOTER_HEIGHT
        )

        for i, host in enumerate(self.hosts[:max_visible_hosts]):
            start_y = Config.HOST_SECTION_START_Y + (i * section_height)
            # Check if this section would fit within the terminal bounds
            if (
                start_y + section_height > self.term.height - footer_space
            ):  # Leave space for footer
                logging.debug(
                    f"Skipping host {host} - would render outside bounds (start_y={start_y}, height={section_height}, term_height={self.term.height})"
                )
                continue
            self.host_sections[host] = HostSection(
                host, start_y, section_height, self.step_change_callback
            )
            logging.debug(
                f"Created host section for {host}: start_y={start_y}, height={section_height}, end_y={start_y + section_height}"
            )

    def get_max_visible_hosts(self) -> int:
        """
        Calculate the maximum number of visible hosts based on terminal height.

        Returns:
            Maximum number of hosts that can be displayed
        """
        available_height = self.term.height - (
            Config.HEADER_HEIGHT + Config.FOOTER_HEIGHT
        )
        min_host_height = Config.MIN_HOST_HEIGHT
        return min(len(self.hosts), available_height // min_host_height)

    def get_available_height(self) -> int:
        """
        Get the available height for host sections.

        Returns:
            Available height in terminal rows
        """
        if self.term.height < Config.MIN_TERMINAL_HEIGHT:
            return self.term.height - Config.SMALL_TERMINAL_HEADER_FOOTER
        else:
            return self.term.height - (Config.HEADER_HEIGHT + Config.FOOTER_HEIGHT)

    def get_section_height(self) -> int:
        """
        Calculate the height for each host section.

        Returns:
            Height in terminal rows for each section
        """
        if self.term.height < Config.MIN_TERMINAL_HEIGHT:
            # Small terminal: ensure section fits within terminal bounds
            available_height = self.term.height - Config.SMALL_TERMINAL_HEADER_FOOTER
            max_section_height = (
                self.term.height
                - Config.HOST_SECTION_START_Y
                - Config.SMALL_TERMINAL_FOOTER_SPACE
            )
            # Ensure we don't return negative values
            return max(1, min(available_height, max_section_height))
        else:
            # Normal terminal: calculate based on available space and number of hosts
            available_height = self.term.height - (
                Config.HEADER_HEIGHT + Config.FOOTER_HEIGHT
            )
            max_visible_hosts = min(
                len(self.hosts), available_height // Config.MIN_HOST_HEIGHT
            )

            if max_visible_hosts == 0:
                return Config.MIN_HOST_HEIGHT

            return max(Config.MIN_HOST_HEIGHT, available_height // max_visible_hosts)

    def add_host_section(self, host: str, start_y: int, section_height: int) -> None:
        """
        Add a host section at a specific position.

        Args:
            host: Hostname
            start_y: Starting Y position
            section_height: Height of the section
        """
        self.host_sections[host] = HostSection(
            host, start_y, section_height, self.step_change_callback
        )
        logging.debug(
            f"Added host section for {host}: start_y={start_y}, height={section_height}"
        )

    def remove_host_section(self, host: str) -> None:
        """
        Remove a host section.

        Args:
            host: Hostname to remove
        """
        if host in self.host_sections:
            del self.host_sections[host]
            logging.debug(f"Removed host section for {host}")

    def get_host_section(self, host: str) -> Optional[HostSection]:
        """
        Get a host section by hostname.

        Args:
            host: Hostname

        Returns:
            HostSection object or None if not found
        """
        return self.host_sections.get(host)

    def get_all_host_sections(self) -> Dict[str, HostSection]:
        """
        Get all host sections.

        Returns:
            Dictionary of all host sections
        """
        return self.host_sections.copy()

    def get_visible_hosts(self) -> List[str]:
        """
        Get list of visible hostnames.

        Returns:
            List of hostnames that have sections
        """
        return list(self.host_sections.keys())

    def get_hidden_hosts(self) -> List[str]:
        """
        Get list of hosts that are not visible.

        Returns:
            List of hostnames that don't have sections
        """
        return [host for host in self.hosts if host not in self.host_sections]

    def is_host_visible(self, host: str) -> bool:
        """
        Check if a host is visible.

        Args:
            host: Hostname to check

        Returns:
            True if host has a section, False otherwise
        """
        return host in self.host_sections

    def get_section_position(self, host: str) -> Optional[Tuple[int, int]]:
        """
        Get the position and size of a host section.

        Args:
            host: Hostname

        Returns:
            Tuple of (start_y, height) or None if not found
        """
        section = self.get_host_section(host)
        if section:
            return (section.start_y, section.height)
        return None

    def validate_layout(self) -> bool:
        """
        Validate that the current layout is valid.

        Returns:
            True if layout is valid, False otherwise
        """
        try:
            # Check that all sections fit within terminal bounds
            for host, section in self.host_sections.items():
                if section.start_y < 0:
                    logging.error(
                        f"Host {host} section starts at negative Y position: {section.start_y}"
                    )
                    return False
                if section.start_y + section.height > self.term.height:
                    logging.error(
                        f"Host {host} section extends beyond terminal height: {section.start_y + section.height} > {self.term.height}"
                    )
                    return False
                # For small terminals, allow smaller sections
                min_height = (
                    Config.SMALL_TERMINAL_MIN_HOST_HEIGHT
                    if self.term.height < Config.MIN_TERMINAL_HEIGHT
                    else Config.MIN_HOST_HEIGHT
                )
                if section.height < min_height:
                    logging.error(
                        f"Host {host} section height too small: {section.height} < {min_height}"
                    )
                    return False

            # Check for overlapping sections
            sections = list(self.host_sections.values())
            for i, section1 in enumerate(sections):
                for section2 in sections[i + 1 :]:
                    if self._sections_overlap(section1, section2):
                        logging.error(
                            f"Sections overlap: {section1.hostname} and {section2.hostname}"
                        )
                        return False

            return True

        except Exception as e:
            logging.error(f"Error validating layout: {e}")
            return False

    def _sections_overlap(self, section1: HostSection, section2: HostSection) -> bool:
        """
        Check if two sections overlap.

        Args:
            section1: First host section
            section2: Second host section

        Returns:
            True if sections overlap, False otherwise
        """
        return not (
            section1.start_y + section1.height <= section2.start_y
            or section2.start_y + section2.height <= section1.start_y
        )

    def get_layout_info(self) -> Dict[str, Any]:
        """
        Get comprehensive layout information.

        Returns:
            Dictionary containing layout details
        """
        return {
            "terminal_width": self.term.width,
            "terminal_height": self.term.height,
            "total_hosts": len(self.hosts),
            "visible_hosts": len(self.host_sections),
            "hidden_hosts": len(self.get_hidden_hosts()),
            "max_visible_hosts": self.get_max_visible_hosts(),
            "available_height": self.get_available_height(),
            "section_height": self.get_section_height(),
            "is_small_terminal": self.term.height < Config.MIN_TERMINAL_HEIGHT,
            "layout_valid": self.validate_layout(),
        }

    def resize_layout(self) -> Dict[str, HostSection]:
        """
        Recalculate layout after terminal resize.

        Returns:
            Updated dictionary of host sections
        """
        logging.debug("Recalculating layout after terminal resize")
        self.host_sections.clear()
        return self.setup_layout()


# Import Colors here to avoid circular imports
from .host_section import Colors
