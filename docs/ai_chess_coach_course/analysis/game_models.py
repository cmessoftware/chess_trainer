"""Canonical DTOs for Module 07.0 — F07-001 game import."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class PlyRecord:
    """One mainline half-move with board state."""

    ply: int
    move_number: int
    san: str
    uci: str
    fen_before: str
    fen_after: str
    side_to_move: Literal["white", "black"]
    score_diff: float | None = None


@dataclass
class NormalizedGame:
    """Normalized game ready for the Module 07 pipeline (F07-001)."""

    game_id: str
    headers: dict[str, str]
    plies: list[PlyRecord]
    result: str
    pgn: str
    source: Literal["pgn", "database"] = "pgn"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def white_player(self) -> str:
        return self.headers.get("White", "")

    @property
    def black_player(self) -> str:
        return self.headers.get("Black", "")

    def fen_at_ply(self, ply: int) -> str:
        if ply < 0:
            raise ValueError("ply must be >= 0")
        if ply >= len(self.plies):
            if self.plies:
                return self.plies[-1].fen_after
            return self.metadata.get("initial_fen", "")
        return self.plies[ply].fen_before
