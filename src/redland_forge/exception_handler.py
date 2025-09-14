#!/usr/bin/env python3
"""
Exception Handler Module

Provides consistent exception handling and user visibility across the application.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum


class ExceptionSeverity(Enum):
    """Severity levels for exceptions."""

    CRITICAL = "CRITICAL"  # Program-breaking errors that should terminate execution
    HIGH = "HIGH"  # Serious errors that affect functionality but allow continuation
    MEDIUM = (
        "MEDIUM"  # Errors that affect specific operations but don't break the program
    )
    LOW = "LOW"  # Minor errors that can be safely ignored or logged only


class BuildException(Exception):
    """Custom exception class for build-related errors."""

    def __init__(
        self,
        message: str,
        severity: ExceptionSeverity = ExceptionSeverity.MEDIUM,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.severity = severity
        self.user_message = user_message or message
        self.details = details or {}


class ExceptionHandler:
    """Centralized exception handling for the application."""

    @staticmethod
    def handle_exception(
        e: Exception,
        context: str = "",
        hostname: Optional[str] = None,
        show_user: bool = True,
        log_level: int = logging.ERROR,
    ) -> Dict[str, Any]:
        """
        Handle an exception with appropriate logging and user visibility.

        Args:
            e: The exception that occurred
            context: Description of where the exception occurred
            hostname: Hostname associated with the exception (if applicable)
            show_user: Whether to show the exception to the user in the TUI
            log_level: Logging level for this exception

        Returns:
            Dictionary with handling results and user messages
        """
        # Get exception details
        exc_type = type(e).__name__
        exc_message = str(e)
        exc_traceback = traceback.format_exc()

        # Determine severity based on exception type
        severity = ExceptionHandler._determine_severity(e)

        # Create context string
        context_str = f"{context}" if context else ""
        if hostname:
            context_str = f"{hostname}: {context_str}" if context_str else hostname

        # Log the exception
        log_message = (
            f"{context_str}: {exc_type}: {exc_message}"
            if context_str
            else f"{exc_type}: {exc_message}"
        )
        logging.log(log_level, log_message)
        logging.debug(f"Full traceback for {context_str}:")
        logging.debug(exc_traceback)

        # Create user-visible message
        user_message = ExceptionHandler._create_user_message(e, context_str, severity)

        # Determine if this should be shown to user
        should_show_user = show_user and severity in [
            ExceptionSeverity.CRITICAL,
            ExceptionSeverity.HIGH,
        ]

        return {
            "severity": severity,
            "user_message": user_message,
            "should_show_user": should_show_user,
            "log_message": log_message,
            "traceback": exc_traceback,
            "exception_type": exc_type,
            "context": context_str,
        }

    @staticmethod
    def _determine_severity(e: Exception) -> ExceptionSeverity:
        """Determine the severity of an exception based on its type."""
        exc_type = type(e).__name__

        # Critical exceptions that should terminate execution
        critical_exceptions = ["SystemExit", "KeyboardInterrupt", "MemoryError"]

        # High severity exceptions that affect major functionality
        high_severity_exceptions = [
            "ConnectionError",
            "TimeoutError",
            "AuthenticationError",
            "SSHException",
            "FileNotFoundError",
            "PermissionError",
            "OSError",
            "IOError",
            "NameError",
            "ImportError",
        ]

        # Medium severity exceptions for operational issues
        medium_severity_exceptions = [
            "ValueError",
            "TypeError",
            "AttributeError",
            "KeyError",
            "IndexError",
            "RuntimeError",
        ]

        if exc_type in critical_exceptions:
            return ExceptionSeverity.CRITICAL
        elif exc_type in high_severity_exceptions:
            return ExceptionSeverity.HIGH
        elif exc_type in medium_severity_exceptions:
            return ExceptionSeverity.MEDIUM
        else:
            return ExceptionSeverity.LOW

    @staticmethod
    def _create_user_message(
        e: Exception, context: str, severity: ExceptionSeverity
    ) -> str:
        """Create a user-friendly message for the exception."""
        exc_type = type(e).__name__
        exc_message = str(e)

        # Customize messages based on exception type and severity
        if severity == ExceptionSeverity.CRITICAL:
            prefix = "🚨 CRITICAL ERROR"
        elif severity == ExceptionSeverity.HIGH:
            prefix = "❌ ERROR"
        elif severity == ExceptionSeverity.MEDIUM:
            prefix = "⚠️  WARNING"
        else:
            prefix = "ℹ️  INFO"

        if context:
            return f"{prefix} [{context}]: {exc_message}"
        else:
            return f"{prefix}: {exc_message}"

    @staticmethod
    def should_terminate(severity: ExceptionSeverity) -> bool:
        """Determine if the application should terminate based on exception severity."""
        return severity == ExceptionSeverity.CRITICAL

    @staticmethod
    def format_exception_summary(results: Dict[str, Any]) -> str:
        """Format exception results into a summary string for display."""
        severity_emoji = {
            ExceptionSeverity.CRITICAL: "🚨",
            ExceptionSeverity.HIGH: "❌",
            ExceptionSeverity.MEDIUM: "⚠️",
            ExceptionSeverity.LOW: "ℹ️",
        }

        emoji = severity_emoji.get(results["severity"], "❓")
        return f"{emoji} {results['user_message']}"
