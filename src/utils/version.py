"""
TahaBot - Version Management
=============================

Centralized version management system for the TahaBot.
Implements semantic versioning (MAJOR.MINOR.PATCH) with build metadata.

Version Format: MAJOR.MINOR.PATCH[-BUILD]
- MAJOR: Breaking changes or major feature additions
- MINOR: New features, backwards compatible
- PATCH: Bug fixes, backwards compatible
- BUILD: Optional build identifier (e.g., 'dev', 'beta', 'rc1')

Author: حَـــــنَّـــــا
Server: discord.gg/syria
"""

from datetime import datetime
from typing import Dict, Any, Optional


class Version:
    """
    Version management class for TahaBot.
    
    Provides semantic versioning with build metadata and version history tracking.
    All version information is centralized here for consistency across the bot.
    """
    
    # CURRENT VERSION INFORMATION
    # ===========================
    # Update these values for each release following semantic versioning principles
    # MAJOR: Breaking changes or major feature additions (incompatible API changes)
    # MINOR: New features, backwards compatible (new functionality, backwards compatible)
    # PATCH: Bug fixes, backwards compatible (backwards compatible bug fixes)
    # BUILD: Optional build identifier for pre-releases (dev, beta, rc1, etc.)
    MAJOR: int = 1
    MINOR: int = 0
    PATCH: int = 0
    BUILD: Optional[str] = None  # Set to None for stable releases
    
    # VERSION METADATA
    # ================
    # Release date in YYYY-MM-DD format - update with each release
    RELEASE_DATE: str = "2025-09-13"
    
    # BOT INFORMATION
    # ===============
    # Core bot identification and developer information
    BOT_NAME: str = "TahaBot"
    DEVELOPER: str = "حَـــــنَّـــــا"
    SERVER: str = "discord.gg/syria"
    
    @classmethod
    def get_version_string(cls) -> str:
        """
        Get the complete version string following semantic versioning.
        
        Constructs the version string in the format "MAJOR.MINOR.PATCH[-BUILD]"
        where BUILD is optional and only included for pre-releases or development builds.
        
        Returns:
            str: Version string (e.g., "1.0.0", "1.2.3-beta", "2.0.0-rc1")
        """
        # Start with the core semantic version (MAJOR.MINOR.PATCH)
        version: str = f"{cls.MAJOR}.{cls.MINOR}.{cls.PATCH}"
        
        # Append build identifier if present (for pre-releases, development builds, etc.)
        if cls.BUILD:
            version += f"-{cls.BUILD}"
        
        return version
    
    @classmethod
    def get_full_info(cls) -> Dict[str, Any]:
        """
        Get complete version and bot information dictionary.
        
        Returns a comprehensive dictionary containing all version metadata,
        bot identification, and build information. This is useful for
        logging, debugging, and displaying detailed version information.
        
        Returns:
            Dict[str, Any]: Complete version information including:
                - version: Complete version string
                - major/minor/patch: Individual version components
                - build: Build identifier (if any)
                - release_date: Release date
                - bot_name: Bot name
                - developer: Developer information
                - server: Server information
                - build_time: Current build timestamp
        """
        return {
            "version": cls.get_version_string(),
            "major": cls.MAJOR,
            "minor": cls.MINOR,
            "patch": cls.PATCH,
            "build": cls.BUILD,
            "release_date": cls.RELEASE_DATE,
            "bot_name": cls.BOT_NAME,
            "developer": cls.DEVELOPER,
            "server": cls.SERVER,
            "build_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    def get_display_string(cls) -> str:
        """
        Get formatted version string for display purposes.
        
        Returns:
            str: Formatted version string
        """
        version: str = cls.get_version_string()
        return f"{cls.BOT_NAME} v{version}"
    
    @classmethod
    def get_short_info(cls) -> str:
        """
        Get short version info for logging.
        
        Returns:
            str: Short version string
        """
        return f"v{cls.get_version_string()}"
    
    @classmethod
    def is_development(cls) -> bool:
        """
        Check if this is a development build.
        
        Returns:
            bool: True if build contains 'dev', 'beta', or 'rc'
        """
        if not cls.BUILD:
            return False
        return any(keyword in cls.BUILD.lower() for keyword in ['dev', 'beta', 'rc'])
    
    @classmethod
    def is_stable(cls) -> bool:
        """
        Check if this is a stable release.
        
        Returns:
            bool: True if no build identifier or stable build
        """
        return not cls.BUILD or cls.BUILD.lower() in ['stable', 'release']
    
    @classmethod
    def get_release_type(cls) -> str:
        """
        Get the release type based on version and build.
        
        Returns:
            str: Release type ('stable', 'development', 'beta', 'release_candidate')
        """
        if cls.is_stable():
            return "stable"
        elif cls.is_development():
            if 'beta' in cls.BUILD.lower():
                return "beta"
            elif 'rc' in cls.BUILD.lower():
                return "release_candidate"
            else:
                return "development"
        else:
            return "custom"


# Version history for reference
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2025-09-13",
        "changes": [
            "Initial stable version",
            "24/7 Quran streaming functionality",
            "Multiple reciter support",
            "Stage channel integration",
            "Auto-reconnect on disconnect",
            "Beautiful control panel UI with progress tracking",
            "MiniTreeLogger implementation",
            "Surah mapper with Arabic names and emojis",
            "Improved reciter switching",
            "Centralized version management system"
        ]
    }
}


def get_version_info() -> Dict[str, Any]:
    """
    Convenience function to get current version information.
    
    Returns:
        Dict[str, Any]: Current version information
    """
    return Version.get_full_info()


def get_version_string() -> str:
    """
    Convenience function to get version string.
    
    Returns:
        str: Current version string
    """
    return Version.get_version_string()