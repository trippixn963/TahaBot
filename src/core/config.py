"""
QuranBot - Configuration Management
===================================

Robust configuration system with environment variable loading,
validation, and error handling for the QuranBot Discord application.

Features:
- Environment variable management with .env file support
- Discord token validation and security checks
- Audio directory validation and auto-creation
- Comprehensive error handling with detailed logging
- Type-safe configuration with dataclass implementation

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
# This allows configuration without hardcoding sensitive values
load_dotenv()


@dataclass
class Config:
    """
    Comprehensive configuration class for QuranBot.
    
    Manages all bot configuration including Discord authentication,
    audio settings, and file paths with built-in validation.
    
    Attributes:
        discord_token: Discord bot token for API authentication
        default_reciter: Primary reciter for audio playback
        stage_channel_id: Target Discord stage channel ID
        audio_dir: Path to audio files directory
    """
    
    # Discord Bot Configuration
    # Required Discord bot token for API authentication
    discord_token: str

    # Audio Playback Settings
    # Default reciter selection (Saad Al Ghamdi has the most complete collection)
    default_reciter: str = "Saad Al Ghamdi"
    
    # Target Discord stage channel ID where the bot will stream
    # This should be configured via environment variable
    stage_channel_id: Optional[int] = None

    # File System Paths
    # Audio directory path relative to project root
    # Navigate from src/core/ to project root, then to audio/
    audio_dir: Path = Path(__file__).parent.parent.parent / "audio"


def get_config() -> Config:
    """Get configuration instance with error handling."""
    try:
        # Retrieve Discord bot token from environment variables
        # This token is required for Discord API authentication
        discord_token: Optional[str] = os.getenv("DISCORD_TOKEN")
        
        # Validate that the Discord token is present
        # Without this token, the bot cannot connect to Discord
        if not discord_token:
            # Attempt to use structured logging for better error display
            # Import logger here to avoid circular import issues
            try:
                from src.core.logger import logger
                logger.error_tree("Missing Discord Token", ValueError("DISCORD_TOKEN not found"), [
                    ("Environment File", ".env file may be missing or incomplete"),
                    ("Solution", "Create .env file with DISCORD_TOKEN=your_token_here")
                ])
            except ImportError:
                # Fallback to simple print if logger not available
                print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
                print("   Create a .env file with DISCORD_TOKEN=your_token_here")
            
            # Terminate program since bot cannot function without Discord token
            sys.exit(1)
        
        # Get optional stage channel ID from environment
        stage_channel_id_str = os.getenv("STAGE_CHANNEL_ID")
        stage_channel_id = int(stage_channel_id_str) if stage_channel_id_str else None

        # Create configuration instance with validated Discord token
        config = Config(discord_token=discord_token, stage_channel_id=stage_channel_id)
        
        # Ensure audio directory exists for Quran audio files
        # This directory contains the reciter folders with MP3 files
        if not config.audio_dir.exists():
            try:
                from src.core.logger import logger
                logger.tree("⚠️ Audio Directory Missing", [
                    ("Expected Path", str(config.audio_dir)),
                    ("Action", "Creating directory"),
                    ("Status", "Auto-creating with parent directories")
                ])
            except ImportError:
                # Fallback logging if logger not available
                print(f"⚠️ Audio directory not found: {config.audio_dir}")
                print(f"   Creating audio directory...")
            
            # Create the audio directory with parent directories if needed
            # exist_ok=True prevents errors if directory already exists
            config.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Return successfully created and validated configuration
        return config
        
    except Exception as e:
        # Handle any unexpected errors during configuration loading
        # This ensures graceful failure with helpful error information
        try:
            from src.core.logger import logger
            logger.error_tree("Failed to load configuration", e, [
                ("Config Path", str(Path.cwd())),
                ("Error Type", type(e).__name__)
            ])
        except ImportError:
            # Fallback error handling if logger not available
            print(f"❌ CRITICAL ERROR: Failed to load configuration: {e}")
        
        # Terminate program since configuration is essential for bot operation
        sys.exit(1)