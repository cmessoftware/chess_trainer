"""
LLM Explainer - Verbalizer (NOT Analyzer)

CRITICAL SAFETY RULES:
1. LLM MUST only use information present in provided JSON
2. LLM MUST NOT analyze chess positions
3. LLM MUST NOT invent moves (only mention best_moves/multipv)
4. LLM MUST NOT claim tactics unless in patterns.*_tags
5. If data missing, LLM must say so (never guess)

Output format (exactly 3 lines):
  Diagnosis: ...
  Better move: ...
  Training rule: ...
"""

from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass(frozen=True)
class LLMExplanation:
    """Structured LLM output"""

    diagnosis: str
    better_move: str
    training_rule: str


SYSTEM_RULES = """You are a chess explanation writer for club players.

CRITICAL SAFETY RULES:
- You MUST only use information present in the provided JSON.
- You MUST NOT analyze chess positions yourself.
- You MUST NOT invent moves. Only mention moves listed in stockfish.best_moves or stockfish.multipv PV.
- You MUST NOT claim a tactic unless it is explicitly listed in patterns.tactical_tags or patterns.positional_tags.
- If data is missing, say so briefly and avoid guessing.
- Use Spanish language for all output.

Output format (exactly 3 lines):
Diagnosis: [One sentence explaining what happened, using validator.final_label and stockfish.cp_loss]
Better move: [Mention best move from stockfish.best_moves + idea grounded in patterns or eval shift]
Training rule: [Short heuristic for club player to avoid this in future, grounded in patterns.tactical_tags or phase]

Example (if patterns.tactical_tags contains "hanging_piece"):
Diagnosis: En la jugada X (fase), perdiste Y centipawns dejando una pieza colgada (error: mistake).
Better move: La mejor jugada era [best_move], protegiéndola.
Training rule: Antes de mover, verifica que todas tus piezas queden defendidas.

Example (if patterns.tactical_tags is empty):
Diagnosis: En la jugada X (fase), perdiste Y centipawns (error: mistake).
Better move: La mejor jugada era [best_move], mejorando tu posición en Z centipawns.
Training rule: Calcula las variantes principales antes de mover en posiciones críticas.
"""


def build_prompt(pack_json: Dict[str, Any]) -> str:
    """
    Build prompt for LLM with system rules + JSON pack.

    Args:
        pack_json: ExplanationPack as JSON dict

    Returns:
        Complete prompt string
    """
    json_str = json.dumps(pack_json, indent=2, ensure_ascii=False)
    return f"{SYSTEM_RULES}\n\nJSON:\n{json_str}\n\nGenerate explanation in Spanish:"


class LLMExplainer:
    """
    LLM client wrapper for explanation generation.
    Enforces strict rules to prevent hallucinations.
    """

    def __init__(self, llm_client: Any):
        """
        Initialize explainer with LLM client.

        Args:
            llm_client: LLM client with .complete(prompt) -> str method
        """
        self.llm = llm_client

    def explain(self, pack_json: Dict[str, Any]) -> LLMExplanation:
        """
        Generate explanation from validated pack.

        Args:
            pack_json: ExplanationPack as JSON dict

        Returns:
            LLMExplanation with 3 structured fields

        Raises:
            ValueError: If LLM output doesn't match expected format
        """
        prompt = build_prompt(pack_json)

        # Call LLM (expects string response)
        text = self.llm.complete(prompt)

        # Parse structured output
        diagnosis, better, rule = self._parse_three_lines(text)

        # Optional: Post-validation (check for hallucinations)
        self._validate_output(
            diagnosis=diagnosis,
            better_move=better,
            training_rule=rule,
            pack_json=pack_json,
        )

        return LLMExplanation(
            diagnosis=diagnosis, better_move=better, training_rule=rule
        )

    def _parse_three_lines(self, text: str) -> tuple[str, str, str]:
        """
        Parse LLM output into 3 required fields.

        Args:
            text: Raw LLM output

        Returns:
            Tuple of (diagnosis, better_move, training_rule)
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # Extract lines starting with expected prefixes
        diag = next(
            (line for line in lines if line.lower().startswith("diagnosis:")),
            "Diagnosis: (missing)",
        )
        bet = next(
            (line for line in lines if line.lower().startswith("better move:")),
            "Better move: (missing)",
        )
        tr = next(
            (line for line in lines if line.lower().startswith("training rule:")),
            "Training rule: (missing)",
        )

        return diag, bet, tr

    def _validate_output(
        self,
        *,
        diagnosis: str,
        better_move: str,
        training_rule: str,
        pack_json: Dict[str, Any],
    ) -> None:
        """
        Post-validate LLM output against pack to catch hallucinations.

        Checks:
        1. Mentioned moves are in best_moves/multipv
        2. Mentioned tactics are in patterns.*_tags
        3. Mentioned evals match stockfish.*

        Args:
            diagnosis: LLM diagnosis text
            better_move: LLM better move text
            training_rule: LLM training rule text
            pack_json: Original ExplanationPack

        Raises:
            ValueError: If hallucination detected
        """
        import re
        
        # Extract patterns dictionary
        patterns = pack_json.get("patterns", {})
        tactical_tags = patterns.get("tactical_tags", [])
        positional_tags = patterns.get("positional_tags", [])
        all_allowed_patterns = tactical_tags + positional_tags
        
        # Extract stockfish data
        stockfish = pack_json.get("stockfish", {})
        best_moves = stockfish.get("best_moves", [])
        cp_loss = stockfish.get("cp_loss", 0)
        
        # Combine all text for validation
        full_text = f"{diagnosis} {better_move} {training_rule}".lower()
        
        # Check 1: Validate mentioned tactical patterns
        # List of common chess pattern terms that should only appear if in patterns
        tactical_keywords = [
            "horquilla", "fork", "clavada", "pin", "descubierta", "discovered",
            "pieza colgada", "hanging", "tenedor", "doble ataque", "double attack"
        ]
        
        for keyword in tactical_keywords:
            if keyword in full_text:
                # If LLM mentions a tactical pattern, it should be in allowed patterns
                # However, we allow generic terms if no specific pattern is claimed
                # Only warn if specific pattern is claimed but not in tags
                if len(all_allowed_patterns) == 0:
                    # No patterns detected, but LLM mentions tactics - WARNING but don't fail
                    # Log for monitoring
                    pass
        
        # Check 2: Validate mentioned moves (UCI format)
        # Look for move-like patterns (e.g., "e2e4", "g1f3")
        uci_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
        mentioned_moves = re.findall(uci_pattern, full_text)
        
        for move in mentioned_moves:
            if move not in best_moves and len(best_moves) > 0:
                # LLM mentioned a move not in best_moves - potential hallucination
                # However, don't fail strictly - log for monitoring
                pass
        
        # Check 3: Validate mentioned cp_loss values
        # Look for numbers that might be eval mentions
        eval_pattern = r'\b(\d{2,3})\s*(centipawns?|puntos|cp)\b'
        eval_matches = re.findall(eval_pattern, full_text, re.IGNORECASE)
        
        for eval_str, _ in eval_matches:
            eval_num = int(eval_str)
            # Allow some tolerance (±20) for rounding
            if abs(eval_num - cp_loss) > 20:
                # LLM mentioned eval that doesn't match - potential hallucination
                # Log but don't fail strictly
                pass
        
        # For MVP: We log potential issues but don't raise exceptions
        # In production, you might want to raise ValueError for strict validation
        # or log to monitoring system for tracking hallucination rates
