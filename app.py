#!/usr/bin/python3
"""
Build Redland Text UI - Main Application

Main application logic for the parallel build monitoring TUI.
"""

import logging
import os
import sys
import time
from typing import Dict, List, Optional

from blessed import Terminal

from config import Config
from statistics_manager import StatisticsManager
from layout_manager import LayoutManager
from renderer import Renderer
from input_handler import InputHandler
from host_visibility_manager import HostVisibilityManager
from parallel_ssh_manager import ParallelSSHManager
from color_manager import ColorManager, set_color_mode, supports_color, colorize


class BuildTUI:
    """Main TUI application for parallel build monitoring."""

    def __init__(
        self, hosts: List[str], tarball: str, max_concurrent: Optional[int] = None
    ):
        try:
            logging.debug("Initializing BuildTUI")
            self.hosts = hosts
            self.tarball = tarball

            # Validate tarball file exists before proceeding
            if not os.path.exists(tarball):
                raise FileNotFoundError(
                    f"Tarball file not found: {tarball}\n"
                    f"Please check the file path and ensure the file exists."
                )
            logging.debug(f"Tarball file validated: {tarball}")

            logging.debug("Initializing blessed terminal")
            self.term = Terminal()
            logging.debug("Blessed terminal initialized successfully")

            # Test terminal properties
            logging.debug(
                f"Terminal width: {self.term.width}, height: {self.term.height}"
            )
            logging.debug(f"Terminal type: {self.term.type}")
            logging.debug(f"Terminal kind: {self.term.kind}")

            self.ssh_manager = ParallelSSHManager(max_concurrent or min(4, len(hosts)))

            # Set build script path (script lives one level up from build-tui)
            script_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "build-redland.py")
            )
            logging.debug(f"Resolved build script path: {script_path}")

            # Validate build script exists early; it's required for operation
            if not os.path.isfile(script_path):
                raise FileNotFoundError(
                    f"Build script not found: {script_path}\n"
                    f"Expected 'build-redland.py' to exist next to the admin directory."
                )

            self.ssh_manager.set_build_script_path(script_path)

            # Initialize managers
            self.statistics_manager = StatisticsManager(hosts)
            self.layout_manager = LayoutManager(self.term, hosts)
            self.renderer = Renderer(self.term, self.statistics_manager)
            self.input_handler = InputHandler(self.term)
            self.host_visibility_manager = HostVisibilityManager(
                self.term, self.layout_manager, hosts
            )

            self.host_sections = {}
            self.running = True
            self.focused_host = 0

            logging.debug("Setting up layout")
            self.setup_layout()
            logging.debug("BuildTUI initialization completed successfully")
        except FileNotFoundError:
            # Re-raise FileNotFoundError without logging traceback
            raise
        except Exception as e:
            import traceback

            logging.error(f"Error in BuildTUI.__init__: {e}")
            logging.error("Full traceback:")
            logging.error(traceback.format_exc())
            print(f"Error in BuildTUI.__init__: {e}")
            print("Full traceback:")
            traceback.print_exc()
            raise

    def setup_layout(self) -> None:
        """Calculate and create host sections using LayoutManager."""
        try:
            logging.debug(
                f"Setting up layout for {len(self.hosts)} hosts on terminal {self.term.width}x{self.term.height}"
            )

            # Use LayoutManager to setup layout
            self.host_sections = self.layout_manager.setup_layout()

            logging.debug(
                f"Layout setup completed: {len(self.host_sections)} host sections created"
            )
        except Exception as e:
            import traceback

            logging.error(f"Error in setup_layout: {e}")
            logging.error("Full traceback:")
            logging.error(traceback.format_exc())
            print(f"Error in setup_layout: {e}")
            print("Full traceback:")
            traceback.print_exc()
            raise

    def render(self) -> None:
        """Render the entire UI."""
        try:
            # Check for updates
            has_updates = False

            # Check for updates
            for host, section in self.host_sections.items():
                if host in self.ssh_manager.results:
                    result = self.ssh_manager.results[host]
                    old_status = section.status

                    section.update_status(result["status"])

                    # Add new output lines using processed_lines counter
                    new_lines = result["output"][section.processed_lines :]
                    if new_lines:
                        logging.debug(
                            f"Processing {len(new_lines)} new lines for {host}"
                        )
                        for line in new_lines:
                            logging.debug(f"Adding line to {host}: '{line.strip()}'")
                            section.add_output(line)
                            section.processed_lines += 1
                            has_updates = True

                            # Update current step based on new output lines
                    for line in new_lines:
                        # Debug: log the line being processed for step detection
                        logging.debug(f"Step detection for {host}: '{line.strip()}'")

                        # Use the new step detection method
                        section.detect_step_from_output(line)

                        # Log state after step detection for debugging
                        if (
                            "make check" in line
                            or "make succeeded" in line
                            or "configure" in line
                        ):
                            logging.info(
                                f"After step detection for {host}: current_step='{section.current_step}' from line: '{line.strip()}'"
                            )

                    # Check if status changed
                    if old_status != section.status:
                        has_updates = True

                    # Check if host visibility should change due to timeout
                    if result["status"] in ["SUCCESS", "FAILED"]:
                        time_since_update = time.time() - section.last_update
                        # If host is about to be hidden (or just was hidden), trigger update
                        timeout_window = Config.HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS
                        timeout_threshold = Config.HOST_VISIBILITY_TIMEOUT_SECONDS
                        if (
                            (timeout_threshold - timeout_window)
                            <= time_since_update
                            <= (timeout_threshold + timeout_window)
                        ):
                            has_updates = True
                            logging.debug(
                                f"Host {host} timeout visibility change detected, triggering render"
                            )
                else:
                    # Check if this host just started
                    if section.status == "IDLE":
                        has_updates = True

            # Use the renderer to handle all UI rendering
            self.renderer.render_full_ui(
                self.tarball,
                self.host_sections,
                self.ssh_manager.results,
                self.ssh_manager.connection_queue,
                self.ssh_manager.active_connections,
                has_updates,
            )

        except Exception as e:
            # Fallback to simple output if blessed fails
            import traceback

            print(f"TUI Error: {e}")
            print("Full traceback:")
            traceback.print_exc()
            print("Falling back to simple output mode...")
            self._simple_output_mode()

    def _simple_output_mode(self) -> None:
        """Fallback simple output mode when blessed fails."""
        print("\n" + "=" * 80)
        print("Build Redland - Simple Output Mode")
        print("=" * 80)

        for host in self.hosts:
            status = "IDLE"
            if host in self.ssh_manager.results:
                status = self.ssh_manager.results[host]["status"]

            print(f"{host}: {status}")

            if host in self.ssh_manager.results:
                result = self.ssh_manager.results[host]
                for line in result["output"][-5:]:  # Show last 5 lines
                    print(f"  {line}")
            print()

    def handle_input(self) -> None:
        """Handle keyboard input using InputHandler."""
        self.input_handler.handle_input(
            on_quit=self._on_quit,
            on_navigate_up=self._on_navigate_up,
            on_navigate_down=self._on_navigate_down,
            on_show_help=self._on_show_help,
        )

    def _on_quit(self) -> None:
        """Handle quit request."""
        self.running = False

    def _on_navigate_up(self) -> None:
        """Handle up navigation."""
        self.focused_host = max(0, self.focused_host - 1)

    def _on_navigate_down(self) -> None:
        """Handle down navigation."""
        self.focused_host = min(len(self.host_sections) - 1, self.focused_host + 1)

    def _on_show_help(self) -> None:
        """Handle help request."""
        self.show_help()

    def show_help(self) -> None:
        """Show help screen using InputHandler."""
        self.input_handler.show_help()

    def run(self) -> None:
        """Main UI loop."""
        try:
            with self.term.fullscreen(), self.term.hidden_cursor():
                # Add ALL hosts to the queue (not just visible ones)
                logging.debug(f"Adding all {len(self.hosts)} hosts to build queue")
                for host in self.hosts:
                    self.ssh_manager.add_host(host, self.tarball)

                # Start initial builds up to concurrency limit
                self.ssh_manager.start_builds()

                # Main loop
                while self.running:
                    try:
                        # Handle input
                        self.handle_input()

                        # Start new builds if slots are available
                        self.ssh_manager.start_builds()

                        # Update host visibility - hide completed hosts and show new ones
                        self._update_host_visibility()

                        # Render UI
                        self.render()

                        # Small delay to prevent high CPU usage and reduce flickering
                        time.sleep(0.1)  # Back to 0.1 to reduce flickering
                    except Exception as e:
                        import traceback

                        logging.error(f"Error in main loop: {e}")
                        logging.error("Full traceback:")
                        logging.error(traceback.format_exc())
                        print(f"Error in main loop: {e}")
                        print("Full traceback:")
                        traceback.print_exc()
                        break

        except KeyboardInterrupt:
            print("\nBuild interrupted by user")
        except Exception as e:
            import traceback

            logging.error(f"Error in run method: {e}")
            logging.error("Full traceback:")
            logging.error(traceback.format_exc())
            print(f"Error in run method: {e}")
            print("Full traceback:")
            traceback.print_exc()
        finally:
            # Clean up
            try:
                print(self.term.normal_cursor())
                print(self.term.exit_fullscreen())
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")
                print(f"Error during cleanup: {e}")

    def _update_host_visibility(self) -> None:
        """Update which hosts are visible using HostVisibilityManager."""
        # Update host visibility using the manager
        self.host_visibility_manager.update_host_visibility(
            self.ssh_manager.results,
            self.ssh_manager.connection_queue,
            self.ssh_manager.active_connections,
        )

        # Update our host_sections reference to match the manager's state
        self.host_sections = self.host_visibility_manager.get_host_sections()


def read_hosts_from_file(filename: str) -> List[str]:
    """Read hosts from a file, one per line."""
    hosts = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip blank lines and comments
                if not line or line.startswith("#"):
                    continue
                # If hostname doesn't contain @, assume current user
                if "@" not in line:
                    import getpass

                    username = getpass.getuser()
                    line = f"{username}@{line}"
                hosts.append(line)
    except FileNotFoundError:
        logging.error(f"Hosts file not found: {filename}")
        raise

    if not hosts:
        logging.warning(f"No valid hosts found in {filename}")

    return hosts
