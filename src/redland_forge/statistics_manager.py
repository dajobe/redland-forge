#!/usr/bin/python3
"""
Statistics Manager Module

A module for managing and calculating build statistics in the TUI.
"""

import logging
from typing import Dict, List, Any


class StatisticsManager:
    """Manages build statistics and progress tracking."""

    def __init__(self, all_hosts: List[str]):
        """
        Initialize the statistics manager.

        Args:
            all_hosts: List of all hosts being processed
        """
        self.all_hosts = all_hosts

    def calculate_statistics(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate build statistics for use in header and footer.

        Args:
            host_sections: Dictionary of host sections (visible hosts)
            ssh_results: Dictionary of SSH results from ParallelSSHManager

        Returns:
            Dictionary containing build statistics
        """
        visible_hosts = list(host_sections.keys())
        total_hosts = len(
            self.all_hosts
        )  # Total hosts provided (including non-visible)

        # Calculate statistics for ALL hosts being processed (not just visible ones)
        all_processed_hosts = list(ssh_results.keys())

        completed = sum(
            1
            for hostname, result in ssh_results.items()
            if result["status"] == "SUCCESS"
        )
        failed = sum(
            1
            for hostname, result in ssh_results.items()
            if result["status"] == "FAILED"
        )
        # Only count active hosts that are currently visible on screen
        active = sum(
            1
            for hostname in visible_hosts
            if hostname in ssh_results
            and ssh_results[hostname]["status"]
            in ["CONNECTING", "PREPARING", "BUILDING"]
        )

        # Debug logging for statistics
        logging.debug(f"Statistics calculation:")
        logging.debug(f"  Visible hosts: {visible_hosts}")
        logging.debug(f"  All results: {list(ssh_results.keys())}")
        for hostname in visible_hosts:
            if hostname in ssh_results:
                status = ssh_results[hostname]["status"]
                logging.debug(f"  {hostname}: status={status}")
            else:
                logging.debug(f"  {hostname}: no results")
        logging.debug(f"  Active count: {active}")

        total_completed = completed + failed
        # Calculate progress based on all hosts being processed
        overall_progress = total_completed / total_hosts * 100 if total_hosts else 0

        return {
            "active": active,
            "completed": completed,
            "failed": failed,
            "total_completed": total_completed,
            "overall_progress": overall_progress,
            "total_hosts": total_hosts,
            "visible_hosts": len(visible_hosts),
            "processed_hosts": len(all_processed_hosts),
        }

    def get_status_summary(self, stats: Dict[str, Any]) -> str:
        """
        Generate a status summary string.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Formatted status summary string
        """
        return f"Global Status: {stats['active']} active, {stats['completed']} completed, {stats['failed']} failed"

    def get_progress_summary(self, stats: Dict[str, Any]) -> str:
        """
        Generate a progress summary string.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Formatted progress summary string
        """
        return f"Visible Progress: {stats['overall_progress']:.1f}% ({stats['total_completed']}/{stats['total_hosts']})"

    def get_host_status_breakdown(
        self, ssh_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Get a breakdown of host statuses.

        Args:
            ssh_results: Dictionary of SSH results

        Returns:
            Dictionary mapping status to count
        """
        status_counts = {}
        for result in ssh_results.values():
            status = result.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    def get_visible_host_status_breakdown(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Get a breakdown of visible host statuses.

        Args:
            host_sections: Dictionary of host sections (visible hosts)
            ssh_results: Dictionary of SSH results

        Returns:
            Dictionary mapping status to count for visible hosts
        """
        visible_hosts = list(host_sections.keys())
        status_counts = {}

        for hostname in visible_hosts:
            if hostname in ssh_results:
                status = ssh_results[hostname].get("status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
            else:
                status_counts["UNKNOWN"] = status_counts.get("UNKNOWN", 0) + 1

        return status_counts

    def is_build_complete(self, stats: Dict[str, Any]) -> bool:
        """
        Check if the build is complete.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            True if build is complete, False otherwise
        """
        return stats["total_completed"] >= stats["total_hosts"]

    def get_completion_percentage(self, stats: Dict[str, Any]) -> float:
        """
        Get the completion percentage.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Completion percentage (0.0 to 100.0)
        """
        return stats["overall_progress"]

    def get_remaining_hosts(self, stats: Dict[str, Any]) -> int:
        """
        Get the number of remaining hosts.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Number of remaining hosts
        """
        return stats["total_hosts"] - stats["total_completed"]

    def get_success_rate(self, stats: Dict[str, Any]) -> float:
        """
        Get the success rate as a percentage.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Success rate percentage (0.0 to 100.0)
        """
        if stats["total_completed"] == 0:
            return 0.0
        return (stats["completed"] / stats["total_completed"]) * 100

    def get_failure_rate(self, stats: Dict[str, Any]) -> float:
        """
        Get the failure rate as a percentage.

        Args:
            stats: Statistics dictionary from calculate_statistics

        Returns:
            Failure rate percentage (0.0 to 100.0)
        """
        if stats["total_completed"] == 0:
            return 0.0
        return (stats["failed"] / stats["total_completed"]) * 100

    def get_detailed_statistics(
        self, host_sections: Dict[str, Any], ssh_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get detailed statistics including breakdowns and rates.

        Args:
            host_sections: Dictionary of host sections (visible hosts)
            ssh_results: Dictionary of SSH results

        Returns:
            Dictionary containing detailed statistics
        """
        basic_stats = self.calculate_statistics(host_sections, ssh_results)

        return {
            **basic_stats,
            "host_status_breakdown": self.get_host_status_breakdown(ssh_results),
            "visible_host_status_breakdown": self.get_visible_host_status_breakdown(
                host_sections, ssh_results
            ),
            "is_complete": self.is_build_complete(basic_stats),
            "remaining_hosts": self.get_remaining_hosts(basic_stats),
            "success_rate": self.get_success_rate(basic_stats),
            "failure_rate": self.get_failure_rate(basic_stats),
            "status_summary": self.get_status_summary(basic_stats),
            "progress_summary": self.get_progress_summary(basic_stats),
        }
