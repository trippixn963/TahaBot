"""
QuranBot UI Module
===================

User interface components for Discord interactions and control panels.

This module provides the interactive user interface components that allow
Discord users to control the bot's audio playback, search for surahs, and
manage reciter selection through beautiful Discord embeds and buttons.

Components:
- ControlPanel: Interactive Discord UI with playback controls and surah search

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .control_panel import ControlPanel

__all__ = ["ControlPanel"]