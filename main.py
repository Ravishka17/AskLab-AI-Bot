#!/usr/bin/env python3
"""
AskLab AI Bot Entry Point
Main entry point that initializes and runs the Discord bot
"""
import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import bot
from bot import bot
from config import DISCORD_BOT_TOKEN

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env file")
        exit(1)
    
    print("🚀 Starting AskLab AI Bot...")
    bot.run(DISCORD_BOT_TOKEN)