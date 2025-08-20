#!/usr/bin/python3
"""
SSH Connection Module

A utility module for managing SSH connections with paramiko.
"""

import logging
import socket
from typing import Optional, Tuple

import paramiko


class BuildRedlandError(Exception):
    """Base exception for Build Redland TUI errors."""

    pass


class SSHConnectionError(BuildRedlandError):
    """Raised when SSH connection fails."""

    def __init__(
        self, hostname: str, message: str, original_error: Optional[Exception] = None
    ):
        self.hostname = hostname
        self.original_error = original_error
        super().__init__(f"SSH connection failed for {hostname}: {message}")


class FileTransferError(BuildRedlandError):
    """Raised when file transfer fails."""

    def __init__(self, hostname: str, local_path: str, remote_path: str, message: str):
        self.hostname = hostname
        self.local_path = local_path
        self.remote_path = remote_path
        super().__init__(
            f"File transfer failed for {hostname} ({local_path} -> {remote_path}): {message}"
        )


class BuildExecutionError(BuildRedlandError):
    """Raised when build execution fails."""

    def __init__(self, hostname: str, exit_code: int, message: str):
        self.hostname = hostname
        self.exit_code = exit_code
        super().__init__(
            f"Build failed for {hostname} (exit code {exit_code}): {message}"
        )


class BuildTimeoutError(BuildRedlandError):
    """Raised when build times out."""

    def __init__(self, hostname: str, timeout_seconds: int):
        self.hostname = hostname
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Build timed out for {hostname} after {timeout_seconds} seconds"
        )


class TerminalError(BuildRedlandError):
    """Raised when terminal operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(f"Terminal error: {message}")


class ConfigurationError(BuildRedlandError):
    """Raised when configuration is invalid."""

    pass


def parse_hostname(hostname: str) -> Tuple[Optional[str], str]:
    """
    Parse hostname into username and hostname parts.

    Args:
        hostname: Hostname string that may contain username@hostname format

    Returns:
        Tuple of (username, hostname) where username may be None
    """
    if "@" in hostname:
        username, host = hostname.split("@", 1)
        return username, host
    return None, hostname


class SSHConnection:
    """Manages SSH connections using paramiko."""

    def __init__(
        self, hostname: str, username: Optional[str] = None, timeout: int = 30
    ):
        """
        Initialize SSH connection.

        Args:
            hostname: Target hostname
            username: SSH username (optional)
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.username = username
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None

    def connect(self) -> bool:
        """
        Establish SSH connection.

        Returns:
            True if connection successful, raises SSHConnectionError otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with username if provided
            if self.username:
                self.client.connect(
                    self.hostname, username=self.username, timeout=self.timeout
                )
            else:
                self.client.connect(self.hostname, timeout=self.timeout)

            logging.debug(f"SSH connection established to {self.hostname}")
            return True

        except paramiko.AuthenticationException as e:
            logging.error(f"Authentication failed for {self.hostname}: {e}")
            raise SSHConnectionError(self.hostname, "Authentication failed", e)
        except paramiko.SSHException as e:
            logging.error(f"SSH error for {self.hostname}: {e}")
            raise SSHConnectionError(self.hostname, "SSH protocol error", e)
        except socket.timeout as e:
            logging.error(f"Connection timeout for {self.hostname}: {e}")
            raise SSHConnectionError(self.hostname, "Connection timeout", e)
        except Exception as e:
            logging.error(f"Failed to connect to {self.hostname}: {e}")
            raise SSHConnectionError(self.hostname, f"Connection failed: {str(e)}", e)

    def get_effective_username(self) -> Optional[str]:
        """
        Get the effective username being used for the SSH connection.
        
        Returns:
            Username string or None if not connected or unable to determine
        """
        if not self.client or not self.client.get_transport():
            return None
            
        # If username was explicitly provided, return it
        if self.username:
            return self.username
            
        # Try to get username from the SSH transport
        try:
            transport = self.client.get_transport()
            if transport:
                return transport.get_username()
        except:
            pass
            
        return None

    def get_effective_connection_string(self) -> str:
        """
        Get the effective connection string in user@hostname format.
        
        Returns:
            Connection string in user@hostname format, or just hostname if username unavailable
        """
        effective_username = self.get_effective_username()
        if effective_username:
            return f"{effective_username}@{self.hostname}"
        return self.hostname

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command and return (exit_code, stdout, stderr).

        Args:
            command: Command to execute

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.client:
            return -1, "", "Not connected"

        try:
            stdin, stdout, stderr = self.client.exec_command(
                command, timeout=self.timeout
            )
            exit_code = stdout.channel.recv_exit_status()

            stdout_str = stdout.read().decode("utf-8", errors="ignore")
            stderr_str = stderr.read().decode("utf-8", errors="ignore")

            return exit_code, stdout_str, stderr_str

        except Exception as e:
            logging.error(f"Command execution failed on {self.hostname}: {e}")
            return -1, "", str(e)

    def transfer_file(self, local_path: str, remote_path: str) -> bool:
        """
        Transfer a file using SFTP.

        Args:
            local_path: Local file path
            remote_path: Remote file path

        Returns:
            True if transfer successful

        Raises:
            FileTransferError: If transfer fails
        """
        if not self.client:
            raise FileTransferError(
                self.hostname, local_path, remote_path, "Not connected"
            )

        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            self.sftp.put(local_path, remote_path)
            logging.debug(f"Transferred {local_path} to {self.hostname}:{remote_path}")
            return True

        except FileNotFoundError as e:
            raise FileTransferError(
                self.hostname,
                local_path,
                remote_path,
                f"Local file not found: {str(e)}",
            )
        except PermissionError as e:
            raise FileTransferError(
                self.hostname, local_path, remote_path, f"Permission denied: {str(e)}"
            )
        except Exception as e:
            raise FileTransferError(
                self.hostname, local_path, remote_path, f"Transfer failed: {str(e)}"
            )

    def close(self) -> None:
        """Close SSH connection."""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logging.debug(f"SSH connection closed to {self.hostname}")

    def is_connected(self) -> bool:
        """
        Check if SSH connection is active.

        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and self.client.get_transport() is not None

    def get_transport(self) -> Optional[paramiko.Transport]:
        """
        Get the underlying paramiko transport.

        Returns:
            Paramiko transport object or None if not connected
        """
        if self.client:
            return self.client.get_transport()
        return None
