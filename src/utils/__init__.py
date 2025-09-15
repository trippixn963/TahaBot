"""
QuranBot Utils Module
======================

Utility components and helper functions for QuranBot.

This module provides utility classes and functions that support various
aspects of the bot's functionality, including search capabilities and
version management.

Utilities:
- SurahSearch: Fuzzy search functionality for finding Surahs by name or number
- Version: Centralized version management with semantic versioning

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .search import SurahSearch
from .version import Version, get_version_info, get_version_string

__all__ = [
    "SurahSearch",
    "Version",
    "get_version_info", 
    "get_version_string"
]
