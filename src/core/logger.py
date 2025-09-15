"""
QuranBot - Logger Module
========================

Custom logging system with EST timezone support and tree-style formatting.
Provides structured logging for Discord bot events with visual formatting
and file output for debugging and monitoring.

Features:
- Unique run ID generation for tracking bot sessions
- EST timezone timestamp formatting
- Tree-style log formatting for structured data
- Console and file output simultaneously
- Emoji-enhanced log levels for visual clarity

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import uuid
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Tuple, Optional


class MiniTreeLogger:
    """
    Custom logger with tree-style formatting and EST timezone support.
    
    Provides structured logging capabilities for the QuranBot:
    - Unique run ID for each bot session
    - EST timezone timestamps (UTC-5)
    - Tree-style formatting for hierarchical data
    - Simultaneous console and file output
    - Emoji-enhanced log levels for visual clarity
    
    Log files are stored in logs/ directory with daily rotation.
    """
    
    def __init__(self) -> None:
        """
        Initialize the logger with unique run ID and daily log file rotation.
        
        Creates logs directory if it doesn't exist and generates a unique
        run ID for tracking this bot session. Also cleans up old log files.
        """
        self.run_id: str = str(uuid.uuid4())[:8]  # Short unique ID for this run
        self.log_file: Path = Path('logs') / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Clean up old log files on startup
        self._cleanup_old_logs()
        
        # Write session start header with run ID
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"NEW SESSION STARTED - RUN ID: {self.run_id}\n")
            f.write(f"{self._get_timestamp()}\n")
            f.write(f"{'='*60}\n\n")
    
    def _cleanup_old_logs(self) -> None:
        """
        Clean up log files older than 30 days.
        
        Automatically removes old log files to prevent disk space issues.
        Runs on bot startup to keep logs directory clean.
        """
        try:
            logs_dir = Path('logs')
            if not logs_dir.exists():
                return
            
            # Get current time
            now = datetime.now()
            
            # Check each log file
            deleted_count = 0
            for log_file in logs_dir.glob('*.log'):
                # Get file modification time
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                # If file is older than 30 days, delete it
                if (now - file_time).days > 30:
                    log_file.unlink()
                    deleted_count += 1
            
            # Log cleanup results (but don't use self._write since it's not initialized yet)
            if deleted_count > 0:
                print(f"[LOG CLEANUP] Deleted {deleted_count} old log files (>30 days)")
                
        except Exception as e:
            print(f"[LOG CLEANUP ERROR] Failed to clean old logs: {e}")
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in Eastern timezone (auto EST/EDT).
        
        Returns:
            str: Formatted timestamp string in ET (auto-adjusts for daylight saving)
        """
        # Use system local time which is set to America/New_York
        # This automatically handles EST/EDT based on the date
        current_time = datetime.now()
        # Determine if we're in EDT (summer) or EST (winter)
        tz_name = "EDT" if current_time.month >= 3 and current_time.month <= 11 else "EST"
        return current_time.strftime(f'[%I:%M:%S %p {tz_name}]')
    
    def _write(self, message: str, emoji: str = "", include_timestamp: bool = True) -> None:
        """
        Write log message to both console and file.
        
        Args:
            message (str): The log message to write
            emoji (str): Optional emoji to prefix the message
            include_timestamp (bool): Whether to include timestamp
        """
        if include_timestamp:
            timestamp: str = self._get_timestamp()
            full_message: str = f"{timestamp} {emoji} {message}" if emoji else f"{timestamp} {message}"
        else:
            full_message: str = f"{emoji} {message}" if emoji else message
        
        # Output to console
        print(full_message)
        
        # Write to log file (without RUN ID on every line)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{full_message}\n")
    
    def tree(self, title: str, items: List[Tuple[str, str]], emoji: str = "📦") -> None:
        """
        Log structured data in tree format.
        
        Creates a hierarchical tree structure for logging structured data
        like bot status, command execution details, etc.
        
        Args:
            title (str): Main title for the tree
            items (List[Tuple[str, str]]): List of (key, value) tuples to display
            emoji (str): Emoji to prefix the title
        """
        # Add line break before tree for better readability
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n")
        
        # Only use emoji parameter if title doesn't already contain one
        if emoji and not any(char in title for char in "🎵🔌✅❌⚠️🎙️🎛️⏸️▶️⏹️⏭️🔍📖🔄✋🌐🤖🕌🧹💾📂ℹ️🗑️🛑🔀🔁⏮️🎯🚫"):
            self._write(f"{title}", emoji=emoji)
        else:
            self._write(f"{title}")
        for i, (key, value) in enumerate(items):
            prefix: str = "└─" if i == len(items) - 1 else "├─"
            self._write(f"  {prefix} {key}: {value}", include_timestamp=False)
        
        # Add line break after tree
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n")
    
    def info(self, msg: str) -> None:
        """Log an informational message."""
        self._write(msg, "ℹ️")
    
    def success(self, msg: str) -> None:
        """Log a success message."""
        self._write(msg, "✅")
    
    def error(self, msg: str) -> None:
        """Log an error message."""
        self._write(msg, "❌")
    
    def warning(self, msg: str) -> None:
        """Log a warning message."""
        self._write(msg, "⚠️")
    
    def error_tree(self, title: str, error: Exception, context: Optional[List[Tuple[str, str]]] = None) -> None:
        """
        Log an error in tree format with context.
        
        Args:
            title (str): Error title
            error (Exception): The exception that occurred
            context (Optional[List[Tuple[str, str]]]): Additional context as (key, value) tuples
        """
        items = []
        items.append(("Error Type", type(error).__name__))
        items.append(("Message", str(error)))
        
        if context:
            for key, value in context:
                items.append((key, str(value)))
        
        self.tree(title, items)


# Global logger instance for use throughout the bot
logger = MiniTreeLogger()