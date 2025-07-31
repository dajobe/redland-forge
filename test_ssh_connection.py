#!/usr/bin/python3
"""
Unit tests for SSHConnection class and related functions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import paramiko
import socket

from ssh_connection import (
    SSHConnection,
    parse_hostname,
    SSHConnectionError,
    FileTransferError,
    BuildExecutionError,
    BuildTimeoutError,
    TerminalError,
    ConfigurationError,
    BuildRedlandError,
)


class TestParseHostname(unittest.TestCase):
    """Test cases for parse_hostname function."""

    def test_parse_hostname_with_username(self):
        """Test parsing hostname with username."""
        username, hostname = parse_hostname("user@example.com")
        self.assertEqual(username, "user")
        self.assertEqual(hostname, "example.com")

    def test_parse_hostname_without_username(self):
        """Test parsing hostname without username."""
        username, hostname = parse_hostname("example.com")
        self.assertIsNone(username)
        self.assertEqual(hostname, "example.com")

    def test_parse_hostname_with_at_in_username(self):
        """Test parsing hostname with @ in username."""
        username, hostname = parse_hostname("user@domain@example.com")
        self.assertEqual(username, "user")  # Splits on first @
        self.assertEqual(hostname, "domain@example.com")

    def test_parse_hostname_empty(self):
        """Test parsing empty hostname."""
        username, hostname = parse_hostname("")
        self.assertIsNone(username)
        self.assertEqual(hostname, "")


class TestSSHConnection(unittest.TestCase):
    """Test cases for SSHConnection class."""

    def setUp(self):
        """Set up test fixtures."""
        self.connection = SSHConnection("test.example.com", "testuser", 30)

    def test_initialization(self):
        """Test SSHConnection initialization."""
        self.assertEqual(self.connection.hostname, "test.example.com")
        self.assertEqual(self.connection.username, "testuser")
        self.assertEqual(self.connection.timeout, 30)
        self.assertIsNone(self.connection.client)
        self.assertIsNone(self.connection.sftp)

    def test_initialization_without_username(self):
        """Test SSHConnection initialization without username."""
        connection = SSHConnection("test.example.com")
        self.assertEqual(connection.hostname, "test.example.com")
        self.assertIsNone(connection.username)
        self.assertEqual(connection.timeout, 30)

    def test_is_connected_not_connected(self):
        """Test is_connected when not connected."""
        self.assertFalse(self.connection.is_connected())

    def test_is_connected_connected(self):
        """Test is_connected when connected."""
        # Mock the client and transport
        mock_client = Mock()
        mock_transport = Mock()
        mock_client.get_transport.return_value = mock_transport
        self.connection.client = mock_client

        self.assertTrue(self.connection.is_connected())

    def test_is_connected_no_transport(self):
        """Test is_connected when client exists but no transport."""
        mock_client = Mock()
        mock_client.get_transport.return_value = None
        self.connection.client = mock_client

        self.assertFalse(self.connection.is_connected())

    def test_get_transport_not_connected(self):
        """Test get_transport when not connected."""
        self.assertIsNone(self.connection.get_transport())

    def test_get_transport_connected(self):
        """Test get_transport when connected."""
        mock_client = Mock()
        mock_transport = Mock()
        mock_client.get_transport.return_value = mock_transport
        self.connection.client = mock_client

        self.assertEqual(self.connection.get_transport(), mock_transport)

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_success(self, mock_ssh_client_class):
        """Test successful connection."""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.return_value = None

        result = self.connection.connect()

        self.assertTrue(result)
        self.assertEqual(self.connection.client, mock_client)
        mock_client.set_missing_host_key_policy.assert_called_once()
        # Check that it was called with AutoAddPolicy (don't check exact object)
        call_args = mock_client.set_missing_host_key_policy.call_args[0]
        self.assertIsInstance(call_args[0], paramiko.AutoAddPolicy)
        mock_client.connect.assert_called_once_with(
            "test.example.com", username="testuser", timeout=30
        )

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_success_without_username(self, mock_ssh_client_class):
        """Test successful connection without username."""
        connection = SSHConnection("test.example.com")
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.return_value = None

        result = connection.connect()

        self.assertTrue(result)
        mock_client.connect.assert_called_once_with("test.example.com", timeout=30)

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_authentication_failed(self, mock_ssh_client_class):
        """Test connection with authentication failure."""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = paramiko.AuthenticationException(
            "Auth failed"
        )

        with self.assertRaises(SSHConnectionError) as context:
            self.connection.connect()

        self.assertIn("Authentication failed", str(context.exception))
        self.assertEqual(context.exception.hostname, "test.example.com")

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_ssh_exception(self, mock_ssh_client_class):
        """Test connection with SSH exception."""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = paramiko.SSHException("SSH error")

        with self.assertRaises(SSHConnectionError) as context:
            self.connection.connect()

        self.assertIn("SSH protocol error", str(context.exception))

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_timeout(self, mock_ssh_client_class):
        """Test connection timeout."""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = socket.timeout("Connection timeout")

        with self.assertRaises(SSHConnectionError) as context:
            self.connection.connect()

        self.assertIn("Connection timeout", str(context.exception))

    @patch("ssh_connection.paramiko.SSHClient")
    def test_connect_general_exception(self, mock_ssh_client_class):
        """Test connection with general exception."""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = Exception("General error")

        with self.assertRaises(SSHConnectionError) as context:
            self.connection.connect()

        self.assertIn("Connection failed", str(context.exception))

    def test_execute_command_not_connected(self):
        """Test command execution when not connected."""
        exit_code, stdout, stderr = self.connection.execute_command("ls")

        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Not connected")

    def test_execute_command_success(self):
        """Test successful command execution."""
        # Mock the client and command execution
        mock_client = Mock()
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_stdout.channel = mock_channel
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.read.return_value = b"file1.txt\nfile2.txt\n"
        mock_stderr.read.return_value = b""

        self.connection.client = mock_client

        exit_code, stdout, stderr = self.connection.execute_command("ls")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "file1.txt\nfile2.txt\n")
        self.assertEqual(stderr, "")
        mock_client.exec_command.assert_called_once_with("ls", timeout=30)

    def test_execute_command_with_error(self):
        """Test command execution with error."""
        # Mock the client and command execution
        mock_client = Mock()
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_stdout.channel = mock_channel
        mock_channel.recv_exit_status.return_value = 1
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"No such file or directory\n"

        self.connection.client = mock_client

        exit_code, stdout, stderr = self.connection.execute_command("ls /nonexistent")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "No such file or directory\n")

    def test_execute_command_exception(self):
        """Test command execution with exception."""
        mock_client = Mock()
        mock_client.exec_command.side_effect = Exception("Command failed")
        self.connection.client = mock_client

        exit_code, stdout, stderr = self.connection.execute_command("ls")

        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Command failed")

    def test_transfer_file_not_connected(self):
        """Test file transfer when not connected."""
        with self.assertRaises(FileTransferError) as context:
            self.connection.transfer_file("/local/file", "/remote/file")

        self.assertIn("Not connected", str(context.exception))

    def test_transfer_file_success(self):
        """Test successful file transfer."""
        # Mock the client and SFTP
        mock_client = Mock()
        mock_sftp = Mock()
        mock_client.open_sftp.return_value = mock_sftp

        self.connection.client = mock_client

        result = self.connection.transfer_file("/local/file", "/remote/file")

        self.assertTrue(result)
        mock_client.open_sftp.assert_called_once()
        mock_sftp.put.assert_called_once_with("/local/file", "/remote/file")

    def test_transfer_file_sftp_already_exists(self):
        """Test file transfer when SFTP already exists."""
        # Mock the client and existing SFTP
        mock_client = Mock()
        mock_sftp = Mock()

        self.connection.client = mock_client
        self.connection.sftp = mock_sftp

        result = self.connection.transfer_file("/local/file", "/remote/file")

        self.assertTrue(result)
        mock_client.open_sftp.assert_not_called()  # Should not create new SFTP
        mock_sftp.put.assert_called_once_with("/local/file", "/remote/file")

    def test_transfer_file_file_not_found(self):
        """Test file transfer with file not found error."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_sftp.put.side_effect = FileNotFoundError("File not found")
        mock_client.open_sftp.return_value = mock_sftp

        self.connection.client = mock_client

        with self.assertRaises(FileTransferError) as context:
            self.connection.transfer_file("/local/file", "/remote/file")

        self.assertIn("Local file not found", str(context.exception))

    def test_transfer_file_permission_error(self):
        """Test file transfer with permission error."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_sftp.put.side_effect = PermissionError("Permission denied")
        mock_client.open_sftp.return_value = mock_sftp

        self.connection.client = mock_client

        with self.assertRaises(FileTransferError) as context:
            self.connection.transfer_file("/local/file", "/remote/file")

        self.assertIn("Permission denied", str(context.exception))

    def test_transfer_file_general_error(self):
        """Test file transfer with general error."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_sftp.put.side_effect = Exception("Transfer failed")
        mock_client.open_sftp.return_value = mock_sftp

        self.connection.client = mock_client

        with self.assertRaises(FileTransferError) as context:
            self.connection.transfer_file("/local/file", "/remote/file")

        self.assertIn("Transfer failed", str(context.exception))

    def test_close_with_sftp_and_client(self):
        """Test closing connection with both SFTP and client."""
        mock_client = Mock()
        mock_sftp = Mock()

        self.connection.client = mock_client
        self.connection.sftp = mock_sftp

        self.connection.close()

        mock_sftp.close.assert_called_once()
        mock_client.close.assert_called_once()

    def test_close_with_client_only(self):
        """Test closing connection with client only."""
        mock_client = Mock()
        self.connection.client = mock_client

        self.connection.close()

        mock_client.close.assert_called_once()

    def test_close_with_nothing(self):
        """Test closing connection with no active connections."""
        # Should not raise any exceptions
        self.connection.close()


class TestExceptionClasses(unittest.TestCase):
    """Test cases for exception classes."""

    def test_ssh_connection_error(self):
        """Test SSHConnectionError."""
        original_error = Exception("Original error")
        error = SSHConnectionError(
            "test.example.com", "Connection failed", original_error
        )

        self.assertEqual(error.hostname, "test.example.com")
        self.assertEqual(error.original_error, original_error)
        self.assertIn("SSH connection failed for test.example.com", str(error))

    def test_file_transfer_error(self):
        """Test FileTransferError."""
        error = FileTransferError(
            "test.example.com", "/local/file", "/remote/file", "Transfer failed"
        )

        self.assertEqual(error.hostname, "test.example.com")
        self.assertEqual(error.local_path, "/local/file")
        self.assertEqual(error.remote_path, "/remote/file")
        self.assertIn("File transfer failed for test.example.com", str(error))

    def test_build_execution_error(self):
        """Test BuildExecutionError."""
        error = BuildExecutionError("test.example.com", 1, "Build failed")

        self.assertEqual(error.hostname, "test.example.com")
        self.assertEqual(error.exit_code, 1)
        self.assertIn("Build failed for test.example.com", str(error))

    def test_build_timeout_error(self):
        """Test BuildTimeoutError."""
        error = BuildTimeoutError("test.example.com", 3600)

        self.assertEqual(error.hostname, "test.example.com")
        self.assertEqual(error.timeout_seconds, 3600)
        self.assertIn("Build timed out for test.example.com", str(error))

    def test_terminal_error(self):
        """Test TerminalError."""
        original_error = Exception("Original error")
        error = TerminalError("Terminal failed", original_error)

        self.assertEqual(error.original_error, original_error)
        self.assertIn("Terminal error", str(error))

    def test_inheritance(self):
        """Test that all exceptions inherit from BuildRedlandError."""
        exceptions = [
            SSHConnectionError("test", "error"),
            FileTransferError("test", "/local", "/remote", "error"),
            BuildExecutionError("test", 1, "error"),
            BuildTimeoutError("test", 30),
            TerminalError("error"),
            ConfigurationError(),
        ]

        for exc in exceptions:
            self.assertIsInstance(exc, BuildRedlandError)


if __name__ == "__main__":
    unittest.main()
