"""
Chess Trainer Components Package
================================

This package contains reusable components for the Chess Trainer application:

Components:
- database_connector: PostgreSQL database connection management
- interactive_chess_board: Interactive chess board with drag & drop
- chess_board_*: Various chess board implementations

Author: Chess Trainer Team
Date: 2026-01-16
"""

__version__ = "1.0.0"
__all__ = [
    "database_connector",
    "interactive_chess_board",
    "chess_board_standalone",
    "chess_board_fixed",
    "chess_board_simple",
]
