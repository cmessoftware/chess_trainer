"""
Analysis Pipeline V7 - Validated Explanation System

Prevents LLM hallucinations by grounding ALL feedback in:
- Stored Stockfish analysis (per-move, in DB)
- Stored ML predictions (error_label)
- Stored temporal patterns (streaks, cascades)

The LLM ONLY verbalizes a structured JSON we build.
If something is not in JSON, it must not appear in the explanation.

Architecture:
- validator.py: ML vs Stockfish cross-validation
- pattern_engine.py: Conservative pattern detection
- explanation_pack.py: JSON structure for LLM
- llm_explainer.py: LLM verbalizer (no chess analysis)
- pipeline.py: Orchestrator
"""

from .validator import validate_prediction, classify_cp_loss, ValidationResult, Label
from .pattern_engine import PatternEngine, PatternResult
from .explanation_pack import ExplanationPack, build_explanation_pack
from .llm_explainer import LLMExplainer, LLMExplanation
from .pipeline import generate_validated_feedback
from .repository_adapters import V7RepositoryAdapter, create_v7_repos

__all__ = [
    "validate_prediction",
    "classify_cp_loss",
    "ValidationResult",
    "Label",
    "PatternEngine",
    "PatternResult",
    "ExplanationPack",
    "build_explanation_pack",
    "LLMExplainer",
    "LLMExplanation",
    "generate_validated_feedback",
    "V7RepositoryAdapter",
    "create_v7_repos",
]
