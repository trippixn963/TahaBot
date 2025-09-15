"""
QuranBot Audio Service Module
==============================

Audio streaming and playback functionality for 24/7 Quran recitation.

This module provides the core audio service that handles continuous streaming
of Quran recitations with support for multiple reciters, automatic reconnection,
and seamless playback management.

Components:
- AudioService: Main audio streaming service with 24/7 operation

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .audio_service import AudioService

__all__ = ["AudioService"]