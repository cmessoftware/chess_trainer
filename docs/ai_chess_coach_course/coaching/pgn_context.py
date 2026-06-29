"""Extract short PGN windows from games.pgn for critical-move coaching."""

from __future__ import annotations

import io
from typing import Any

import chess.pgn

DEFAULT_PLIES_BEFORE = 4
DEFAULT_PLIES_AFTER = 4


def player_is_white(player_moves: Any, player_name: str) -> bool:
    if player_moves is None or player_moves.empty:
        return True
    row = player_moves.iloc[0]
    if row.get("white_player") == player_name:
        return True
    if row.get("black_player") == player_name:
        return False
    return True


def player_ply_index(move_number: int, *, is_white: bool) -> int:
    """Map feature move_number (player's nth move) to 0-based mainline ply index."""
    if move_number < 1:
        raise ValueError("move_number must be >= 1")
    return (move_number - 1) * 2 + (0 if is_white else 1)


def parse_pgn_sans(pgn_text: str) -> list[str]:
    if not pgn_text or not str(pgn_text).strip():
        return []
    game = chess.pgn.read_game(io.StringIO(str(pgn_text)))
    if game is None:
        return []
    board = game.board()
    sans: list[str] = []
    for move in game.mainline_moves():
        sans.append(board.san(move))
        board.push(move)
    return sans


def fetch_game_pgn(repo: Any, game_id: str) -> str | None:
    """Load PGN for one game from games.pgn in the course database."""
    if repo is None or not game_id or not repo.has_table("games"):
        return None

    from sqlalchemy import select

    from data_access.features_repository import GAMES_TABLE

    stmt = select(GAMES_TABLE.c.pgn).where(GAMES_TABLE.c.game_id == game_id)
    with repo.engine.connect() as connection:
        row = connection.execute(stmt).first()
    if row is None or row[0] is None:
        return None
    return str(row[0])


def format_san_window(
    sans: list[str],
    center_ply: int,
    *,
    plies_before: int = DEFAULT_PLIES_BEFORE,
    plies_after: int = DEFAULT_PLIES_AFTER,
) -> str:
    if not sans or center_ply < 0 or center_ply >= len(sans):
        return ""

    start = max(0, center_ply - plies_before)
    end = min(len(sans), center_ply + plies_after + 1)
    parts: list[str] = []
    for ply in range(start, end):
        full_move = ply // 2 + 1
        san = sans[ply]
        if ply % 2 == 0:
            parts.append(f"{full_move}. {san}")
        else:
            parts.append(f"{full_move}...{san}")
    return " ".join(parts)


def extract_pgn_window_for_player_move(
    pgn_text: str,
    move_number: int,
    *,
    is_white: bool,
    plies_before: int = DEFAULT_PLIES_BEFORE,
    plies_after: int = DEFAULT_PLIES_AFTER,
) -> str:
    sans = parse_pgn_sans(pgn_text)
    if not sans:
        return ""
    center = player_ply_index(move_number, is_white=is_white)
    return format_san_window(
        sans,
        center,
        plies_before=plies_before,
        plies_after=plies_after,
    )


def extract_tactical_line(
    sans: list[str],
    root_ply: int,
    *,
    plies_ahead: int = 3,
) -> str | None:
    """Format opponent reply + follow-up plies after a coached-player move."""
    if not sans or root_ply < 0 or root_ply >= len(sans):
        return None

    parts: list[str] = []
    for offset in range(1, plies_ahead + 1):
        ply = root_ply + offset
        if ply >= len(sans):
            break
        full_move = ply // 2 + 1
        san = sans[ply]
        if ply % 2 == 0:
            parts.append(f"{full_move}. {san}")
        else:
            parts.append(f"{full_move}...{san}")
    return " ".join(parts) if parts else None


def format_player_move_label(
    move_number: int,
    *,
    pgn_text: str | None = None,
    sans: list[str] | None = None,
    is_white: bool = True,
    fallback_san: str | None = None,
) -> str:
    """Build coached-player move label from PGN (authoritative) with DB fallback."""
    resolved_sans = sans if sans is not None else parse_pgn_sans(pgn_text or "")
    if resolved_sans and move_number >= 1:
        ply = player_ply_index(move_number, is_white=is_white)
        if 0 <= ply < len(resolved_sans):
            return f"{move_number}. {resolved_sans[ply]}"
    if fallback_san and str(fallback_san).strip():
        return f"{move_number}. {str(fallback_san).strip()}"
    return f"jugada {move_number}"


def enrich_critical_moves_with_pgn(
    critical_moves: list[dict[str, Any]],
    *,
    pgn_text: str | None,
    is_white: bool,
    plies_before: int = DEFAULT_PLIES_BEFORE,
    plies_after: int = DEFAULT_PLIES_AFTER,
) -> list[dict[str, Any]]:
    if not pgn_text or not critical_moves:
        return critical_moves

    sans = parse_pgn_sans(pgn_text)
    if not sans:
        return critical_moves

    enriched: list[dict[str, Any]] = []
    for moment in critical_moves:
        updated = dict(moment)
        move_number = moment.get("move_number")
        if move_number is None:
            enriched.append(updated)
            continue
        center = player_ply_index(int(move_number), is_white=is_white)
        window = format_san_window(
            sans,
            center,
            plies_before=plies_before,
            plies_after=plies_after,
        )
        if window:
            updated["context_pgn"] = window
        fallback = moment.get("move_san")
        if fallback is None and isinstance(moment.get("move"), str) and ". " in moment["move"]:
            fallback = moment["move"].split(". ", 1)[1]
        updated["move"] = format_player_move_label(
            int(move_number),
            sans=sans,
            is_white=is_white,
            fallback_san=fallback,
        )
        if not updated.get("tactical_line"):
            tactical = extract_tactical_line(sans, center, plies_ahead=3)
            if tactical:
                updated["tactical_line"] = tactical
        enriched.append(updated)
    return enriched
