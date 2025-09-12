#!/usr/bin/python3
"""
Build Summary Collector Module

Collects build results and generates formatted summaries for stdout output.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .text_formatter import format_duration


@dataclass
class BuildResult:
    """Represents the result of a build for a specific host."""

    host_name: str
    success: bool
    error_message: Optional[str] = None
    configure_time: Optional[float] = None
    make_time: Optional[float] = None
    total_time: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class BuildSummaryCollector:
    """Collects build results and timing data."""

    def __init__(self):
        """Initialize the build summary collector."""
        self.build_start_time = time.time()
        self.host_results: Dict[str, BuildResult] = {}
        self.host_start_times: Dict[str, float] = {}

        logging.debug("BuildSummaryCollector initialized")

    def start_build_tracking(self, host_name: str) -> None:
        """
        Start tracking build time for a specific host.

        Args:
            host_name: Name of the host to track
        """
        self.host_start_times[host_name] = time.time()
        logging.debug(f"Started tracking build for {host_name}")

    def stop_build_tracking(self, host_name: str) -> None:
        """
        Stop tracking build time for a specific host.

        Args:
            host_name: Name of the host to stop tracking
        """
        if host_name in self.host_start_times:
            del self.host_start_times[host_name]
            logging.debug(f"Stopped tracking build for {host_name}")

    def record_build_result(
        self,
        host_name: str,
        success: bool,
        error_message: Optional[str] = None,
        configure_time: Optional[float] = None,
        make_time: Optional[float] = None,
        total_time: Optional[float] = None,
    ) -> None:
        """
        Record the result of a build for a specific host.

        Args:
            host_name: Name of the host
            success: Whether the build was successful
            error_message: Error message if build failed
            configure_time: Time taken for configure step in seconds
            make_time: Time taken for make step in seconds
            total_time: Total build time in seconds
        """
        start_time = self.host_start_times.get(host_name)
        end_time = time.time()

        # Calculate total time if not provided
        if total_time is None and start_time is not None:
            total_time = end_time - start_time

        # Create build result
        result = BuildResult(
            host_name=host_name,
            success=success,
            error_message=error_message,
            configure_time=configure_time,
            make_time=make_time,
            total_time=total_time,
            start_time=start_time,
            end_time=end_time,
        )

        self.host_results[host_name] = result

        if total_time is not None:
            logging.debug(
                f"Recorded build result for {host_name}: success={success}, "
                f"total_time={total_time:.2f}s"
            )
        else:
            logging.debug(
                f"Recorded build result for {host_name}: success={success}, "
                f"total_time=None"
            )

    def get_build_result(self, host_name: str) -> Optional[BuildResult]:
        """
        Get the build result for a specific host.

        Args:
            host_name: Name of the host

        Returns:
            BuildResult if available, None otherwise
        """
        return self.host_results.get(host_name)

    def get_all_results(self) -> Dict[str, BuildResult]:
        """
        Get all build results.

        Returns:
            Dictionary of all build results by host name
        """
        return self.host_results.copy()

    def get_successful_builds(self) -> List[BuildResult]:
        """
        Get all successful builds.

        Returns:
            List of successful build results
        """
        return [result for result in self.host_results.values() if result.success]

    def get_failed_builds(self) -> List[BuildResult]:
        """
        Get all failed builds.

        Returns:
            List of failed build results
        """
        return [result for result in self.host_results.values() if not result.success]

    def get_total_build_time(self) -> float:
        """
        Get the total time from first build start to now.

        Returns:
            Total time in seconds
        """
        return time.time() - self.build_start_time

    def _format_duration(self, seconds: Optional[float]) -> str:
        """
        Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds (can be None)

        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "unknown"

        return format_duration(seconds)

    def generate_summary(self) -> str:
        """
        Generate formatted summary for stdout output.

        Returns:
            Formatted summary string
        """
        total_time = self.get_total_build_time()
        all_results = list(self.host_results.values())

        if not all_results:
            summary = []
            summary.append("=" * 60)
            summary.append("BUILD SUMMARY")
            summary.append("=" * 60)
            summary.append(f"Total time: {self._format_duration(total_time)}")
            summary.append("\nNo builds completed.\n")
            summary.append("=" * 60)
            return "\n".join(summary)

        # Determine column widths
        host_col_width = max([len(r.host_name) for r in all_results] + [len("Host")])
        status_col_width = max([len("SUCCESS"), len("FAILED")])
        time_col_width = max(
            [len(self._format_duration(r.total_time)) for r in all_results]
            + [len("Time Taken")]
        )

        # Add padding
        host_col_width += 2
        status_col_width += 2
        time_col_width += 2

        total_width = host_col_width + status_col_width + time_col_width + 3

        summary = []

        # Header
        summary.append("=" * total_width)
        summary.append("BUILD SUMMARY".center(total_width))
        summary.append("=" * total_width)
        summary.append(
            f"Total time: {self._format_duration(total_time)}".center(total_width)
        )
        summary.append("")

        # Table Header
        header = (
            f"│{'Host'.center(host_col_width)}│"
            f"{'Status'.center(status_col_width)}│"
            f"{'Time Taken'.center(time_col_width)}│"
        )
        summary.append(
            "┌"
            + "─" * host_col_width
            + "┬"
            + "─" * status_col_width
            + "┬"
            + "─" * time_col_width
            + "┐"
        )
        summary.append(header)
        summary.append(
            "├"
            + "─" * host_col_width
            + "┼"
            + "─" * status_col_width
            + "┼"
            + "─" * time_col_width
            + "┤"
        )

        # Table Rows
        for result in sorted(all_results, key=lambda r: r.host_name):
            status = "SUCCESS" if result.success else "FAILED"
            time_str = self._format_duration(result.total_time)

            row = (
                f"│ {result.host_name.ljust(host_col_width - 1)}│"
                f" {status.ljust(status_col_width - 1)}│"
                f" {time_str.rjust(time_col_width - 1)}│"
            )
            summary.append(row)

        # Footer
        summary.append(
            "└"
            + "─" * host_col_width
            + "┴"
            + "─" * status_col_width
            + "┴"
            + "─" * time_col_width
            + "┘"
        )
        summary.append("")

        # Overall stats
        successful = self.get_successful_builds()
        total_builds = len(all_results)
        success_rate = len(successful) / total_builds * 100 if total_builds > 0 else 0
        summary.append(
            f"Overall: {len(successful)}/{total_builds} builds successful ({success_rate:.1f}%)"
        )
        summary.append("=" * total_width)

        return "\n".join(summary)

    def print_summary(self) -> None:
        """Print the build summary to stdout."""
        summary = self.generate_summary()
        print(summary)
        logging.info("Build summary printed to stdout")

    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get a statistics summary for internal use.

        Returns:
            Dictionary containing summary statistics
        """
        successful = self.get_successful_builds()
        failed = self.get_failed_builds()
        total_builds = len(self.host_results)

        return {
            "total_builds": total_builds,
            "successful_builds": len(successful),
            "failed_builds": len(failed),
            "success_rate": (
                len(successful) / total_builds * 100 if total_builds > 0 else 0
            ),
            "total_time": self.get_total_build_time(),
            "hosts": list(self.host_results.keys()),
        }
