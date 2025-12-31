#!/usr/bin/env python3
"""
AskLab AI Bot Entry Point - app.py
This file imports and runs the main bot logic from asklab_ai_bot.__main__
"""

import sys
import os

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and run the main bot
if __name__ == "__main__":
    from asklab_ai_bot.__main__ import main
    main()
