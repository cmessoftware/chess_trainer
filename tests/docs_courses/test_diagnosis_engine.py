"""Tests for V4 DiagnosisEngine and board-based pattern detectors."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.diagnosis import DiagnosisEngine
from coaching.diagnosis.detectors.tactical import UndefendedPawnDetector
from coaching.diagnosis.models import DiagnosisContext
from coaching.pgn_context import parse_pgn_sans, player_ply_index
from coaching.root_cause import analyze_critical_moves

ROOT_CAUSE_PGN = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O
9. h3 Nb8 10. d4 Nbd7 11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7 14. Bg5 b4 15. Nb1 h6
16. Bh4 c5 17. dxe5 Nxe4 18. Bxe7 Qxe7 19. exd6 Qf6 20. Nbd2 Nxd6 21. c4 Rxe5
22. Nxe5 Qxe5 23. Rg1 Qf6 24. Qf3 *
"""


def _row(move_san: str, score_diff: float, error_label: str = "mistake") -> pd.Series:
    return pd.Series(
        {
            "move_san": move_san,
            "score_diff": score_diff,
            "error_label": error_label,
            "phase": "middlegame",
            "branching_factor": 20,
        }
    )


def _sans_through(line: str) -> list[str]:
    board = chess.Board()
    sans: list[str] = []
    for san in line.split():
        sans.append(san)
        board.push_san(san)
    return sans


def test_undefended_pawn_detector_on_board():
    """Board unit test — pawn push leaves a pawn capturable."""
    before = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w KQ - 4 6")
    after_player = before.copy()
    after_player.push_san("b4")
    after_opponent = after_player.copy()
    after_opponent.push_san("Nxe4")

    context = DiagnosisContext(
        row=_row("b4", 600.0, "blunder"),
        error_label="blunder",
        cp_loss=600.0,
        player_color=chess.WHITE,
        root_ply=10,
        sans=["b4", "Nxe4"],
        player_move_san="b4",
        opponent_move_san="Nxe4",
        tactical_line="Nxe4",
        opponent_reply="Nxe4",
        before_board=before,
        after_player_board=after_player,
        after_opponent_board=after_opponent,
    )
    match = UndefendedPawnDetector().detect(context)
    assert match is not None
    assert match.pattern_id in {"undefended_pawn", "loose_piece_after_pawn_push", "hanging_piece"}


def test_diagnosis_engine_produces_specific_issue_for_pawn_push():
    prefix = _sans_through("e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 b3 O-O Bb2 d6")
    sans = prefix + ["b4", "Nxe4"]
    engine = DiagnosisEngine()
    diagnosis = engine.diagnose(
        _row("b4", 600.0, "blunder"),
        error_label="blunder",
        sans=sans,
        root_ply=len(prefix),
        is_white=True,
        tactical_line="Nxe4",
        opponent_reply="Nxe4",
    )
    assert diagnosis.primary_pattern in {
        "undefended_pawn",
        "loose_piece_after_pawn_push",
        "hanging_piece",
        "fork",
    }
    assert "jaques, capturas y amenazas" not in diagnosis.lesson_hint.lower()
    assert diagnosis.material_change != "none"
    assert "b4" in diagnosis.issue or "peón" in diagnosis.issue.lower()


def test_analyze_critical_moves_uses_v4_fields_with_heuristic_fallback():
    player_moves = pd.DataFrame(
        [
            {
                "move_number": 21,
                "move_san": "c4",
                "error_label": "blunder",
                "score_diff": 600.0,
                "phase": "middlegame",
                "white_player": "Alice",
                "black_player": "Bob",
            }
        ]
    )
    labels = pd.Series(["blunder"])
    explanations = [{"predicted_label": "blunder"}]
    feature_rows = pd.DataFrame(
        {
            "king_safety": [0],
            "self_mobility": [8],
            "branching_factor": [30],
            "move_number": [21],
        }
    )
    moments = analyze_critical_moves(
        player_moves,
        labels,
        explanations,
        feature_rows,
        pgn_text=ROOT_CAUSE_PGN,
        is_white=True,
        player_name="Alice",
        max_moments=1,
    )
    assert moments
    moment = moments[0]
    assert "material_change" in moment
    assert "jaques, capturas y amenazas" not in moment.get("lesson", "").lower()
    assert moment.get("issue") or moment.get("concept")
    assert moment["pattern"] in {
        "undefended_pawn",
        "loose_piece_after_pawn_push",
        "hanging_piece",
        "tactical_oversight",
        "passive_piece",
        "fork",
        "pin",
    }
