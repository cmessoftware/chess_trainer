# config/tactical_analysis_config.py

TACTICAL_ANALYSIS_SETTINGS = {
    "stockfish_depth": 8,
    "skip_opening_moves": True,
    "opening_move_threshold": 6,
    "min_branching_for_analysis": 5,
    "enable_eval_cache": True,
    "multipv": 2,
    "parallel_processes": 4,
}

PHASE_DEPTHS = {
    "opening": 4,
    "middlegame": 8,
    "endgame": 6
}