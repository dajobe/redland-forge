#!/usr/bin/python3
"""
Unit tests for OutputBuffer class.
"""

import unittest
from redland_forge.output_buffer import OutputBuffer


class TestOutputBuffer(unittest.TestCase):
    """Test cases for OutputBuffer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.buffer = OutputBuffer(max_lines=5)

    def test_initialization(self):
        """Test buffer initialization."""
        buffer = OutputBuffer(max_lines=10)
        self.assertEqual(buffer.max_lines, 10)
        self.assertEqual(len(buffer.lines), 0)
        self.assertEqual(buffer.total_lines_processed, 0)

    def test_add_line(self):
        """Test adding lines to buffer."""
        self.buffer.add_line("Line 1")
        self.assertEqual(len(self.buffer), 1)
        self.assertEqual(self.buffer.lines[0], "Line 1")
        self.assertEqual(self.buffer.total_lines_processed, 1)

        self.buffer.add_line("Line 2")
        self.assertEqual(len(self.buffer), 2)
        self.assertEqual(self.buffer.lines[1], "Line 2")
        self.assertEqual(self.buffer.total_lines_processed, 2)

    def test_max_lines_limit(self):
        """Test that buffer respects max_lines limit."""
        # Add more lines than max_lines
        for i in range(10):
            self.buffer.add_line(f"Line {i}")

        # Should only keep the most recent 5 lines
        self.assertEqual(len(self.buffer), 5)
        self.assertEqual(self.buffer.total_lines_processed, 10)

        # Should have the last 5 lines
        expected_lines = ["Line 5", "Line 6", "Line 7", "Line 8", "Line 9"]
        self.assertEqual(self.buffer.lines, expected_lines)

    def test_get_recent_lines(self):
        """Test getting recent lines from buffer."""
        # Add some lines
        for i in range(3):
            self.buffer.add_line(f"Line {i}")

        # Get recent lines
        recent = self.buffer.get_recent_lines(2)
        self.assertEqual(recent, ["Line 1", "Line 2"])

        # Get more lines than available
        recent = self.buffer.get_recent_lines(5)
        self.assertEqual(recent, ["Line 0", "Line 1", "Line 2"])

        # Get 0 lines - should return all lines when count is 0
        recent = self.buffer.get_recent_lines(0)
        self.assertEqual(recent, ["Line 0", "Line 1", "Line 2"])

    def test_get_all_lines(self):
        """Test getting all lines from buffer."""
        # Add some lines
        for i in range(3):
            self.buffer.add_line(f"Line {i}")

        all_lines = self.buffer.get_all_lines()
        self.assertEqual(all_lines, ["Line 0", "Line 1", "Line 2"])

        # Should return a copy, not the original list
        all_lines.append("Should not affect original")
        self.assertEqual(len(self.buffer), 3)
        self.assertEqual(self.buffer.lines, ["Line 0", "Line 1", "Line 2"])

    def test_clear(self):
        """Test clearing the buffer."""
        # Add some lines
        for i in range(3):
            self.buffer.add_line(f"Line {i}")

        self.assertEqual(len(self.buffer), 3)
        self.assertEqual(self.buffer.total_lines_processed, 3)

        # Clear the buffer
        self.buffer.clear()

        self.assertEqual(len(self.buffer), 0)
        self.assertEqual(self.buffer.total_lines_processed, 0)
        self.assertEqual(self.buffer.lines, [])

    def test_len_operator(self):
        """Test len() operator."""
        self.assertEqual(len(self.buffer), 0)

        self.buffer.add_line("Line 1")
        self.assertEqual(len(self.buffer), 1)

        self.buffer.add_line("Line 2")
        self.assertEqual(len(self.buffer), 2)

    def test_getitem_operator(self):
        """Test [] operator for getting lines by index."""
        # Add some lines
        for i in range(3):
            self.buffer.add_line(f"Line {i}")

        self.assertEqual(self.buffer[0], "Line 0")
        self.assertEqual(self.buffer[1], "Line 1")
        self.assertEqual(self.buffer[2], "Line 2")

        # Test negative indexing
        self.assertEqual(self.buffer[-1], "Line 2")
        self.assertEqual(self.buffer[-2], "Line 1")
        self.assertEqual(self.buffer[-3], "Line 0")

    def test_getitem_index_error(self):
        """Test that [] operator raises IndexError for invalid indices."""
        # Empty buffer
        with self.assertRaises(IndexError):
            _ = self.buffer[0]

        # Add one line
        self.buffer.add_line("Line 1")

        # Valid index
        self.assertEqual(self.buffer[0], "Line 1")

        # Invalid index
        with self.assertRaises(IndexError):
            _ = self.buffer[1]

        with self.assertRaises(IndexError):
            _ = self.buffer[-2]

    def test_get_total_lines_processed(self):
        """Test getting total lines processed."""
        self.assertEqual(self.buffer.get_total_lines_processed(), 0)

        self.buffer.add_line("Line 1")
        self.assertEqual(self.buffer.get_total_lines_processed(), 1)

        self.buffer.add_line("Line 2")
        self.assertEqual(self.buffer.get_total_lines_processed(), 2)

        # Even after clearing, total should remain
        self.buffer.clear()
        self.assertEqual(self.buffer.get_total_lines_processed(), 0)

    def test_is_full(self):
        """Test is_full() method."""
        # Buffer starts empty
        self.assertFalse(self.buffer.is_full())

        # Add lines up to max
        for i in range(5):
            self.buffer.add_line(f"Line {i}")
            if i < 4:
                self.assertFalse(self.buffer.is_full())
            else:
                self.assertTrue(self.buffer.is_full())

        # Add more lines (should still be full)
        self.buffer.add_line("Line 5")
        self.assertTrue(self.buffer.is_full())

    def test_edge_cases(self):
        """Test edge cases."""
        # Buffer with max_lines = 0
        buffer = OutputBuffer(max_lines=0)
        buffer.add_line("Line 1")
        self.assertEqual(len(buffer), 0)
        self.assertEqual(buffer.get_total_lines_processed(), 1)

        # Buffer with max_lines = 1
        buffer = OutputBuffer(max_lines=1)
        buffer.add_line("Line 1")
        buffer.add_line("Line 2")
        self.assertEqual(len(buffer), 1)
        self.assertEqual(buffer.lines[0], "Line 2")

        # Empty buffer operations
        self.assertEqual(self.buffer.get_recent_lines(5), [])
        self.assertEqual(self.buffer.get_all_lines(), [])
        self.assertFalse(self.buffer.is_full())

    def test_large_buffer(self):
        """Test buffer with large max_lines."""
        buffer = OutputBuffer(max_lines=1000)

        # Add many lines
        for i in range(1000):
            buffer.add_line(f"Line {i}")

        self.assertEqual(len(buffer), 1000)
        self.assertTrue(buffer.is_full())

        # Add one more line
        buffer.add_line("Line 1000")
        self.assertEqual(len(buffer), 1000)
        self.assertEqual(buffer.lines[0], "Line 1")  # First line should be dropped
        self.assertEqual(buffer.lines[-1], "Line 1000")  # Last line should be newest

    def test_string_types(self):
        """Test buffer with different string types."""
        # Empty string
        self.buffer.add_line("")
        self.assertEqual(self.buffer[0], "")

        # Unicode string
        self.buffer.add_line("Unicode: 🚀")
        self.assertEqual(self.buffer[1], "Unicode: 🚀")

        # Long string
        long_string = "x" * 1000
        self.buffer.add_line(long_string)
        self.assertEqual(self.buffer[2], long_string)


if __name__ == "__main__":
    unittest.main()
