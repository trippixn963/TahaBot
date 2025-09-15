"""
QuranBot - Professional Discord Audio Bot
==========================================

Advanced 24/7 Quran streaming bot for Discord with comprehensive features
including multi-reciter support, stage channel integration, and robust
error handling for continuous operation.

Features:
- 24/7 continuous audio streaming
- Multiple reciter support with Arabic names
- Stage channel integration with speaker management
- Auto-reconnection on network interruptions
- Beautiful control panel with progress tracking
- Professional logging system with EST timezone
- Comprehensive error handling and recovery

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v2.0.0
"""

from .bot import TahaBot
from .core import Config, get_config, logger
from .services import AudioService, DurationManager, get_mp3_duration

__version__ = "2.0.0"

__all__ = [
    "TahaBot",
    "Config", 
    "get_config",
    "logger",
    "AudioService",
    "DurationManager",
    "get_mp3_duration",
    "__version__",
]