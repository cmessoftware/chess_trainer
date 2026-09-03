"""F07-019 — compare the played move with MultiPV candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chess

from analysis.engine_eval import PlayerScore, open_stockfish
from analysis.game_models import PlayerColor, parse_player_color
from analysis.mental_model.candidate_taxonomy import classify_candidate_move
from analysis.mental_model.models import CandidateCategory
from analysis.multipv import (
    CandidateLine,
    MultiPVResult,
    PlayedMoveEval,
    analyze_multipv,
    evaluate_played_move,
)
from analysis.notation import parse_legal_move

_PIECE_CP = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass(frozen=True)
class MoveConsequence:
    """Observable one-ply outcome (not LLM narrative)."""

    gives_check: bool
    is_capture: bool
    is_mate: bool
    material_delta_cp: int
    opponent_pv_san: str | None
    tags: tuple[str, ...]


@dataclass(frozen=True)
class CandidateDiff:
    """Played move vs one MultiPV line (player POV)."""

    candidate: CandidateLine
    eval_gap_cp: int
    same_move: bool
    purpose: CandidateCategory
    purpose_differs: bool
    consequence: MoveConsequence
    pv_san: tuple[str, ...]


@dataclass(frozen=True)
class PlayedVsCandidates:
    """F07-019 — evaluation, purpose proxy, and consequence diffs."""

    fen: str
    player_color: PlayerColor
    played: PlayedMoveEval
    played_purpose: CandidateCategory
    played_consequence: MoveConsequence
    best: CandidateLine | None
    eval_gap_vs_best_cp: int
    played_is_best: bool
    in_multipv: bool
    diffs: tuple[CandidateDiff, ...]


def _side_material_cp(board: chess.Board, color: chess.Color) -> int:
    total = 0
    for piece in board.piece_map().values():
        if piece.color == color:
            total += _PIECE_CP[piece.piece_type]
    return total


def _player_balance_cp(board: chess.Board, player_color: PlayerColor) -> int:
    color = chess.WHITE if player_color == "white" else chess.BLACK
    return _side_material_cp(board, color) - _side_material_cp(board, not color)


def describe_consequence(
    fen: str,
    move_uci: str,
    player_color: PlayerColor,
    pv_san: tuple[str, ...] = (),
) -> MoveConsequence:
    board = chess.Board(fen)
    move = parse_legal_move(fen, move_uci)
    before = _player_balance_cp(board, player_color)
    is_capture = board.is_capture(move)
    is_castle = board.is_castling(move)
    is_promo = move.promotion is not None
    board.push(move)
    after = _player_balance_cp(board, player_color)
    gives_check = board.is_check()
    is_mate = board.is_checkmate()
    tags: list[str] = []
    if is_capture:
        tags.append("CAPTURE")
    if gives_check:
        tags.append("CHECK")
    if is_mate:
        tags.append("MATE")
    if is_castle:
        tags.append("CASTLE")
    if is_promo:
        tags.append("PROMOTION")
    opponent = pv_san[1] if len(pv_san) > 1 else None
    return MoveConsequence(
        gives_check=gives_check,
        is_capture=is_capture,
        is_mate=is_mate,
        material_delta_cp=after - before,
        opponent_pv_san=opponent,
        tags=tuple(tags),
    )


def _eval_gap(candidate: PlayerScore, played: PlayerScore) -> int:
    return candidate.as_cp_units() - played.as_cp_units()


def compare_played_to_candidates(
    fen: str,
    move_uci: str,
    *,
    engine: Any | None = None,
    depth: int = 12,
    multipv: int = 3,
    player_color: PlayerColor | str | int | None = None,
    multipv_result: MultiPVResult | None = None,
    played: PlayedMoveEval | None = None,
) -> PlayedVsCandidates:
    """Diff the played move against MultiPV lines (F07-019).

    Purpose uses D1–D5 categories until F07-018 (structured objectives).
    """
    board = chess.Board(fen)
    stm: PlayerColor = "white" if board.turn == chess.WHITE else "black"
    color = stm if player_color is None else (
        player_color if player_color in ("white", "black") else parse_player_color(player_color)
    )
    move = parse_legal_move(fen, move_uci)

    def _run(eng: Any) -> PlayedVsCandidates:
        mpv = multipv_result or analyze_multipv(
            fen, engine=eng, depth=depth, multipv=multipv, player_color=color
        )
        played_eval = played or evaluate_played_move(
            fen,
            move.uci(),
            engine=eng,
            depth=depth,
            multipv=multipv,
            player_color=color,
            multipv_result=mpv,
        )
        played_purpose = classify_candidate_move(board, move)
        played_cons = describe_consequence(
            fen, played_eval.move_uci, color, played_eval.pv_san
        )
        diffs: list[CandidateDiff] = []
        for line in mpv.lines:
            cand_move = parse_legal_move(fen, line.move_uci)
            purpose = classify_candidate_move(board, cand_move)
            diffs.append(
                CandidateDiff(
                    candidate=line,
                    eval_gap_cp=_eval_gap(line.player_score, played_eval.player_score),
                    same_move=line.move_uci == played_eval.move_uci,
                    purpose=purpose,
                    purpose_differs=purpose != played_purpose,
                    consequence=describe_consequence(
                        fen, line.move_uci, color, line.pv_san
                    ),
                    pv_san=line.pv_san,
                )
            )
        best = mpv.lines[0] if mpv.lines else None
        gap_best = _eval_gap(best.player_score, played_eval.player_score) if best else 0
        return PlayedVsCandidates(
            fen=board.fen(),
            player_color=color,
            played=played_eval,
            played_purpose=played_purpose,
            played_consequence=played_cons,
            best=best,
            eval_gap_vs_best_cp=gap_best,
            played_is_best=bool(best and best.move_uci == played_eval.move_uci),
            in_multipv=played_eval.in_multipv,
            diffs=tuple(diffs),
        )

    if engine is not None:
        return _run(engine)
    if played is not None and multipv_result is not None:
        return _run(None)
    with open_stockfish() as eng:
        return _run(eng)
