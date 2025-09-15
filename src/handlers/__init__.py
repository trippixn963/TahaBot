"""
QuranBot Handlers Module
=========================

Handler components for specialized Discord functionality.

This module provides handlers that manage specific aspects of Discord interactions,
including rich presence updates and other specialized features.

Handlers:
- PresenceHandler: Discord rich presence management with surah and reciter display

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .presence_handler import PresenceHandler

__all__ = ["PresenceHandler"]
