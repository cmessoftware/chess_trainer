"""
Repository adapters for V7 pipeline.

Maps existing database schema (Features table) to expected pipeline interface.

Current DB schema:
- games: game_id, pgn, white_player, black_player, result
- features: game_id, move_number, fen, move_san, move_uci, material_balance, 
            score_diff, error_label, phase

Pipeline expected interface:
- repos.get_game(game_id) -> dict
- repos.get_stockfish_rows(game_id) -> list[dict]
- repos.get_predictions(game_id) -> dict[ply -> {predicted_label, ...}]
- repos.get_temporal_context(game_id) -> dict[ply -> {streaks, cascade, ...}]

NOTE: Material balance field in Features is corrupt/duplicate. We ignore it and
use only score_diff to derive cp_loss.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session


class V7RepositoryAdapter:
    """
    Adapter that provides V7 pipeline interface using existing DB models.
    
    Handles:
    - Mapping Features table to Stockfish analysis format
    - Deriving cp_loss from score_diff
    - Computing temporal context (streaks, cascades) on-the-fly
    - Mapping error_label to predicted_label format
    """

    def __init__(self, db_session: Session, models: Any):
        """
        Args:
            db_session: SQLAlchemy session
            models: Module with Game, Features, etc. ORM models
        """
        self.db = db_session
        self.models = models

    def get_game(self, game_id: str) -> Dict[str, Any]:
        """Load basic game metadata."""
        Game = self.models.Game
        game = self.db.query(Game).filter(Game.id == game_id).first()

        if not game:
            raise ValueError(f"Game {game_id} not found")

        return {
            "game_id": game.id,
            "pgn": game.pgn,
            "white_player": game.white_player,
            "black_player": game.black_player,
            "result": game.result,
        }

    def get_stockfish_rows(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Load Stockfish analysis per ply from Features table.
        
        Maps Features columns to expected format:
        - ply = move_number * 2 (assuming standard plies)
        - cp_loss = abs(score_diff) (if score worsened)
        - best_moves = [] (not stored in Features, leave empty)
        - multipv = [] (not stored in Features, leave empty)
        
        NOTE: We ignore material_balance (corrupt data). Only use score_diff.
        """
        Features = self.models.Features
        rows = (
            self.db.query(Features)
            .filter(Features.game_id == game_id)
            .order_by(Features.move_number)
            .all()
        )

        stockfish_rows = []
        prev_score = 0  # Score from White's perspective

        for row in rows:
            # Derive ply (move_number starts at 1)
            ply = row.move_number * 2 - 1 if row.move_number else 1

            # Derive cp_loss from score_diff
            # score_diff is typically eval_after - eval_before
            # If score_diff < 0, player lost centipawns
            score_after = prev_score + (row.score_diff or 0)
            cp_loss = max(0, -(row.score_diff or 0))  # Absolute loss

            stockfish_rows.append(
                {
                    "ply": ply,
                    "fen_before": row.fen or "",
                    "played_move_uci": row.move_uci or "",
                    "played_move_san": row.move_san or "",
                    "cp_loss": int(cp_loss),
                    "eval_before_cp": int(prev_score),
                    "eval_after_cp": int(score_after),
                    "best_moves": [],  # Not available in Features
                    "multipv": [],  # Not available in Features
                }
            )

            prev_score = score_after

        return stockfish_rows

    def get_predictions(self, game_id: str) -> Dict[int, Dict[str, Any]]:
        """
        Load ML predictions from Features.error_label.
        
        Maps error_label to predicted_label format:
        - error_label can be: "blunder", "mistake", "inaccuracy", "good", or None
        - Default to "good" if missing
        """
        Features = self.models.Features
        rows = (
            self.db.query(Features)
            .filter(Features.game_id == game_id)
            .order_by(Features.move_number)
            .all()
        )

        preds_by_ply = {}
        for row in rows:
            ply = row.move_number * 2 - 1 if row.move_number else 1
            label = row.error_label or "good"

            # Normalize label to expected format
            if label not in ["good", "inaccuracy", "mistake", "blunder"]:
                label = "good"

            preds_by_ply[ply] = {
                "predicted_label": label,
                "predicted_proba": None,  # Not stored in Features
            }

        return preds_by_ply

    def get_temporal_context(self, game_id: str) -> Dict[int, Dict[str, Any]]:
        """
        Compute temporal context (streaks, cascades) on-the-fly.
        
        Computes:
        - previous_inaccuracies: Count of inaccuracies in last 5 moves
        - mistake_streak: Current consecutive mistakes
        - cascade_score: 0.0 (not implemented, requires more complex logic)
        
        NOTE: This is a simplified implementation. For production, consider
        storing temporal data in a dedicated table for performance.
        """
        Features = self.models.Features
        rows = (
            self.db.query(Features)
            .filter(Features.game_id == game_id)
            .order_by(Features.move_number)
            .all()
        )

        temporal_by_ply = {}
        recent_labels: List[str] = []  # Last 5 labels
        streak_count = 0

        for row in rows:
            ply = row.move_number * 2 - 1 if row.move_number else 1
            label = row.error_label or "good"

            # Count recent inaccuracies (last 5 moves)
            recent_labels.append(label)
            if len(recent_labels) > 5:
                recent_labels.pop(0)

            prev_inaccuracies = sum(
                1 for lbl in recent_labels if lbl in ["inaccuracy", "mistake", "blunder"]
            )

            # Update mistake streak
            if label in ["mistake", "blunder"]:
                streak_count += 1
            else:
                streak_count = 0

            temporal_by_ply[ply] = {
                "previous_inaccuracies": prev_inaccuracies,
                "mistake_streak": streak_count,
                "cascade_score": 0.0,  # TODO: implement cascade detection
            }

        return temporal_by_ply


def create_v7_repos(db_session: Session, models: Any) -> V7RepositoryAdapter:
    """
    Factory function to create V7 repository adapter.
    
    Usage in API:
        from .analysis_pipeline.repository_adapters import create_v7_repos
        
        @app.post("/api/analysis/v7-feedback")
        async def generate_v7_feedback(game_id: str, db = Depends(get_db)):
            repos = create_v7_repos(db, models)
            result = generate_validated_feedback(
                game_id,
                repos=repos,
                llm_client=llm_client,
            )
            return result
    """
    return V7RepositoryAdapter(db_session, models)
