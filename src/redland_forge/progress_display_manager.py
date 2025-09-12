#!/usr/bin/python3
"""
Progress Display Manager for the application.

Manages progress display for ongoing builds using historical timing data.
"""

import logging
import time
from typing import Dict, Optional

from .text_formatter import format_duration


class ProgressDisplayManager:
    """Manages progress display for ongoing builds"""

    def __init__(self, timing_cache, cache_key_func=None):
        """
        Initialize the progress display manager.

        Args:
            timing_cache: BuildTimingCache instance for timing data
            cache_key_func: Optional function to get cache key from host name
        """
        self.timing_cache = timing_cache
        self.cache_key_func = cache_key_func or (lambda host: host)
        self.build_start_times = {}  # host_name -> start_time
        self.build_steps = {}  # host_name -> current_step
        logging.debug("ProgressDisplayManager initialized")

    def start_build_tracking(self, host_name: str) -> None:
        """
        Start tracking build time for a host.

        Args:
            host_name: Name of the host to track
        """
        self.build_start_times[host_name] = time.time()
        self.build_steps[host_name] = "extract"
        logging.debug(f"Started build tracking for {host_name}")

    def update_build_step(self, host_name: str, step: str) -> None:
        """
        Update the current build step for a host.

        Args:
            host_name: Name of the host
            step: Current build step (extract, configure, make, check, install)
        """
        if host_name in self.build_steps:
            self.build_steps[host_name] = step
            logging.debug(f"Updated build step for {host_name}: {step}")

    def get_progress_display(self, host_name: str) -> Optional[str]:
        """
        Get progress display string for a host.

        Args:
            host_name: Name of the host

        Returns:
            Progress display string or None if no progress available
        """
        if host_name not in self.build_start_times:
            return None

        current_step = self.build_steps.get(host_name, "extract")
        elapsed_time = time.time() - self.build_start_times[host_name]

        # Get progress estimate from timing cache using cache key
        cache_key = self.cache_key_func(host_name)
        progress = self.timing_cache.get_progress_estimate(
            cache_key, current_step, elapsed_time
        )

        if progress:
            return f"Progress: {progress}"

        return None

    def get_time_estimate(self, host_name: str) -> Optional[str]:
        """
        Get time estimate for remaining build time.

        Args:
            host_name: Name of the host

        Returns:
            Time estimate string or None if no estimate available
        """
        if host_name not in self.build_start_times:
            return None

        current_step = self.build_steps.get(host_name, "extract")
        elapsed_time = time.time() - self.build_start_times[host_name]

        # Get host statistics for time estimates using cache key
        cache_key = self.cache_key_func(host_name)
        stats = self.timing_cache.get_host_statistics(cache_key)
        if not stats:
            return None

        avg_times = stats["average_times"]

        # Calculate remaining time based on current step
        if current_step == "extract":
            # Extract is usually quick, estimate 5 seconds
            remaining = 5.0
        elif current_step == "configure":
            # For configure step: remaining = make + make_check + remaining configure time
            configure_avg = avg_times.get("configure", 0)
            remaining = avg_times.get("make", 0) + avg_times.get("make_check", 0)
            if elapsed_time < configure_avg:
                remaining += configure_avg - elapsed_time
        elif current_step == "make":
            # For make step: remaining = make_check + remaining make time
            make_avg = avg_times.get("make", 0)
            remaining = avg_times.get("make_check", 0)
            if elapsed_time < make_avg:
                remaining += make_avg - elapsed_time
            # If we're past the average make time, just return make_check time
        elif current_step == "check":
            # For check step: remaining = total build time - elapsed time so far
            total_avg = avg_times.get("total", 0)
            if total_avg > 0:
                remaining = max(0, total_avg - elapsed_time)
            else:
                # Fallback: estimate remaining check time
                check_avg = avg_times.get("make_check", 0)
                remaining = max(0, check_avg - elapsed_time)
        elif current_step == "install":
            # For install step: remaining = total build time - elapsed time so far
            total_avg = avg_times.get("total", 0)
            if total_avg > 0:
                remaining = max(0, total_avg - elapsed_time)
            else:
                # Fallback: estimate remaining install time
                install_avg = avg_times.get("install", 0)
                remaining = max(0, install_avg - elapsed_time)
        else:
            remaining = 0

        if remaining > 0:
            return f"ETA: {format_duration(remaining)}"

        return None

    def get_detailed_progress(self, host_name: str) -> Optional[str]:
        """
        Get detailed progress information including step and estimates.

        Args:
            host_name: Name of the host

        Returns:
            Detailed progress string or None if no progress available
        """
        if host_name not in self.build_start_times:
            return None

        current_step = self.build_steps.get(host_name, "extract")
        elapsed_time = time.time() - self.build_start_times[host_name]

        # Get progress percentage using cache key
        cache_key = self.cache_key_func(host_name)
        progress = self.timing_cache.get_progress_estimate(
            cache_key, current_step, elapsed_time
        )

        # Get time estimate
        time_est = self.get_time_estimate(host_name)

        # Build detailed progress string
        parts = [f"Step: {current_step}"]

        if progress:
            parts.append(f"Progress: {progress}")

        if time_est:
            parts.append(time_est)

        if elapsed_time > 0:
            parts.append(f"Elapsed: {format_duration(elapsed_time)}")

        return " | ".join(parts)

    def complete_build_tracking(self, host_name: str) -> None:
        """
        Complete tracking for a host when build finishes.

        Args:
            host_name: Name of the host
        """
        if host_name in self.build_start_times:
            del self.build_start_times[host_name]
            logging.debug(f"Completed build tracking for {host_name}")

        if host_name in self.build_steps:
            del self.build_steps[host_name]

    def get_active_builds(self) -> Dict[str, Dict[str, any]]:
        """
        Get information about all actively tracked builds.

        Returns:
            Dictionary mapping host names to build information
        """
        active_builds = {}

        for host_name in self.build_start_times:
            if host_name in self.build_start_times:
                elapsed_time = time.time() - self.build_start_times[host_name]
                current_step = self.build_steps.get(host_name, "extract")

                active_builds[host_name] = {
                    "step": current_step,
                    "elapsed_time": elapsed_time,
                    "progress": self.get_progress_display(host_name),
                    "time_estimate": self.get_time_estimate(host_name),
                    "detailed_progress": self.get_detailed_progress(host_name),
                }

        return active_builds

    def get_host_progress_info(self, host_name: str) -> Dict[str, any]:
        """
        Get progress information for a specific host.

        Args:
            host_name: Name of the host

        Returns:
            Dictionary with progress information for the host
        """
        if host_name not in self.build_start_times:
            return {}

        elapsed_time = time.time() - self.build_start_times[host_name]
        current_step = self.build_steps.get(host_name, "extract")

        return {
            "step": current_step,
            "elapsed_time": elapsed_time,
            "progress": self.get_progress_display(host_name),
            "time_estimate": self.get_time_estimate(host_name),
            "detailed_progress": self.get_detailed_progress(host_name),
        }

    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        self.build_start_times.clear()
        self.build_steps.clear()
        logging.debug("ProgressDisplayManager cleanup completed")
