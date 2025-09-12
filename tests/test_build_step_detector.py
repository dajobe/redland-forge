#!/usr/bin/python3
"""
Unit tests for BuildStep class and build step detection functions.
"""

import unittest
import re

from redland_forge.build_step_detector import (
    BuildStep,
    detect_build_step,
    get_step_by_name,
    get_step_priority,
    get_all_step_names,
    add_custom_step,
    remove_step,
    reset_to_default_steps,
    detect_step_completion,
    BUILD_STEPS,
)


class TestBuildStep(unittest.TestCase):
    """Test cases for BuildStep class."""

    def test_initialization(self):
        """Test BuildStep initialization."""
        step = BuildStep("test", ["pattern1", "pattern2"], priority=5)

        self.assertEqual(step.name, "test")
        self.assertEqual(step.priority, 5)
        self.assertEqual(len(step.patterns), 2)
        self.assertTrue(all(isinstance(p, re.Pattern) for p in step.patterns))

    def test_matches_single_pattern(self):
        """Test matching with single pattern."""
        step = BuildStep("test", [r"Building .* version"])

        self.assertTrue(step.matches("Building 1.0.0 version"))
        self.assertTrue(step.matches("BUILDING 2.1.3 VERSION"))
        self.assertFalse(step.matches("Building something else"))
        self.assertFalse(step.matches("Not building"))

    def test_matches_multiple_patterns(self):
        """Test matching with multiple patterns."""
        step = BuildStep("test", [r"Running configure", r"configure succeeded"])

        self.assertTrue(step.matches("Running configure"))
        self.assertTrue(step.matches("configure succeeded"))
        self.assertTrue(step.matches("CONFIGURE SUCCEEDED"))
        self.assertFalse(step.matches("configure failed"))
        self.assertFalse(step.matches("Running make"))

    def test_matches_case_insensitive(self):
        """Test that patterns are case insensitive."""
        step = BuildStep("test", [r"Building .* version"])

        self.assertTrue(step.matches("Building 1.0.0 version"))
        self.assertTrue(step.matches("BUILDING 1.0.0 VERSION"))
        self.assertTrue(step.matches("building 1.0.0 version"))

    def test_matches_complex_pattern(self):
        """Test matching with complex regex patterns."""
        step = BuildStep("test", [r"Running make(?!.*check)(?!.*install)"])

        self.assertTrue(step.matches("Running make"))
        self.assertTrue(step.matches("Running make all"))
        self.assertFalse(step.matches("Running make check"))
        self.assertFalse(step.matches("Running make install"))

    def test_get_pattern_count(self):
        """Test get_pattern_count method."""
        step = BuildStep("test", ["pattern1", "pattern2", "pattern3"])
        self.assertEqual(step.get_pattern_count(), 3)

        step = BuildStep("test", [])
        self.assertEqual(step.get_pattern_count(), 0)

    def test_add_pattern(self):
        """Test add_pattern method."""
        step = BuildStep("test", ["pattern1"])
        self.assertEqual(step.get_pattern_count(), 1)

        step.add_pattern("pattern2")
        self.assertEqual(step.get_pattern_count(), 2)
        self.assertTrue(step.matches("pattern2"))

    def test_remove_pattern(self):
        """Test remove_pattern method."""
        step = BuildStep("test", ["pattern1", "pattern2"])
        self.assertEqual(step.get_pattern_count(), 2)

        # Remove existing pattern
        self.assertTrue(step.remove_pattern("pattern1"))
        self.assertEqual(step.get_pattern_count(), 1)
        self.assertFalse(step.matches("pattern1"))
        self.assertTrue(step.matches("pattern2"))

        # Try to remove non-existent pattern
        self.assertFalse(step.remove_pattern("nonexistent"))
        self.assertEqual(step.get_pattern_count(), 1)

    def test_matches_empty_line(self):
        """Test matching with empty line."""
        step = BuildStep("test", [r"Building .* version"])
        self.assertFalse(step.matches(""))
        self.assertFalse(step.matches("   "))

    def test_matches_special_characters(self):
        """Test matching with special characters."""
        step = BuildStep("test", [r"✓ Build completed successfully"])
        self.assertTrue(step.matches("✓ Build completed successfully"))
        self.assertTrue(step.matches("✓ BUILD COMPLETED SUCCESSFULLY"))
        self.assertFalse(step.matches("Build completed successfully"))  # Missing ✓


class TestDetectBuildStep(unittest.TestCase):
    """Test cases for detect_build_step function."""

    def test_detect_starting_step(self):
        """Test detection of starting step."""
        result = detect_build_step("Building 1.0.0 version", "")
        self.assertEqual(result, "starting")

    def test_detect_extract_step(self):
        """Test detection of extract step."""
        result = detect_build_step("Extracting tarball", "")
        self.assertEqual(result, "extract")

    def test_detect_configure_step(self):
        """Test detection of configure step."""
        result = detect_build_step("Running configure", "")
        self.assertEqual(result, "configure")

        result = detect_build_step("configure succeeded", "")
        self.assertEqual(result, "configure")

    def test_detect_make_step(self):
        """Test detection of make step."""
        result = detect_build_step("Running make", "")
        self.assertEqual(result, "make")

        result = detect_build_step("make succeeded", "")
        self.assertEqual(result, "make")

    def test_detect_check_step(self):
        """Test detection of check step."""
        result = detect_build_step("Running make check", "")
        self.assertEqual(result, "check")

        result = detect_build_step("make check succeeded", "")
        self.assertEqual(result, "check")

    def test_detect_install_step(self):
        """Test detection of install step."""
        result = detect_build_step("Running make install", "")
        self.assertEqual(result, "install")

        result = detect_build_step("make install succeeded", "")
        self.assertEqual(result, "install")

    def test_detect_bindings_step(self):
        """Test detection of bindings step."""
        result = detect_build_step("Building Python bindings", "")
        self.assertEqual(result, "bindings")

    def test_detect_completed_step(self):
        """Test detection of completed step."""
        result = detect_build_step("Total time taken: 120 seconds", "")
        self.assertEqual(result, "completed")

        result = detect_build_step("✓ Build completed successfully", "")
        self.assertEqual(result, "completed")

    def test_no_match(self):
        """Test when no step matches."""
        result = detect_build_step("Some random output", "")
        self.assertIsNone(result)

    def test_priority_higher_step(self):
        """Test that higher priority step is detected."""
        result = detect_build_step("Running make", "starting")
        self.assertEqual(result, "make")  # make (4) > starting (1)

    def test_priority_lower_step(self):
        """Test that lower priority step is not detected."""
        result = detect_build_step("Building 1.0.0 version", "make")
        self.assertIsNone(result)  # starting (1) < make (4)

    def test_priority_same_step(self):
        """Test that same priority step is not detected."""
        result = detect_build_step("Running make", "make")
        self.assertIsNone(result)

    def test_priority_highest_match(self):
        """Test that highest priority matching step is selected."""
        # Create a step that matches both "make" and "check" patterns
        result = detect_build_step("Running make check", "starting")
        self.assertEqual(result, "check")  # check (5) > make (4)

    def test_strip_whitespace(self):
        """Test that whitespace is stripped from input."""
        result = detect_build_step("  Building 1.0.0 version  ", "")
        self.assertEqual(result, "starting")

    def test_empty_line(self):
        """Test with empty line."""
        result = detect_build_step("", "")
        self.assertIsNone(result)

        result = detect_build_step("   ", "")
        self.assertIsNone(result)


class TestStepCompletionDetection(unittest.TestCase):
    """Test cases for step completion detection."""

    def test_detect_step_completion_success(self):
        """Test detection of step completion."""
        # Test check step completion
        result = detect_step_completion("make check succeeded", "check")
        self.assertTrue(result)

        # Test install step completion
        result = detect_step_completion("make install succeeded", "install")
        self.assertTrue(result)

        # Test make step completion
        result = detect_step_completion("make succeeded", "make")
        self.assertTrue(result)

        # Test configure step completion
        result = detect_step_completion("configure succeeded", "configure")
        self.assertTrue(result)

    def test_detect_step_completion_no_match(self):
        """Test step completion detection when no match."""
        # Test with wrong step
        result = detect_step_completion("make check succeeded", "make")
        self.assertFalse(result)

        # Test with non-completion line
        result = detect_step_completion("some random output", "check")
        self.assertFalse(result)

        # Test with non-existent step
        result = detect_step_completion("make check succeeded", "nonexistent")
        self.assertFalse(result)

    def test_detect_step_completion_case_insensitive(self):
        """Test step completion detection is case insensitive."""
        result = detect_step_completion("MAKE CHECK SUCCEEDED", "check")
        self.assertTrue(result)

        result = detect_step_completion("Configure Succeeded", "configure")
        self.assertTrue(result)


class TestBuildStepUtilities(unittest.TestCase):
    """Test cases for build step utility functions."""

    def test_get_step_by_name(self):
        """Test get_step_by_name function."""
        step = get_step_by_name("starting")
        self.assertIsNotNone(step)
        self.assertEqual(step.name, "starting")
        self.assertEqual(step.priority, 1)

        step = get_step_by_name("nonexistent")
        self.assertIsNone(step)

    def test_get_step_priority(self):
        """Test get_step_priority function."""
        priority = get_step_priority("starting")
        self.assertEqual(priority, 1)

        priority = get_step_priority("make")
        self.assertEqual(priority, 4)

        priority = get_step_priority("nonexistent")
        self.assertEqual(priority, -1)

    def test_get_all_step_names(self):
        """Test get_all_step_names function."""
        names = get_all_step_names()

        # Should return all step names in priority order
        expected_names = [
            "starting",
            "extract",
            "configure",
            "make",
            "check",
            "install",
            "bindings",
            "completed",
        ]
        self.assertEqual(names, expected_names)

        # Should be sorted by priority
        priorities = [get_step_priority(name) for name in names]
        self.assertEqual(priorities, sorted(priorities))

    def test_add_custom_step(self):
        """Test add_custom_step function."""
        # Add a custom step
        step = add_custom_step("custom", [r"Custom pattern"], priority=10)

        self.assertEqual(step.name, "custom")
        self.assertEqual(step.priority, 10)

        # Verify it was added to BUILD_STEPS
        found_step = get_step_by_name("custom")
        self.assertIsNotNone(found_step)
        self.assertEqual(found_step.priority, 10)

        # Verify it can be detected
        result = detect_build_step("Custom pattern", "")
        self.assertEqual(result, "custom")

        # Clean up
        remove_step("custom")

    def test_add_custom_step_duplicate_name(self):
        """Test adding step with duplicate name."""
        with self.assertRaises(ValueError):
            add_custom_step("starting", [r"pattern"], priority=10)

    def test_remove_step(self):
        """Test remove_step function."""
        # Add a step to remove
        add_custom_step("temp", [r"temp pattern"], priority=10)

        # Verify it exists
        self.assertIsNotNone(get_step_by_name("temp"))

        # Remove it
        self.assertTrue(remove_step("temp"))

        # Verify it's gone
        self.assertIsNone(get_step_by_name("temp"))

        # Try to remove non-existent step
        self.assertFalse(remove_step("nonexistent"))

    def test_reset_to_default_steps(self):
        """Test reset_to_default_steps function."""
        # Add a custom step
        add_custom_step("custom", [r"pattern"], priority=10)
        self.assertIsNotNone(get_step_by_name("custom"))

        # Reset to defaults
        reset_to_default_steps()

        # Custom step should be gone
        self.assertIsNone(get_step_by_name("custom"))

        # Default steps should be present
        self.assertIsNotNone(get_step_by_name("starting"))
        self.assertIsNotNone(get_step_by_name("make"))
        self.assertIsNotNone(get_step_by_name("completed"))


class TestBuildStepsIntegration(unittest.TestCase):
    """Integration tests for build step detection."""

    def test_complete_build_sequence(self):
        """Test detection of a complete build sequence."""
        build_output = [
            "Building 1.0.0 version",
            "Extracting tarball",
            "Running configure",
            "configure succeeded",
            "Running make",
            "make succeeded",
            "Running make check",
            "make check succeeded",
            "Running make install",
            "make install succeeded",
            "Building Python bindings",
            "Total time taken: 120 seconds",
        ]

        current_step = ""
        detected_steps = []

        for line in build_output:
            new_step = detect_build_step(line, current_step)
            if new_step:
                current_step = new_step
                detected_steps.append(new_step)

        expected_steps = [
            "starting",
            "extract",
            "configure",
            "make",
            "check",
            "install",
            "bindings",
            "completed",
        ]
        self.assertEqual(detected_steps, expected_steps)

    def test_build_steps_priority_order(self):
        """Test that BUILD_STEPS are in priority order."""
        priorities = [step.priority for step in BUILD_STEPS]
        self.assertEqual(priorities, sorted(priorities))

    def test_build_steps_unique_names(self):
        """Test that all build steps have unique names."""
        names = [step.name for step in BUILD_STEPS]
        self.assertEqual(len(names), len(set(names)))

    def test_build_steps_valid_patterns(self):
        """Test that all build step patterns are valid regex."""
        for step in BUILD_STEPS:
            for pattern in step.patterns:
                # If we can access the pattern, it's valid
                self.assertIsInstance(pattern.pattern, str)


if __name__ == "__main__":
    unittest.main()
