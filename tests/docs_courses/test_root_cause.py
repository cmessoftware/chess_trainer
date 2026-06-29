"""Tests for root-cause critical move analysis (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.root_cause import (
    analyze_critical_moves,
    build_critical_incidents,
    find_root_move_number,
)

SAMPLE_PGN = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O
9. h3 Nb8 10. d4 Nbd7 11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7 14. Bg5 b4 15. Nb1 h6
16. Bh4 c5 17. dxe5 Nxe4 18. Bxe7 Qxe7 19. exd6 Qf6 20. Nbd2 Nxd6 21. c4 Rxe5
22. Nxe5 Qxe5 23. Rg1 Qf6 24. Qf3 *
"""


def _game_rows_white_mistake_chain() -> pd.DataFrame:
    """White makes an early mistake; a later blunder is a consequence."""
    rows = []
    for move_number, error_label, score_diff, move_san in [
        (14, "mistake", 180.0, "e5"),
        (21, "blunder", 600.0, "c4"),
        (26, "blunder", 900.0, "Rd3"),
    ]:
        rows.append(
            {
                "game_id": "g1",
                "move_number": move_number,
                "player_color": 1,
                "error_label": error_label,
                "score_diff": score_diff,
                "move_san": move_san,
                "phase": "middlegame",
                "white_player": "Alice",
                "black_player": "Bob",
                "king_safety": 0.0,
                "self_mobility": 10,
                "branching_factor": 20,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "material_total": 38,
            }
        )
    for move_number, move_san in [
        (14, "h6"),
        (21, "Rxe5"),
        (26, "Bxd3"),
    ]:
        rows.append(
            {
                "game_id": "g1",
                "move_number": move_number,
                "player_color": 0,
                "error_label": "good",
                "score_diff": 10.0,
                "move_san": move_san,
                "phase": "middlegame",
                "white_player": "Alice",
                "black_player": "Bob",
            }
        )
    return pd.DataFrame(rows)


def test_find_root_move_number_walks_back_to_earlier_mistake():
    game_rows = _game_rows_white_mistake_chain()
    lookup = {
        14: game_rows[(game_rows["move_number"] == 14) & (game_rows["player_color"] == 1)].iloc[0],
        21: game_rows[(game_rows["move_number"] == 21) & (game_rows["player_color"] == 1)].iloc[0],
        26: game_rows[(game_rows["move_number"] == 26) & (game_rows["player_color"] == 1)].iloc[0],
    }
    root = find_root_move_number(
        21,
        is_white=True,
        player_lookup={int(k): v for k, v in lookup.items()},
        walkback_plies=20,
    )
    assert root == 14


def test_build_critical_incidents_groups_late_blunder_under_root():
    player_moves = pd.DataFrame(
        {
            "game_id": ["g1"] * 3,
            "move_number": [14, 21, 26],
            "move_san": ["e5", "c4", "Rd3"],
            "white_player": ["Alice"] * 3,
            "black_player": ["Bob"] * 3,
        }
    )
    labels = pd.Series(["mistake", "blunder", "blunder"])
    incidents = build_critical_incidents(
        player_moves,
        labels,
        game_rows=_game_rows_white_mistake_chain(),
        player_name="Alice",
        walkback_plies=20,
    )
    roots = {item.root_move_number for item in incidents}
    assert 14 in roots
    assert 26 not in roots
    root_incident = next(item for item in incidents if item.root_move_number == 14)
    assert 21 in root_incident.consequence_move_numbers or 26 in root_incident.consequence_move_numbers


def test_analyze_critical_moves_includes_instructional_fields():
    player_moves = pd.DataFrame(
        {
            "game_id": ["g1"],
            "move_number": [21],
            "move_san": ["c4"],
            "phase": ["middlegame"],
            "white_player": ["Alice"],
            "black_player": ["Bob"],
        }
    )
    labels = pd.Series(["blunder"])
    explanations = [
        {
            "predicted_label": "blunder",
            "top_positive_features": [{"feature": "branching_factor", "impact": 0.2}],
            "top_negative_features": [],
        }
    ]
    feature_rows = pd.DataFrame(
        {
            "king_safety": [0],
            "self_mobility": [8],
            "branching_factor": [30],
            "move_number": [21],
            "has_castling_rights": [1],
            "is_pawn_endgame": [0],
            "material_total": [36],
        }
    )
    game_rows = _game_rows_white_mistake_chain()
    moments = analyze_critical_moves(
        player_moves,
        labels,
        explanations,
        feature_rows,
        game_rows=game_rows,
        player_name="Alice",
        pgn_text=SAMPLE_PGN,
        is_white=True,
    )
    assert len(moments) >= 1
    moment = moments[0]
    assert moment["root_cause"] is True
    assert moment["pattern"] in {
        "undefended_pawn",
        "loose_piece_after_pawn_push",
        "hanging_piece",
        "tactical_oversight",
        "passive_rook",
        "king_safety",
        "fork",
        "pin",
        "skewer",
        "loose_piece",
        "passive_piece",
    }
    assert "eval_shift" in moment
    assert "score_cp" not in str(moment)
    assert moment.get("tactical_line") or moment.get("consequence")
