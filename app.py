#!/usr/bin/env python3
"""
Main entry point for AskLab AI Discord Bot on fps.ms.
This file is the required entry point for fps.ms container hosting.

IMPORTANT: fps.ms requires this file to be named 'app.py'
"""

import os
import sys

# Add the project root to sys.path so we can import asklab_ai_bot package
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and run the main bot from asklab_ai_bot package
from asklab_ai_bot.__main__ import main

if __name__ == "__main__":
    main()
