#!/usr/bin/env python3
"""
Main entry point for AskLab AI Discord Bot.
This file imports the main module from asklab_ai_bot package and runs the bot.

Usage:
    python main.py
    python -m asklab_ai_bot
"""

import os
import sys

# Add the project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and run the main function from asklab_ai_bot package
from asklab_ai_bot.__main__ import main

if __name__ == "__main__":
    main()
