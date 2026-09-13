#!/usr/bin/env python3
"""Compatibility entry point for native transport checks, not PCB approval."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_pcba_native import main


if __name__ == "__main__":
    main()
