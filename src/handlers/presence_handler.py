"""
QuranBot - Rich Presence Handler
=================================

Manages Discord rich presence updates to show currently playing surah.
Updates bot's status to "Listening to: 📖 Surah Name"

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import discord
from typing import Optional, Dict, Any
from src.core.logger import logger


class PresenceHandler:
    """
    Handles Discord rich presence updates for the bot.
    
    This class manages the bot's Discord presence status to show which surah
    is currently being played. It provides a dynamic "Listening to" status
    that changes with each surah, enhancing user engagement and providing
    real-time information about the bot's activity.
    
    Features:
    - Dynamic surah-specific presence updates
    - Intelligent change detection to avoid spam updates
    - Idle state management when not actively playing
    - Complete presence clearing functionality
    - Comprehensive error handling and logging
    
    The presence updates are visible to all Discord users who can see the bot,
    providing transparency about the current recitation being played.
    """
    
    # Comprehensive mapping of all 114 Quranic surahs
    # Uses Arabic transliteration (not translation) for authentic naming
    # This dictionary maps surah numbers (1-114) to their proper Arabic names
    # Used for rich presence updates to show which surah is currently playing
    SURAH_NAMES: Dict[int, str] = {
        1: "Al-Fatiha",
        2: "Al-Baqarah", 
        3: "Ali 'Imran",
        4: "An-Nisa",
        5: "Al-Ma'idah",
        6: "Al-An'am",
        7: "Al-A'raf",
        8: "Al-Anfal",
        9: "At-Tawbah",
        10: "Yunus",
        11: "Hud",
        12: "Yusuf",
        13: "Ar-Ra'd",
        14: "Ibrahim",
        15: "Al-Hijr",
        16: "An-Nahl",
        17: "Al-Isra",
        18: "Al-Kahf",
        19: "Maryam",
        20: "Ta-Ha",
        21: "Al-Anbiya",
        22: "Al-Hajj",
        23: "Al-Mu'minun",
        24: "An-Nur",
        25: "Al-Furqan",
        26: "Ash-Shu'ara",
        27: "An-Naml",
        28: "Al-Qasas",
        29: "Al-'Ankabut",
        30: "Ar-Rum",
        31: "Luqman",
        32: "As-Sajdah",
        33: "Al-Ahzab",
        34: "Saba",
        35: "Fatir",
        36: "Ya-Sin",
        37: "As-Saffat",
        38: "Sad",
        39: "Az-Zumar",
        40: "Ghafir",
        41: "Fussilat",
        42: "Ash-Shura",
        43: "Az-Zukhruf",
        44: "Ad-Dukhan",
        45: "Al-Jathiyah",
        46: "Al-Ahqaf",
        47: "Muhammad",
        48: "Al-Fath",
        49: "Al-Hujurat",
        50: "Qaf",
        51: "Adh-Dhariyat",
        52: "At-Tur",
        53: "An-Najm",
        54: "Al-Qamar",
        55: "Ar-Rahman",
        56: "Al-Waqi'ah",
        57: "Al-Hadid",
        58: "Al-Mujadila",
        59: "Al-Hashr",
        60: "Al-Mumtahanah",
        61: "As-Saff",
        62: "Al-Jumu'ah",
        63: "Al-Munafiqun",
        64: "At-Taghabun",
        65: "At-Talaq",
        66: "At-Tahrim",
        67: "Al-Mulk",
        68: "Al-Qalam",
        69: "Al-Haqqah",
        70: "Al-Ma'arij",
        71: "Nuh",
        72: "Al-Jinn",
        73: "Al-Muzzammil",
        74: "Al-Muddaththir",
        75: "Al-Qiyamah",
        76: "Al-Insan",
        77: "Al-Mursalat",
        78: "An-Naba",
        79: "An-Nazi'at",
        80: "'Abasa",
        81: "At-Takwir",
        82: "Al-Infitar",
        83: "Al-Mutaffifin",
        84: "Al-Inshiqaq",
        85: "Al-Buruj",
        86: "At-Tariq",
        87: "Al-A'la",
        88: "Al-Ghashiyah",
        89: "Al-Fajr",
        90: "Al-Balad",
        91: "Ash-Shams",
        92: "Al-Layl",
        93: "Ad-Duha",
        94: "Ash-Sharh",
        95: "At-Tin",
        96: "Al-'Alaq",
        97: "Al-Qadr",
        98: "Al-Bayyinah",
        99: "Az-Zalzalah",
        100: "Al-'Adiyat",
        101: "Al-Qari'ah",
        102: "At-Takathur",
        103: "Al-'Asr",
        104: "Al-Humazah",
        105: "Al-Fil",
        106: "Quraysh",
        107: "Al-Ma'un",
        108: "Al-Kawthar",
        109: "Al-Kafirun",
        110: "An-Nasr",
        111: "Al-Masad",
        112: "Al-Ikhlas",
        113: "Al-Falaq",
        114: "An-Nas"
    }
    
    def __init__(self, bot: discord.Client) -> None:
        """
        Initialize the presence handler.
        
        Args:
            bot: Discord bot client instance
        """
        # Store reference to the Discord bot client for presence updates
        self.bot = bot
        
        # Track current surah to avoid unnecessary presence updates
        # This prevents spam updates when the same surah is played
        self.current_surah: Optional[int] = None
        
    async def update_presence(self, surah_number: int, reciter: Optional[str] = None) -> None:
        """
        Update bot's rich presence to show currently playing surah.
        
        This method dynamically updates the bot's Discord presence to display
        which surah is currently being recited and by whom. It intelligently avoids
        unnecessary updates when the same surah is played multiple times.
        
        The presence will show as "Listening to: 📖 [Surah Name]" in Discord,
        with an optional state field showing "Recited by [Reciter Name]" when
        a reciter is provided. This provides users with comprehensive real-time
        information about the current recitation.
        
        Args:
            surah_number: Number of the surah being played (1-114)
            reciter: Name of the reciter (optional) - displayed in state field
            
        Raises:
            Exception: If Discord API call fails, logged but not re-raised
        """
        try:
            # Only update if surah changed to avoid unnecessary API calls
            # This prevents spam updates when the same surah is replayed
            if self.current_surah == surah_number:
                return
                
            # Update the tracked current surah for future comparison
            self.current_surah = surah_number
            
            # Get the Arabic transliteration name for the surah
            # Fallback to generic "Surah X" if not found in the mapping
            surah_name = self.SURAH_NAMES.get(surah_number, f"Surah {surah_number}")
            
            # Create Discord activity with listening type and surah name
            # Using "listening" type shows "Listening to: 📖 Surah Name" in Discord
            # The state field can optionally show the reciter's name for additional context
            activity_kwargs = {
                "type": discord.ActivityType.listening,
                "name": f"📖 {surah_name}"
            }
            
            # Add reciter information in state field if provided
            # This enhances the presence by showing who is reciting the current surah
            if reciter:
                activity_kwargs["state"] = f"Recited by {reciter}"
            
            # Create the Discord Activity object with the configured parameters
            activity = discord.Activity(**activity_kwargs)
            
            # Update the bot's rich presence with the new activity
            # This will be visible to all users who can see the bot
            await self.bot.change_presence(activity=activity)
            
            presence_info = [
                ("Surah", f"{surah_number} - {surah_name}"),
                ("Status", f"Listening to 📖 {surah_name}"),
                ("Type", "Activity.listening")
            ]
            
            if reciter:
                presence_info.append(("Reciter", reciter))
            
            logger.tree("🎵 Rich Presence Updated", presence_info)
            
        except Exception as e:
            logger.error_tree("Failed to update rich presence", e, [
                ("Surah Number", str(surah_number)),
                ("Error Type", type(e).__name__)
            ])
    
    async def clear_presence(self) -> None:
        """
        Clear the bot's rich presence status.
        
        This method removes the bot's current activity status from Discord,
        effectively clearing the "Listening to" display. This is useful
        when the bot stops playing or during shutdown procedures.
        
        After clearing, the bot will appear without any activity status
        until a new presence is set via update_presence() or set_idle_presence().
        
        Raises:
            Exception: If Discord API call fails, logged but not re-raised
        """
        try:
            # Clear the bot's rich presence by setting activity to None
            # This removes the "Listening to" status from the bot's profile
            await self.bot.change_presence(activity=None)
            
            # Reset the tracked surah to allow future updates
            self.current_surah = None
            
            logger.tree("🔄 Rich Presence Cleared", [
                ("Status", "None"),
                ("Action", "Presence removed")
            ])
            
        except Exception as e:
            logger.error_tree("Failed to clear rich presence", e, [
                ("Error Type", type(e).__name__)
            ])
    
    async def set_idle_presence(self) -> None:
        """
        Set presence to idle state when not playing.
        
        This method sets a generic idle presence that indicates the bot
        is available for Quran streaming but not currently playing a specific
        surah. It shows "Listening to: 📖 Quran 24/7" as the status.
        
        This is typically used during bot startup, when no surah is actively
        being played, or when the bot is in a waiting state.
        
        Raises:
            Exception: If Discord API call fails, logged but not re-raised
        """
        try:
            # Create a generic idle presence when not actively playing a specific surah
            # This shows "Listening to 📖 Quran 24/7" as a general status
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="📖 Quran 24/7"
            )
            
            # Update the bot's presence with the idle status
            await self.bot.change_presence(activity=activity)
            
            # Reset tracked surah since we're in idle state
            self.current_surah = None
            
            logger.tree("⏸️ Rich Presence Set to Idle", [
                ("Status", "Listening to 📖 Quran 24/7"),
                ("State", "Idle")
            ])
            
        except Exception as e:
            logger.error_tree("Failed to set idle presence", e, [
                ("Error Type", type(e).__name__)
            ])