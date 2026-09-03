"""F07-006+ — engine-side critical-position triggers (not human E1–E11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import chess

from analysis.engine_eval import EvaluationLoss, NormalizedPlyEval, ply_evaluation_loss
from analysis.multipv import MultiPVResult, analyze_multipv

EngineTriggerCode = Literal["EVALUATION_DROP", "ONLY_MOVE"]

EVALUATION_DROP: EngineTriggerCode = "EVALUATION_DROP"
ONLY_MOVE: EngineTriggerCode = "ONLY_MOVE"
DEFAULT_EVALUATION_DROP_CP = 150
DEFAULT_ONLY_MOVE_GAP_CP = 150
ONLY_MOVE_SOLE_LEGAL_GAP = 100_000


@dataclass(frozen=True)
class EngineTrigger:
    """One engine trigger decision (F07-006+)."""

    code: EngineTriggerCode
    fired: bool
    eval_loss: int
    threshold_cp: int
    detail: str = ""


def evaluation_drop_trigger(
    loss: EvaluationLoss | int,
    *,
    threshold_cp: int = DEFAULT_EVALUATION_DROP_CP,
) -> EngineTrigger:
    """Fire ``EVALUATION_DROP`` when player-POV ``eval_loss`` meets the threshold."""
    eval_loss = loss.eval_loss if isinstance(loss, EvaluationLoss) else int(loss)
    if threshold_cp < 0:
        raise ValueError("threshold_cp must be >= 0")
    return EngineTrigger(
        code=EVALUATION_DROP,
        fired=eval_loss >= threshold_cp,
        eval_loss=eval_loss,
        threshold_cp=threshold_cp,
    )


def ply_evaluation_drop(
    ply_eval: NormalizedPlyEval,
    *,
    threshold_cp: int = DEFAULT_EVALUATION_DROP_CP,
    mate_cp: int = 100_000,
) -> EngineTrigger:
    """F07-005 loss + F07-006 trigger for a player-normalized ply."""
    return evaluation_drop_trigger(
        ply_evaluation_loss(ply_eval, mate_cp=mate_cp),
        threshold_cp=threshold_cp,
    )


def only_move_trigger(
    result: MultiPVResult,
    *,
    gap_cp: int = DEFAULT_ONLY_MOVE_GAP_CP,
    fen: str | None = None,
) -> EngineTrigger:
    """Fire ``ONLY_MOVE`` when there is one legal move or one sufficient MultiPV line.

    Sufficient means PV1 is at least ``gap_cp`` better than PV2 (player POV).
    """
    if gap_cp < 0:
        raise ValueError("gap_cp must be >= 0")
    board = chess.Board(fen or result.fen)
    legal = board.legal_moves.count()
    if legal == 1:
        return EngineTrigger(
            code=ONLY_MOVE,
            fired=True,
            eval_loss=ONLY_MOVE_SOLE_LEGAL_GAP,
            threshold_cp=gap_cp,
        )
    if len(result.lines) < 2:
        fired = len(result.lines) == 1
        return EngineTrigger(
            code=ONLY_MOVE,
            fired=fired,
            eval_loss=ONLY_MOVE_SOLE_LEGAL_GAP if fired else 0,
            threshold_cp=gap_cp,
        )
    gap = max(
        0,
        int(
            result.lines[0].player_score.as_cp_units()
            - result.lines[1].player_score.as_cp_units()
        ),
    )
    return EngineTrigger(
        code=ONLY_MOVE,
        fired=gap >= gap_cp,
        eval_loss=gap,
        threshold_cp=gap_cp,
    )


def ply_only_move(
    fen: str,
    *,
    engine=None,
    depth: int = 12,
    multipv: int = 3,
    player_color=None,
    gap_cp: int = DEFAULT_ONLY_MOVE_GAP_CP,
    multipv_result: MultiPVResult | None = None,
) -> EngineTrigger:
    """F07-007 on a FEN (runs MultiPV unless ``multipv_result`` is provided)."""
    result = multipv_result or analyze_multipv(
        fen,
        engine=engine,
        depth=depth,
        multipv=multipv,
        player_color=player_color,
    )
    return only_move_trigger(result, gap_cp=gap_cp, fen=fen)
