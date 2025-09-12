#!/usr/bin/python3
"""
Parallel SSH Manager Module

A module for managing parallel SSH connections and builds using paramiko.
"""

import logging
import os
import threading
import time
from typing import Dict, List, Optional

import paramiko

from .config import Config
from .color_manager import ColorManager
from .host_section import Colors
from .exception_handler import ExceptionHandler, ExceptionSeverity
from .ssh_connection import (
    SSHConnection,
    parse_hostname,
    BuildRedlandError,
    SSHConnectionError,
    FileTransferError,
    BuildExecutionError,
    BuildTimeoutError,
    TerminalError,
    ConfigurationError,
)


class ParallelSSHManager:
    """Manages parallel SSH connections and builds using paramiko."""

    def __init__(
        self, max_concurrent: int = 4, bindings_languages: Optional[List[str]] = None
    ):
        """
        Initialize the parallel SSH manager.

        Args:
            max_concurrent: Maximum number of concurrent builds
            bindings_languages: Optional list of language bindings to build.
        """
        self.max_concurrent = max_concurrent
        self.active_connections = {}
        self.connection_queue = []
        self.results = {}
        self.lock = threading.Lock()
        self.build_script_path = None
        self.build_start_callback = None
        self.bindings_languages = bindings_languages

    def add_host(self, hostname: str, tarball: str) -> None:
        """
        Add a host to the build queue.

        Args:
            hostname: Hostname to add (can include username@hostname)
            tarball: Path to the tarball to build
        """
        self.connection_queue.append((hostname, tarball))

    def set_build_script_path(self, script_path: str) -> None:
        """
        Set the path to the build script.

        Args:
            script_path: Path to the build script (build-agent.py)
        """
        self.build_script_path = script_path

    def set_build_start_callback(self, callback):
        """
        Set callback function to be called when a build starts.

        Args:
            callback: Function to call with hostname when build starts
        """
        self.build_start_callback = callback

    def start_builds(self) -> None:
        """Start builds up to concurrency limit."""
        while (
            len(self.active_connections) < self.max_concurrent and self.connection_queue
        ):
            hostname, tarball = self.connection_queue.pop(0)
            logging.debug(
                f"Starting build for {hostname} (queue size: {len(self.connection_queue)})"
            )
            self._start_build(hostname, tarball)

    def _start_build(self, hostname: str, tarball: str) -> None:
        """
        Start a build on a specific host.

        Args:
            hostname: Hostname to build on
            tarball: Path to the build script
        """
        # Notify that build is starting
        if self.build_start_callback:
            try:
                self.build_start_callback(hostname)
            except Exception as e:
                logging.error(f"Error in build start callback for {hostname}: {e}")

        thread = threading.Thread(target=self._build_worker, args=(hostname, tarball))
        thread.daemon = True
        thread.start()
        self.active_connections[hostname] = thread

    def _build_worker(self, hostname: str, tarball: str) -> None:
        """
        Worker thread for building on a host using real SSH.

        Args:
            hostname: Hostname to build on
            tarball: Path to the tarball
        """
        with self.lock:
            self.results[hostname] = {"status": "CONNECTING", "output": []}

        # Parse hostname for username
        username, host = parse_hostname(hostname)

        # Create SSH connection
        ssh = SSHConnection(host, username)

        try:
            # Connect to host
            try:
                if not ssh.connect():
                    with self.lock:
                        self.results[hostname]["status"] = "FAILED"
                        self.results[hostname]["output"].append(
                            "✗ Failed to establish SSH connection"
                        )
                    logging.error(f"SSH connection failed for {hostname}")
                    return

            except Exception as e:
                exception_results = ExceptionHandler.handle_exception(
                    e, "SSH connection failed", hostname, show_user=True
                )
                with self.lock:
                    self.results[hostname]["status"] = "FAILED"
                    self.results[hostname]["output"].append(
                        ExceptionHandler.format_exception_summary(exception_results)
                    )
                return

            with self.lock:
                self.results[hostname]["status"] = "PREPARING"
                self.results[hostname]["output"].append("SSH connection established")

            # Get system info
            exit_code, stdout, stderr = ssh.execute_command("uname -a")
            if exit_code == 0:
                with self.lock:
                    self.results[hostname]["output"].append(f"System: {stdout.strip()}")

            # Get CPU count
            exit_code, stdout, stderr = ssh.execute_command("nproc")
            if exit_code == 0:
                cpu_count = stdout.strip()
                with self.lock:
                    self.results[hostname]["output"].append(f"CPUs: {cpu_count}")

            # Resolve remote build directory to an absolute path for SFTP
            # Prefer SFTP normalize to get the remote home directory reliably
            try:
                if not ssh.sftp:
                    ssh.sftp = ssh.client.open_sftp()
                remote_home_dir = ssh.sftp.normalize(".")
            except Exception as e:
                # Fallback: try shell to get HOME
                exception_results = ExceptionHandler.handle_exception(
                    e, "SFTP directory resolution failed, using fallback", hostname, show_user=False
                )
                with self.lock:
                    self.results[hostname]["output"].append(
                        f"⚠️  Using fallback directory resolution due to SFTP issue"
                    )
                exit_code, stdout, _ = ssh.execute_command("pwd")
                remote_home_dir = stdout.strip() if exit_code == 0 else ""

            remote_build_dir = (
                f"{remote_home_dir}/build"
                if remote_home_dir
                else Config.BUILD_DIRECTORY
            )

            # Report the discovered/used build directory in the host output
            with self.lock:
                self.results[hostname]["output"].append(
                    f"Using build directory: {remote_build_dir}"
                )

            # Ensure build directory exists (script will clean/recreate as needed)
            ssh.execute_command(f"mkdir -p '{remote_build_dir}'")

            # Transfer build script to home directory if available
            if self.build_script_path and os.path.exists(self.build_script_path):
                if ssh.transfer_file(
                    self.build_script_path,
                    f"{remote_home_dir}/{Config.BUILD_SCRIPT_NAME}",
                ):
                    with self.lock:
                        self.results[hostname]["output"].append(
                            "Build script transferred"
                        )
                else:
                    with self.lock:
                        self.results[hostname]["output"].append(
                            "Failed to transfer build script"
                        )

            # Transfer tarball to home directory
            if ssh.transfer_file(
                tarball, f"{remote_home_dir}/{os.path.basename(tarball)}"
            ):
                with self.lock:
                    self.results[hostname]["status"] = "BUILDING"
                    self.results[hostname]["output"].append(
                        "Tarball transferred, starting build"
                    )
            else:
                with self.lock:
                    self.results[hostname]["status"] = "FAILED"
                    self.results[hostname]["output"].append(
                        "Failed to transfer tarball"
                    )
                return

            # Extract package name
            tarball_name = os.path.basename(tarball)
            package_name = (
                tarball_name.replace(".tar.gz", "")
                .replace(".tar.bz2", "")
                .replace(".tar.xz", "")
            )

            # Change to home directory and start build so working area is $HOME/build
            build_cmd = f"cd '{remote_home_dir}' && python3 {Config.BUILD_SCRIPT_NAME} {tarball_name} --no-print-hostname"
            if self.bindings_languages:
                build_cmd += (
                    f" --bindings-languages {','.join(self.bindings_languages)}"
                )

            # Execute build command with real-time output monitoring
            stdin, stdout, stderr = ssh.client.exec_command(build_cmd)

            # Set build timeout
            build_timeout = Config.BUILD_TIMEOUT_SECONDS
            build_start_time = time.time()

            # Monitor output in real-time
            try:
                while not stdout.channel.exit_status_ready():
                    # Check if SSH connection is still alive
                    if (
                        not ssh.client.get_transport()
                        or not ssh.client.get_transport().is_active()
                    ):
                        with self.lock:
                            self.results[hostname]["status"] = "FAILED"
                            self.results[hostname]["output"].append(
                                "✗ SSH connection lost during build"
                            )
                        logging.warning(f"SSH connection lost for {hostname}")
                        return

                    # Check for build timeout
                    if time.time() - build_start_time > build_timeout:
                        with self.lock:
                            self.results[hostname]["status"] = "FAILED"
                            self.results[hostname]["output"].append(
                                f"✗ Build timed out after {build_timeout//3600} hours"
                            )
                        logging.warning(f"Build timed out for {hostname}")
                        raise BuildTimeoutError(hostname, build_timeout)

                    # Read available output
                    if stdout.channel.recv_ready():
                        line = stdout.readline()
                        if line:
                            with self.lock:
                                # Add host prefix with color like the original script
                                host_prefix = f"{ColorManager.get_ansi_color('BRIGHT_CYAN')}{hostname}>{ColorManager.get_ansi_color('RESET')} "
                                stdout_line = f"{host_prefix}{line.strip()}"
                                logging.debug(f"Adding stdout line: {stdout_line}")
                                self.results[hostname]["output"].append(stdout_line)

                                # Debug: Log specific lines we're interested in
                                if (
                                    "Running make" in line
                                    or "ceil, floor, round" in line
                                ):
                                    logging.info(
                                        f"Captured key line for {hostname}: '{line.strip()}'"
                                    )

                    # Read stderr
                    if stdout.channel.recv_stderr_ready():
                        line = stderr.readline()
                        if line:
                            with self.lock:
                                # Use [STDERR] prefix like the original script, with color
                                stderr_line = f"{ColorManager.get_ansi_color('BRIGHT_YELLOW')}[STDERR]{ColorManager.get_ansi_color('RESET')} {line.strip()}"
                                logging.debug(f"Adding stderr line: {stderr_line}")
                                self.results[hostname]["output"].append(stderr_line)

                                # Debug: Log specific lines we're interested in
                                if (
                                    "Running make" in line
                                    or "ceil, floor, round" in line
                                ):
                                    logging.info(
                                        f"Captured key stderr line for {hostname}: '{line.strip()}'"
                                    )

                    time.sleep(0.1)  # Small delay to prevent busy waiting

                # Get final exit code
                exit_code = stdout.channel.recv_exit_status()

                # Read any remaining output that might have been buffered
                # This is important to capture final completion messages
                remaining_stdout = stdout.read().decode("utf-8", errors="ignore")
                remaining_stderr = stderr.read().decode("utf-8", errors="ignore")

                # Add any remaining output lines
                if remaining_stdout:
                    for line in remaining_stdout.splitlines():
                        if line.strip():
                            with self.lock:
                                host_prefix = f"{ColorManager.get_ansi_color('BRIGHT_CYAN')}{hostname}>{ColorManager.get_ansi_color('RESET')} "
                                stdout_line = f"{host_prefix}{line.strip()}"
                                logging.debug(
                                    f"Adding remaining stdout line: {stdout_line}"
                                )
                                self.results[hostname]["output"].append(stdout_line)

                if remaining_stderr:
                    for line in remaining_stderr.splitlines():
                        if line.strip():
                            with self.lock:
                                stderr_line = f"{ColorManager.get_ansi_color('BRIGHT_YELLOW')}[STDERR]{ColorManager.get_ansi_color('RESET')} {line.strip()}"
                                logging.debug(
                                    f"Adding remaining stderr line: {stderr_line}"
                                )
                                self.results[hostname]["output"].append(stderr_line)

                # Set final status based on exit code
                with self.lock:
                    if exit_code == 0:
                        self.results[hostname]["status"] = "SUCCESS"
                        success_msg = "✓ Build completed successfully"
                        self.results[hostname]["output"].append(success_msg)
                        logging.debug(
                            f"Build completed successfully for {hostname}: {success_msg}"
                        )
                    elif exit_code == 255:
                        # SSH-specific error codes
                        self.results[hostname]["status"] = "FAILED"
                        failure_msg = f"✗ SSH connection failed (exit code {exit_code})"
                        self.results[hostname]["output"].append(failure_msg)
                        logging.error(
                            f"SSH connection failed for {hostname}: {failure_msg}"
                        )
                    elif exit_code > 0:
                        # Build failed
                        self.results[hostname]["status"] = "FAILED"
                        failure_msg = f"✗ Build failed with exit code {exit_code}"
                        self.results[hostname]["output"].append(failure_msg)
                        logging.debug(f"Build failed for {hostname}: {failure_msg}")
                    else:
                        # Unexpected exit code
                        self.results[hostname]["status"] = "FAILED"
                        failure_msg = (
                            f"✗ Build ended with unexpected exit code {exit_code}"
                        )
                        self.results[hostname]["output"].append(failure_msg)
                        logging.warning(
                            f"Unexpected exit code for {hostname}: {failure_msg}"
                        )

            except Exception as e:
                # Handle exceptions during output monitoring
                exception_results = ExceptionHandler.handle_exception(
                    e, "Build monitoring failed", hostname, show_user=True
                )
                with self.lock:
                    self.results[hostname]["status"] = "FAILED"
                    self.results[hostname]["output"].append(
                        ExceptionHandler.format_exception_summary(exception_results)
                    )

        except Exception as e:
            exception_results = ExceptionHandler.handle_exception(
                e, "Build process failed", hostname, show_user=True
            )
            with self.lock:
                self.results[hostname]["status"] = "FAILED"
                self.results[hostname]["output"].append(
                    ExceptionHandler.format_exception_summary(exception_results)
                )

        finally:
            # Clean up SSH connection
            ssh.close()

            # Remove from active connections
            with self.lock:
                if hostname in self.active_connections:
                    del self.active_connections[hostname]

    def get_results(self) -> Dict[str, Dict[str, any]]:
        """
        Get the current build results.

        Returns:
            Dictionary of build results by hostname
        """
        return self.results

    def get_active_connections(self) -> Dict[str, any]:
        """
        Get the current active connections.

        Returns:
            Dictionary of active connections by hostname
        """
        return self.active_connections

    def get_connection_queue(self) -> List[tuple]:
        """
        Get the current connection queue.

        Returns:
            List of (hostname, tarball) tuples in the queue
        """
        return self.connection_queue.copy()

    def is_build_complete(self) -> bool:
        """
        Check if all builds are complete.

        Returns:
            True if all builds are complete, False otherwise
        """
        return len(self.active_connections) == 0 and len(self.connection_queue) == 0

    def get_build_status_summary(self) -> Dict[str, int]:
        """
        Get a summary of build statuses.

        Returns:
            Dictionary with counts of each status
        """
        status_counts = {
            "CONNECTING": 0,
            "PREPARING": 0,
            "BUILDING": 0,
            "SUCCESS": 0,
            "FAILED": 0,
        }

        for result in self.results.values():
            status = result.get("status", "UNKNOWN")
            if status in status_counts:
                status_counts[status] += 1

        return status_counts
