"""
Validator Module - ML vs Stockfish Cross-Validation

Validates ML predictions against Stockfish cp_loss ground truth.
Classification mapping:
  cp_loss <= 40 -> good
  40 < cp_loss <= 90 -> inaccuracy
  90 < cp_loss <= 200 -> mistake
  cp_loss > 200 -> blunder

Final label policy:
  - Default: stockfish_label (engine is ground truth)
  - Optional: prefer_model_if_close (keep ML if matches Stockfish bucket)
"""

from dataclasses import dataclass
from typing import Literal

Label = Literal["good", "inaccuracy", "mistake", "blunder"]


@dataclass(frozen=True)
class ValidationResult:
    """Result of ML vs Stockfish validation"""

    predicted_label: Label
    stockfish_label: Label
    final_label: Label
    cp_loss: int
    model_disagreement: bool


def classify_cp_loss(cp_loss: int) -> Label:
    """
    Classify move quality based on centipawn loss.

    Args:
        cp_loss: Centipawn loss from Stockfish analysis

    Returns:
        Label classification (good/inaccuracy/mistake/blunder)
    """
    if cp_loss <= 40:
        return "good"
    if cp_loss <= 90:
        return "inaccuracy"
    if cp_loss <= 200:
        return "mistake"
    return "blunder"


def validate_prediction(
    predicted_label: Label,
    cp_loss: int,
    *,
    final_label_policy: Literal[
        "stockfish_wins", "prefer_model_if_close"
    ] = "stockfish_wins",
) -> ValidationResult:
    """
    Validate ML prediction against Stockfish ground truth.

    Args:
        predicted_label: Label predicted by ML model
        cp_loss: Centipawn loss from Stockfish
        final_label_policy: Policy for resolving disagreements
            - "stockfish_wins": Always use Stockfish label (default)
            - "prefer_model_if_close": Keep ML if matches Stockfish bucket

    Returns:
        ValidationResult with final label and disagreement flag
    """
    stockfish_label = classify_cp_loss(cp_loss)
    disagreement = predicted_label != stockfish_label

    if final_label_policy == "prefer_model_if_close":
        # Conservative: only keep model if it matches Stockfish bucket exactly
        final_label: Label = predicted_label if not disagreement else stockfish_label
    else:
        # Default: Stockfish always wins
        final_label = stockfish_label

    return ValidationResult(
        predicted_label=predicted_label,
        stockfish_label=stockfish_label,
        final_label=final_label,
        cp_loss=cp_loss,
        model_disagreement=disagreement,
    )
