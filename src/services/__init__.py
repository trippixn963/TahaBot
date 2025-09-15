"""
QuranBot Services Module
=========================

Service layer components for QuranBot functionality.

This module provides specialized services that handle specific aspects of the bot's
operation, including audio streaming, state management, and external integrations.

Services:
- AudioService: 24/7 audio streaming with multi-reciter support and auto-reconnection
- DurationManager: MP3 duration extraction and caching for accurate timing

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .audio.audio_service import AudioService
from .duration_manager import DurationManager, get_duration_manager, get_mp3_duration

__all__ = [
    "AudioService",
    "DurationManager", 
    "get_duration_manager",
    "get_mp3_duration"
]