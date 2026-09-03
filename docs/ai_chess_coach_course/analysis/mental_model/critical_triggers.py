"""Detect E1–E11 human critical triggers from board state and optional features."""

from __future__ import annotations

import chess

from coaching.diagnosis.board_utils import PIECE_VALUES, attacked_undefended
from analysis.mental_model.models import HumanTrigger, HumanTriggerCode

LABELS: dict[HumanTriggerCode, str] = {
    HumanTriggerCode.FREE_MATERIAL: "Material aparentemente gratis o pieza en prise",
    HumanTriggerCode.CHECK_CAPTURE_THREAT: "Jaque, captura o amenaza directa",
    HumanTriggerCode.UNEXPECTED_MOVE: "Jugada inesperada del rival",
    HumanTriggerCode.PAWN_TEMPO: "Avance de peón con tempo sobre una pieza",
    HumanTriggerCode.LINE_OPEN_CLOSE: "Se abre o cierra columna, diagonal o fila",
    HumanTriggerCode.PAWN_STRUCTURE: "Cambio importante de estructura de peones",
    HumanTriggerCode.KING_ATTACK: "Ataque al rey o reyes expuestos",
    HumanTriggerCode.TRAPPED_OVERLOADED: "Pieza sin defensor o presionada",
    HumanTriggerCode.IRREVERSIBLE: "Jugada irreversible (avance, captura mayor, cambio)",
    HumanTriggerCode.MULTIPLE_CANDIDATES: "Varias candidatas razonables",
    HumanTriggerCode.EVAL_SHIFT: "La evaluación cambió: tranquilo ↔ táctico",
}

EVAL_SHIFT_CP = 80
UNEXPECTED_EVAL_CP = 120


def _opponent_hanging(board: chess.Board, player: chess.Color) -> list[str]:
    opponent = not player
    evidence: list[str] = []
    for square, piece in attacked_undefended(board, opponent, min_value=1):
        name = chess.piece_name(piece.piece_type)
        evidence.append(f"{name} rival en {chess.square_name(square)} sin defensa adecuada")
    return evidence


def _last_move_was_capture_or_check(board: chess.Board) -> list[str]:
    """E2: the opponent's last ply, not 'any legal capture exists' (that is almost always true)."""
    if not board.move_stack:
        return []
    move = board.peek()
    prior = board.copy()
    prior.pop()
    evidence: list[str] = []
    if prior.is_capture(move):
        evidence.append(f"La última jugada fue captura ({move.uci()})")
    if prior.gives_check(move):
        evidence.append("La última jugada dio jaque")
    return evidence


def _forcing_situation(board: chess.Board) -> list[str]:
    evidence: list[str] = []
    if board.is_check():
        evidence.append("Estás en jaque")
    evidence.extend(_last_move_was_capture_or_check(board))
    return evidence


def _pawn_attacks_piece(board: chess.Board) -> list[str]:
    if not board.move_stack:
        return []
    move = board.peek()
    piece = board.piece_at(move.to_square)
    if piece is None or piece.piece_type != chess.PAWN:
        return []
    attacked = board.attacks(move.to_square)
    evidence: list[str] = []
    for sq in attacked:
        target = board.piece_at(sq)
        if target and target.color != piece.color and target.piece_type != chess.KING:
            evidence.append(
                f"Peón en {chess.square_name(move.to_square)} ataca "
                f"{chess.piece_name(target.piece_type)} en {chess.square_name(sq)}"
            )
    return evidence


def _opponent_threats(board: chess.Board, player: chess.Color) -> list[str]:
    """Pieces we lose or king threats after opponent's last move."""
    opponent = not player
    evidence: list[str] = []
    king_sq = board.king(player)
    if king_sq is not None and board.is_attacked_by(opponent, king_sq):
        evidence.append(f"Tu rey en {chess.square_name(king_sq)} está atacado")
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != player or piece.piece_type == chess.KING:
            continue
        if board.is_attacked_by(opponent, square) and not board.is_attacked_by(player, square):
            evidence.append(
                f"Tu {chess.piece_name(piece.piece_type)} en {chess.square_name(square)} está atacada"
            )
    return evidence[:4]


def _king_exposure(board: chess.Board, player: chess.Color) -> list[str]:
    king_sq = board.king(player)
    if king_sq is None:
        return []
    attackers = board.attackers(not player, king_sq)
    if len(attackers) >= 1:
        return [f"Rey expuesto en {chess.square_name(king_sq)}"]
    if not board.has_kingside_castling_rights(player) and not board.has_queenside_castling_rights(player):
        file = chess.square_file(king_sq)
        if file in (3, 4):
            return ["Rey aún en zona central — considerar seguridad"]
    return []


def detect_human_triggers(
    board: chess.Board,
    *,
    score_diff_before: float | None = None,
    score_diff_after: float | None = None,
    candidate_count: int | None = None,
) -> list[HumanTrigger]:
    """Return triggered E-codes for the player to move (post-opponent-move position)."""
    player = board.turn
    triggers: list[HumanTrigger] = []

    hanging = _opponent_hanging(board, player)
    if hanging:
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.FREE_MATERIAL,
                LABELS[HumanTriggerCode.FREE_MATERIAL],
                0.85,
                hanging[:3],
            )
        )

    forcing = _forcing_situation(board)
    threats = _opponent_threats(board, player)
    if forcing or threats:
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.CHECK_CAPTURE_THREAT,
                LABELS[HumanTriggerCode.CHECK_CAPTURE_THREAT],
                0.9,
                (forcing + threats)[:4],
            )
        )

    pawn_tempo = _pawn_attacks_piece(board)
    if pawn_tempo:
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.PAWN_TEMPO,
                LABELS[HumanTriggerCode.PAWN_TEMPO],
                0.82,
                pawn_tempo,
            )
        )

    if board.move_stack:
        move = board.peek()
        piece = board.piece_at(move.to_square)
        prior = board.copy()
        prior.pop()
        last_was_capture = prior.is_capture(move)
        if last_was_capture and piece is not None and piece.piece_type == chess.PAWN:
            triggers.append(
                HumanTrigger(
                    HumanTriggerCode.PAWN_STRUCTURE,
                    LABELS[HumanTriggerCode.PAWN_STRUCTURE],
                    0.7,
                    [f"Cambio de estructura: captura de peón en {chess.square_name(move.to_square)}"],
                )
            )
        captured_type = None
        if last_was_capture:
            captured = prior.piece_at(move.to_square)
            if captured is not None:
                captured_type = captured.piece_type
        if captured_type is not None and PIECE_VALUES.get(captured_type, 0) >= 3:
            triggers.append(
                HumanTrigger(
                    HumanTriggerCode.IRREVERSIBLE,
                    LABELS[HumanTriggerCode.IRREVERSIBLE],
                    0.75,
                    ["Captura de pieza mayor o cambio material"],
                )
            )

    king_ev = _king_exposure(board, player)
    if king_ev:
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.KING_ATTACK,
                LABELS[HumanTriggerCode.KING_ATTACK],
                0.8,
                king_ev,
            )
        )

    own_hanging = attacked_undefended(board, player, min_value=3)
    if own_hanging:
        sq, piece = own_hanging[0]
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.TRAPPED_OVERLOADED,
                LABELS[HumanTriggerCode.TRAPPED_OVERLOADED],
                0.78,
                [f"Tu {chess.piece_name(piece.piece_type)} en {chess.square_name(sq)} sin defensa"],
            )
        )

    if score_diff_before is not None and score_diff_after is not None:
        delta = abs(float(score_diff_after) - float(score_diff_before))
        if delta >= EVAL_SHIFT_CP:
            triggers.append(
                HumanTrigger(
                    HumanTriggerCode.EVAL_SHIFT,
                    LABELS[HumanTriggerCode.EVAL_SHIFT],
                    min(0.95, 0.6 + delta / 400),
                    [f"Cambio de eval ≈ {delta:.0f} cp"],
                )
            )
            if delta >= UNEXPECTED_EVAL_CP:
                triggers.append(
                    HumanTrigger(
                        HumanTriggerCode.UNEXPECTED_MOVE,
                        LABELS[HumanTriggerCode.UNEXPECTED_MOVE],
                        0.75,
                        ["Salto grande de evaluación tras la jugada rival"],
                    )
                )

    if candidate_count is not None and candidate_count >= 3:
        triggers.append(
            HumanTrigger(
                HumanTriggerCode.MULTIPLE_CANDIDATES,
                LABELS[HumanTriggerCode.MULTIPLE_CANDIDATES],
                0.7,
                [f"{candidate_count} candidatas con evaluaciones cercanas"],
            )
        )

    # Deduplicate by code keeping highest confidence
    by_code: dict[HumanTriggerCode, HumanTrigger] = {}
    for trigger in triggers:
        existing = by_code.get(trigger.code)
        if existing is None or trigger.confidence > existing.confidence:
            by_code[trigger.code] = trigger
    return list(by_code.values())
