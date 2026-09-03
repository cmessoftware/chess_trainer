"""Notable critical moments: exchanges, structure, recapture, center, tactical mess."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import chess

from coaching.diagnosis.board_utils import PIECE_VALUES

# c–f files, ranks 3–6 (includes c3 gambit and d4/d5/e4/e5)
_CENTER_FILES = {2, 3, 4, 5}
_CENTER_RANKS = {2, 3, 4, 5}
_POISONED_QUEEN_TO = {
    chess.WHITE: {chess.B2, chess.A2, chess.H2, chess.C2},
    chess.BLACK: {chess.B7, chess.A7, chess.H7, chess.C7},
}


class NotableKind(str, Enum):
    PIECE_EXCHANGE = "piece_exchange"
    PAWN_STRUCTURE = "pawn_structure"
    RECAPTURE_CHOICE = "recapture_choice"
    CENTER_DECISION = "center_decision"
    TACTICAL_MESS = "tactical_mess"


@dataclass(frozen=True)
class NotableReason:
    kind: NotableKind
    evidence: str


def _is_center(square: int) -> bool:
    return chess.square_file(square) in _CENTER_FILES and chess.square_rank(square) in _CENTER_RANKS


def _last_capture(board: chess.Board) -> tuple[chess.Move, int, int] | None:
    """Return (move, captured_piece_type, to_square) if the last ply was a capture."""
    if not board.move_stack:
        return None
    move = board.peek()
    prior = board.copy()
    prior.pop()
    if not prior.is_capture(move):
        return None
    if prior.is_en_passant(move):
        return move, chess.PAWN, move.to_square
    captured = prior.piece_at(move.to_square)
    if captured is None:
        return None
    return move, captured.piece_type, move.to_square


def _recaptures_to(board: chess.Board, square: int) -> list[chess.Move]:
    return [
        move
        for move in board.legal_moves
        if board.is_capture(move) and move.to_square == square
    ]


def _can_take_undefended(board: chess.Board, min_value: int) -> list[str]:
    player = board.turn
    hits: list[str] = []
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        victim = board.piece_at(move.to_square)
        if victim is None or victim.piece_type == chess.KING:
            continue
        value = PIECE_VALUES.get(victim.piece_type, 0)
        if value < min_value:
            continue
        if board.is_attacked_by(player, move.to_square) and not board.is_attacked_by(
            not player, move.to_square
        ):
            hits.append(
                f"Puede tomar {chess.piece_name(victim.piece_type)} en "
                f"{chess.square_name(move.to_square)} sin defensor"
            )
    return hits


def _poisoned_queen_grabs(board: chess.Board) -> list[str]:
    player = board.turn
    targets = _POISONED_QUEEN_TO[player]
    hits: list[str] = []
    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.QUEEN:
            continue
        if not board.is_capture(move) or move.to_square not in targets:
            continue
        hits.append(f"Dama puede entrar a {chess.square_name(move.to_square)} (lío táctico)")
    return hits


def detect_notable_critical(board: chess.Board) -> list[NotableReason]:
    """Sparse critical moments — not every hanging pawn or king on the d-file."""
    reasons: list[NotableReason] = []
    seen: set[NotableKind] = set()

    def add(kind: NotableKind, evidence: str) -> None:
        if kind in seen:
            return
        seen.add(kind)
        reasons.append(NotableReason(kind=kind, evidence=evidence))

    capture = _last_capture(board)
    if capture is not None:
        _move, captured_type, to_sq = capture
        recaptures = _recaptures_to(board, to_sq)
        value = PIECE_VALUES.get(captured_type, 0)
        if len(recaptures) >= 2:
            add(
                NotableKind.RECAPTURE_CHOICE,
                f"Retomar en {chess.square_name(to_sq)} de {len(recaptures)} maneras",
            )
        elif len(recaptures) >= 1 and _is_center(to_sq):
            add(
                NotableKind.RECAPTURE_CHOICE,
                f"Retomar o no en el centro ({chess.square_name(to_sq)}; peón/dama/gambito)",
            )
        if captured_type == chess.PAWN:
            add(
                NotableKind.PAWN_STRUCTURE,
                f"Última jugada cambió peones en {chess.square_name(to_sq)}",
            )
        if value >= 3:
            add(
                NotableKind.PIECE_EXCHANGE,
                f"Cambio de pieza ({chess.piece_name(captured_type)}) en {chess.square_name(to_sq)}",
            )
        if _is_center(to_sq):
            add(
                NotableKind.CENTER_DECISION,
                f"Contacto en el centro ({chess.square_name(to_sq)})",
            )

    if board.is_check():
        add(NotableKind.TACTICAL_MESS, "Jaque — hay que resolver sí o sí")
    for line in _can_take_undefended(board, min_value=5):
        add(NotableKind.TACTICAL_MESS, line)
        break
    for line in _poisoned_queen_grabs(board):
        add(NotableKind.TACTICAL_MESS, line)
        break

    return reasons
