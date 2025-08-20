#!/usr/bin/python3
"""
Build Redland Text UI - Main Application

Main application logic for the parallel build monitoring TUI.
"""

import getpass
import logging
import os
import re
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
from auto_exit_manager import AutoExitManager
from build_summary_collector import BuildSummaryCollector
from progress_display_manager import ProgressDisplayManager


class BuildTUI:
    """Main TUI application for parallel build monitoring."""

    def __init__(
        self,
        hosts: List[str],
        tarball: str,
        max_concurrent: Optional[int] = None,
        auto_exit_delay: Optional[int] = None,
        auto_exit_enabled: Optional[bool] = None,
        cache_file: Optional[str] = None,
        cache_retention: Optional[int] = None,
        cache_enabled: Optional[bool] = None,
        progress_enabled: Optional[bool] = None,
    ):
        try:
            logging.debug("Initializing BuildTUI")
            self.hosts = hosts
            self.tarball = tarball
            
            # Get current user for cache key construction
            self.current_user = getpass.getuser()
            logging.debug(f"Current user: {self.current_user}")

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

            # Create step change callback for progress tracking (will be updated after progress_display_manager is initialized)
            self.step_change_callback = None

            self.layout_manager = LayoutManager(
                self.term, hosts, None
            )  # Will be set after progress_display_manager is initialized
            self.input_handler = InputHandler(self.term)
            self.host_visibility_manager = HostVisibilityManager(
                self.term, self.layout_manager, hosts
            )

            # Initialize build summary collector
            self.build_summary_collector = BuildSummaryCollector()

            # Use command-line parameters if provided, otherwise use config defaults
            auto_exit_delay = (
                auto_exit_delay
                if auto_exit_delay is not None
                else Config.AUTO_EXIT_DELAY_SECONDS
            )
            auto_exit_enabled = (
                auto_exit_enabled
                if auto_exit_enabled is not None
                else Config.AUTO_EXIT_ENABLED
            )

            self.auto_exit_manager = AutoExitManager(
                exit_delay_seconds=auto_exit_delay, enabled=auto_exit_enabled
            )

            # Set up auto-exit callback
            self.auto_exit_manager.set_exit_callback(self._trigger_exit)

            # Set up build start callback for timing tracking
            self.ssh_manager.set_build_start_callback(self._on_build_start)

            # Initialize timing cache if enabled
            self.timing_cache = None
            if cache_enabled is None or cache_enabled:
                cache_file_path = (
                    cache_file if cache_file is not None else Config.TIMING_CACHE_FILE
                )
                cache_retention_days = (
                    cache_retention
                    if cache_retention is not None
                    else Config.TIMING_CACHE_RETENTION_DAYS
                )

                try:
                    from build_timing_cache import BuildTimingCache

                    self.timing_cache = BuildTimingCache(
                        cache_file_path=cache_file_path,
                        retention_days=cache_retention_days,
                    )
                    logging.debug(
                        f"Timing cache initialized: {cache_file_path}, retention: {cache_retention_days} days"
                    )
                except ImportError as e:
                    logging.warning(f"Failed to import BuildTimingCache: {e}")
                    self.timing_cache = None
            else:
                logging.debug("Timing cache disabled")

            # Initialize progress display manager if timing cache is available
            self.progress_display_manager = None
            if self.timing_cache and (progress_enabled is None or progress_enabled):
                try:
                    self.progress_display_manager = ProgressDisplayManager(
                        self.timing_cache, self._get_cache_key
                    )
                    logging.debug("Progress display manager initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize ProgressDisplayManager: {e}")
                    self.progress_display_manager = None
            else:
                logging.debug("Progress display manager disabled")

            # Now that progress_display_manager is initialized, set up the step change callback
            self.step_change_callback = self._create_step_change_callback()
            logging.debug(
                f"Created step change callback: {self.step_change_callback is not None}"
            )

            # Update the layout manager with the step change callback
            self.layout_manager.step_change_callback = self.step_change_callback
            logging.debug(
                f"Updated layout manager step change callback: {self.layout_manager.step_change_callback is not None}"
            )

            # Update the host visibility manager with the step change callback
            self.host_visibility_manager.step_change_callback = (
                self.step_change_callback
            )
            logging.debug(
                f"Updated host visibility manager step change callback: {self.host_visibility_manager.step_change_callback is not None}"
            )

            # Update existing host sections to use the step change callback
            for host_section in self.layout_manager.host_sections.values():
                host_section.step_change_callback = self.step_change_callback
                logging.debug(
                    f"Updated host section {host_section.hostname} step change callback: {host_section.step_change_callback is not None}"
                )

            # Initialize progress info for all host sections after they're created
            if self.progress_display_manager and hasattr(self, "layout_manager"):
                for host_name in hosts:
                    if host_name in self.layout_manager.host_sections:
                        host_section = self.layout_manager.host_sections[host_name]
                        if hasattr(host_section, "progress_info"):
                            host_section.progress_info = (
                                self.progress_display_manager.get_host_progress_info(
                                    host_name
                                )
                            )
                            logging.debug(
                                f"Initialized progress info for {host_name}: {host_section.progress_info}"
                            )

            # Initialize renderer with auto-exit manager
            self.renderer = Renderer(
                self.term, self.statistics_manager, self.auto_exit_manager
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

    def _create_step_change_callback(self):
        """Create the step change callback function."""
        logging.debug("Creating step change callback function")

        def step_change_callback(host_name: str, step: str) -> None:
            """Callback for when build steps change on a host."""
            logging.debug(f"Step change callback called for {host_name}: {step}")

            if self.progress_display_manager:
                self.progress_display_manager.update_build_step(host_name, step)
                logging.debug(f"Updated build step for {host_name}: {step}")
            else:
                logging.debug(f"No progress display manager available for {host_name}")

            # Also update the host section's progress info
            if (
                hasattr(self, "host_visibility_manager")
                and self.host_visibility_manager
            ):
                if host_name in self.host_visibility_manager.host_sections:
                    host_section = self.host_visibility_manager.host_sections[host_name]
                    if hasattr(host_section, "progress_info"):
                        host_section.progress_info = (
                            self.progress_display_manager.get_host_progress_info(
                                host_name
                            )
                            if self.progress_display_manager
                            else {}
                        )
                        logging.debug(
                            f"Updated progress info for {host_name}: {host_section.progress_info}"
                        )
                else:
                    logging.debug(
                        f"Host {host_name} not found in host visibility manager host sections"
                    )
            else:
                logging.debug("No host visibility manager available")

        logging.debug(
            f"Step change callback function created: {step_change_callback is not None}"
        )
        return step_change_callback

    def _get_cache_key(self, host_name: str) -> str:
        """
        Get the proper cache key for a host in user@hostname format.
        
        Args:
            host_name: Host name as provided (may or may not include username)
            
        Returns:
            Cache key in user@hostname format
        """
        # If host_name already contains @, return as-is
        if "@" in host_name:
            return host_name
        # Otherwise, prepend current user
        return f"{self.current_user}@{host_name}"

    def _trigger_exit(self) -> None:
        """Trigger application exit (called by auto-exit manager)."""
        logging.info("Auto-exit triggered, setting running to False")
        self.running = False

    def _on_build_start(self, host_name: str) -> None:
        """Called when a build starts on a specific host."""
        logging.debug(f"Build started for {host_name}, starting timing tracking")
        self.build_summary_collector.start_build_tracking(host_name)

        # Start progress tracking if enabled
        if self.progress_display_manager:
            self.progress_display_manager.start_build_tracking(host_name)
            logging.debug(f"Started progress tracking for {host_name}")

            # Update the host section's progress info
            if hasattr(self, "layout_manager") and self.layout_manager:
                if host_name in self.layout_manager.host_sections:
                    host_section = self.layout_manager.host_sections[host_name]
                    if hasattr(host_section, "progress_info"):
                        host_section.progress_info = (
                            self.progress_display_manager.get_host_progress_info(
                                host_name
                            )
                        )
                        logging.debug(
                            f"Updated initial progress info for {host_name}: {host_section.progress_info}"
                        )

    def _extract_build_timing(self, output_lines: List[str]) -> Dict[str, float]:
        """
        Extract build timing data from output lines.

        Args:
            output_lines: List of output lines from the build

        Returns:
            Dictionary with timing data: {"configure": float, "make": float, "make_check": float}
        """
        timing_data = {}

        for line in output_lines:
            line = line.strip()
            # Look for timing patterns like "configure succeeded (8.0 secs)"
            if "configure succeeded" in line and "secs" in line:
                try:
                    # Extract time from "(8.0 secs)" format
                    time_match = re.search(r"\(([\d.]+)\s*secs?\)", line)
                    if time_match:
                        timing_data["configure"] = float(time_match.group(1))
                except (ValueError, AttributeError):
                    pass
            elif "make succeeded" in line and "secs" in line and "check" not in line:
                try:
                    time_match = re.search(r"\(([\d.]+)\s*secs?\)", line)
                    if time_match:
                        timing_data["make"] = float(time_match.group(1))
                except (ValueError, AttributeError):
                    pass
            elif "make check succeeded" in line and "secs" in line:
                try:
                    time_match = re.search(r"\(([\d.]+)\s*secs?\)", line)
                    if time_match:
                        timing_data["make_check"] = float(time_match.group(1))
                except (ValueError, AttributeError):
                    pass

        return timing_data

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

    def _on_navigate_left(self) -> None:
        """Handle left navigation between all hosts."""
        # Navigate to previous host (including completed ones)
        self.focused_host = (self.focused_host - 1) % len(self.hosts)

    def _on_navigate_right(self) -> None:
        """Handle right navigation between all hosts."""
        # Navigate to next host (including completed ones)
        self.focused_host = (self.focused_host + 1) % len(self.hosts)

    def _on_toggle_fullscreen(self) -> None:
        """Handle full-screen toggle for current host."""
        # TODO: Implement full-screen mode
        logging.debug(f"Full-screen toggle requested for host {self.focused_host}")

    def _on_escape(self) -> None:
        """Handle escape key press."""
        # TODO: Implement escape functionality based on current mode
        logging.debug("Escape key pressed")

    def _on_toggle_menu(self) -> None:
        """Handle menu toggle."""
        # TODO: Implement menu system
        logging.debug("Menu toggle requested")

    def _on_page_up(self) -> None:
        """Handle page up for log scrolling."""
        # TODO: Implement log scrolling
        logging.debug("Page up requested")

    def _on_page_down(self) -> None:
        """Handle page down for log scrolling."""
        # TODO: Implement log scrolling
        logging.debug("Page down requested")

    def _on_home(self) -> None:
        """Handle home key for log navigation."""
        # TODO: Implement log navigation
        logging.debug("Home key pressed")

    def _on_end(self) -> None:
        """Handle end key for log navigation."""
        # TODO: Implement log navigation
        logging.debug("End key pressed")

    def show_help(self) -> None:
        """Show help screen using InputHandler."""
        self.input_handler.show_help()

    def _handle_input_key(self, key) -> None:
        """Handle a single key press using the InputHandler."""
        self.input_handler._handle_key(
            key,
            on_quit=self._on_quit,
            on_navigate_up=self._on_navigate_up,
            on_navigate_down=self._on_navigate_down,
            on_show_help=self._on_show_help,
            on_navigate_left=self._on_navigate_left,
            on_navigate_right=self._on_navigate_right,
            on_toggle_fullscreen=self._on_toggle_fullscreen,
            on_escape=self._on_escape,
            on_toggle_menu=self._on_toggle_menu,
            on_page_up=self._on_page_up,
            on_page_down=self._on_page_down,
            on_home=self._on_home,
            on_end=self._on_end,
        )

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
                        # Handle input with proper terminal mode
                        with self.term.cbreak():
                            # Check for input with a very short timeout
                            key = self.term.inkey(timeout=0.05)
                            if key:
                                self._handle_input_key(key)

                        # Start new builds if slots are available
                        self.ssh_manager.start_builds()

                        # Update host visibility - hide completed hosts and show new ones
                        self._update_host_visibility()

                        # Continuously update progress info for all active builds
                        self._update_progress_info()

                        # Check for build completion and trigger auto-exit if needed
                        self._check_build_completion()

                        # Render UI
                        self.render()

                        # Small delay to prevent high CPU usage and reduce flickering
                        time.sleep(0.05)  # Reduced delay for more responsive input
                    except Exception as e:
                        import traceback

                        logging.error(f"Error in main loop: {e}")
                        logging.error("Full traceback:")
                        logging.error(traceback.format_exc())
                        print(f"Error in main loop: {e}")
                        print("Full traceback:")
                        print(traceback.format_exc())
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
                # Print build summary before cleanup
                if hasattr(self, "build_summary_collector"):
                    self.build_summary_collector.print_summary()

                # Clean up auto-exit manager
                if hasattr(self, "auto_exit_manager"):
                    self.auto_exit_manager.cleanup()

                # Clean up progress display manager
                if (
                    hasattr(self, "progress_display_manager")
                    and self.progress_display_manager
                ):
                    self.progress_display_manager.cleanup()

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

    def _check_build_completion(self) -> None:
        """Check for build completion and trigger auto-exit if needed."""
        # Check if any new builds have completed
        current_results = self.ssh_manager.get_results()

        for host_name, result in current_results.items():
            # Check if this is a newly completed build
            if result["status"] in ["SUCCESS", "FAILED"]:
                # Check if we already have a result for this host
                existing_result = self.build_summary_collector.get_build_result(
                    host_name
                )
                if existing_result is None:
                    # This is a new completion, record it
                    success = result["status"] == "SUCCESS"
                    error_message = None

                    # Try to extract error message from output
                    if not success and result.get("output"):
                        # Look for error messages in the output
                        output_lines = result["output"]
                        for line in reversed(output_lines):  # Start from end
                            if (
                                line.startswith("✗")
                                or "error" in line.lower()
                                or "failed" in line.lower()
                            ):
                                error_message = line.strip()
                                break

                    # Calculate total time before stopping tracking
                    total_time = None
                    start_time = self.build_summary_collector.host_start_times.get(
                        host_name
                    )
                    if start_time is not None:
                        total_time = time.time() - start_time

                    # Extract timing data from build output
                    timing_data = self._extract_build_timing(result.get("output", []))

                    # Record the build result with calculated total time
                    self.build_summary_collector.record_build_result(
                        host_name=host_name,
                        success=success,
                        error_message=error_message,
                        total_time=total_time,
                    )

                    # Record timing data in cache if available
                    if self.timing_cache and timing_data:
                        try:
                            # Get proper cache key in user@hostname format
                            cache_key = self._get_cache_key(host_name)
                            self.timing_cache.record_build_timing(
                                host_name=cache_key,
                                configure_time=timing_data.get("configure", 0.0),
                                make_time=timing_data.get("make", 0.0),
                                make_check_time=timing_data.get("make_check", 0.0),
                                total_time=total_time or 0.0,
                                success=success,
                            )
                            logging.debug(
                                f"Recorded timing data for {cache_key} (original: {host_name}): {timing_data}"
                            )
                        except Exception as e:
                            logging.warning(
                                f"Failed to record timing data for {host_name}: {e}"
                            )

                    # Stop tracking build time for this host
                    self.build_summary_collector.stop_build_tracking(host_name)

                    # Complete progress tracking if enabled
                    if self.progress_display_manager:
                        self.progress_display_manager.complete_build_tracking(host_name)
                        logging.debug(f"Completed progress tracking for {host_name}")

                    logging.debug(
                        f"Build completed for {host_name}: success={success}, total_time={total_time:.2f}s"
                    )

        # Check if ALL builds are now complete and trigger auto-exit
        if self.ssh_manager.is_build_complete():
            # Only trigger auto-exit if we haven't already
            if not self.auto_exit_manager.is_countdown_active():
                logging.info("All builds completed, starting auto-exit countdown")
                # Trigger auto-exit for the overall completion
                self.auto_exit_manager.on_build_completed("all_builds", True)

    def _handle_step_change(self, host_name: str, step: str) -> None:
        """
        Handle step changes from host sections.

        Args:
            host_name: Name of the host
            step: New step name
        """
        if self.step_change_callback:
            self.step_change_callback(host_name, step)
        else:
            logging.debug(
                f"Step change callback not available for {host_name} -> {step}"
            )

    def _update_progress_info(self) -> None:
        """Continuously update progress info for all active builds."""
        if not self.progress_display_manager:
            return

        # Update progress info for all active builds
        for host_name in self.host_visibility_manager.host_sections:
            host_section = self.host_visibility_manager.host_sections[host_name]

            # Only update if this host is actively building
            if host_name in self.ssh_manager.active_connections:
                if hasattr(host_section, "progress_info"):
                    # Get current progress info
                    current_progress = (
                        self.progress_display_manager.get_host_progress_info(host_name)
                    )
                    if current_progress:
                        # Update the host section's progress info
                        host_section.progress_info = current_progress
                        logging.debug(
                            f"Updated continuous progress info for {host_name}: {current_progress}"
                        )


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
