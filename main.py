#!/usr/bin/env python3
"""
Timenote Desktop App Launcher
Main entry point for the Timenote application
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
from main import main

if __name__ == "__main__":
    main()