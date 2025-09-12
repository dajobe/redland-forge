#!/usr/bin/python3
"""
Output Buffer Module

A utility module for managing output buffering with automatic line limiting.
"""

from typing import List


class OutputBuffer:
    """Efficient output buffer for managing build output lines."""

    def __init__(self, max_lines: int = 100):
        """
        Initialize output buffer.

        Args:
            max_lines: Maximum number of lines to keep in buffer
        """
        self.max_lines = max_lines
        self.lines = []
        self.total_lines_processed = 0

    def add_line(self, line: str) -> None:
        """
        Add a line to the buffer.

        Args:
            line: Line to add
        """
        self.total_lines_processed += 1

        # If max_lines is 0, don't store any lines
        if self.max_lines == 0:
            return

        self.lines.append(line)

        # Keep only the most recent lines
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines :]

    def get_recent_lines(self, count: int) -> List[str]:
        """
        Get the most recent lines from the buffer.

        Args:
            count: Number of lines to retrieve

        Returns:
            List of recent lines
        """
        if count <= 0:
            return self.lines.copy()
        return self.lines[-count:] if len(self.lines) > count else self.lines

    def get_all_lines(self) -> List[str]:
        """
        Get all lines in the buffer.

        Returns:
            List of all lines
        """
        return self.lines.copy()

    def clear(self) -> None:
        """Clear the buffer."""
        self.lines.clear()
        self.total_lines_processed = 0

    def __len__(self) -> int:
        """Return the number of lines in the buffer."""
        return len(self.lines)

    def __getitem__(self, index: int) -> str:
        """Get a line by index."""
        return self.lines[index]

    def get_total_lines_processed(self) -> int:
        """
        Get the total number of lines that have been processed.

        Returns:
            Total number of lines processed since creation
        """
        return self.total_lines_processed

    def is_full(self) -> bool:
        """
        Check if the buffer is at maximum capacity.

        Returns:
            True if buffer is at max_lines, False otherwise
        """
        return len(self.lines) >= self.max_lines
