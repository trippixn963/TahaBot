#!/bin/bash

# TahaBot Runner Script
# ======================
# 
# Professional launcher script for TahaBot 24/7 streaming bot.
# Handles virtual environment setup, dependency installation, and bot execution
# with comprehensive error handling and user-friendly output.
#
# Features:
# - Automatic virtual environment creation and activation
# - Dependency installation with pip
# - Force mode with --kill flag for existing instances
# - Colored output for better user experience
# - Proper argument passthrough to main.py
#
# Usage:
#   ./run.sh           # Normal start
#   ./run.sh --kill    # Force start (kill existing instances)
#
# Author: حَـــــنَّـــــا
# Server: discord.gg/syria

# COLOR DEFINITIONS FOR ENHANCED OUTPUT
# =====================================
# Define ANSI color codes for terminal output styling
RED='\033[0;31m'      # Red color for errors and warnings
GREEN='\033[0;32m'    # Green color for success messages
YELLOW='\033[1;33m'   # Yellow color for informational messages
NC='\033[0m'          # No Color - reset to default terminal color

# DISPLAY LAUNCHER HEADER
# =======================
echo -e "${GREEN}🕌 QuranBot Launcher${NC}"
echo "========================"

# VIRTUAL ENVIRONMENT MANAGEMENT
# ==============================
# Check if virtual environment exists and create/activate as needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    
    # Create new virtual environment using Python 3
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
    
    # DEPENDENCY INSTALLATION
    # =======================
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    
    # Activate the virtual environment
    source venv/bin/activate
    
    # Upgrade pip to latest version for better compatibility
    pip install --upgrade pip
    
    # Install all required dependencies from requirements.txt
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    # Virtual environment exists, simply activate it
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
fi

# FORCE MODE HANDLING
# ===================
# Check for --kill flag to enable force mode
if [ "$1" == "--kill" ]; then
    echo -e "${RED}⚡ Force mode: Killing existing instances${NC}"
    
    # Kill any existing Python processes running main.py
    # This prevents conflicts when multiple instances are running
    pkill -f "python.*main.py" 2>/dev/null
    
    # Brief pause to ensure processes are terminated
    sleep 1
fi

# BOT EXECUTION
# =============
echo -e "${GREEN}🚀 Starting TahaBot 24/7...${NC}"
echo "========================"

# Execute the bot with all passed arguments
# The "$@" passes through any command-line arguments to main.py
python main.py "$@"