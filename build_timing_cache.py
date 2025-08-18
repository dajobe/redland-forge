"""
Build Timing Cache System

This module provides persistent storage and retrieval of build timing data
to enable progress estimates for ongoing builds.
"""

import json
import os
import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class BuildTimingRecord:
    """Individual build timing record with remote host timing data"""
    timestamp: float
    configure_time: float
    make_time: float
    make_check_time: float
    total_time: float
    success: bool


class BuildTimingCache:
    """Manages persistent build timing data for progress estimates"""
    
    def __init__(self, cache_file_path: str = None, retention_days: int = 1):
        """
        Initialize the build timing cache.
        
        Args:
            cache_file_path: Path to cache file relative to ~ (default: .config/build-tui/timing-cache.json)
            retention_days: Number of days to retain timing data (default: 1)
        """
        # Set default path if none provided
        if cache_file_path is None:
            cache_file_path = os.path.expanduser("~/.config/build-tui/timing-cache.json")
        # If it's a relative path, make it relative to home directory
        elif not os.path.isabs(cache_file_path):
            cache_file_path = os.path.expanduser(f"~/{cache_file_path}")
        self.cache_file_path = cache_file_path
        self.retention_days = retention_days
        self.cache_data = self._load_cache()
        self._cleanup_old_data()
        
        logging.debug(f"BuildTimingCache initialized: {self.cache_file_path}, "
                     f"retention: {retention_days} days")
    
    def _load_cache(self) -> Dict[str, Any]:
        """
        Load cache from file, create if doesn't exist.
        
        Returns:
            Cache data dictionary with default structure if file doesn't exist
        """
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r') as f:
                    data = json.load(f)
                    # Validate version and structure
                    if data.get('version') == '1.0':
                        logging.debug(f"Loaded existing cache from {self.cache_file_path}")
                        return data
                    else:
                        logging.warning(f"Cache version mismatch, creating new cache")
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load cache: {e}")
        
        # Return default structure
        default_cache = {
            "version": "1.0",
            "cache_retention_days": self.retention_days,
            "hosts": {}
        }
        logging.debug("Created new default cache structure")
        return default_cache
    
    def _save_cache(self) -> None:
        """Save cache to file with error handling."""
        try:
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            with open(self.cache_file_path, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
            logging.debug(f"Cache saved to {self.cache_file_path}")
        except IOError as e:
            logging.error(f"Failed to save cache: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Remove data older than retention period."""
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        removed_hosts = []
        
        for host_name in list(self.cache_data['hosts'].keys()):
            host_data = self.cache_data['hosts'][host_name]
            
            # Check if this is a demo/test host (very short TTL)
            if self._is_demo_host(host_name):
                from config import Config
                demo_hours = getattr(Config, 'TIMING_CACHE_DEMO_RETENTION_HOURS', 1)
                demo_cutoff = time.time() - (demo_hours * 60 * 60)  # Configurable TTL for demo hosts
                if host_data['last_updated'] < demo_cutoff:
                    del self.cache_data['hosts'][host_name]
                    removed_hosts.append(host_name)
                    logging.debug(f"Removed demo host {host_name} (last updated: {host_data['last_updated']}, demo cutoff: {demo_cutoff})")
            # Regular hosts use normal retention
            elif host_data['last_updated'] < cutoff_time:
                del self.cache_data['hosts'][host_name]
                removed_hosts.append(host_name)
                logging.debug(f"Removed host {host_name} (last updated: {host_data['last_updated']}, cutoff: {cutoff_time})")
        
        if removed_hosts:
            logging.info(f"Cleaned up old timing data for hosts: {removed_hosts}")
            self._save_cache()
    
    def _is_demo_host(self, host_name: str) -> bool:
        """
        Check if a host name indicates it's a demo/test host.
        
        Args:
            host_name: Name of the host to check
            
        Returns:
            True if this appears to be a demo/test host
        """
        demo_indicators = [
            'demo', 'test', 'example', 'sample', 'temp', 'tmp',
            'localhost', '127.0.0.1', '::1', 'dummy', 'fake'
        ]
        
        host_lower = host_name.lower()
        return any(indicator in host_lower for indicator in demo_indicators)
    
    def record_build_timing(self, host_name: str, configure_time: float, 
                          make_time: float, make_check_time: float, total_time: float, success: bool) -> None:
        """
        Record timing data for a completed build.
        
        Args:
            host_name: Name of the host
            configure_time: Time taken for configure step in seconds (from remote host)
            make_time: Time taken for make step in seconds (from remote host)
            make_check_time: Time taken for make check step in seconds (from remote host)
            total_time: Total build time in seconds (from remote host)
            success: Whether the build was successful
        """
        if host_name not in self.cache_data['hosts']:
            self.cache_data['hosts'][host_name] = {
                "last_updated": time.time(),
                "total_builds": 0,
                "average_times": {"configure": 0, "make": 0, "make_check": 0, "total": 0},
                "recent_builds": []
            }
        
        host_data = self.cache_data['hosts'][host_name]
        host_data['last_updated'] = time.time()
        host_data['total_builds'] += 1
        
        # Update averages
        current_avg = host_data['average_times']
        total_builds = host_data['total_builds']
        
        current_avg['configure'] = (
            (current_avg['configure'] * (total_builds - 1) + configure_time) / total_builds
        )
        current_avg['make'] = (
            (current_avg['make'] * (total_builds - 1) + make_time) / total_builds
        )
        current_avg['make_check'] = (
            (current_avg['make_check'] * (total_builds - 1) + make_check_time) / total_builds
        )
        current_avg['total'] = (
            (current_avg['total'] * (total_builds - 1) + total_time) / total_builds
        )
        
        # Add to recent builds (keep last 10)
        recent_build = BuildTimingRecord(
            timestamp=time.time(),
            configure_time=configure_time,
            make_time=make_time,
            make_check_time=make_check_time,
            total_time=total_time,
            success=success
        )
        
        host_data['recent_builds'].append(asdict(recent_build))
        if len(host_data['recent_builds']) > 10:
            host_data['recent_builds'] = host_data['recent_builds'][-10:]
        
        logging.debug(f"Recorded timing for {host_name}: configure={configure_time:.1f}s, "
                     f"make={make_time:.1f}s, make_check={make_check_time:.1f}s, "
                     f"total={total_time:.1f}s, success={success}")
        
        self._save_cache()
    
    def get_progress_estimate(self, host_name: str, current_step: str, 
                            elapsed_time: float) -> Optional[str]:
        """
        Get progress estimate for ongoing build.
        
        Args:
            host_name: Name of the host
            current_step: Current build step ('extract', 'configure', 'make', 'check', 'install', 'completed')
            elapsed_time: Time elapsed since build start in seconds
            
        Returns:
            Progress percentage string (e.g., "45.2%") or None if no data available
        """
        if host_name not in self.cache_data['hosts']:
            return None
        
        host_data = self.cache_data['hosts'][host_name]
        avg_times = host_data['average_times']
        
        if current_step == "extract":
            # Extract step: progress based on typical extract time (usually 2-10 seconds)
            # Use a reasonable estimate that accounts for network/tar extraction time
            extract_time = 8.0  # More realistic estimate
            progress = min(100, (elapsed_time / extract_time) * 100)
            return f"{progress:.1f}%"
        elif current_step == "configure":
            if avg_times['configure'] > 0:
                progress = min(100, (elapsed_time / avg_times['configure']) * 100)
                return f"{progress:.1f}%"
        elif current_step == "make":
            if avg_times['total'] > 0:
                # Include configure time in total estimate
                total_elapsed = elapsed_time + avg_times['configure']
                progress = min(100, (total_elapsed / avg_times['total']) * 100)
                return f"{progress:.1f}%"
        elif current_step == "check":
            if avg_times['total'] > 0:
                # Include configure and make time in total estimate
                total_elapsed = elapsed_time + avg_times['configure'] + avg_times['make']
                progress = min(100, (total_elapsed / avg_times['total']) * 100)
                return f"{progress:.1f}%"
        elif current_step == "install":
            if avg_times['total'] > 0:
                # Include configure, make, and check time in total estimate
                total_elapsed = elapsed_time + avg_times['configure'] + avg_times['make'] + avg_times['make_check']
                progress = min(100, (total_elapsed / avg_times['total']) * 100)
                return f"{progress:.1f}%"
        elif current_step == "completed":
            return "100.0%"
        
        return None
    
    def get_host_statistics(self, host_name: str) -> Optional[Dict[str, Any]]:
        """
        Get timing statistics for a specific host.
        
        Args:
            host_name: Name of the host
            
        Returns:
            Dictionary with host statistics or None if host not found
        """
        if host_name not in self.cache_data['hosts']:
            return None
        
        host_data = self.cache_data['hosts'][host_name]
        return {
            "total_builds": host_data['total_builds'],
            "last_updated": host_data['last_updated'],
            "average_times": host_data['average_times'].copy(),
            "recent_builds": host_data['recent_builds'][-5:]  # Last 5 builds
        }
    
    def get_all_hosts(self) -> list:
        """
        Get list of all hosts with timing data.
        
        Returns:
            List of host names
        """
        return list(self.cache_data['hosts'].keys())
    
    def clear_host_data(self, host_name: str) -> bool:
        """
        Clear all timing data for a specific host.
        
        Args:
            host_name: Name of the host
            
        Returns:
            True if host data was cleared, False if host not found
        """
        if host_name in self.cache_data['hosts']:
            del self.cache_data['hosts'][host_name]
            logging.info(f"Cleared timing data for host: {host_name}")
            self._save_cache()
            return True
        return False
    
    def clear_all_data(self) -> None:
        """Clear all timing data from cache."""
        self.cache_data['hosts'] = {}
        logging.info("Cleared all timing data from cache")
        self._save_cache()
    
    def clear_demo_hosts(self) -> None:
        """Clear all demo/test host data from cache."""
        demo_hosts = []
        for host_name in list(self.cache_data['hosts'].keys()):
            if self._is_demo_host(host_name):
                demo_hosts.append(host_name)
                del self.cache_data['hosts'][host_name]
        
        if demo_hosts:
            logging.info(f"Cleared demo host data for: {demo_hosts}")
            self._save_cache()
        else:
            logging.debug("No demo hosts found to clear")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.
        
        Returns:
            Dictionary with cache information
        """
        total_hosts = len(self.cache_data['hosts'])
        total_builds = sum(
            host_data['total_builds'] 
            for host_data in self.cache_data['hosts'].values()
        )
        
        return {
            "version": self.cache_data['version'],
            "cache_file": self.cache_file_path,
            "retention_days": self.retention_days,
            "total_hosts": total_hosts,
            "total_builds": total_builds,
            "cache_size_bytes": os.path.getsize(self.cache_file_path) if os.path.exists(self.cache_file_path) else 0
        }
