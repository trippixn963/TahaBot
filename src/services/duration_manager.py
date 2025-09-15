"""
QuranBot - MP3 Duration Manager
================================

Extracts and caches actual durations from MP3 files.
Provides accurate duration information for each surah and reciter combination.

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path
from mutagen.mp3 import MP3
from src.core.logger import logger


class DurationManager:
    """
    Manages MP3 duration extraction and caching.
    
    This class reads actual durations from MP3 files and caches them
    for quick access. It automatically updates when new files are added.
    """
    
    def __init__(self, audio_dir: str = "audio"):
        """
        Initialize the duration manager with audio directory and cache setup.
        
        This constructor sets up the duration manager by establishing the audio
        directory path, cache file location, and initializing the duration cache.
        It automatically loads existing cached durations and scans for any new
        MP3 files that need duration extraction.
        
        Args:
            audio_dir: Directory containing audio files organized by reciter
        """
        # Set up the audio directory path for scanning MP3 files
        self.audio_dir = Path(audio_dir)
        
        # Define cache file location in project root for persistence
        self.cache_file = Path("duration_cache.json")
        
        # Initialize the duration cache dictionary
        # Key format: "Reciter Name:Surah Number" -> Duration in seconds
        self.duration_cache: Dict[str, float] = {}
        
        # Load existing cache from file to preserve previous extractions
        self._load_cache()
        
        # Scan for new files and update cache with any missing durations
        self._update_cache()
    
    def _load_cache(self) -> None:
        """
        Load duration cache from JSON file if it exists.
        
        This method attempts to load previously cached duration data from the
        JSON file. If the file exists and is valid, it populates the cache
        with the saved durations to avoid re-extracting metadata from MP3 files.
        """
        if self.cache_file.exists():
            try:
                # Load cached durations from JSON file
                with open(self.cache_file, 'r') as f:
                    self.duration_cache = json.load(f)
                
                logger.tree("📁 Duration Cache Loaded", [
                    ("Cache File", str(self.cache_file)),
                    ("Entries", len(self.duration_cache))
                ])
            except Exception as e:
                # If cache file is corrupted, log error and start with empty cache
                logger.error_tree("Failed to load duration cache", e)
                self.duration_cache = {}
    
    def _save_cache(self) -> None:
        """
        Save duration cache to JSON file for persistence.
        
        This method writes the current duration cache to the JSON file with
        pretty formatting (indentation) for readability. This ensures that
        extracted durations are preserved across bot restarts.
        """
        try:
            # Save cache with pretty formatting for readability
            with open(self.cache_file, 'w') as f:
                json.dump(self.duration_cache, f, indent=2)
            
            logger.tree("💾 Duration Cache Saved", [
                ("Cache File", str(self.cache_file)),
                ("Entries", len(self.duration_cache))
            ])
        except Exception as e:
            # Log error but don't crash - cache will be rebuilt on next scan
            logger.error_tree("Failed to save duration cache", e)
    
    def _get_mp3_duration(self, file_path: Path) -> Optional[float]:
        """
        Extract duration from an MP3 file using mutagen library.
        
        This method uses the mutagen library to read MP3 file metadata and
        extract the actual duration. This provides accurate timing information
        that may differ from estimated durations based on file size.
        
        Args:
            file_path: Path to the MP3 file to analyze
            
        Returns:
            Duration in seconds, or None if extraction fails
        """
        try:
            # Use mutagen to read MP3 metadata
            audio = MP3(file_path)
            
            # Extract duration from audio info
            duration = audio.info.length
            
            return duration
        except Exception as e:
            # Log error but don't crash - this file will be skipped
            logger.error_tree(f"Failed to extract duration from {file_path}", e)
            return None
    
    def _update_cache(self) -> None:
        """
        Scan audio directory and update cache with any new files.
        
        This method recursively scans the audio directory structure to find
        new MP3 files that haven't been cached yet. It processes each reciter
        directory and extracts durations for any uncached surah files.
        """
        if not self.audio_dir.exists():
            logger.warning_tree("Audio directory not found", [
                ("Directory", str(self.audio_dir))
            ])
            return
        
        # Track if any new durations were added
        updated = False
        
        # AUDIO DIRECTORY SCANNING
        # ========================
        # Scan all reciter directories (e.g., "Saad Al Ghamdi", "Abdul Basit Abdul Samad")
        for reciter_dir in self.audio_dir.iterdir():
            if not reciter_dir.is_dir():
                continue
            
            # Get reciter name from directory name
            reciter_name = reciter_dir.name
            
            # Scan all MP3 files in the reciter's directory
            for mp3_file in reciter_dir.glob("*.mp3"):
                # Extract surah number from filename (e.g., "001.mp3" -> 1)
                try:
                    surah_num = int(mp3_file.stem)
                except ValueError:
                    # Skip files that don't follow the naming convention
                    continue
                
                # Create unique cache key for this reciter-surah combination
                cache_key = f"{reciter_name}:{surah_num}"
                
                # Skip if already cached to avoid unnecessary processing
                if cache_key in self.duration_cache:
                    continue
                
                # Extract duration from MP3 file and cache it
                duration = self._get_mp3_duration(mp3_file)
                if duration is not None:
                    self.duration_cache[cache_key] = duration
                    updated = True
                    logger.tree("🎵 Duration Extracted", [
                        ("Reciter", reciter_name),
                        ("Surah", surah_num),
                        ("Duration", f"{duration:.1f} seconds"),
                        ("File", mp3_file.name)
                    ])
        
        # Save cache if any new durations were added
        if updated:
            self._save_cache()
    
    def get_duration(self, surah_number: int, reciter: str) -> Optional[float]:
        """
        Get the actual duration for a specific surah and reciter combination.
        
        This method provides the primary interface for retrieving MP3 durations.
        It first checks the cache for quick access, and if not found, attempts
        to extract the duration directly from the MP3 file and cache it.
        
        Args:
            surah_number: The surah number (1-114)
            reciter: The reciter name (must match directory name exactly)
            
        Returns:
            Duration in seconds, or None if not found or extraction fails
        """
        # Create cache key using the same format as the scanning process
        # Keep reciter name as-is (with spaces) to match directory structure
        cache_key = f"{reciter}:{surah_number}"
        
        # Check cache first for fastest response
        if cache_key in self.duration_cache:
            return self.duration_cache[cache_key]
        
        # CACHE MISS - ATTEMPT DIRECT EXTRACTION
        # ======================================
        # Try to extract duration directly from the MP3 file
        mp3_path = self.audio_dir / reciter / f"{surah_number:03d}.mp3"
        if mp3_path.exists():
            duration = self._get_mp3_duration(mp3_path)
            if duration is not None:
                # Cache the newly extracted duration for future use
                self.duration_cache[cache_key] = duration
                self._save_cache()
                return duration
        
        # Return None if file doesn't exist or extraction failed
        return None
    
    def refresh_cache(self) -> None:
        """
        Force a full refresh of the duration cache.
        
        This method clears all cached durations and rescans the entire audio
        directory to rebuild the cache from scratch. This is useful when
        the cache becomes corrupted or when you want to ensure all durations
        are up-to-date with the current audio files.
        """
        logger.tree("🔄 Refreshing Duration Cache", [
            ("Action", "Clearing existing cache"),
            ("Directory", str(self.audio_dir))
        ])
        
        # Clear all cached durations
        self.duration_cache = {}
        
        # Rescan all audio files to rebuild the cache
        self._update_cache()


# GLOBAL INSTANCE MANAGEMENT
# ==========================
# Singleton pattern for the duration manager to ensure only one instance exists
_duration_manager: Optional[DurationManager] = None


def get_duration_manager() -> DurationManager:
    """
    Get or create the global duration manager instance.
    
    This function implements the singleton pattern to ensure only one
    DurationManager instance exists throughout the application lifecycle.
    This prevents multiple cache files and ensures consistent duration data.
    
    Returns:
        DurationManager: The global duration manager instance
    """
    global _duration_manager
    if _duration_manager is None:
        _duration_manager = DurationManager()
    return _duration_manager


def get_mp3_duration(surah_number: int, reciter: str) -> float:
    """
    Get the actual MP3 duration for a surah and reciter combination.
    
    This is the main public interface for getting MP3 durations. It provides
    a convenient wrapper around the DurationManager with a sensible default
    fallback duration for cases where the actual duration cannot be determined.
    
    Args:
        surah_number: The surah number (1-114)
        reciter: The reciter name
        
    Returns:
        Duration in seconds, defaults to 180 (3 minutes) if not found
    """
    # Get the global duration manager instance
    manager = get_duration_manager()
    
    # Attempt to get the actual duration
    duration = manager.get_duration(surah_number, reciter)
    
    # Return actual duration or sensible default fallback
    # 180 seconds (3 minutes) is a reasonable default for most Quran recitations
    return duration if duration is not None else 180.0