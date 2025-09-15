#!/usr/bin/env python3
"""
TahaBot - 24/7 Quran Streaming Bot Entry Point
==============================================

A Discord bot built for continuous Quran recitation in voice channels.
Features 24/7 streaming with multiple reciter support and auto-reconnection.

Author: حَـــــنَّـــــا
Server: discord.gg/syria
Version: v1.0.0

Discord Bot Features:
- 24/7 continuous audio streaming
- Auto-reconnect on disconnect
- Multiple reciter support
- Stage channel support
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add src directory to Python path for imports
# This allows importing from src/ modules without package installation
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import discord
from src.core.logger import logger
from src.core.lock_manager import LockManager
from src.bot import TahaBot
from src.utils.version import Version


async def main() -> None:
    """
    Main entry point for TahaBot Discord bot.
    
    This function handles the complete bot lifecycle:
    1. Loads environment configuration
    2. Validates Discord bot token
    3. Initializes bot instance with proper intents
    4. Establishes connection to Discord API
    5. Starts 24/7 audio streaming
    6. Handles graceful shutdown on interruption
    
    Raises:
        SystemExit: If bot token is missing or bot fails to start
    """
    # INSTANCE LOCKING SYSTEM
    # =======================
    # Create lock manager to ensure only one bot instance runs at a time
    # This prevents conflicts and resource competition between multiple instances
    lock_manager = LockManager()
    
    # Check for existing instances and kill if requested via --kill flag
    # This allows force-starting the bot even if another instance is running
    if "--kill" in sys.argv:
        logger.tree("⚡ Force Mode", [
            ("Action", "Killing existing instances"),
            ("Reason", "--kill flag provided")
        ])
        lock_manager.kill_existing()
    
    # Acquire exclusive lock for this bot instance
    # If another instance is running, exit gracefully with helpful message
    if not lock_manager.acquire():
        logger.error_tree("Cannot start bot", Exception("Another instance is already running"), [
            ("Solution", "Use 'python3 main.py --kill' to force start"),
            ("Lock File", "bot.lock")
        ])
        sys.exit(1)
    
    # Load environment variables from .env file
    # This includes the critical DISCORD_TOKEN for bot authentication
    load_dotenv()
    
    # Display beautiful startup information with bot details
    # This provides immediate feedback about bot configuration and status
    logger.tree("🕌 TahaBot 24/7 Starting", [
        ("Version", Version.get_short_info()),
        ("Developer", Version.DEVELOPER),
        ("Server", Version.SERVER),
        ("Mode", "24/7 Automatic Streaming"),
        ("Stage Channel", "1402566993630199808"),
        ("Instance Lock", "Protected")
    ])
    
    # Retrieve and validate Discord bot token from environment
    # This token is absolutely required for Discord API authentication
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error_tree("Missing Discord Token", ValueError("DISCORD_TOKEN not found"), [
            ("Environment File", ".env file may be missing or incomplete"),
            ("Solution", "Create .env file with DISCORD_TOKEN=your_token_here"),
            ("Current Directory", str(Path.cwd()))
        ])
        sys.exit(1)
    
    # Initialize bot instance variable for proper cleanup on exit
    bot: Optional[TahaBot] = None
    
    try:
        # Create TahaBot instance with all components initialized
        logger.tree("🤖 Creating TahaBot Instance", [
            ("Component", "TahaBot"),
            ("Status", "Initializing")
        ])
        bot = TahaBot()
        
        # Connect to Discord Gateway and start the bot
        # This establishes the WebSocket connection to Discord servers
        logger.tree("🌐 Connecting to Discord", [
            ("API", "Discord Gateway"),
            ("Status", "Establishing connection")
        ])
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.tree("✋ Keyboard Interrupt", [
            ("Action", "Shutdown requested"),
            ("Method", "Ctrl+C")
        ])
        
    except discord.LoginFailure as e:
        logger.error_tree("Discord Authentication Failed", e, [
            ("Token Length", str(len(token)) if token else "0"),
            ("Possible Cause", "Invalid or expired Discord token"),
            ("Solution", "Check your DISCORD_TOKEN in .env file")
        ])
        
    except discord.PrivilegedIntentsRequired as e:
        logger.error_tree("Missing Required Discord Intents", e, [
            ("Required Intents", "message_content, guilds, voice_states"),
            ("Solution", "Enable intents in Discord Developer Portal"),
            ("Portal URL", "https://discord.com/developers/applications")
        ])
        
    except Exception as e:
        logger.error_tree("Fatal Error Occurred", e, [
            ("Error Type", type(e).__name__),
            ("Python Version", sys.version.split()[0]),
            ("Working Directory", str(Path.cwd()))
        ])
        
    finally:
        # Ensure graceful shutdown regardless of how the bot was stopped
        # This guarantees proper cleanup of resources and connections
        if bot:
            try:
                logger.tree("🔄 Graceful Shutdown", [
                    ("Component", "TahaBot"),
                    ("Method", "Clean shutdown")
                ])
                # Perform clean shutdown of audio service and Discord connection
                await bot.shutdown()
            except Exception as e:
                logger.error_tree("Error during shutdown", e, [
                    ("Component", "Bot shutdown"),
                    ("Action", "Forcing exit")
                ])
        
        # Release the instance lock to allow future bot instances
        # This ensures clean shutdown and proper resource cleanup
        lock_manager.release()
        
        # Log successful shutdown completion
        logger.success("TahaBot 24/7 stopped successfully")


if __name__ == "__main__":
    """
    Script entry point for direct execution.
    
    Sets working directory and runs the main async function.
    Handles KeyboardInterrupt gracefully for clean shutdown.
    """
    # Set working directory to project root for consistent file paths
    # This ensures all relative paths work correctly regardless of execution location
    os.chdir(project_root)
    
    try:
        # Run the async main function which handles the entire bot lifecycle
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully with user-friendly message
        print("\n✋ 24/7 Bot stopped by user")
        logger.tree("✋ Application Terminated", [
            ("Terminated By", "User"),
            ("Method", "Keyboard interrupt")
        ])
    except SystemExit as e:
        # Re-raise SystemExit to honor exit codes from main function
        # This preserves the intended exit status for proper error handling
        raise
    except Exception as e:
        # Handle any unexpected errors during startup with detailed logging
        logger.error_tree("Unhandled Exception in Main", e, [
            ("Error Type", type(e).__name__),
            ("Error Details", str(e)),
            ("Python Version", sys.version.split()[0])
        ])
        print(f"\n❌ Critical Error: {e}")
        sys.exit(1)