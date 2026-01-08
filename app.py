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

# Import and run bot
if __name__ == "__main__":
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env file")
        exit(1)
    
    print("🚀 Starting AskLab AI Bot...")
    
    try:
        # Import bot components
        from bot import bot
        
        # Run the bot
        bot.run(discord_token)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed.")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        exit(1)