#!/usr/bin/python3
"""
Text Formatter Module

A utility module for text formatting operations with ANSI color code support.
"""

import re
import unicodedata
from typing import List


def visual_length(text: str) -> int:
    """
    Calculate the visual length of text, excluding ANSI escape codes and accounting for wide characters.

    Args:
        text: Text to measure (may contain ANSI color codes)

    Returns:
        Visual width of the text in terminal columns
    """
    # Remove ANSI escape codes for length calculation
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned_text = ansi_escape.sub("", text)

    # Calculate visual width accounting for wide characters
    width = 0
    for char in cleaned_text:
        # Check if character is wide (like emojis, CJK characters, etc.)
        if unicodedata.east_asian_width(char) in ("W", "F"):
            width += 2  # Wide characters take 2 terminal columns
        else:
            width += 1  # Normal characters take 1 terminal column

    return width


class TextFormatter:
    """Utility class for text formatting operations."""

    @staticmethod
    def truncate_text(text: str, max_width: int, suffix: str = "...") -> str:
        """
        Truncate text to fit within specified width, accounting for ANSI color codes.

        Args:
            text: Text to truncate (may contain ANSI color codes)
            max_width: Maximum visual width
            suffix: Suffix to add when truncating

        Returns:
            Truncated text with color codes preserved
        """
        if visual_length(text) <= max_width:
            return text

        # Calculate available space for text content
        suffix_width = visual_length(suffix)
        available_width = max_width - suffix_width

        if available_width <= 0:
            return suffix

        # Remove ANSI escape codes for length calculation
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        text_content = ansi_escape.sub("", text)

        # Find the actual text content (without color codes) to truncate
        if len(text_content) > available_width:
            truncated_text = text_content[:available_width] + suffix
            # Reconstruct with color codes
            color_match = re.match(r"(\x1b\[[0-9;]*m)?(.*)", text)
            if color_match:
                color_code = color_match.group(1) or ""
                return color_code + truncated_text
            return truncated_text

        return text

    @staticmethod
    def center_text(text: str, width: int) -> str:
        """
        Center text within specified width, accounting for ANSI color codes.

        Args:
            text: Text to center (may contain ANSI color codes)
            width: Total width to center within

        Returns:
            Centered text with padding
        """
        text_width = visual_length(text)
        if text_width >= width:
            return text

        left_padding = (width - text_width) // 2
        right_padding = width - text_width - left_padding

        return (" " * left_padding) + text + (" " * right_padding)

    @staticmethod
    def pad_text(text: str, width: int, align: str = "left") -> str:
        """
        Pad text to specified width with specified alignment.

        Args:
            text: Text to pad (may contain ANSI color codes)
            width: Target width
            align: Alignment ('left', 'center', 'right')

        Returns:
            Padded text
        """
        text_width = visual_length(text)
        if text_width >= width:
            return text

        if align == "center":
            return TextFormatter.center_text(text, width)
        elif align == "right":
            padding = width - text_width
            return (" " * padding) + text
        else:  # left alignment
            padding = width - text_width
            return text + (" " * padding)

    @staticmethod
    def build_bordered_line(
        content: str, box_width: int, left_border: str = "│ ", right_border: str = "│"
    ) -> str:
        """
        Build a line with borders that fits exactly within the specified width.

        Args:
            content: The content to display (can include ANSI color codes)
            box_width: The total width of the line including borders
            left_border: The left border string
            right_border: The right border string

        Returns:
            A string that is exactly box_width visual characters wide
        """
        # Calculate how much space we have for the content (excluding borders)
        content_width = (
            box_width - visual_length(left_border) - visual_length(right_border)
        )

        # Truncate content if it's too long to fit
        if visual_length(content) > content_width:
            content = TextFormatter.truncate_text(content, content_width)

        # Center the content
        content = TextFormatter.center_text(content, content_width)

        # Build the complete line
        return left_border + content + right_border

    @staticmethod
    def strip_ansi_codes(text: str) -> str:
        """
        Remove all ANSI escape codes from text.

        Args:
            text: Text that may contain ANSI color codes

        Returns:
            Text with all ANSI codes removed
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-9;]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    @staticmethod
    def extract_color_codes(text: str) -> tuple:
        """
        Extract color codes from text.

        Args:
            text: Text that may contain ANSI color codes

        Returns:
            Tuple of (color_codes, clean_text)
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-9;]*[ -/]*[@-~])")
        color_codes = ansi_escape.findall(text)
        clean_text = ansi_escape.sub("", text)
        return color_codes, clean_text
