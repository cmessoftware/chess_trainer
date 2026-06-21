"""Kaggle competition package configuration (isolated from course modules)."""

from __future__ import annotations

from pathlib import Path

COMPETITION_ROOT = Path(__file__).resolve().parents[1]
COURSE_ROOT = COMPETITION_ROOT.parent / "ai_chess_coach_course"
DEFAULT_SQLITE_PATH = COURSE_ROOT / "course_data.sqlite"
DEFAULT_OUTPUT_DIR = COMPETITION_ROOT / "output"

EXCLUDED_SOURCES = frozenset({"stockfish"})

# Kaggle spec (8 elo_band buckets, no Stockfish slice) — total 9_700 games.
KAGGLE_ELO_BAND_GAME_QUOTAS: dict[str, int] = {
    "<1200": 1500,
    "1200-1399": 1500,
    "1400-1599": 1500,
    "1600-1799": 1500,
    "1800-1999": 1200,
    "2000-2199": 1000,
    "2200-2399": 800,
    "2400+": 700,
}
KAGGLE_TARGET_GAME_COUNT = sum(KAGGLE_ELO_BAND_GAME_QUOTAS.values())

TIME_CONTROL_TARGET_SHARES: dict[str, float] = {
    "bullet": 0.15,
    "blitz": 0.40,
    "rapid": 0.40,
    "classical": 0.05,
}

COMPLETION_THRESHOLD = 0.95
BAND_UNDERFILL_WARNING_RATIO = 0.85
TIME_CONTROL_WARNING_TOLERANCE = 0.20

ELO_BAND_ORDER: tuple[str, ...] = tuple(KAGGLE_ELO_BAND_GAME_QUOTAS.keys())

TRAIN_TEST_SPLIT = 0.20
RANDOM_STATE = 42
TARGET_COLUMN = "error_label"
TARGET_CLASSES: tuple[str, ...] = ("good", "inaccuracy", "mistake", "blunder")

TACTICAL_TAG_VALUES: tuple[str, ...] = (
    "check",
    "fork",
    "pin",
    "discovered_attack",
    "mate",
)

PUBLIC_FEATURE_COLUMNS: tuple[str, ...] = (
    # Player / game context
    "player_elo",
    "elo_band",
    "time_control_bucket",
    "phase",
    "opening",
    "move_number",
    # Board state (position)
    "fen",
    "move_san",
    "material_total",
    "material_balance",
    "num_pieces",
    "has_castling_rights",
    "is_pawn_endgame",
    # Strategic / tactical proxies (human-pattern features)
    "branching_factor",
    "self_mobility",
    "opponent_mobility",
    "king_safety",
    "center_control",
    "is_low_mobility",
    "is_center_controlled",
    # Tactical motifs (board-pattern detection, no engine)
    "tactical_tag",
    "tag_check",
    "tag_fork",
    "tag_pin",
    "tag_discovered_attack",
    "tag_mate",
)

FORBIDDEN_EXPORT_COLUMNS: frozenset[str] = frozenset(
    {
        "score_cp",
        "score_diff",
        "depth_score_diff",
        "mate_in",
        "cp_loss",
        "best_move_score",
        "played_score_cp",
        "score_delta",
        "best_score_cp",
        "source",
        "game_id",
        "player_color",
        "white_elo",
        "black_elo",
        "white_player",
        "black_player",
        "skill_group",
        "export_skill_group",
        "skill_group_description",
        "time_control",
        "time_control_seconds",
        "result",
        "tags",
    }
)

# Raw feature columns loaded from SQLite (read-only course schema).
FEATURE_LOAD_COLUMNS: tuple[str, ...] = (
    "game_id",
    "move_number",
    "player_color",
    "white_elo",
    "black_elo",
    "source",
    "time_control",
    "opening",
    "fen",
    "move_san",
    "material_total",
    "material_balance",
    "num_pieces",
    "king_safety",
    "center_control",
    "has_castling_rights",
    "is_pawn_endgame",
    "is_low_mobility",
    "is_center_controlled",
    "score_cp",
    "score_diff",
    "phase",
    "branching_factor",
    "self_mobility",
    "opponent_mobility",
    "error_label",
    "tags",
)
