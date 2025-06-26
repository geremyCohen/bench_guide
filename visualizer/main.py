#!/usr/bin/env python3
"""
Refactored Benchmark Visualizer Tool

Main entry point for the modular benchmark visualizer.
"""

import sys
from pathlib import Path

# Add the visualizer directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from cli.commands import CLI


def main():
    """Main entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()