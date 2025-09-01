#!/usr/bin/python3
"""
Configuration Module

A centralized configuration class for Build Redland TUI application settings.
"""

import logging
from typing import Dict, Any
from color_manager import ColorManager


class Config:
    """Configuration class for Build Redland TUI."""

    # Build process settings
    BUILD_TIMEOUT_SECONDS = 7200  # 2 hours
    # Remote build directory (relative to remote user's home)
    # Use $HOME so shell commands expand it; code resolves an absolute path for SFTP
    BUILD_DIRECTORY = "$HOME/build"
    BUILD_SCRIPT_NAME = "build-redland.py"

    # UI rendering settings
    MIN_RENDER_INTERVAL_SECONDS = 0.2
    TIMER_UPDATE_INTERVAL_SECONDS = 1.0
    HOST_VISIBILITY_TIMEOUT_SECONDS = 10.0
    HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS = 0.5  # Window around timeout for updates

    # Terminal layout settings
    MIN_TERMINAL_HEIGHT = 10
    MIN_HOST_HEIGHT = 8
    HEADER_HEIGHT = 4
    FOOTER_HEIGHT = 4
    TERMINAL_MARGIN = 2
    BORDER_PADDING = 4

    # Small terminal layout settings
    SMALL_TERMINAL_HEADER_FOOTER = 2  # Minimal header/footer space for small terminals
    SMALL_TERMINAL_MIN_HOST_HEIGHT = 3  # Minimum host height for small terminals
    SMALL_TERMINAL_MAX_VISIBLE_HOSTS = 1  # Maximum visible hosts for small terminals
    HOST_SECTION_START_Y = 3  # Starting Y position for host sections
    SMALL_TERMINAL_FOOTER_SPACE = 1  # Footer space for small terminals

    # SSH connection settings
    SSH_TIMEOUT_SECONDS = 30
    SSH_CONNECTION_RETRIES = 3

    # Output buffering settings
    MAX_OUTPUT_LINES_PER_HOST = 100
    OUTPUT_BUFFER_OVERFLOW_MARGIN = 3  # Lines to leave for "..." truncation

    # Status update settings
    STATUS_UPDATE_INTERVAL_SECONDS = 0.1

    # Auto-exit settings
    AUTO_EXIT_DELAY_SECONDS = 300  # 5 minutes
    AUTO_EXIT_ENABLED = True  # Can be disabled via config
    AUTO_EXIT_SHOW_COUNTDOWN = True  # Show countdown in UI

    # Timing cache settings
    TIMING_CACHE_FILE = ".config/build-tui/timing-cache.json"
    TIMING_CACHE_RETENTION_DAYS = 30
    TIMING_CACHE_KEEP_BUILDS = 5  # Number of recent builds to keep
    TIMING_CACHE_DEMO_RETENTION_HOURS = 1  # Demo hosts get 1 hour TTL
    TIMING_CACHE_ENABLED = True
    TIMING_CACHE_SHOW_PROGRESS = True

    # File transfer settings
    SFTP_CHUNK_SIZE = 8192

    # Logging settings
    DEFAULT_LOG_LEVEL = logging.INFO
    DEBUG_LOG_LEVEL = logging.DEBUG
    LOG_FILE = "debug.log"

    @classmethod
    def get_build_settings(cls) -> Dict[str, Any]:
        """
        Get all build process settings.

        Returns:
            Dictionary containing build process settings
        """
        return {
            "BUILD_TIMEOUT_SECONDS": cls.BUILD_TIMEOUT_SECONDS,
            "BUILD_DIRECTORY": cls.BUILD_DIRECTORY,
            "BUILD_SCRIPT_NAME": cls.BUILD_SCRIPT_NAME,
        }

    @classmethod
    def get_ui_settings(cls) -> Dict[str, Any]:
        """
        Get all UI rendering settings.

        Returns:
            Dictionary containing UI rendering settings
        """
        return {
            "MIN_RENDER_INTERVAL_SECONDS": cls.MIN_RENDER_INTERVAL_SECONDS,
            "TIMER_UPDATE_INTERVAL_SECONDS": cls.TIMER_UPDATE_INTERVAL_SECONDS,
            "HOST_VISIBILITY_TIMEOUT_SECONDS": cls.HOST_VISIBILITY_TIMEOUT_SECONDS,
            "HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS": cls.HOST_VISIBILITY_TIMEOUT_WINDOW_SECONDS,
            "AUTO_EXIT_DELAY_SECONDS": cls.AUTO_EXIT_DELAY_SECONDS,
            "AUTO_EXIT_ENABLED": cls.AUTO_EXIT_ENABLED,
            "AUTO_EXIT_SHOW_COUNTDOWN": cls.AUTO_EXIT_SHOW_COUNTDOWN,
            "TIMING_CACHE_FILE": cls.TIMING_CACHE_FILE,
            "TIMING_CACHE_RETENTION_DAYS": cls.TIMING_CACHE_RETENTION_DAYS,
            "TIMING_CACHE_KEEP_BUILDS": cls.TIMING_CACHE_KEEP_BUILDS,
            "TIMING_CACHE_ENABLED": cls.TIMING_CACHE_ENABLED,
            "TIMING_CACHE_SHOW_PROGRESS": cls.TIMING_CACHE_SHOW_PROGRESS,
        }

    @classmethod
    def get_layout_settings(cls) -> Dict[str, Any]:
        """
        Get all terminal layout settings.

        Returns:
            Dictionary containing terminal layout settings
        """
        return {
            "MIN_TERMINAL_HEIGHT": cls.MIN_TERMINAL_HEIGHT,
            "MIN_HOST_HEIGHT": cls.MIN_HOST_HEIGHT,
            "HEADER_HEIGHT": cls.HEADER_HEIGHT,
            "FOOTER_HEIGHT": cls.FOOTER_HEIGHT,
            "TERMINAL_MARGIN": cls.TERMINAL_MARGIN,
            "BORDER_PADDING": cls.BORDER_PADDING,
        }

    @classmethod
    def get_ssh_settings(cls) -> Dict[str, Any]:
        """
        Get all SSH connection settings.

        Returns:
            Dictionary containing SSH connection settings
        """
        return {
            "SSH_TIMEOUT_SECONDS": cls.SSH_TIMEOUT_SECONDS,
            "SSH_CONNECTION_RETRIES": cls.SSH_CONNECTION_RETRIES,
        }

    @classmethod
    def get_output_settings(cls) -> Dict[str, Any]:
        """
        Get all output buffering settings.

        Returns:
            Dictionary containing output buffering settings
        """
        return {
            "MAX_OUTPUT_LINES_PER_HOST": cls.MAX_OUTPUT_LINES_PER_HOST,
            "OUTPUT_BUFFER_OVERFLOW_MARGIN": cls.OUTPUT_BUFFER_OVERFLOW_MARGIN,
        }

    @classmethod
    def get_logging_settings(cls) -> Dict[str, Any]:
        """
        Get all logging settings.

        Returns:
            Dictionary containing logging settings
        """
        return {
            "DEFAULT_LOG_LEVEL": cls.DEFAULT_LOG_LEVEL,
            "DEBUG_LOG_LEVEL": cls.DEBUG_LOG_LEVEL,
            "LOG_FILE": cls.LOG_FILE,
        }

    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """
        Get all configuration settings organized by category.

        Returns:
            Dictionary containing all configuration settings
        """
        return {
            "build": cls.get_build_settings(),
            "ui": cls.get_ui_settings(),
            "layout": cls.get_layout_settings(),
            "ssh": cls.get_ssh_settings(),
            "output": cls.get_output_settings(),
            "logging": cls.get_logging_settings(),
            "colors": ColorManager.get_color_settings(),
        }

    @classmethod
    def validate_settings(cls) -> bool:
        """
        Validate that all configuration settings are within acceptable ranges.

        Returns:
            True if all settings are valid, False otherwise
        """
        try:
            # Validate build settings
            if cls.BUILD_TIMEOUT_SECONDS <= 0:
                return False

            # Validate UI settings
            if cls.MIN_RENDER_INTERVAL_SECONDS <= 0:
                return False
            if cls.TIMER_UPDATE_INTERVAL_SECONDS <= 0:
                return False
            if cls.HOST_VISIBILITY_TIMEOUT_SECONDS <= 0:
                return False

            # Validate layout settings
            if cls.MIN_TERMINAL_HEIGHT <= 0:
                return False
            if cls.MIN_HOST_HEIGHT <= 0:
                return False
            if cls.HEADER_HEIGHT <= 0:
                return False
            if cls.FOOTER_HEIGHT <= 0:
                return False

            # Validate SSH settings
            if cls.SSH_TIMEOUT_SECONDS <= 0:
                return False
            if cls.SSH_CONNECTION_RETRIES <= 0:
                return False

            # Validate output settings
            if cls.MAX_OUTPUT_LINES_PER_HOST <= 0:
                return False
            if cls.OUTPUT_BUFFER_OVERFLOW_MARGIN < 0:
                return False

            # Validate status mappings
            if not ColorManager.STATUS_COLORS or not ColorManager.STATUS_SYMBOLS:
                return False

            return True

        except Exception:
            return False

    @classmethod
    def get_setting(cls, name: str) -> Any:
        """
        Get a specific configuration setting by name.

        Args:
            name: Name of the setting to retrieve

        Returns:
            Value of the setting

        Raises:
            AttributeError: If the setting doesn't exist
        """
        if hasattr(cls, name):
            return getattr(cls, name)
        else:
            raise AttributeError(f"Configuration setting '{name}' not found")

    @classmethod
    def list_settings(cls) -> list:
        """
        Get a list of all configuration setting names.

        Returns:
            List of setting names
        """
        return [
            attr
            for attr in dir(cls)
            if not attr.startswith("_") and not callable(getattr(cls, attr))
        ]
