#!/usr/bin/python3
"""
Auto-Exit Manager Module

Manages automatic exit after build completion with configurable delay.
"""

import logging
import threading
import time
from typing import Optional, Callable


class AutoExitManager:
    """Manages automatic exit after build completion."""
    
    def __init__(self, exit_delay_seconds: int = 300, enabled: bool = True):
        """
        Initialize the auto-exit manager.
        
        Args:
            exit_delay_seconds: Delay in seconds before auto-exit (default: 300 = 5 minutes)
            enabled: Whether auto-exit is enabled
        """
        self.exit_delay_seconds = exit_delay_seconds
        self.enabled = enabled
        self.last_build_completion_time: Optional[float] = None
        self.exit_timer: Optional[threading.Timer] = None
        self.is_exiting = False
        self.exit_callback: Optional[Callable[[], None]] = None
        
        logging.debug(f"AutoExitManager initialized with {exit_delay_seconds}s delay, enabled={enabled}")
    
    def set_exit_callback(self, callback: Callable[[], None]) -> None:
        """
        Set the callback function to call when auto-exit should occur.
        
        Args:
            callback: Function to call for exit
        """
        self.exit_callback = callback
        logging.debug("Exit callback set")
    
    def on_build_completed(self, host_name: str, success: bool) -> None:
        """
        Called when any build completes (success or failure).
        
        Args:
            host_name: Name of the host that completed
            success: Whether the build was successful
        """
        if not self.enabled:
            return
            
        self.last_build_completion_time = time.time()
        logging.debug(f"Build completed for {host_name} (success={success}), scheduling auto-exit")
        self._schedule_exit()
    
    def _schedule_exit(self) -> None:
        """Schedule exit after configured delay."""
        if self.exit_timer:
            self.exit_timer.cancel()
            logging.debug("Previous auto-exit timer cancelled")
        
        self.exit_timer = threading.Timer(
            self.exit_delay_seconds, 
            self._perform_exit
        )
        self.exit_timer.start()
        logging.info(f"Auto-exit countdown started: {self.exit_delay_seconds} seconds remaining")
        logging.debug(f"Auto-exit scheduled in {self.exit_delay_seconds} seconds")
    
    def _perform_exit(self) -> None:
        """Perform the actual exit."""
        if not self.enabled or self.is_exiting:
            return
            
        logging.info("Auto-exit timer expired, triggering exit")
        self.is_exiting = True
        
        if self.exit_callback:
            try:
                self.exit_callback()
            except Exception as e:
                logging.error(f"Error in exit callback: {e}")
        else:
            logging.warning("No exit callback set, cannot perform auto-exit")
    
    def cancel_exit(self) -> None:
        """Cancel the scheduled auto-exit."""
        if self.exit_timer:
            self.exit_timer.cancel()
            self.exit_timer = None
            logging.debug("Auto-exit cancelled")
    
    def get_remaining_time(self) -> Optional[int]:
        """
        Get remaining time until auto-exit in seconds.
        
        Returns:
            Remaining seconds, or None if no exit is scheduled
        """
        if not self.exit_timer or not self.last_build_completion_time:
            return None
        
        elapsed = time.time() - self.last_build_completion_time
        remaining = self.exit_delay_seconds - elapsed
        return max(0, int(remaining))
    
    def get_countdown_display(self) -> Optional[str]:
        """
        Get a formatted countdown string for display.
        
        Returns:
            Formatted countdown string, or None if no countdown active
        """
        remaining = self.get_remaining_time()
        if remaining is None:
            return None
        
        if remaining <= 0:
            return "Exiting..."
        
        minutes = remaining // 60
        seconds = remaining % 60
        
        if minutes > 0:
            countdown_text = f"Auto-exit in {minutes}m {seconds}s"
        else:
            countdown_text = f"Auto-exit in {seconds}s"
        
        logging.debug(f"Countdown display: {countdown_text} (remaining: {remaining}s)")
        return countdown_text
    
    def is_countdown_active(self) -> bool:
        """
        Check if countdown is currently active.
        
        Returns:
            True if countdown is active, False otherwise
        """
        return self.exit_timer is not None and not self.is_exiting
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.exit_timer:
            self.exit_timer.cancel()
            self.exit_timer = None
        logging.debug("AutoExitManager cleanup completed")
