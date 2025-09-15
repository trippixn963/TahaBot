"""
Control Panel UI for QuranBot
=============================

Beautiful Discord embed control panel for managing Quran playback.

Features:
- Surah names in Arabic and English
- Progress bar with time display
- Multiple control buttons
- Reciter selection with Arabic names
- Loop and shuffle controls

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import discord
from discord import Embed, ButtonStyle, SelectOption
from discord.ui import Button, View, Select, Modal, TextInput
from typing import Optional, List, Dict, Any
import asyncio
import time
from datetime import timedelta

from src.core.logger import logger
from src.data.surahs import SURAH_NAMES
from src.services.duration_manager import get_mp3_duration
from src.utils.search import SurahSearch
from src.services.audio.audio_service import AudioService


class ControlPanel(View):
    """
    Discord UI View for audio playback control.
    
    Beautiful interface with progress bars, Arabic text,
    and comprehensive playback controls.
    
    Attributes:
        audio_service: Reference to the audio service
        message: The Discord message containing this panel
        loop_mode: Current loop mode (off/single/all)
        shuffle_mode: Whether shuffle is enabled
    """
    
    def __init__(self, audio_service: AudioService, bot_user: discord.ClientUser) -> None:
        """
        Initialize the control panel.
        
        Args:
            audio_service: The audio service to control
            bot_user: The bot user object for avatar
        """
        # Initialize Discord View with no timeout for persistent panel
        # This ensures the control panel remains interactive indefinitely
        super().__init__(timeout=None)
        
        # Store reference to audio service for controlling playback
        self.audio_service: AudioService = audio_service
        
        # Store bot user reference for avatar display in embeds
        self.bot_user: discord.ClientUser = bot_user
        
        # Message reference will be set when panel is sent to Discord
        self.message: Optional[discord.Message] = None
        
        # Loop modes: "off" (no loop), "single" (loop current surah), "all" (loop all surahs)
        self.loop_mode: str = "off"
        
        # Shuffle mode for random surah order (currently not implemented)
        self.shuffle_mode: bool = False
        
        # Progress tracking for visual progress bar display
        self.current_progress: float = 0
        
        # Duration will be updated based on current surah
        self.total_duration: float = 180
        self.update_duration_for_surah()
        
        # Track when current playback started for progress calculation
        self.start_time: float = time.time()
        
        # Background task for updating progress bar in real-time
        self.progress_task: Optional[asyncio.Task] = None
        
        # Track last surah to detect surah changes for progress reset
        # Initialize with current displayed surah
        self._last_surah: int = self.audio_service.current_status.get("current_surah", 1)
        
        # User interaction tracking for community engagement
        # These fields store the last user who interacted with the control panel
        # and what action they performed, displayed in the status embed
        self.last_interaction_user: Optional[str] = None
        self.last_interaction_action: Optional[str] = None
    
    def get_reciter_arabic(self, reciter: str) -> str:
        """
        Get Arabic name for reciter.
        
        Args:
            reciter: English reciter name
            
        Returns:
            Arabic reciter name
        """
        try:
            reciter_arabic_names: Dict[str, str] = {
                "Saad Al Ghamdi": "سعد الغامدي",
                "Abdul Basit Abdul Samad": "عبد الباسط عبد الصمد",
                "Maher Al Muaiqly": "ماهر المعيقلي",
                "Muhammad Al Luhaidan": "محمد اللحيدان",
                "Rashid Al Afasy": "راشد العفاسي",
                "Yasser Al Dosari": "ياسر الدوسري"
            }
            return reciter_arabic_names.get(reciter, reciter)
        except Exception as e:
            logger.error_tree("Failed to get Arabic reciter name", e, [
                ("Reciter", reciter)
            ])
            return reciter
    
    def update_duration_for_surah(self, surah_number: int = None) -> None:
        """Update the total duration based on the current surah and reciter."""
        # Use provided surah number or get current
        if surah_number is None:
            # Get the displayed surah number (what the user sees in the control panel)
            # The control panel shows current_surah, so use that for duration
            surah_number = self.audio_service.current_surah
        
        # Get current reciter
        reciter = self.audio_service.current_status.get("reciter", self.audio_service.default_reciter)
        
        # Get the actual MP3 duration or fall back to estimate
        self.total_duration = get_mp3_duration(surah_number, reciter)
    
    def format_time(self, seconds: float) -> str:
        """
        Format seconds to MM:SS or HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        try:
            # Handle negative time values gracefully
            if seconds < 0:
                return "00:00"
            
            # Convert seconds to hours, minutes, and seconds
            # Use integer division to get whole numbers only
            hours: int = int(seconds // 3600)
            minutes: int = int((seconds % 3600) // 60)
            secs: int = int(seconds % 60)
            
            # Format time based on duration
            # Show hours only if duration is over 1 hour
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                # Standard MM:SS format for shorter durations
                return f"{minutes:02d}:{secs:02d}"
        except Exception as e:
            logger.error_tree("Failed to format time", e, [
                ("Seconds", str(seconds))
            ])
            return "00:00"
    
    def create_status_embed(self) -> Embed:
        """
        Create a beautiful status embed with current playback information.
        
        Returns:
            Discord embed with enhanced playback status
        """
        try:
            # Get current playback status from audio service
            status: Dict[str, Any] = self.audio_service.current_status
            current_surah: int = status.get("current_surah", 1)
            
            # Retrieve surah information including Arabic and English names
            # Fallback to default values if surah not found in mapping
            surah_info: Dict[str, str] = SURAH_NAMES.get(current_surah, {
                "arabic": "سورة",
                "english": f"Surah {current_surah}",
                "translation": ""
            })
            
            # Create Discord embed with dark theme (Discord dark mode color)
            # RGB(47, 49, 54) matches Discord's dark theme background
            embed: Embed = Embed(color=discord.Color.from_rgb(47, 49, 54))
            
            # Add bot avatar as thumbnail for visual appeal
            # This makes the embed feel more personal and branded
            if self.bot_user and self.bot_user.avatar:
                embed.set_thumbnail(url=self.bot_user.avatar.url)
            
            # Surah field in black box
            embed.add_field(
                name="Surah:",
                value=f"```\n{surah_info['english']} - {surah_info['arabic']}\n```",
                inline=False
            )
            
            # Reciter field with Arabic name in black box
            reciter: str = status.get("reciter", "Unknown")
            reciter_arabic: str = self.get_reciter_arabic(reciter)
            embed.add_field(
                name="Reciter:",
                value=f"```\n{reciter} - {reciter_arabic}\n```",
                inline=False
            )
            
            # Calculate current progress based on start time
            if self.start_time and self.audio_service.current_status.get("playing"):
                elapsed: float = time.time() - self.start_time
                self.current_progress = min(elapsed, self.total_duration)
            
            # Progress field with time display in black box
            time_display: str = self.format_time(self.current_progress) + " / " + self.format_time(self.total_duration)
            embed.add_field(
                name="Progress:",
                value=f"```\n{time_display}\n```",
                inline=False
            )
            
            # Add last interaction field for community transparency
            # This shows the most recent user action for engagement tracking
            if self.last_interaction_user and self.last_interaction_action:
                embed.add_field(
                    name="Last Action:",
                    value=f"{self.last_interaction_user} {self.last_interaction_action}",
                    inline=False
                )
            
            return embed
            
        except Exception as e:
            logger.error_tree("Failed to create status embed", e, [
                ("Current Surah", str(self.audio_service.current_status.get("current_surah", "Unknown")))
            ])
            # Return basic embed on error
            return Embed(
                title="❌ Error",
                description="Failed to create status display",
                color=discord.Color.red()
            )
    
    async def send_panel(self, channel: discord.TextChannel) -> discord.Message:
        """
        Send the control panel to a Discord channel.
        
        Args:
            channel: The channel to send the panel to
            
        Returns:
            The sent message containing the panel
        """
        try:
            # Clear existing items and rebuild
            self.clear_items()
            
            # Add Reciter selector (Row 0)
            reciters: List[str] = self.audio_service.get_available_reciters()
            if reciters:
                self.add_item(ReciterSelect(reciters, self.audio_service))
            
            # Add Search button (Row 1)
            self.add_item(SearchButton(self.audio_service, self))
            
            # Add control buttons (Row 2)
            self.add_item(PreviousButton(self.audio_service))
            self.add_item(ShuffleButton(self))
            self.add_item(LoopButton(self))
            self.add_item(NextButton(self.audio_service))
            
            # Update duration for current surah
            current_surah = self.audio_service.current_status.get("current_surah", 1)
            self.update_duration_for_surah(current_surah)
            
            # Send panel
            embed: Embed = self.create_status_embed()
            self.message = await channel.send(embed=embed, view=self)
            
            # Set start time for progress tracking
            self.start_time = time.time()
            
            # Start progress update task
            if not self.progress_task:
                self.progress_task = asyncio.create_task(self.update_progress_loop())
            
            logger.tree("🎛️ Control Panel Deployed", [
            ("Channel", channel.name),
            ("Channel ID", str(channel.id)),
            ("Components", "Reciter selector, Search, Controls")
        ])
            return self.message
            
        except Exception as e:
            logger.error_tree("Failed to send control panel", e, [
                ("Channel", channel.name if channel else "Unknown"),
                ("Channel ID", str(channel.id) if channel else "Unknown")
            ])
            raise
    
    async def update_progress_loop(self) -> None:
        """
        Periodically update the progress display every 5 seconds.
        """
        while True:
            try:
                # Wait 5 seconds between updates
                await asyncio.sleep(5)
                
                # Update the panel with new progress
                if self.message and self.audio_service.current_status.get("playing"):
                    await self.update_panel()
                    
                # Reset progress and update duration when track changes
                current_surah: int = self.audio_service.current_status.get("current_surah", 1)
                
                if self._last_surah and self._last_surah != current_surah:
                    # Update duration for the displayed surah (current_surah)
                    self.update_duration_for_surah(current_surah)
                    # Reset progress timer
                    self.start_time = time.time()
                    self.current_progress = 0
                    # Log the surah change
                    logger.tree("🔄 Control Panel Detected Surah Change", [
                        ("Previous Surah", str(self._last_surah)),
                        ("New Surah", str(current_surah)),
                        ("Duration", f"{self.total_duration} seconds")
                    ])
                self._last_surah = current_surah
                
            except Exception as e:
                logger.error_tree("Progress update error", e, [
                    ("Update Interval", "5 seconds"),
                    ("Panel Status", "Active" if self.message else "Inactive")
                ])
                await asyncio.sleep(5)
    
    async def update_panel(self) -> None:
        """
        Update the existing control panel message.
        
        Updates the embed with current status information.
        """
        if self.message:
            try:
                await self.message.edit(
                    embed=self.create_status_embed(),
                    view=self
                )
            except discord.NotFound:
                logger.tree("⚠️ Control Panel Message Not Found", [
                    ("Action", "Message reference cleared"),
                    ("Reason", "Discord message was deleted")
                ])
                self.message = None
            except Exception as e:
                logger.error_tree("Failed to update control panel", e, [
                    ("Panel Message", "Present" if self.message else "Missing"),
                    ("Update Type", "Embed and View refresh")
                ])


# Search Modal
class SurahSearchModal(Modal):
    """Modal for searching Surahs."""
    
    def __init__(self, audio_service: AudioService, control_panel: ControlPanel) -> None:
        super().__init__(title="Search for a Surah")
        self.audio_service: AudioService = audio_service
        self.control_panel: ControlPanel = control_panel
        self.searcher: SurahSearch = SurahSearch()
        
        # Add search input field
        self.search_input: TextInput = TextInput(
            label="Enter Surah name or number",
            placeholder="e.g. '2', 'Baqarah', 'البقرة', 'The Cow'",
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=50
        )
        self.add_item(self.search_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle search submission."""
        query: str = self.search_input.value.strip()
        logger.tree("🔍 Search Request", [
            ("User", str(interaction.user)),
            ("Query", query),
            ("Timestamp", interaction.created_at.strftime("%H:%M:%S") if hasattr(interaction, 'created_at') else "Now")
        ])
        
        # Search for Surahs
        results: List[Dict[str, Any]] = self.searcher.search(query, limit=5)
        
        if not results:
            logger.tree("⚠️ Search Query Returned No Results", [
                ("User", str(interaction.user)),
                ("Query", query),
                ("Search Engine", "SurahSearch"),
                ("Limit", "5 results")
            ])
            embed = discord.Embed(
                title="❌ No Results Found",
                description=f"No Surahs found matching **'{query}'**",
                color=discord.Color.red()
            )
            # Set footer with developer credit and avatar
            try:
                developer = await interaction.client.fetch_user(interaction.user.id)  # Use interaction user for now
                developer_avatar = developer.avatar.url if developer and developer.avatar else None
            except:
                developer_avatar = None
            embed.set_footer(text="Developed By: حَـــــنَّـــــا", icon_url=developer_avatar)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return
        
        # If single exact match, play it directly
        if len(results) == 1 and results[0]['score'] >= 0.95:
            surah: Dict[str, Any] = results[0]
            # Update audio service to play this surah
            self.audio_service.current_surah = surah['number']
            
            # Update presence for the new surah
            self.audio_service.update_presence_for_current()
            
            # Stop current playback and immediately play the selected surah
            if self.audio_service.voice_client:
                if self.audio_service.voice_client.is_playing():
                    self.audio_service.voice_client.stop()
                # Small delay to ensure stop completes
                await asyncio.sleep(0.1)
                # Explicitly play the selected surah
                await self.audio_service.play_next()
            
            # Reset progress timer
            self.control_panel.start_time = time.time()
            self.control_panel.current_progress = 0
            
            # Update control panel
            if self.control_panel:
                self.control_panel.last_interaction_user = f"<@{interaction.user.id}>"
                self.control_panel.last_interaction_action = f"selected Surah {surah['number']}"
                await self.control_panel.update_panel()
            
            embed = discord.Embed(
                title="✅ Now Playing",
                description=f"**{surah['number']}. {surah['english']}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Arabic Name", value=surah['arabic'], inline=True)
            embed.add_field(name="Translation", value=surah['translation'], inline=False)
            # Set footer with developer credit and avatar
            try:
                developer = await interaction.client.fetch_user(interaction.user.id)  # Use interaction user for now
                developer_avatar = developer.avatar.url if developer and developer.avatar else None
            except:
                developer_avatar = None
            embed.set_footer(text="Developed By: حَـــــنَّـــــا", icon_url=developer_avatar)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            logger.tree("✅ Search Result Selected", [
                ("User", str(interaction.user)),
                ("Surah Number", str(surah['number'])),
                ("Surah Name", surah['english']),
                ("Action", "Direct play from search")
            ])
            
        else:
            # Show search results with selection buttons
            embed: Embed = Embed(
                title="🔍 Search Results",
                description=f"Found {len(results)} Surah(s) matching '{query}':",
                color=discord.Color.green()
            )
            
            for i, surah in enumerate(results[:5], 1):
                embed.add_field(
                    name=f"{i}. {self.searcher.format_result(surah)}",
                    value=f"*{surah['translation']}*",
                    inline=False
                )
            
            # Create selection view
            view: SurahSelectionView = SurahSelectionView(results[:5], self.audio_service, self.control_panel)
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )


# Custom button for surah selection
class SurahSelectButton(Button):
    """Button for selecting a specific surah."""
    
    def __init__(self, surah: Dict[str, Any], audio_service: AudioService, control_panel: ControlPanel, number: int) -> None:
        super().__init__(
            label=f"{number}. {surah['english']}",
            emoji=surah['emoji'],
            style=ButtonStyle.primary
        )
        self.surah = surah
        self.audio_service = audio_service
        self.control_panel = control_panel
    
    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            logger.tree("🎯 Surah Selection Initiated", [
                ("User", str(interaction.user)),
                ("Surah Number", str(self.surah['number'])),
                ("Surah Name", self.surah.get('english', 'Unknown')),
                ("Action", "Button callback triggered")
            ])
            
            # Check if user is in stage channel
            if self.audio_service and self.audio_service.voice_client and self.audio_service.voice_client.channel:
                stage_channel = self.audio_service.voice_client.channel
                # Check if user is in the members list
                member = interaction.guild.get_member(interaction.user.id)
                if member and member.voice and member.voice.channel != stage_channel:
                    logger.tree("🚫 Access Denied - Surah Selection", [
                        ("User", str(interaction.user)),
                        ("Action Attempted", "Surah selection"),
                        ("Reason", "User not in stage channel"),
                        ("Required", "Stage channel membership")
                    ])
                    embed = discord.Embed(
                        title="❌ Access Denied",
                        description="You must be in the stage channel to select a surah!",
                        color=discord.Color.red()
                    )
                    embed.set_footer(
                        text="QuranBot • Join the stage to control playback",
                        icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    return
        except Exception as e:
            logger.error_tree("Permission check failed", e, [
                ("Check Type", "Stage channel membership"),
                ("User", str(interaction.user)),
                ("Action", "Surah selection")
            ])
        
        try:
            # First respond to the interaction
            embed = discord.Embed(
                title="✅ Surah Selected",
                description=f"**{self.surah['number']}. {self.surah['english']}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Arabic Name", value=self.surah['arabic'], inline=True)
            embed.add_field(name="Translation", value=self.surah['translation'], inline=False)
            # Set footer with developer credit and avatar
            try:
                developer = await interaction.client.fetch_user(interaction.user.id)  # Use interaction user for now
                developer_avatar = developer.avatar.url if developer and developer.avatar else None
            except:
                developer_avatar = None
            embed.set_footer(text="Developed By: حَـــــنَّـــــا", icon_url=developer_avatar)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            logger.tree("✅ Surah Selected Successfully", [
                ("User", str(interaction.user)),
                ("Surah Number", str(self.surah['number'])),
                ("Surah Name", self.surah['english']),
                ("Source", "Selection button")
            ])
            
            # Update audio service to play this surah
            self.audio_service.current_surah = self.surah['number']
            
            # Update presence for the new surah
            self.audio_service.update_presence_for_current()
            
            # Stop current playback and immediately play the selected surah
            if self.audio_service.voice_client:
                if self.audio_service.voice_client.is_playing():
                    self.audio_service.voice_client.stop()
                # Small delay to ensure stop completes
                await asyncio.sleep(0.1)
                # Explicitly play the selected surah
                await self.audio_service.play_next()
            
            # Update duration for the selected surah
            self.control_panel.update_duration_for_surah(self.surah['number'])
            # Reset progress timer
            self.control_panel.start_time = time.time()
            self.control_panel.current_progress = 0
            
            # Update control panel separately (not part of interaction response)
            if self.control_panel:
                self.control_panel.last_interaction_user = f"<@{interaction.user.id}>"
                self.control_panel.last_interaction_action = f"selected Surah {self.surah['number']}"
                await self.control_panel.update_panel()
            
        except Exception as e:
            logger.error_tree("Surah selection callback failed", e, [
                ("User", str(interaction.user)),
                ("Surah Number", str(self.surah.get('number', 'Unknown'))),
                ("Surah Name", self.surah.get('english', 'Unknown')),
                ("Callback Stage", "Post-permission check")
            ])
            # If we haven't responded yet, send an error response
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while selecting the surah.",
                    ephemeral=True
                )


# Selection View for search results
class SurahSelectionView(View):
    """View for selecting from search results."""
    
    def __init__(self, results: List[Dict[str, Any]], audio_service: AudioService, control_panel: ControlPanel) -> None:
        super().__init__(timeout=60)
        self.audio_service: AudioService = audio_service
        self.control_panel: ControlPanel = control_panel
        
        # Add button for each result
        for i, surah in enumerate(results[:5], 1):
            button = SurahSelectButton(surah, audio_service, control_panel, i)
            self.add_item(button)


# Base class for buttons with stage permission check
class StageProtectedButton(Button):
    """Base button class with stage channel permission check."""
    
    async def _check_stage_permission(self, interaction: discord.Interaction) -> bool:
        """Check if user is in the stage channel."""
        # Get audio service from the button
        audio_service = None
        if hasattr(self, 'audio_service'):
            audio_service = self.audio_service
        elif hasattr(self, 'panel') and hasattr(self.panel, 'audio_service'):
            audio_service = self.panel.audio_service
        elif hasattr(self, 'control_panel') and hasattr(self.control_panel, 'audio_service'):
            audio_service = self.control_panel.audio_service
        
        if audio_service and audio_service.voice_client and audio_service.voice_client.channel:
            stage_channel = audio_service.voice_client.channel
            if interaction.user not in stage_channel.members:
                logger.tree("🚫 Access Denied - Control Panel Button", [
                    ("User", str(interaction.user)),
                    ("Action Attempted", "Control panel button interaction"),
                    ("Reason", "User not in stage channel"),
                    ("Required", "Stage channel membership")
                ])
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description="You must be in the stage channel to use the control panel!",
                    color=discord.Color.red()
                )
                # Set footer with developer credit and avatar
                try:
                    developer = await interaction.client.fetch_user(interaction.user.id)  # Use interaction user for now
                    developer_avatar = developer.avatar.url if developer and developer.avatar else None
                except:
                    developer_avatar = None
                embed.set_footer(text="Developed By: حَـــــنَّـــــا", icon_url=developer_avatar)
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return False
        return True


# Control Buttons
class SearchButton(StageProtectedButton):
    """Search button for finding surahs."""
    def __init__(self, audio_service: AudioService, control_panel: ControlPanel) -> None:
        super().__init__(label="Search", emoji="🔍", style=ButtonStyle.secondary, row=1)
        self.audio_service: AudioService = audio_service
        self.control_panel: ControlPanel = control_panel
    
    async def callback(self, interaction: discord.Interaction) -> None:
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        logger.tree("🔍 Search Button Activated", [
            ("User", str(interaction.user)),
            ("Action", "Search modal opening"),
            ("Component", "Search button"),
            ("Row", "1")
        ])
        # Update last interaction
        if self.control_panel:
            self.control_panel.last_interaction_user = f"<@{interaction.user.id}>"
            self.control_panel.last_interaction_action = "opened search"
        modal: SurahSearchModal = SurahSearchModal(self.audio_service, self.control_panel)
        await interaction.response.send_modal(modal)


class PreviousButton(StageProtectedButton):
    """Previous surah button."""
    def __init__(self, audio_service: AudioService) -> None:
        super().__init__(label="Previous", emoji="⏮️", style=ButtonStyle.primary, row=2)
        self.audio_service: AudioService = audio_service
    
    async def callback(self, interaction: discord.Interaction) -> None:
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        # Go to previous surah
        current: int = self.audio_service.current_surah
        new_surah: int = current - 1 if current > 1 else 114
        self.audio_service.current_surah = new_surah
        
        # Update presence for the new surah
        self.audio_service.update_presence_for_current()
        logger.tree("⏮️ Previous Surah Navigation", [
            ("User", str(interaction.user)),
            ("Previous Surah", str(current)),
            ("New Surah", str(new_surah)),
            ("Direction", "Backward")
        ])
        self.audio_service.skip()
        
        view: Optional[View] = self.view
        if isinstance(view, ControlPanel):
            # Update duration for the new surah
            view.update_duration_for_surah(new_surah)
            # Reset progress timer
            view.start_time = time.time()
            view.current_progress = 0
            # Update last interaction
            view.last_interaction_user = f"<@{interaction.user.id}>"
            view.last_interaction_action = "went to previous surah"
            await interaction.response.edit_message(
                embed=view.create_status_embed(),
                view=view
            )


class ShuffleButton(StageProtectedButton):
    """Shuffle mode toggle button."""
    def __init__(self, panel: ControlPanel) -> None:
        self.panel: ControlPanel = panel
        self.audio_service = panel.audio_service  # For permission check
        emoji: str = "🔀"
        style: ButtonStyle = ButtonStyle.secondary if not panel.shuffle_mode else ButtonStyle.success
        super().__init__(label="Shuffle", emoji=emoji, style=style, row=2)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        # Toggle shuffle mode
        self.panel.shuffle_mode = not self.panel.shuffle_mode
        self.style = ButtonStyle.success if self.panel.shuffle_mode else ButtonStyle.secondary
        status: str = "enabled" if self.panel.shuffle_mode else "disabled"
        logger.tree(f"🔀 Shuffle Mode {status.title()}", [
            ("User", str(interaction.user)),
            ("Previous State", "Disabled" if status == "enabled" else "Enabled"),
            ("New State", status.title()),
            ("Button Style", "Success" if status == "enabled" else "Secondary")
        ])
        
        view: Optional[View] = self.view
        if isinstance(view, ControlPanel):
            # Update last interaction
            view.last_interaction_user = f"<@{interaction.user.id}>"
            view.last_interaction_action = f"{status} shuffle mode"
            await interaction.response.edit_message(
                embed=view.create_status_embed(),
                view=view
            )


class LoopButton(StageProtectedButton):
    """Loop mode toggle button."""
    def __init__(self, panel: ControlPanel) -> None:
        self.panel: ControlPanel = panel
        self.audio_service = panel.audio_service  # For permission check
        if panel.loop_mode == "off":
            label: str = "Loop"
            emoji: str = "🔁"
            style: ButtonStyle = ButtonStyle.secondary
        elif panel.loop_mode == "single":
            label: str = "Loop 1"
            emoji: str = "🔂"
            style: ButtonStyle = ButtonStyle.success
        else:  # all
            label: str = "Loop All"
            emoji: str = "🔁"
            style: ButtonStyle = ButtonStyle.success
        
        super().__init__(label=label, emoji=emoji, style=style, row=2)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        # Cycle through loop modes
        if self.panel.loop_mode == "off":
            self.panel.loop_mode = "single"
            self.label = "Loop 1"
            self.emoji = "🔂"
        elif self.panel.loop_mode == "single":
            self.panel.loop_mode = "all"
            self.label = "Loop All"
            self.emoji = "🔁"
        else:
            self.panel.loop_mode = "off"
            self.label = "Loop"
            self.emoji = "🔁"
        
        logger.tree("🔁 Loop Mode Changed", [
            ("User", str(interaction.user)),
            ("New Mode", self.panel.loop_mode.title()),
            ("Button Label", self.label),
            ("Button Emoji", self.emoji)
        ])
        
        self.style = ButtonStyle.success if self.panel.loop_mode != "off" else ButtonStyle.secondary
        
        view: Optional[View] = self.view
        if isinstance(view, ControlPanel):
            # Update last interaction
            view.last_interaction_user = f"<@{interaction.user.id}>"
            view.last_interaction_action = f"set loop mode to {self.panel.loop_mode}"
            await interaction.response.edit_message(
                embed=view.create_status_embed(),
                view=view
            )


class NextButton(StageProtectedButton):
    """Next surah button."""
    def __init__(self, audio_service: AudioService) -> None:
        super().__init__(label="Next", emoji="⏭️", style=ButtonStyle.primary, row=2)
        self.audio_service: AudioService = audio_service
    
    async def callback(self, interaction: discord.Interaction) -> None:
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        # Skip to next surah
        current: int = self.audio_service.current_surah
        # Calculate next surah (wraps from 114 to 1)
        next_surah: int = current + 1 if current < 114 else 1
        logger.tree("⏭️ Next Surah Navigation", [
            ("User", str(interaction.user)),
            ("Current Surah", str(current)),
            ("Next Surah", str(next_surah)),
            ("Action", "Skip to next"),
            ("Direction", "Forward")
        ])
        self.audio_service.skip()
        
        view: Optional[View] = self.view
        if isinstance(view, ControlPanel):
            # Update duration for the next surah
            view.update_duration_for_surah(next_surah)
            # Reset progress timer
            view.start_time = time.time()
            view.current_progress = 0
            # Update last interaction
            view.last_interaction_user = f"<@{interaction.user.id}>"
            view.last_interaction_action = "skipped to next surah"
            await interaction.response.edit_message(
                embed=view.create_status_embed(),
                view=view
            )


class StageProtectedSelect(Select):
    """Base select class with stage channel permission check."""
    
    async def _check_stage_permission(self, interaction: discord.Interaction) -> bool:
        """Check if user is in the stage channel."""
        # Get audio service from the select
        audio_service = None
        if hasattr(self, 'audio_service'):
            audio_service = self.audio_service
        
        if audio_service and audio_service.voice_client and audio_service.voice_client.channel:
            stage_channel = audio_service.voice_client.channel
            if interaction.user not in stage_channel.members:
                logger.tree("🚫 Access Denied - Control Panel Select", [
                    ("User", str(interaction.user)),
                    ("Action Attempted", "Control panel select interaction"),
                    ("Reason", "User not in stage channel"),
                    ("Required", "Stage channel membership")
                ])
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description="You must be in the stage channel to use the control panel!",
                    color=discord.Color.red()
                )
                # Set footer with developer credit and avatar
                try:
                    developer = await interaction.client.fetch_user(interaction.user.id)  # Use interaction user for now
                    developer_avatar = developer.avatar.url if developer and developer.avatar else None
                except:
                    developer_avatar = None
                embed.set_footer(text="Developed By: حَـــــنَّـــــا", icon_url=developer_avatar)
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return False
        return True


class ReciterSelect(StageProtectedSelect):
    """Dropdown for selecting reciters."""
    
    def __init__(self, reciters: List[str], audio_service: AudioService) -> None:
        """Initialize reciter selector."""
        # Map English to Arabic names
        reciter_arabic: Dict[str, str] = {
            "Saad Al Ghamdi": "سعد الغامدي",
            "Abdul Basit Abdul Samad": "عبد الباسط عبد الصمد",
            "Maher Al Muaiqly": "ماهر المعيقلي",
            "Muhammad Al Luhaidan": "محمد اللحيدان",
            "Rashid Al Afasy": "راشد العفاسي",
            "Yasser Al Dosari": "ياسر الدوسري"
        }
        
        # Create options from reciter list with Arabic descriptions
        options: List[SelectOption] = [
            SelectOption(
                label=reciter,
                value=reciter,
                description=reciter_arabic.get(reciter, reciter),
                emoji="🎙️"
            )
            for reciter in reciters[:25]
        ]
        
        super().__init__(
            placeholder="Select a Reciter...",
            options=options,
            row=0
        )
        self.audio_service: AudioService = audio_service
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle reciter selection."""
        # Check stage permission
        if not await self._check_stage_permission(interaction):
            return
        
        selected_reciter: str = self.values[0]
        
        # Change reciter
        success: bool = self.audio_service.set_reciter(selected_reciter)
        
        if success:
            view: Optional[View] = self.view
            if isinstance(view, ControlPanel):
                # Update duration for current surah with new reciter
                view.update_duration_for_surah()
                # Update last interaction
                view.last_interaction_user = f"<@{interaction.user.id}>"
                view.last_interaction_action = f"changed reciter to {selected_reciter}"
                await interaction.response.edit_message(
                    embed=view.create_status_embed(),
                    view=view
                )
            logger.tree("✅ Reciter Changed Successfully", [
                ("User", str(interaction.user)),
                ("New Reciter", selected_reciter),
                ("Action", "Reciter selection from dropdown")
            ])
        else:
            logger.error_tree("Failed to change reciter", None, [
                ("User", str(interaction.user)),
                ("Requested Reciter", selected_reciter),
                ("Action", "Reciter selection"),
                ("Success", "False")
            ])
            await interaction.response.send_message(
                f"Failed to change reciter",
                ephemeral=True
            )