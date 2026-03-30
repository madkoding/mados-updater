#!/usr/bin/env python3
"""madOS Updater - Entry point for: python3 -m mados_updater"""

import sys
import os

# Add client directory to path
client_dir = os.path.join(os.path.dirname(__file__), 'client')
sys.path.insert(0, client_dir)

# Import the main function from the renamed module
from mados_updater import main

if __name__ == "__main__":
    main()
