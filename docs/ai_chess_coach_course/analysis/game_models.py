"""Canonical DTOs for Module 07.0 — game import and player selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PlayerColor = Literal["white", "black"]


def parse_player_color(value: str | int) -> PlayerColor:
    if isinstance(value, bool):
        raise ValueError("color must be white/black (or 1/0), not a boolean")
    if isinstance(value, int):
        if value == 1:
            return "white"
        if value == 0:
            return "black"
        raise ValueError(f"Invalid numeric color {value!r}; use 1 (white) or 0 (black)")
    token = str(value).strip().lower()
    if token in {"white", "w", "1"}:
        return "white"
    if token in {"black", "b", "0"}:
        return "black"
    raise ValueError(f"Invalid color {value!r}; use white or black")


def _names_match(left: str, right: str) -> bool:
    a = (left or "").strip()
    b = (right or "").strip()
    return bool(a) and bool(b) and a.casefold() == b.casefold()


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

    def plies_for_color(self, color: PlayerColor) -> list[PlyRecord]:
        return [ply for ply in self.plies if ply.side_to_move == color]

    def select_player(
        self,
        *,
        username: str | None = None,
        color: str | int | None = None,
    ) -> PlayerSelection:
        return select_analyzed_player(self, username=username, color=color)


@dataclass(frozen=True)
class PlayerSelection:
    """F07-002 — moves attributable to the analyzed player."""

    username: str
    color: PlayerColor
    plies: tuple[PlyRecord, ...]

    @property
    def is_white(self) -> bool:
        return self.color == "white"

    @property
    def move_count(self) -> int:
        return len(self.plies)


def select_analyzed_player(
    game: NormalizedGame,
    *,
    username: str | None = None,
    color: str | int | None = None,
) -> PlayerSelection:
    """Resolve White/Black from username and/or color; return that side's plies."""
    name = (username or "").strip()
    requested_color = parse_player_color(color) if color is not None and str(color).strip() != "" else None

    white_name = game.white_player
    black_name = game.black_player
    matches_white = _names_match(name, white_name)
    matches_black = _names_match(name, black_name)

    if not name and requested_color is None:
        raise ValueError("Provide username and/or color to select the analyzed player")

    if name and not matches_white and not matches_black:
        raise ValueError(
            f"Player {name!r} is not in this game (White={white_name!r}, Black={black_name!r})"
        )

    if matches_white and matches_black:
        if requested_color is None:
            raise ValueError(
                f"Username {name!r} matches both White and Black; pass color='white' or color='black'"
            )
        resolved = requested_color
    elif requested_color is not None and name:
        resolved = requested_color
        if resolved == "white" and not matches_white:
            raise ValueError(f"Player {name!r} is Black in this game, not White")
        if resolved == "black" and not matches_black:
            raise ValueError(f"Player {name!r} is White in this game, not Black")
    elif matches_white:
        resolved = "white"
    elif matches_black:
        resolved = "black"
    else:
        resolved = requested_color  # color-only

    assert resolved is not None
    display_name = white_name if resolved == "white" else black_name
    if name:
        display_name = name
    elif not display_name:
        display_name = resolved

    player_plies = tuple(game.plies_for_color(resolved))
    return PlayerSelection(username=display_name, color=resolved, plies=player_plies)
