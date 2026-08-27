#!/usr/bin/env python3
"""Lichess ingest. Same as: python player_ingest.py USER --platform lichess"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from player_ingest import main as ingest_main


if __name__ == "__main__":
    sys.exit(ingest_main([*sys.argv[1:], "--platform", "lichess"]))
