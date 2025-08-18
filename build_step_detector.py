#!/usr/bin/python3
"""
Build Step Detector Module

A utility module for detecting and managing build steps from output lines.
"""

import re
from typing import List, Optional


class BuildStep:
    """Represents a build step with its detection patterns."""

    def __init__(self, name: str, patterns: List[str], priority: int = 0):
        """
        Initialize a build step.

        Args:
            name: Name of the build step
            patterns: List of regex patterns to match this step
            priority: Priority level (higher = more important)
        """
        self.name = name
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        self.priority = priority

    def matches(self, line: str) -> bool:
        """
        Check if the line matches any of this step's patterns.

        Args:
            line: Output line to check

        Returns:
            True if line matches any pattern, False otherwise
        """
        return any(pattern.search(line) for pattern in self.patterns)

    def get_pattern_count(self) -> int:
        """
        Get the number of patterns for this step.

        Returns:
            Number of patterns
        """
        return len(self.patterns)

    def add_pattern(self, pattern: str) -> None:
        """
        Add a new pattern to this step.

        Args:
            pattern: Regex pattern to add
        """
        self.patterns.append(re.compile(pattern, re.IGNORECASE))

    def remove_pattern(self, pattern: str) -> bool:
        """
        Remove a pattern from this step.

        Args:
            pattern: Regex pattern to remove

        Returns:
            True if pattern was found and removed, False otherwise
        """
        for i, compiled_pattern in enumerate(self.patterns):
            if compiled_pattern.pattern == pattern:
                del self.patterns[i]
                return True
        return False


# Define build steps in order of execution
BUILD_STEPS = [
    BuildStep("starting", [r"Building .* version"], priority=1),
    BuildStep("extract", [r"Extracting tarball"], priority=2),
    BuildStep("configure", [r"Running configure", r"configure succeeded"], priority=3),
    BuildStep(
        "make",
        [
            r"Running make(?!.*check)(?!.*install)",
            r"make succeeded(?!.*check)(?!.*install)",
        ],
        priority=4,
    ),
    BuildStep("check", [r"Running make.*check", r"make check succeeded"], priority=5),
    BuildStep(
        "install", [r"Running make install", r"make install succeeded"], priority=6
    ),
    BuildStep("bindings", [r"Building .* bindings"], priority=7),
    BuildStep(
        "completed",
        [r"Total time taken", r"✓ Build completed successfully"],
        priority=8,
    ),
]


def detect_build_step(line: str, current_step: str) -> Optional[str]:
    """
    Detect the build step from a line of output.

    Args:
        line: The output line to analyze
        current_step: The current step name

    Returns:
        The new step name if detected, None if no change
    """
    line = line.strip()

    # Find the highest priority step that matches
    best_match = None
    best_priority = -1

    for step in BUILD_STEPS:
        if step.matches(line):
            # Only update if this step has higher priority than current
            current_priority = next(
                (s.priority for s in BUILD_STEPS if s.name == current_step), -1
            )
            if step.priority > current_priority:
                if step.priority > best_priority:
                    best_match = step.name
                    best_priority = step.priority

    return best_match


def detect_step_completion(line: str, current_step: str) -> bool:
    """
    Detect if the current step has completed based on the output line.

    Args:
        line: The output line to analyze
        current_step: The current step name

    Returns:
        True if the current step has completed, False otherwise
    """
    line = line.strip()
    
    # Get the current step object
    current_step_obj = get_step_by_name(current_step)
    if not current_step_obj:
        return False
    
    # Check if any of the current step's patterns match this line
    # and if the line contains completion indicators
    if current_step_obj.matches(line):
        # Look for completion indicators in the line
        completion_indicators = ["succeeded", "completed", "finished", "done"]
        return any(indicator in line.lower() for indicator in completion_indicators)
    
    # Special handling for extract step completion
    if current_step == "extract":
        # Extract step completes when we see configure-related output
        if "Running configure" in line or "configure succeeded" in line:
            return True
    
    return False


def get_step_by_name(name: str) -> Optional[BuildStep]:
    """
    Get a build step by name.

    Args:
        name: Name of the step to find

    Returns:
        BuildStep object if found, None otherwise
    """
    for step in BUILD_STEPS:
        if step.name == name:
            return step
    return None


def get_step_priority(name: str) -> int:
    """
    Get the priority of a build step by name.

    Args:
        name: Name of the step

    Returns:
        Priority value, or -1 if step not found
    """
    step = get_step_by_name(name)
    return step.priority if step else -1


def get_all_step_names() -> List[str]:
    """
    Get all build step names in priority order.

    Returns:
        List of step names sorted by priority
    """
    return [step.name for step in sorted(BUILD_STEPS, key=lambda s: s.priority)]


def add_custom_step(name: str, patterns: List[str], priority: int) -> BuildStep:
    """
    Add a custom build step.

    Args:
        name: Name of the new step
        patterns: List of regex patterns
        priority: Priority level

    Returns:
        The newly created BuildStep

    Raises:
        ValueError: If step with same name already exists
    """
    if get_step_by_name(name):
        raise ValueError(f"Build step '{name}' already exists")

    step = BuildStep(name, patterns, priority)
    BUILD_STEPS.append(step)
    # Re-sort by priority
    BUILD_STEPS.sort(key=lambda s: s.priority)
    return step


def remove_step(name: str) -> bool:
    """
    Remove a build step by name.

    Args:
        name: Name of the step to remove

    Returns:
        True if step was found and removed, False otherwise
    """
    for i, step in enumerate(BUILD_STEPS):
        if step.name == name:
            del BUILD_STEPS[i]
            return True
    return False


def reset_to_default_steps() -> None:
    """Reset BUILD_STEPS to the default configuration."""
    global BUILD_STEPS
    BUILD_STEPS = [
        BuildStep("starting", [r"Building .* version"], priority=1),
        BuildStep("extract", [r"Extracting tarball"], priority=2),
        BuildStep(
            "configure", [r"Running configure", r"configure succeeded"], priority=3
        ),
        BuildStep(
            "make",
            [
                r"Running make(?!.*check)(?!.*install)",
                r"make succeeded(?!.*check)(?!.*install)",
            ],
            priority=4,
        ),
        BuildStep(
            "check", [r"Running make.*check", r"make check succeeded"], priority=5
        ),
        BuildStep(
            "install", [r"Running make install", r"make install succeeded"], priority=6
        ),
        BuildStep("bindings", [r"Building .* bindings"], priority=7),
        BuildStep(
            "completed",
            [r"Total time taken", r"✓ Build completed successfully"],
            priority=8,
        ),
    ]
