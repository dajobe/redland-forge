#!/usr/bin/python3
"""
Redland Forge Text UI - Entry Point

Thin wrapper script for the parallel build monitoring TUI.
"""

import argparse
import logging
import os
import sys
from typing import List

# Add the src directory to Python path so we can import redland_forge
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from redland_forge.app import BuildTUI, set_color_mode, read_hosts_from_file, parse_arguments, format_host_table, _main_impl
from redland_forge.config import Config
from redland_forge.exception_handler import ExceptionHandler


def main():
    """Entry point for the redland-forge application."""
    return _main_impl()


if __name__ == "__main__":
    sys.exit(main())
