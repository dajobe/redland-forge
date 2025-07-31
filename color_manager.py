#!/usr/bin/env python3
"""
Color Manager - Centralized color management for Build TUI

This module provides a centralized interface for all color-related functionality,
including ANSI color codes, status colors, terminal color support detection,
and color formatting utilities.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional


class ColorManager:
    """Centralized color management for the Build TUI application."""

    # Global color mode setting
    _color_forced: Optional[bool] = None  # None = auto, True = force, False = disable

    # ANSI color code definitions - centralized for easy modification
    ANSI_COLORS = {
        "RESET": "\033[0m",
        "BLACK": "\033[30m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "MAGENTA": "\033[35m",
        "CYAN": "\033[36m",
        "WHITE": "\033[37m",
        "BRIGHT_RED": "\033[91m",
        "BRIGHT_GREEN": "\033[92m",
        "BRIGHT_YELLOW": "\033[93m",
        "BRIGHT_BLUE": "\033[94m",
        "BRIGHT_MAGENTA": "\033[95m",
        "BRIGHT_CYAN": "\033[96m",
        "BG_RED": "\033[41m",
        "BG_GREEN": "\033[42m",
        "BG_YELLOW": "\033[43m",
        "BG_BLUE": "\033[44m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
        "ITALIC": "\033[3m",
        "UNDERLINE": "\033[4m",
    }

    # Status color mappings
    STATUS_COLORS = {
        "IDLE": "DIM",
        "CONNECTING": "BRIGHT_CYAN",
        "PREPARING": "BRIGHT_MAGENTA",
        "BUILDING": "BRIGHT_YELLOW",
        "SUCCESS": "BRIGHT_GREEN",
        "FAILED": "BRIGHT_RED",
        "WARNING": "BRIGHT_YELLOW",
    }

    # Status symbols
    STATUS_SYMBOLS = {
        "IDLE": "⏳",
        "CONNECTING": "🔌",
        "PREPARING": "📦",
        "BUILDING": "🔨",
        "SUCCESS": "✓",
        "FAILED": "✗",
        "WARNING": "⚠",
    }

    # Default colors
    DEFAULT_BORDER_COLOR = "WHITE"

    @classmethod
    def set_color_mode(cls, mode: str) -> None:
        """
        Set color mode: 'auto', 'always', or 'never'.
        
        Args:
            mode: Color mode to set ('auto', 'always', 'never')
            
        Raises:
            ValueError: If mode is not one of the valid options
        """
        if mode == "auto":
            cls._color_forced = None
        elif mode == "always":
            cls._color_forced = True
        elif mode == "never":
            cls._color_forced = False
        else:
            raise ValueError(
                f"Invalid color mode: {mode}. Use 'auto', 'always', or 'never'"
            )

    @classmethod
    def supports_color(cls) -> bool:
        """
        Check if the terminal supports color output.
        
        Returns:
            True if colors are supported, False otherwise
        """
        # Check if color is explicitly forced or disabled
        if cls._color_forced is not None:
            return cls._color_forced

        # Check if we're in a terminal
        if not sys.stdout.isatty():
            return False

        # Check for common color-supporting terminals
        term = os.environ.get("TERM", "")
        if term in ("xterm", "xterm-256color", "screen", "screen-256color", "linux"):
            return True

        # Check for common platforms
        platform = sys.platform
        if platform in ("linux", "darwin"):  # Linux and macOS
            return True

        return False

    @classmethod
    def get_ansi_color(cls, color_name: str) -> str:
        """
        Get the ANSI color code for a color name.
        
        Args:
            color_name: Name of the color (e.g., "RED", "BRIGHT_GREEN", "BOLD")
            
        Returns:
            ANSI color code, or RESET if not found
        """
        return cls.ANSI_COLORS.get(color_name, cls.ANSI_COLORS["RESET"])

    @classmethod
    def get_status_color(cls, status: str) -> str:
        """
        Get the color name for a specific status.
        
        Args:
            status: Status name (e.g., "SUCCESS", "FAILED")
            
        Returns:
            Color name for the status, or DEFAULT_BORDER_COLOR if not found
        """
        return cls.STATUS_COLORS.get(status, cls.DEFAULT_BORDER_COLOR)

    @classmethod
    def get_status_ansi_color(cls, status: str) -> str:
        """
        Get the ANSI color code for a specific status.
        
        Args:
            status: Status name (e.g., "SUCCESS", "FAILED")
            
        Returns:
            ANSI color code for the status
        """
        color_name = cls.get_status_color(status)
        return cls.get_ansi_color(color_name)

    @classmethod
    def get_status_symbol(cls, status: str) -> str:
        """
        Get the symbol for a specific status.
        
        Args:
            status: Status name (e.g., "SUCCESS", "FAILED")
            
        Returns:
            Symbol for the status, or empty string if not found
        """
        return cls.STATUS_SYMBOLS.get(status, "")

    @classmethod
    def colorize(cls, text: str, color_name: str) -> str:
        """
        Add color to text using a color name.
        
        Args:
            text: Text to colorize
            color_name: Name of the color (e.g., "RED", "BRIGHT_GREEN")
            
        Returns:
            Colorized text with ANSI codes, or original text if colors not supported
        """
        if not cls.supports_color():
            return text
            
        color_code = cls.get_ansi_color(color_name)
        reset_code = cls.ANSI_COLORS["RESET"]
        return f"{color_code}{text}{reset_code}"

    @classmethod
    def get_color_settings(cls) -> Dict[str, Any]:
        """
        Get all color and formatting settings.
        
        Returns:
            Dictionary containing color and formatting settings
        """
        return {
            "DEFAULT_BORDER_COLOR": cls.DEFAULT_BORDER_COLOR,
            "ANSI_COLORS": cls.ANSI_COLORS.copy(),
            "STATUS_COLORS": cls.STATUS_COLORS.copy(),
            "STATUS_SYMBOLS": cls.STATUS_SYMBOLS.copy(),
        }

    @classmethod
    def add_custom_color(cls, name: str, ansi_code: str) -> None:
        """
        Add a custom color to the ANSI_COLORS dictionary.
        
        Args:
            name: Name of the custom color
            ansi_code: ANSI escape sequence for the color
        """
        cls.ANSI_COLORS[name] = ansi_code
        logging.debug(f"Added custom color: {name} = {repr(ansi_code)}")

    @classmethod
    def add_custom_status_color(cls, status: str, color_name: str) -> None:
        """
        Add a custom status color mapping.
        
        Args:
            status: Status name
            color_name: Color name to map to the status
        """
        cls.STATUS_COLORS[status] = color_name
        logging.debug(f"Added custom status color: {status} -> {color_name}")

    @classmethod
    def add_custom_status_symbol(cls, status: str, symbol: str) -> None:
        """
        Add a custom status symbol.
        
        Args:
            status: Status name
            symbol: Symbol to use for the status
        """
        cls.STATUS_SYMBOLS[status] = symbol
        logging.debug(f"Added custom status symbol: {status} -> {symbol}")

    @classmethod
    def get_available_colors(cls) -> list:
        """
        Get a list of all available color names.
        
        Returns:
            List of available color names
        """
        return list(cls.ANSI_COLORS.keys())

    @classmethod
    def get_available_statuses(cls) -> list:
        """
        Get a list of all available status names.
        
        Returns:
            List of available status names
        """
        return list(cls.STATUS_COLORS.keys())

    @classmethod
    def validate_color_name(cls, color_name: str) -> bool:
        """
        Validate if a color name exists.
        
        Args:
            color_name: Color name to validate
            
        Returns:
            True if color exists, False otherwise
        """
        return color_name in cls.ANSI_COLORS

    @classmethod
    def validate_status_name(cls, status: str) -> bool:
        """
        Validate if a status name exists.
        
        Args:
            status: Status name to validate
            
        Returns:
            True if status exists, False otherwise
        """
        return status in cls.STATUS_COLORS


# Convenience functions for backward compatibility
def set_color_mode(mode: str) -> None:
    """Set color mode: 'auto', 'always', or 'never'."""
    ColorManager.set_color_mode(mode)


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    return ColorManager.supports_color()


def colorize(text: str, color: str) -> str:
    """Add color to text if terminal supports it."""
    return ColorManager.colorize(text, color)


# Legacy Colors class for backward compatibility
class Colors:
    """Legacy Colors class for backward compatibility - now uses ColorManager."""
    
    @classmethod
    def _get_color(cls, color_name: str) -> str:
        """Get ANSI color code from ColorManager."""
        return ColorManager.get_ansi_color(color_name)
    
    # Reset all formatting
    @property
    def RESET(self) -> str:
        return self._get_color("RESET")

    # Text colors
    @property
    def BLACK(self) -> str:
        return self._get_color("BLACK")
    
    @property
    def RED(self) -> str:
        return self._get_color("RED")
    
    @property
    def GREEN(self) -> str:
        return self._get_color("GREEN")
    
    @property
    def YELLOW(self) -> str:
        return self._get_color("YELLOW")
    
    @property
    def BLUE(self) -> str:
        return self._get_color("BLUE")
    
    @property
    def MAGENTA(self) -> str:
        return self._get_color("MAGENTA")
    
    @property
    def CYAN(self) -> str:
        return self._get_color("CYAN")
    
    @property
    def WHITE(self) -> str:
        return self._get_color("WHITE")

    # Bright text colors
    @property
    def BRIGHT_RED(self) -> str:
        return self._get_color("BRIGHT_RED")
    
    @property
    def BRIGHT_GREEN(self) -> str:
        return self._get_color("BRIGHT_GREEN")
    
    @property
    def BRIGHT_YELLOW(self) -> str:
        return self._get_color("BRIGHT_YELLOW")
    
    @property
    def BRIGHT_BLUE(self) -> str:
        return self._get_color("BRIGHT_BLUE")
    
    @property
    def BRIGHT_MAGENTA(self) -> str:
        return self._get_color("BRIGHT_MAGENTA")
    
    @property
    def BRIGHT_CYAN(self) -> str:
        return self._get_color("BRIGHT_CYAN")

    # Background colors
    @property
    def BG_RED(self) -> str:
        return self._get_color("BG_RED")
    
    @property
    def BG_GREEN(self) -> str:
        return self._get_color("BG_GREEN")
    
    @property
    def BG_YELLOW(self) -> str:
        return self._get_color("BG_YELLOW")
    
    @property
    def BG_BLUE(self) -> str:
        return self._get_color("BG_BLUE")

    # Text formatting
    @property
    def BOLD(self) -> str:
        return self._get_color("BOLD")
    
    @property
    def DIM(self) -> str:
        return self._get_color("DIM")
    
    @property
    def ITALIC(self) -> str:
        return self._get_color("ITALIC")
    
    @property
    def UNDERLINE(self) -> str:
        return self._get_color("UNDERLINE") 