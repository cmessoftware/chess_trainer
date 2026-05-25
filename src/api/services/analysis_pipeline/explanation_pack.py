"""
Explanation Pack - JSON Structure for LLM

Builds a complete, self-contained JSON with ALL information needed
for generating explanations. The LLM must ONLY use data present in this pack.

Structure:
{
  "game_id": "...",
  "ply": 23,
  "phase": "middlegame",
  "played_move": "e2e4",
  "final_label": "mistake",
  "validator": {
     "predicted_label": "...",
     "stockfish_label": "...",
     "final_label": "...",
     "cp_loss": 123,
     "model_disagreement": true
  },
  "stockfish": {
     "eval_before_cp": 15,
     "eval_after_cp": -110,
     "cp_loss": 125,
     "best_moves": ["g1f3","d2d4"],
     "multipv": [...]
  },
  "patterns": {
     "tactical_tags": ["pin"],
     "positional_tags": ["exposed_king"]
  },
  "temporal_context": {
     "previous_inaccuracies": 2,
     "mistake_streak": 3,
     "cascade_score": 0.72
  }
}
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Literal, Optional

Label = Literal["good", "inaccuracy", "mistake", "blunder"]


@dataclass
class ExplanationPack:
    """
    Complete data pack for LLM explanation generation.
    Contains ALL information needed; LLM must not add external data.
    """

    game_id: str
    ply: int
    phase: str
    played_move: str  # UCI notation
    final_label: Label

    validator: Dict[str, Any]
    stockfish: Dict[str, Any]
    patterns: Dict[str, Any]
    temporal_context: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)


def phase_from_ply(ply: int, total_plies: Optional[int] = None) -> str:
    """
    Determine game phase from ply number.

    Simple heuristic (can be replaced with piece-count based logic):
    - Opening: plies 1-20
    - Middlegame: plies 21-60
    - Endgame: plies 61+

    Args:
        ply: Current ply number
        total_plies: Total plies in game (optional, for proportional calc)

    Returns:
        Phase name ("opening", "middlegame", "endgame")
    """
    if total_plies:
        # Proportional: first 25%, middle 50%, last 25%
        proportion = ply / total_plies
        if proportion < 0.25:
            return "opening"
        if proportion < 0.75:
            return "middlegame"
        return "endgame"

    # Fixed thresholds
    if ply <= 20:
        return "opening"
    if ply <= 60:
        return "middlegame"
    return "endgame"


def build_explanation_pack(
    *,
    game_id: str,
    ply: int,
    played_move_uci: str,
    final_label: Label,
    validator: Dict[str, Any],
    stockfish_row: Dict[str, Any],
    patterns: Dict[str, Any],
    temporal_context: Dict[str, Any],
    total_plies: Optional[int] = None,
) -> ExplanationPack:
    """
    Build a complete explanation pack from validated data.

    Args:
        game_id: Unique game identifier
        ply: Ply number (half-move count)
        played_move_uci: Move played in UCI notation
        final_label: Final validated label
        validator: Validation result dict
        stockfish_row: Stockfish analysis dict
        patterns: Pattern detection result dict
        temporal_context: Temporal patterns dict
        total_plies: Total plies in game (optional)

    Returns:
        ExplanationPack ready for LLM consumption
    """
    return ExplanationPack(
        game_id=game_id,
        ply=ply,
        phase=phase_from_ply(ply, total_plies),
        played_move=played_move_uci,
        final_label=final_label,
        validator=validator,
        stockfish={
            "eval_before_cp": stockfish_row.get("eval_before_cp"),
            "eval_after_cp": stockfish_row.get("eval_after_cp"),
            "cp_loss": stockfish_row.get("cp_loss"),
            "best_moves": stockfish_row.get("best_moves", []) or [],
            "multipv": stockfish_row.get("multipv", []) or [],
        },
        patterns=patterns,
        temporal_context=temporal_context,
    )
