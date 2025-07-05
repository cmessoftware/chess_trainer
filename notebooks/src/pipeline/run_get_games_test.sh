#!/bin/bash
set -e

# Run the Python script to generate PGN from chess server
python /app/src/scripts/generate_pgn_from_chess_servers.py --server lichess.org --users cmess4401 cmess1315 --since 2025-01-01