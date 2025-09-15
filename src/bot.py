"""
TahaBot Discord Bot - Main Bot Class
====================================

The core Discord bot class that handles 24/7 Quran streaming in voice channels.

Features:
- 24/7 continuous audio streaming
- Auto-reconnect on disconnect
- Multiple reciter support
- Stage channel support
- Modular audio service architecture

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import asyncio
import discord
from discord.ext import commands
from typing import Optional, Union

from src.core.logger import logger
from src.core.config import Config, get_config
from src.core.persistence import PersistenceManager
from src.services.audio.audio_service import AudioService
from src.ui.control_panel import ControlPanel
from src.handlers.presence_handler import PresenceHandler


class TahaBot(commands.Bot):
    """
    Main Discord bot class for TahaBot.
    
    Handles all Discord voice interactions including:
    - Connecting to stage/voice channels
    - Managing 24/7 audio playback
    - Auto-reconnection on disconnect
    - Audio service integration
    
    Attributes:
        config (Config): Configuration instance
        audio_service (AudioService): Audio service for playback
        control_panel (ControlPanel): Interactive control panel UI
    """
    
    def __init__(self) -> None:
        """
        Initialize the TahaBot.
        
        Sets up:
        - Configuration loading
        - Audio service initialization
        - Discord intents
        - Command prefix (unused for 24/7 bot)
        """
        # Load configuration from environment variables and .env file
        self.config: Config = get_config()
        
        # STATE PERSISTENCE SYSTEM
        # ========================
        # Initialize persistence manager for automatic state saving
        # This maintains continuity across bot restarts by saving current surah and reciter
        self.persistence: PersistenceManager = PersistenceManager()
        
        # Load previously saved state if it exists
        # This allows the bot to resume from where it left off after a restart
        saved_state = self.persistence.load_state()
        
        # Initialize the audio service with saved state for seamless continuity
        # If no saved state exists, defaults to Surah 1 and Saad Al Ghamdi
        self.audio_service: AudioService = AudioService(
            saved_surah=saved_state.get('current_surah'),
            saved_reciter=saved_state.get('reciter')
        )
        
        # Control panel will be created when we send it to the stage channel
        self.control_panel: Optional[ControlPanel] = None
        
        # Track which channel the control panel was sent to for management
        self.panel_channel_id: Optional[int] = None  # Will be set when panel is sent
        
        # Initialize presence handler for rich presence updates
        self.presence_handler: PresenceHandler = PresenceHandler(self)
        
        # Pass presence handler to audio service
        self.audio_service.presence_handler = self.presence_handler
        
        # Configure Discord bot intents for required functionality
        # These intents allow the bot to access specific Discord features
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.guilds = True  # Required for guild/server information
        intents.voice_states = True  # Required for voice channel monitoring
        
        # Initialize the Discord bot with configured settings
        # command_prefix is unused since this is a 24/7 bot, not a command-based bot
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # Disable default help command
        )
        
        logger.tree("🤖 QuranBot Initialized", [
            ("Audio Service", "Ready"),
            ("Command Prefix", "!"),
            ("Intents", "message_content, guilds, voice_states")
        ])
    
    async def on_ready(self) -> None:
        """
        Event handler for bot ready state.
        
        Triggers when bot successfully connects to Discord.
        Sets bot presence and starts 24/7 streaming.
        """
        logger.tree("✅ Bot Ready", [
            ("Bot Name", self.user.name),
            ("Bot ID", str(self.user.id)),
            ("Activity", "Listening to the Holy Quran 📖")
        ])
        
        # Set initial idle presence
        await self.presence_handler.set_idle_presence()
        
        # Begin the 24/7 streaming process
        # This connects to the stage channel and starts continuous playback
        await self.start_streaming()
        
        # Start automatic state saving every 30 seconds
        # This ensures the bot's current state is preserved in case of unexpected shutdown
        await self.persistence.start_auto_save(self.audio_service)
    
    async def start_streaming(self) -> None:
        """
        Start 24/7 audio streaming.
        
        Connects to configured stage channel and begins
        continuous audio playback using the audio service.
        """
        try:
            # Retrieve the target channel from Discord using the configured channel ID
            # This channel ID is set in the config and points to the stage channel
            channel: Optional[Union[discord.StageChannel, discord.VoiceChannel]] = self.get_channel(self.config.stage_channel_id)
            if not channel:
                logger.error_tree("Channel Not Found", ValueError("Channel not found"), [
                    ("Channel ID", str(self.config.stage_channel_id)),
                    ("Action", "Cannot start streaming")
                ])
                return
            
            # Log connection attempt with detailed channel information
            logger.tree("🔌 Connecting to Channel", [
                ("Channel", channel.name),
                ("Channel ID", str(channel.id)),
                ("Type", "Stage Channel" if isinstance(channel, discord.StageChannel) else "Voice Channel")
            ])
            
            # Attempt to connect to the voice/stage channel using the audio service
            # This handles both voice channels and stage channels automatically
            connected: bool = await self.audio_service.connect(channel)
            
            if connected:
                # Send the interactive control panel to the stage channel
                # Stage channels support text messages, allowing users to interact with controls
                await self.send_control_panel(channel)
                
                # Begin the infinite 24/7 playback loop
                # This runs continuously until the bot is stopped
                await self.audio_service.start_continuous_playback()
            else:
                logger.error_tree("Connection Failed", Exception("Failed to connect"), [
                    ("Channel", channel.name if channel else "Unknown"),
                    ("Action", "Streaming aborted")
                ])
            
        except Exception as e:
            logger.error_tree("Streaming Start Failed", e, [
                ("Component", "Streaming service"),
                ("Channel ID", str(self.config.stage_channel_id))
            ])
    
    async def send_control_panel(self, voice_channel: Union[discord.StageChannel, discord.VoiceChannel]) -> None:
        """
        Send control panel to the stage channel itself.
        
        Stage channels in Discord can receive text messages directly,
        so we send the control panel to the stage channel.
        
        Args:
            voice_channel: The voice/stage channel bot is connected to
        """
        try:
            # Handle stage channels which support direct text messaging
            # Stage channels are special Discord channels that allow both voice and text
            if isinstance(voice_channel, discord.StageChannel):
                # Verify bot has permission to send messages in the stage channel
                if voice_channel.permissions_for(voice_channel.guild.me).send_messages:
                    # Clean up any existing messages before sending the control panel
                    # This ensures a clean interface for users
                    if voice_channel.permissions_for(voice_channel.guild.me).manage_messages:
                        try:
                            logger.tree("🧹 Purging Stage Messages", [
                        ("Channel", voice_channel.name),
                        ("Action", "Clearing old messages")
                    ])
                            # Delete up to 100 messages to clean the channel
                            deleted = await voice_channel.purge(limit=100)
                            logger.tree("✅ Messages Purged", [
                        ("Channel", voice_channel.name),
                        ("Messages Deleted", str(len(deleted)))
                    ])
                        except Exception as e:
                            logger.tree("⚠️ Message Purge Failed", [
                                ("Error", str(e)),
                                ("Channel", voice_channel.name),
                                ("Action", "Continuing without purge")
                            ])
                    
                    # Create the interactive control panel with audio service integration
                    self.control_panel = ControlPanel(self.audio_service, self.user)
                    
                    # Send the control panel to the stage channel
                    await self.control_panel.send_panel(voice_channel)
                    
                    # Remember which channel the panel was sent to for future management
                    self.panel_channel_id = voice_channel.id
                    
                    logger.tree("🎛️ Control Panel Sent", [
                        ("Channel", voice_channel.name),
                        ("Type", "Stage Channel"),
                        ("Status", "Active")
                    ])
                else:
                    # Log permission issue but don't fail the entire process
                    logger.tree("⚠️ Insufficient Permissions", [
                        ("Channel", voice_channel.name),
                        ("Missing Permission", "Send Messages"),
                        ("Action", "Control panel not sent")
                    ])
            
            # Regular voice channels don't support text messages
            # Skip control panel for these channels as they can't display it
            else:
                logger.tree("⚠️ Control Panel Skipped", [
                    ("Channel", voice_channel.name),
                    ("Reason", "Voice channels don't support text"),
                    ("Type", "Voice Channel")
                ])
                
        except Exception as e:
            logger.error_tree("Control Panel Send Failed", e, [
                ("Channel", voice_channel.name if voice_channel else "Unknown"),
                ("Channel Type", type(voice_channel).__name__ if voice_channel else "Unknown")
            ])
    
    async def on_voice_state_update(
        self, 
        member: discord.Member, 
        before: discord.VoiceState, 
        after: discord.VoiceState
    ) -> None:
        """
        Handle voice state updates for auto-reconnection.
        
        Args:
            member: The member whose voice state changed
            before: Previous voice state
            after: New voice state
            
        Reconnects bot if it gets disconnected from voice.
        """
        # Monitor voice state changes to detect bot disconnections
        # This ensures automatic reconnection if the bot gets kicked or disconnected
        if member == self.user and before.channel and not after.channel:
            logger.tree("⚠️ Bot Disconnected", [
                ("Previous Channel", before.channel.name if before.channel else "Unknown"),
                ("Action", "Attempting reconnection in 5 seconds")
            ])
            
            # Wait 5 seconds before attempting reconnection
            # This prevents rapid reconnection attempts and respects rate limits
            await asyncio.sleep(5)
            
            # Restart the streaming process to reconnect to the stage channel
            await self.start_streaming()
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the bot.
        
        Stops audio playback, disconnects from voice,
        and closes the Discord connection.
        """
        logger.tree("🔄 Bot Shutdown Initiated", [
            ("Action", "Graceful shutdown"),
            ("Components", "Audio service, Voice connection")
        ])
        
        # Stop the automatic state saving task
        # This prevents saving during shutdown to avoid corruption
        self.persistence.stop_auto_save()
        
        # Save final state before shutdown for immediate restoration on restart
        # This ensures the bot resumes from the exact position when restarted
        if self.audio_service:
            self.persistence.save_state(
                self.audio_service.current_surah,
                self.audio_service.default_reciter
            )
        
        # Stop audio playback and disconnect from voice channel
        # This ensures clean shutdown of the audio service
        self.audio_service.stop()
        await self.audio_service.disconnect()
        
        # Close the Discord bot connection
        # This terminates the bot's connection to Discord servers
        await self.close()
        logger.tree("✅ Bot Shutdown Complete", [
            ("Status", "Success"),
            ("All Connections", "Closed")
        ])