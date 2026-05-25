"""
Pipeline - Validated Explanation Orchestrator

Main entry point: generate_validated_feedback(game_id)

Orchestrates:
1. Load game data from DB
2. Load Stockfish analysis per ply
3. Load ML predictions per ply
4. Validate ML vs Stockfish (validator)
5. Detect patterns (pattern_engine)
6. Build explanation packs
7. Generate LLM explanations
8. Return structured feedback

Threading: Pure functions (validator, pattern_engine) are deterministic.
I/O operations (DB, LLM) are orchestrated here.
"""

from typing import Any, Dict, List
from .validator import validate_prediction
from .pattern_engine import PatternEngine
from .explanation_pack import build_explanation_pack
from .llm_explainer import LLMExplainer


def generate_validated_feedback(
    game_id: str,
    *,
    repos: Any,  # Repository interface (adapt to your project)
    llm_client: Any,  # LLM client interface
    cp_loss_threshold: int = 90,
    max_items: int = 10,
) -> Dict[str, Any]:
    """
    Generate validated feedback for a game using grounded analysis.

    Architecture V7: LLM does NOT analyze chess, only verbalizes validated JSON.

    Args:
        game_id: Unique game identifier
        repos: Repository interface providing:
            - get_game(game_id) -> dict
            - get_stockfish_rows(game_id) -> list[dict]
            - get_predictions(game_id) -> dict[ply -> {predicted_label, ...}]
            - get_temporal_context(game_id) -> dict[ply -> {streaks, cascade, ...}]
        llm_client: LLM client with .complete(prompt) -> str method
        cp_loss_threshold: Minimum cp_loss to consider critical (default: 90)
        max_items: Maximum critical moves to analyze (default: 10)

    Returns:
        {
          "game_id": ...,
          "stats": {
            "num_moves_analyzed": ...,
            "num_critical": ...,
            "num_disagreements": ...
          },
          "critical_feedback": [
            {
              "ply": ...,
              "final_label": ...,
              "model_disagreement": ...,
              "explanation": {
                "diagnosis": ...,
                "better_move": ...,
                "training_rule": ...
              },
              "pack": {...}  # Optional: for debugging
            },
            ...
          ]
        }
    """

    # Step 1: Load game data (for metadata, not used in MVP)
    _ = repos.get_game(game_id)  # Validate game exists

    # Step 2: Load Stockfish analysis (per ply)
    # Expected format: [
    #   {
    #     "ply": 23,
    #     "fen_before": "...",
    #     "played_move_uci": "e2e4",
    #     "cp_loss": 125,
    #     "eval_before_cp": 15,
    #     "eval_after_cp": -110,
    #     "best_moves": ["g1f3", "d2d4"],
    #     "multipv": [{"rank": 1, "pv": [...], "eval_cp": ...}, ...]
    #   },
    #   ...
    # ]
    stockfish_rows: List[Dict[str, Any]] = repos.get_stockfish_rows(game_id)

    # Step 3: Load ML predictions
    # Expected format: {ply: {"predicted_label": "mistake", ...}, ...}
    preds_by_ply: Dict[int, Dict[str, Any]] = repos.get_predictions(game_id)

    # Step 4: Load temporal context
    # Expected format: {ply: {"previous_inaccuracies": 2, "mistake_streak": 3, ...}, ...}
    temporal_by_ply: Dict[int, Dict[str, Any]] = repos.get_temporal_context(game_id)

    # Initialize modules
    pattern_engine = PatternEngine()
    explainer = LLMExplainer(llm_client)

    critical_items = []
    disagreements = 0

    # Step 5: Select critical moves
    candidates = []
    for row in stockfish_rows:
        ply = int(row["ply"])
        cp_loss = int(row.get("cp_loss") or 0)
        pred = preds_by_ply.get(ply)

        # Get predicted label (default to "good" if missing)
        predicted_label = (pred or {}).get("predicted_label", "good")

        # Validate ML vs Stockfish
        validation = validate_prediction(predicted_label, cp_loss)

        # Get temporal context
        temporal = temporal_by_ply.get(ply, {})
        streak = int(temporal.get("mistake_streak") or 0)
        cascade_score = float(temporal.get("cascade_score") or 0.0)

        # Determine if move is critical
        is_critical = (
            cp_loss >= cp_loss_threshold
            or validation.final_label in ("mistake", "blunder")
            or streak >= 3
            or cascade_score >= 0.7
        )

        if is_critical:
            candidates.append((validation.cp_loss, ply, row, validation, temporal))

    # Sort by impact (highest cp_loss first)
    candidates.sort(reverse=True, key=lambda x: x[0])
    candidates = candidates[:max_items]

    # Step 6-8: Process each critical move
    for _, ply, row, validation, temporal in candidates:
        if validation.model_disagreement:
            disagreements += 1

        # Detect patterns
        patterns = pattern_engine.detect(
            fen_before=row.get("fen_before") or row.get("fen") or "",
            played_move_uci=row.get("played_move_uci")
            or row.get("played_move")
            or "",
            best_move_uci=(row.get("best_moves") or [None])[0],
            multipv_lines=row.get("multipv") or [],
        )

        # Build explanation pack
        pack = build_explanation_pack(
            game_id=game_id,
            ply=ply,
            played_move_uci=row.get("played_move_uci")
            or row.get("played_move")
            or "",
            final_label=validation.final_label,
            validator={
                "predicted_label": validation.predicted_label,
                "stockfish_label": validation.stockfish_label,
                "final_label": validation.final_label,
                "cp_loss": validation.cp_loss,
                "model_disagreement": validation.model_disagreement,
            },
            stockfish_row=row,
            patterns={
                "tactical_tags": patterns.tactical_tags,
                "positional_tags": patterns.positional_tags,
            },
            temporal_context={
                "previous_inaccuracies": temporal.get("previous_inaccuracies", 0),
                "mistake_streak": temporal.get("mistake_streak", 0),
                "cascade_score": temporal.get("cascade_score", 0.0),
            },
        )

        # Generate LLM explanation
        pack_json = pack.to_json()
        llm_text = explainer.explain(pack_json)

        critical_items.append(
            {
                "ply": ply,
                "final_label": validation.final_label,
                "model_disagreement": validation.model_disagreement,
                "explanation": {
                    "diagnosis": llm_text.diagnosis,
                    "better_move": llm_text.better_move,
                    "training_rule": llm_text.training_rule,
                },
                "pack": pack_json,  # Optional: keep for debugging
            }
        )

    # Step 9: Return structured feedback
    return {
        "game_id": game_id,
        "stats": {
            "num_moves_analyzed": len(stockfish_rows),
            "num_critical": len(critical_items),
            "num_disagreements": disagreements,
        },
        "critical_feedback": critical_items,
    }
