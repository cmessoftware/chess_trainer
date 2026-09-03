"""F07-016 — UCI/SAN conversion on a concrete board."""

from __future__ import annotations

from collections.abc import Sequence

import chess


def parse_legal_move(fen: str, move: str) -> chess.Move:
    """Parse UCI or SAN; reject illegal moves."""
    board = chess.Board(fen)
    text = move.strip()
    try:
        parsed = chess.Move.from_uci(text)
    except ValueError:
        parsed = None
    if parsed is not None and parsed in board.legal_moves:
        return parsed
    try:
        return board.parse_san(text)
    except ValueError as exc:
        raise ValueError(f"Illegal or unreadable move {move!r} in {fen}") from exc


def uci_to_san(fen: str, uci: str) -> str:
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move {uci} in {fen}")
    return board.san(move)


def san_to_uci(fen: str, san: str) -> str:
    board = chess.Board(fen)
    try:
        return board.parse_san(san).uci()
    except ValueError as exc:
        raise ValueError(f"Illegal or unreadable SAN {san!r} in {fen}") from exc


def pv_uci_to_san(fen: str, pv_uci: Sequence[str]) -> tuple[str, ...]:
    """Convert a UCI PV; stop is not allowed — every ply must be legal."""
    board = chess.Board(fen)
    sans: list[str] = []
    for uci in pv_uci:
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal PV move {uci} after {' '.join(sans) or '(start)'}")
        sans.append(board.san(move))
        board.push(move)
    return tuple(sans)


def roundtrip_uci(fen: str, uci: str) -> str:
    """UCI → SAN → UCI; must recover the same legal move."""
    recovered = san_to_uci(fen, uci_to_san(fen, uci))
    if recovered != chess.Move.from_uci(uci).uci():
        raise ValueError(f"Roundtrip mismatch for {uci}: got {recovered}")
    return recovered
