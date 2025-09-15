"""
QuranBot - State Persistence Manager
====================================

Handles saving and loading bot state to maintain continuity
across restarts. Saves current surah and reciter every 30 seconds.

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.logger import logger


class PersistenceManager:
    """
    Manages persistent state for QuranBot.
    
    Saves and loads bot state including:
    - Current surah number
    - Current reciter
    - Last save timestamp
    """
    
    def __init__(self, state_file: str = "bot_state.json") -> None:
        """
        Initialize the persistence manager.
        
        Args:
            state_file: Name of the JSON file to store state
        """
        # Store state file in project root for easy access
        # Navigate from src/core/ to project root, then store state file
        self.state_file: Path = Path(__file__).parent.parent.parent / state_file
        
        # Auto-save interval in seconds (30 seconds provides good balance)
        self.save_interval: int = 30
        
        # Background task reference for auto-save functionality
        self.save_task: Optional[asyncio.Task] = None
        
        logger.tree("💾 Persistence Manager Initialized", [
            ("State File", str(self.state_file)),
            ("Save Interval", f"{self.save_interval} seconds"),
            ("Auto-save", "Enabled")
        ])
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load the saved state from file.
        
        Returns:
            Dictionary containing saved state or empty dict if no state exists
        """
        try:
            if self.state_file.exists():
                # Load existing state from JSON file
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                logger.tree("📂 State Loaded Successfully", [
                    ("File", str(self.state_file)),
                    ("Surah", str(state.get('current_surah', 1))),
                    ("Reciter", state.get('reciter', 'Unknown')),
                    ("Last Saved", state.get('last_saved', 'Unknown'))
                ])
                
                return state
            else:
                # No previous state file exists, start with default values
                logger.tree("ℹ️ No Previous State Found", [
                    ("File", str(self.state_file)),
                    ("Action", "Starting with defaults"),
                    ("Default Surah", "1"),
                    ("Default Reciter", "Saad Al Ghamdi")
                ])
                return {}
                
        except json.JSONDecodeError as e:
            logger.error_tree("Failed to parse state file", e, [
                ("File", str(self.state_file)),
                ("Error", str(e)),
                ("Action", "Starting with defaults")
            ])
            return {}
            
        except Exception as e:
            logger.error_tree("Failed to load state", e, [
                ("File", str(self.state_file)),
                ("Error Type", type(e).__name__),
                ("Action", "Starting with defaults")
            ])
            return {}
    
    def save_state(self, current_surah: int, reciter: str) -> bool:
        """
        Save the current state to file.
        
        Args:
            current_surah: Current surah number (1-114)
            reciter: Current reciter name
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Create state dictionary with current bot information
            state = {
                "current_surah": current_surah,
                "reciter": reciter,
                "last_saved": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # Save state to JSON file with pretty formatting for readability
            # ensure_ascii=False allows Unicode characters (Arabic names, etc.)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            
            logger.tree("💾 State Saved", [
                ("Surah", str(current_surah)),
                ("Reciter", reciter),
                ("Time", datetime.now().strftime("%H:%M:%S"))
            ])
            
            return True
            
        except Exception as e:
            logger.error_tree("Failed to save state", e, [
                ("File", str(self.state_file)),
                ("Surah", str(current_surah)),
                ("Reciter", reciter)
            ])
            return False
    
    async def start_auto_save(self, audio_service) -> None:
        """
        Start the automatic save task that saves state every 30 seconds.
        
        Args:
            audio_service: The audio service to get state from
        """
        async def auto_save_loop():
            """Inner function for the auto-save loop."""
            while True:
                try:
                    # Wait for the configured save interval before next save
                    await asyncio.sleep(self.save_interval)
                    
                    # Get current state from audio service if it's connected
                    if audio_service and audio_service.is_connected:
                        current_surah = audio_service.current_surah
                        reciter = audio_service.default_reciter
                        
                        # Save the current state to maintain continuity
                        self.save_state(current_surah, reciter)
                        
                except asyncio.CancelledError:
                    # Task was cancelled (shutdown), exit gracefully
                    logger.tree("🛑 Auto-save Stopped", [
                        ("Reason", "Task cancelled"),
                        ("Action", "Exiting auto-save loop")
                    ])
                    break
                    
                except Exception as e:
                    logger.error_tree("Error in auto-save loop", e, [
                        ("Action", "Continuing auto-save"),
                        ("Next Save", f"In {self.save_interval} seconds")
                    ])
                    # Continue the loop even if there's an error
                    # This ensures auto-save doesn't stop due to temporary issues
                    continue
        
        # Cancel any existing save task to prevent multiple auto-save loops
        if self.save_task and not self.save_task.done():
            self.save_task.cancel()
        
        # Start the new auto-save task in the background
        self.save_task = asyncio.create_task(auto_save_loop())
        
        logger.tree("🔄 Auto-save Started", [
            ("Interval", f"{self.save_interval} seconds"),
            ("Status", "Active"),
            ("Task", "Running in background")
        ])
    
    def stop_auto_save(self) -> None:
        """Stop the automatic save task."""
        if self.save_task and not self.save_task.done():
            self.save_task.cancel()
            logger.tree("🛑 Auto-save Stopped", [
                ("Action", "Save task cancelled"),
                ("Status", "Stopped")
            ])
    
    def delete_state(self) -> bool:
        """
        Delete the saved state file.
        
        Returns:
            True if deletion successful or file doesn't exist, False otherwise
        """
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                logger.tree("🗑️ State File Deleted", [
                    ("File", str(self.state_file)),
                    ("Action", "State cleared")
                ])
            return True
            
        except Exception as e:
            logger.error_tree("Failed to delete state file", e, [
                ("File", str(self.state_file))
            ])
            return False