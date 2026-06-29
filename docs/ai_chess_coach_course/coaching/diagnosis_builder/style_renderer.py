"""Per-style coaching text templates (V6-lite, Spanish)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from coaching.diagnosis.material import material_change_label_es
from coaching.diagnosis.models import StructuredDiagnosis

LESSONS_BY_TYPE: dict[str, str] = {
    "tactical": "Antes de mover, identifica la respuesta táctica más forzada del rival.",
    "opening": "En la apertura, prioriza desarrollo armónico y control central antes de la actividad a corto plazo.",
    "positional": "Antes de empujar un peón, pregúntate qué pieza enemiga gana fuerza con tu jugada.",
    "endgame": "En finales, la actividad del rey suele pesar más que ganar un peón aislado.",
}


def _move_label(row: pd.Series) -> str:
    san = str(row.get("move_san") or "").strip()
    move_number = row.get("move_number")
    if san and move_number is not None and not pd.isna(move_number):
        return f"{int(move_number)}. {san}"
    return san or "tu jugada"


def _integrate_supporting(sentence: str, supporting: list[str]) -> str:
    if not supporting:
        return sentence
    base = sentence.rstrip(".")
    extras = supporting[:2]
    if len(extras) == 1:
        return f"{base}; además, {extras[0]}."
    return f"{base}; además, {extras[0]} y {extras[1]}."


def _opening_issue(move_label: str, opponent_reply: str | None) -> str:
    if opponent_reply:
        return (
            f"Con {move_label} permitiste una respuesta activa del rival ({opponent_reply}) "
            f"mientras tu desarrollo no estaba armónico."
        )
    return f"Con {move_label} el desarrollo quedó desequilibrado respecto al plan de apertura."


def _positional_issue(move_label: str, theme: str | None) -> str:
    if theme and "pasiv" in theme.lower():
        return f"Con {move_label} tus piezas perdieron actividad en la posición."
    return f"Con {move_label} la estructura posicional favoreció más al rival que a ti."


def _endgame_issue(move_label: str, move_san: str) -> str:
    san = move_san.lower()
    if san.startswith("k"):
        return f"Con {move_label} tu rey perdió casillas útiles en el final."
    if san.startswith("r"):
        return f"Con {move_label} la torre quedó mal coordinada en el final."
    return f"Con {move_label} la coordinación de piezas empeoró en el final."


def _positional_consequence(supporting: list[str], material_change: str) -> str:
    if supporting:
        return _integrate_supporting(
            "La iniciativa y la actividad de las piezas cambiaron de bando",
            supporting,
        )
    material = material_change_label_es(material_change)
    if material_change != "none":
        return f"La posición cedió {material} y la iniciativa."
    return "Tus piezas quedaron más pasivas y el rival mejoró su coordinación."


def _opening_consequence(supporting: list[str]) -> str:
    base = "El rival igualizó cómodamente y obtuvo mejor central o iniciativa"
    return _integrate_supporting(base, supporting)


def _endgame_consequence(supporting: list[str]) -> str:
    base = "El rival coordinó rey y piezas mayores con más facilidad"
    return _integrate_supporting(base, supporting)


def apply_diagnosis_style(
    diagnosis: StructuredDiagnosis,
    diagnosis_type: str,
    row: pd.Series,
    *,
    opponent_reply: str | None = None,
    tactical_line: str | None = None,
) -> StructuredDiagnosis:
    """Rewrite issue/consequence/lesson according to diagnosis_type."""
    move_label = _move_label(row)
    move_san = str(row.get("move_san") or "")
    supporting = list(diagnosis.supporting_features or [])
    theme = diagnosis.theme
    material = diagnosis.material_change

    sections: dict[str, Any] = {"decision": move_label}

    if diagnosis_type == "tactical":
        issue = diagnosis.issue
        consequence = diagnosis.consequence
        if tactical_line and "secuencia" not in consequence.lower():
            consequence = f"La secuencia {tactical_line} aprovechó el error."
        elif opponent_reply and "rival" not in consequence.lower():
            material_phrase = material_change_label_es(material)
            if material != "none":
                consequence = (
                    f"El rival respondió {opponent_reply} y la posición sufrió {material_phrase}."
                )
            else:
                consequence = f"El rival respondió {opponent_reply} y la iniciativa cambió."
        consequence = _integrate_supporting(consequence, supporting)
        lesson = diagnosis.lesson_hint or LESSONS_BY_TYPE["tactical"]
        sections["tactical_punishment"] = opponent_reply
        sections["consequence"] = consequence
        sections["lesson"] = lesson
    elif diagnosis_type == "opening":
        issue = _opening_issue(move_label, opponent_reply)
        consequence = _opening_consequence(supporting)
        lesson = LESSONS_BY_TYPE["opening"]
        sections["positional_change"] = issue
        sections["consequence"] = consequence
        sections["lesson"] = lesson
        opponent_reply = None
    elif diagnosis_type == "endgame":
        issue = _endgame_issue(move_label, move_san)
        consequence = _endgame_consequence(supporting)
        lesson = LESSONS_BY_TYPE["endgame"]
        sections["positional_change"] = issue
        sections["consequence"] = consequence
        sections["lesson"] = lesson
        opponent_reply = None
    else:
        issue = _positional_issue(move_label, theme)
        issue = _integrate_supporting(issue, supporting[:1])
        consequence = _positional_consequence(supporting[1:], material)
        lesson = LESSONS_BY_TYPE["positional"]
        sections["positional_change"] = issue
        sections["consequence"] = consequence
        sections["lesson"] = lesson
        opponent_reply = None

    diagnosis.diagnosis_type = diagnosis_type
    diagnosis.issue = issue
    diagnosis.consequence = consequence
    diagnosis.lesson_hint = lesson
    diagnosis.sections = sections
    diagnosis.include_opponent_reply = diagnosis_type == "tactical" and bool(opponent_reply)
    return diagnosis
