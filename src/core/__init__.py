"""
QuranBot Core Module
====================

Core functionality and essential components for QuranBot.

This module provides the foundational components that are used throughout
the bot system, including configuration management and structured logging.

Components:
- Config: Configuration management with environment variable support
- get_config: Configuration factory function with validation
- logger: Structured logging system with tree-style output and EST timezone

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

from .config import Config, get_config
from .logger import logger

__all__ = [
    "Config",
    "get_config",
    "logger",
]