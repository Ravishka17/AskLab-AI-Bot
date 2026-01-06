#!/usr/bin/env python3
"""
AskLab AI Bot Entry Point - main.py
Simple entry point that runs app.py
"""

import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Run app.py
if __name__ == "__main__":
    exec(open(os.path.join(PROJECT_ROOT, "app.py")).read())
