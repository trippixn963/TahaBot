"""
QuranBot - Instance Lock Manager
================================

Ensures only one instance of the bot runs at a time using PID file locking.
Automatically cleans up stale locks from crashed processes.

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import os
import sys
import psutil
from pathlib import Path
from typing import Optional

from src.core.logger import logger


class LockManager:
    """
    Manages single instance enforcement using PID file locking.
    
    Creates a lock file containing the process ID to prevent multiple
    instances from running simultaneously. Handles stale lock cleanup
    for processes that crashed without proper cleanup.
    """
    
    def __init__(self, lock_file: str = "bot.lock") -> None:
        """
        Initialize the lock manager.
        
        Args:
            lock_file: Name of the lock file (default: bot.lock)
        """
        # Store the lock file path for PID-based instance management
        self.lock_file: Path = Path(lock_file)
        
        # Get current process ID for lock ownership verification
        self.pid: int = os.getpid()
        
    def acquire(self) -> bool:
        """
        Attempt to acquire the lock.
        
        Returns:
            True if lock acquired successfully, False if another instance is running
        """
        try:
            # Check if a lock file already exists from a previous instance
            if self.lock_file.exists():
                # Read the PID stored in the existing lock file
                try:
                    with open(self.lock_file, 'r') as f:
                        existing_pid = int(f.read().strip())
                    
                    # Verify if the process with that PID is still running
                    if self._is_process_running(existing_pid):
                        # Another instance is actively running, deny this instance
                        logger.error_tree("Another instance is already running", 
                                        Exception("Multiple instances not allowed"), [
                            ("Existing PID", str(existing_pid)),
                            ("Lock File", str(self.lock_file)),
                            ("Action", "Terminating this instance")
                        ])
                        return False
                    else:
                        # The process is dead but lock file remains (stale lock)
                        # Clean up the stale lock to allow this instance to proceed
                        logger.tree("🧹 Cleaning Stale Lock", [
                            ("Old PID", str(existing_pid)),
                            ("Status", "Process not running"),
                            ("Action", "Removing stale lock")
                        ])
                        self.lock_file.unlink()
                        
                except (ValueError, IOError) as e:
                    # Lock file is corrupted or unreadable, remove it
                    logger.tree("⚠️ Invalid Lock File", [
                        ("Error", str(e)),
                        ("Action", "Removing corrupted lock")
                    ])
                    self.lock_file.unlink()
            
            # Create new lock file with current process ID
            # This establishes ownership of the bot instance
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            
            logger.tree("🔒 Instance Lock Acquired", [
                ("PID", str(self.pid)),
                ("Lock File", str(self.lock_file)),
                ("Status", "Bot instance protected")
            ])
            return True
            
        except Exception as e:
            logger.error_tree("Failed to acquire lock", e, [
                ("Lock File", str(self.lock_file)),
                ("PID", str(self.pid))
            ])
            return False
    
    def release(self) -> None:
        """Release the lock by removing the lock file."""
        try:
            if self.lock_file.exists():
                # Verify we own the lock before removing it
                # This prevents accidentally removing another instance's lock
                with open(self.lock_file, 'r') as f:
                    lock_pid = int(f.read().strip())
                
                if lock_pid == self.pid:
                    # We own the lock, safe to remove it
                    self.lock_file.unlink()
                    logger.tree("🔓 Instance Lock Released", [
                        ("PID", str(self.pid)),
                        ("Lock File", str(self.lock_file)),
                        ("Status", "Clean shutdown")
                    ])
                else:
                    # Lock is owned by a different process, don't touch it
                    logger.warning(f"Lock owned by different process: {lock_pid}")
                    
        except Exception as e:
            logger.error_tree("Failed to release lock", e, [
                ("Lock File", str(self.lock_file))
            ])
    
    def _is_process_running(self, pid: int) -> bool:
        """
        Check if a process with given PID is running.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process is running, False otherwise
        """
        try:
            process = psutil.Process(pid)
            # Check if it's a Python process running main.py
            # This ensures we only detect QuranBot instances, not other Python processes
            cmdline = ' '.join(process.cmdline())
            return process.is_running() and 'main.py' in cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process doesn't exist or we don't have permission to access it
            return False
        except Exception:
            # Any other error means we can't verify the process
            return False
    
    def kill_existing(self) -> bool:
        """
        Kill any existing bot instance.
        
        Returns:
            True if an instance was killed, False otherwise
        """
        try:
            if self.lock_file.exists():
                # Read the PID of the existing instance
                with open(self.lock_file, 'r') as f:
                    existing_pid = int(f.read().strip())
                
                if self._is_process_running(existing_pid):
                    # Terminate the existing bot instance
                    process = psutil.Process(existing_pid)
                    process.terminate()
                    
                    logger.tree("⚡ Killed Existing Instance", [
                        ("PID", str(existing_pid)),
                        ("Action", "Process terminated"),
                        ("Status", "Ready for new instance")
                    ])
                    
                    # Remove the lock file to allow new instance to start
                    self.lock_file.unlink()
                    return True
                    
        except Exception as e:
            logger.error_tree("Failed to kill existing instance", e, [
                ("Lock File", str(self.lock_file))
            ])
        
        return False
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()