"""
QuranBot Data Module
=====================

Data components and mappings for QuranBot.

This module provides data structures and mappings that contain
authoritative information about Quranic Surahs and related data.

Data Components:
- SURAH_NAMES: Comprehensive mapping of all 114 Surahs with Arabic and English names
- surah_mapper.json: Extended Surah data with translations and metadata

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .surahs import SURAH_NAMES

__all__ = ["SURAH_NAMES"]
