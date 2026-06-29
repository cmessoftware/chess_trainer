"""Material consequence labels from cp loss or board delta."""

from __future__ import annotations

import chess

from coaching.diagnosis.board_utils import PIECE_VALUES, material_balance
from coaching.instructional_patterns import BLUNDER_CP_THRESHOLD, MISTAKE_CP_THRESHOLD

MATERIAL_NONE = "none"
MATERIAL_LOST_PAWN = "lost pawn"
MATERIAL_LOST_EXCHANGE = "lost exchange"
MATERIAL_LOST_PIECE = "lost piece"
MATERIAL_LOST_MATERIAL = "lost material"


def material_change_from_cp(cp_loss: float) -> str:
    if cp_loss >= BLUNDER_CP_THRESHOLD:
        return MATERIAL_LOST_PIECE
    if cp_loss >= 300:
        return MATERIAL_LOST_EXCHANGE
    if cp_loss >= MISTAKE_CP_THRESHOLD:
        return MATERIAL_LOST_PAWN
    if cp_loss >= 50:
        return MATERIAL_LOST_MATERIAL
    return MATERIAL_NONE


def material_change_from_boards(
    before: chess.Board,
    after: chess.Board,
    player_color: chess.Color,
) -> str:
    delta = material_balance(after, player_color) - material_balance(before, player_color)
    if delta >= 9:
        return MATERIAL_LOST_PIECE
    if delta >= 5:
        return MATERIAL_LOST_EXCHANGE
    if delta >= 1:
        return MATERIAL_LOST_PAWN
    return MATERIAL_NONE


def material_change_label_es(label: str) -> str:
    mapping = {
        MATERIAL_NONE: "sin pérdida material clara",
        MATERIAL_LOST_PAWN: "pérdida de peón",
        MATERIAL_LOST_EXCHANGE: "pérdida de calidad (cambio desfavorable)",
        MATERIAL_LOST_PIECE: "pérdida de pieza",
        MATERIAL_LOST_MATERIAL: "pérdida de material",
    }
    return mapping.get(label, label)
