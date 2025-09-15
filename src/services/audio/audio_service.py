"""
QuranBot - Advanced Audio Service
=================================

Professional audio streaming service for continuous Quran playback
with multi-reciter support, auto-reconnection, and robust error handling.

Features:
- 24/7 continuous audio streaming with seamless playback
- Multiple reciter support with automatic fallback
- Stage channel integration with speaker management
- Auto-reconnection on network interruptions
- Comprehensive error handling and recovery
- Real-time playback status monitoring
- Reciter switching without interruption

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import asyncio
import discord
import time
from pathlib import Path
from typing import Optional, Union, Dict, List, Any

from src.core.logger import logger


class AudioService:
    """
    Advanced audio service for continuous Quran streaming.
    
    Provides comprehensive audio management including voice channel connectivity,
    multi-reciter support, playback control, and automatic error recovery.
    Designed for 24/7 operation with robust reconnection capabilities.
    
    Attributes:
        audio_dir: Path to the audio files directory
        default_reciter: Currently selected reciter
        current_surah: Current surah number being played
        is_playing: Boolean indicating active playback state
        voice_client: Discord voice client instance
        channel: Connected voice/stage channel reference
    """
    
    def __init__(self, saved_surah: Optional[int] = None, saved_reciter: Optional[str] = None) -> None:
        """
        Initialize the audio service.
        
        Args:
            saved_surah: Saved surah number from previous session
            saved_reciter: Saved reciter from previous session
        """
        # Set up audio directory path relative to project root
        # Navigate from src/services/audio/ to project root, then to audio/
        self.audio_dir: Path = Path(__file__).parent.parent.parent.parent / "audio"
        
        # Use saved reciter if available, otherwise default to Saad Al Ghamdi
        # Saad Al Ghamdi has the most complete audio collection
        self.default_reciter: str = saved_reciter or "Saad Al Ghamdi"
        
        # Use saved surah if available, otherwise start from Al-Fatiha (Surah 1)
        self.current_surah: int = saved_surah or 1
        
        # Track playback state for UI updates and status monitoring
        self.is_playing: bool = False
        
        # Discord voice client instance for audio streaming
        self.voice_client: Optional[discord.VoiceClient] = None
        
        # Store channel reference for auto-reconnection purposes
        self.channel: Optional[Union[discord.VoiceChannel, discord.StageChannel]] = None
        
        # Track last reconnection attempt to prevent rapid reconnections
        self.last_reconnect_attempt: float = 0
        self.reconnect_delay: int = 10  # Minimum seconds between reconnection attempts
        
        # Presence handler will be set by the bot after initialization
        self.presence_handler = None
        
        logger.tree("🎵 Audio Service Initialized", [
            ("Audio Directory", str(self.audio_dir)),
            ("Default Reciter", self.default_reciter),
            ("Starting Surah", str(self.current_surah))
        ])
    
    async def connect(self, channel: Union[discord.VoiceChannel, discord.StageChannel]) -> bool:
        """Connect to a voice/stage channel."""
        try:
            # Store channel reference for auto-reconnection in case of disconnection
            # This ensures we can reconnect to the same channel automatically
            self.channel = channel
            
            # Check if already connected to this channel
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel.id == channel.id:
                    logger.tree("ℹ️ Already Connected", [
                        ("Channel", channel.name),
                        ("Status", "Active connection exists")
                    ])
                    return True
                else:
                    # Disconnect from current channel before connecting to new one
                    await self.voice_client.disconnect(force=True)
                    self.voice_client = None
            
            # Connect to voice/stage channel with 60-second timeout
            # reconnect=True enables automatic reconnection on network issues
            self.voice_client = await channel.connect(timeout=60.0, reconnect=True)
            
            # Handle stage channel specific requirements
            # Stage channels require the bot to be "unsuppressed" to transmit audio
            if isinstance(channel, discord.StageChannel):
                try:
                    # Unsuppress the bot to make it an active speaker
                    # This allows audio transmission in stage channels
                    await channel.guild.me.edit(suppress=False)
                    logger.tree("🎙️ Stage Speaker Status", [
                ("Action", "Set as speaker"),
                ("Stage", channel.name)
            ])
                except:
                    # Silently fail if we can't become speaker (permissions issue)
                    # The bot will still connect but may not transmit audio
                    pass
            
            logger.tree("✅ Connected to Channel", [
                ("Channel", channel.name),
                ("Type", type(channel).__name__),
                ("Guild", channel.guild.name if channel.guild else "Unknown")
            ])
            return True
            
        except discord.ClientException as e:
            if "Already connected" in str(e):
                logger.tree("⚠️ Connection Conflict", [
                    ("Error", "Already connected to a voice channel"),
                    ("Action", "Using existing connection")
                ])
                return False
            logger.error_tree("Failed to connect to voice channel", e, [
                ("Channel", channel.name),
                ("Channel Type", type(channel).__name__),
                ("Guild", channel.guild.name if channel.guild else "Unknown")
            ])
            return False
        except Exception as e:
            logger.error_tree("Failed to connect to voice channel", e, [
                ("Channel", channel.name),
                ("Channel Type", type(channel).__name__),
                ("Guild", channel.guild.name if channel.guild else "Unknown")
            ])
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from voice channel."""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            logger.tree("🔌 Disconnected from Voice", [
                ("Action", "Clean disconnect"),
                ("Status", "Success")
            ])
    
    def get_audio_file(self, surah_number: int) -> Optional[str]:
        """Get the audio file path for a surah."""
        # Try the currently selected default reciter first
        # This provides the best user experience by maintaining consistency
        reciter_dir: Path = self.audio_dir / self.default_reciter
        
        # Format surah number as 3-digit string (001, 002, etc.) for consistent file naming
        surah_file: Path = reciter_dir / f"{surah_number:03d}.mp3"
        
        if surah_file.exists():
            return str(surah_file)
        
        # Fallback: Search through all available reciters if default reciter doesn't have this surah
        # This ensures playback continues even if some reciters have incomplete collections
        for reciter_folder in self.audio_dir.iterdir():
            # Skip hidden directories and files
            if reciter_folder.is_dir():
                test_file = reciter_folder / f"{surah_number:03d}.mp3"
                if test_file.exists():
                    # Log which reciter we're using as fallback for transparency
                    logger.tree("🎵 Reciter Fallback", [
                        ("Default Not Found", self.default_reciter),
                        ("Using Instead", reciter_folder.name),
                        ("Surah", str(surah_number))
                    ])
                    return str(test_file)
        
        # Return None if no audio file found for this surah in any reciter
        # This will trigger the skip-to-next-surah logic in the caller
        return None
    
    async def play_next(self) -> bool:
        """Play the next surah in the queue."""
        if not self.voice_client or not self.voice_client.is_connected():
            logger.error_tree("Not Connected", Exception("Voice client not connected"), [
                ("Status", "Disconnected"),
                ("Action", "Cannot play audio")
            ])
            return False
        
        # Retrieve the audio file path for the current surah
        # This handles both default reciter and fallback logic automatically
        audio_file: Optional[str] = self.get_audio_file(self.current_surah)
        
        if not audio_file:
            logger.tree("⚠️ Audio File Missing", [
                ("Surah Number", str(self.current_surah)),
                ("Action", "Skipping to next surah"),
                ("Next Surah", str((self.current_surah % 114) + 1))
            ])
            # Automatically advance to next surah if current one is unavailable
            # Use modulo 114 to cycle through all surahs (1-114) and wrap back to 1
            self.current_surah = (self.current_surah % 114) + 1
            return False
        
        try:
            # Create beautiful logging output for current playback
            surah_info = f"Surah {self.current_surah} ({Path(audio_file).stem})"
            logger.tree(f"🎵 Now Playing", [
                ("Surah", f"{self.current_surah}/114"),
                ("File", Path(audio_file).name),
                ("Reciter", self.default_reciter)
            ])
            
            # Create FFmpeg audio source for Discord voice streaming
            # FFmpeg handles various audio formats and provides high-quality streaming
            source: discord.FFmpegPCMAudio = discord.FFmpegPCMAudio(audio_file)
            
            # Start playback with callback for when audio finishes
            # The after parameter calls _playback_finished() when the audio ends
            self.voice_client.play(
                source,
                after=lambda e: self._playback_finished(e)
            )
            
            # Update playback state for UI and status monitoring
            self.is_playing = True
            
            # Update rich presence to show current surah and reciter
            if self.presence_handler:
                # Use the current surah (before advancing) and include reciter name
                asyncio.create_task(self.presence_handler.update_presence(self.current_surah, self.default_reciter))
            
            # Pre-advance to next surah for seamless continuous playback
            # This ensures the next surah is ready when current one finishes
            self.current_surah = (self.current_surah % 114) + 1
            
            return True
            
        except Exception as e:
            logger.error_tree("Failed to play audio", e, [
                ("Surah", str(self.current_surah)),
                ("Audio File", audio_file if audio_file else "None"),
                ("Reciter", self.default_reciter)
            ])
            return False
    
    def _playback_finished(self, error: Optional[Exception]) -> None:
        """Called when playback finishes."""
        if error:
            finished_surah = (self.current_surah - 1) if self.current_surah > 1 else 114
            logger.error_tree("Playback error occurred", error, [
                ("Surah", str(finished_surah)),
                ("Reciter", self.default_reciter)
            ])
        else:
            finished_surah = (self.current_surah - 1) if self.current_surah > 1 else 114
            logger.success(f"Surah {finished_surah} playback completed")
        
        self.is_playing = False
    
    async def start_continuous_playback(self) -> None:
        """Start continuous 24/7 playback loop."""
        logger.tree("🎵 Starting Continuous Playback", [
            ("Mode", "24/7 Streaming"),
            ("Starting Surah", str(self.current_surah)),
            ("Reciter", self.default_reciter)
        ])
        
        # Infinite loop for 24/7 continuous playback
        # This is the heart of the bot's continuous operation
        while True:
            try:
                # Monitor connection status and handle disconnections gracefully
                # This ensures the bot stays connected even through network issues
                if not self.voice_client or not self.voice_client.is_connected():
                    # Check if enough time has passed since last reconnection attempt
                    current_time = time.time()
                    time_since_last_attempt = current_time - self.last_reconnect_attempt
                    
                    if time_since_last_attempt < self.reconnect_delay:
                        # Too soon to reconnect, wait a bit
                        await asyncio.sleep(1)
                        continue
                    
                    logger.tree("⚠️ Voice Disconnected", [
                        ("Status", "Connection lost"),
                        ("Action", "Attempting reconnection"),
                        ("Delay", f"{self.reconnect_delay} seconds")
                    ])
                    
                    # Only attempt reconnection if we have a stored channel reference
                    if hasattr(self, 'channel') and self.channel:
                        # Update last reconnection attempt time
                        self.last_reconnect_attempt = current_time
                        
                        # Force disconnect any stale connection before reconnecting
                        # This prevents connection conflicts and ensures clean state
                        if self.voice_client:
                            try:
                                await self.voice_client.disconnect(force=True)
                            except:
                                pass  # Ignore errors during disconnect
                            self.voice_client = None
                        
                        # Wait before reconnection attempt to avoid rate limits
                        await asyncio.sleep(self.reconnect_delay)
                        
                        # Attempt to reconnect to the stored channel
                        success = await self.connect(self.channel)
                        if not success:
                            # If reconnection failed, increase delay for next attempt
                            self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # Max 60 seconds
                        else:
                            # Reset delay on successful reconnection
                            self.reconnect_delay = 10
                        continue  # Skip the rest of the loop and try again
                    else:
                        # No channel reference available, exit the loop
                        break
                
                # Check if we need to start playing the next surah
                # Only start new playback if not currently playing and not paused
                if not self.voice_client.is_playing() and not self.voice_client.is_paused():
                    await self.play_next()
                
                # Brief pause to prevent excessive CPU usage
                # 1 second is optimal for responsiveness without wasting resources
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error_tree("Error in playback loop", e, [
                    ("Current Surah", str(self.current_surah)),
                    ("Is Connected", str(self.voice_client.is_connected() if self.voice_client else False)),
                    ("Is Playing", str(self.voice_client.is_playing() if self.voice_client else False))
                ])
                await asyncio.sleep(5)
    
    def pause(self) -> None:
        """Pause playback."""
        # Only pause if currently playing to avoid errors
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            logger.tree("⏸️ Playback Paused", [
                ("Action", "Audio paused"),
                ("Current Surah", str(self.current_surah))
            ])
            # Set presence to idle when paused
            if self.presence_handler:
                asyncio.create_task(self.presence_handler.set_idle_presence())
    
    def resume(self) -> None:
        """Resume playback."""
        # Only resume if currently paused to avoid errors
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            logger.tree("▶️ Playback Resumed", [
                ("Action", "Audio resumed"),
                ("Current Surah", str(self.current_surah))
            ])
    
    def stop(self) -> None:
        """Stop playback."""
        # Stop playback and reset state
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            # Reset playback state since we're manually stopping
            self.is_playing = False
            logger.tree("⏹️ Playback Stopped", [
                ("Action", "Audio stopped"),
                ("Current Surah", str(self.current_surah))
            ])
            # Clear presence when stopped
            if self.presence_handler:
                asyncio.create_task(self.presence_handler.clear_presence())
    
    def skip(self) -> None:
        """Skip to next surah."""
        # Stop current playback to trigger automatic next surah
        if self.voice_client and self.voice_client.is_playing():
            # Stopping will trigger the _playback_finished callback
            # which will then automatically start the next surah
            self.voice_client.stop()
            logger.tree("⏭️ Skipping Surah", [
                ("Current", str((self.current_surah - 1) if self.current_surah > 1 else 114)),
                ("Next", str(self.current_surah))
            ])
    
    def update_presence_for_current(self) -> None:
        """Update presence for the currently playing surah."""
        if self.presence_handler:
            # Get the currently playing surah (adjust for pre-advancement)
            current_playing = (self.current_surah - 1) if self.current_surah > 1 else 114
            asyncio.create_task(self.presence_handler.update_presence(current_playing, self.default_reciter))
    
    def set_reciter(self, reciter_name: str) -> bool:
        """Change the reciter."""
        # Validate that the requested reciter directory exists
        reciter_dir: Path = self.audio_dir / reciter_name
        if reciter_dir.exists() and reciter_dir.is_dir():
            # Store old reciter for logging purposes
            old_reciter = self.default_reciter
            
            # Update the default reciter to the new selection
            self.default_reciter = reciter_name
            
            # Log the reciter change with beautiful tree formatting
            logger.tree(f"🎙️ Reciter Changed", [
                ("From", old_reciter),
                ("To", reciter_name),
                ("Current Surah", str(self.current_surah))
            ])
            
            # Update rich presence with new reciter
            if self.presence_handler and self.is_playing:
                # Get the currently playing surah (adjust for pre-advancement)
                current_playing = (self.current_surah - 1) if self.current_surah > 1 else 114
                asyncio.create_task(self.presence_handler.update_presence(current_playing, reciter_name))
            
            # If currently playing, we need to restart with the same surah
            # Since play_next() advances the surah, we need to go back one
            # to replay the same surah with the new reciter
            if self.voice_client and self.voice_client.is_playing():
                # Go back one surah to counteract the automatic advance
                # This ensures we replay the same surah with the new reciter
                self.current_surah = (self.current_surah - 1) if self.current_surah > 1 else 114
                # Stop current playback, which will trigger play_next()
                # play_next() will then advance back to the correct surah
                self.voice_client.stop()
                
            return True
        else:
            # Provide helpful error information including available reciters
            logger.error_tree("Reciter not found", Exception(f"Invalid reciter: {reciter_name}"), [
                ("Requested Reciter", reciter_name),
                ("Available Reciters", ", ".join(self.get_available_reciters()))
            ])
            return False
    
    def get_available_reciters(self) -> List[str]:
        """Get list of available reciters."""
        reciters: List[str] = []
        
        # Scan audio directory for reciter folders
        for folder in self.audio_dir.iterdir():
            # Only include directories that aren't hidden (don't start with '.')
            # This excludes system files and hidden directories
            if folder.is_dir() and not folder.name.startswith('.'):
                reciters.append(folder.name)
        
        # Return alphabetically sorted list for consistent UI display
        return sorted(reciters)
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to voice channel."""
        return self.voice_client and self.voice_client.is_connected()
    
    @property
    def current_status(self) -> Dict[str, Any]:
        """Get current playback status."""
        return {
            # Connection status for UI display
            "connected": self.is_connected,
            
            # Current playback state (playing/paused/stopped)
            "playing": self.voice_client.is_playing() if self.voice_client else False,
            "paused": self.voice_client.is_paused() if self.voice_client else False,
            
            # Current surah number (1-114)
            "current_surah": self.current_surah,
            
            # Currently selected reciter name
            "reciter": self.default_reciter,
            
            # Channel name for display (None if not connected)
            "channel": self.voice_client.channel.name if self.voice_client and self.voice_client.channel else None
        }