"""Map human trigger codes (E1–E11) to 07-base CriticalityReason names."""

from __future__ import annotations

from analysis.mental_model.models import HumanTriggerCode

HUMAN_TO_07: dict[HumanTriggerCode, list[str]] = {
    HumanTriggerCode.FREE_MATERIAL: ["TacticalThreat", "MaterialTransformation"],
    HumanTriggerCode.CHECK_CAPTURE_THREAT: ["TacticalThreat", "ForcedSequence"],
    HumanTriggerCode.UNEXPECTED_MOVE: ["EvaluationInstability", "PlanTransition"],
    HumanTriggerCode.PAWN_TEMPO: ["TacticalThreat"],
    HumanTriggerCode.LINE_OPEN_CLOSE: ["StructuralTransformation", "PawnBreakAvailable"],
    HumanTriggerCode.PAWN_STRUCTURE: ["StructuralTransformation"],
    HumanTriggerCode.KING_ATTACK: ["KingSafetyChange", "TacticalThreat"],
    HumanTriggerCode.TRAPPED_OVERLOADED: ["TacticalThreat"],
    HumanTriggerCode.IRREVERSIBLE: ["IrreversiblePawnMove", "MaterialTransformation"],
    HumanTriggerCode.MULTIPLE_CANDIDATES: ["CandidateDivergence"],
    HumanTriggerCode.EVAL_SHIFT: ["EvaluationInstability"],
}


def map_triggers_to_07(codes: list[HumanTriggerCode]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        for reason in HUMAN_TO_07.get(code, []):
            if reason not in seen:
                seen.add(reason)
                ordered.append(reason)
    return ordered
