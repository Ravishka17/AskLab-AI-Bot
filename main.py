#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure the package can be imported from the script directory
sys.path.insert(0, str(Path(__file__).parent))

from asklab_ai_bot.__main__ import main


if __name__ == "__main__":
    main()
