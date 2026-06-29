"""Convert precomputed tactical tags into structured chess diagnosis (V5)."""

from __future__ import annotations

from dataclasses import dataclass

from coaching.diagnosis_builder.tags_utils import MATERIAL_TAGS, primary_tactical_tag
from coaching.diagnosis.material import (
    MATERIAL_LOST_EXCHANGE,
    MATERIAL_LOST_PAWN,
    MATERIAL_LOST_PIECE,
    MATERIAL_NONE,
)

THEME_ES: dict[str, str] = {
    "fork": "Ataque doble",
    "pin": "Clavada",
    "skewer": "Enfilada",
    "discovered_attack": "Ataque descubierto",
    "discovered_check": "Jaque descubierto",
    "double_attack": "Ataque doble",
    "hanging_piece": "Pieza colgada",
    "remove_defender": "Eliminación del defensor",
    "back_rank": "Mata en la última fila",
    "passed_pawn": "Peón pasado",
    "promotion": "Promoción",
    "mate": "Mate",
    "mate_threat": "Amenaza de mate",
    "check": "Jaque",
    "piece_lost": "Pérdida de material",
    "exchange_lost": "Pérdida de calidad",
    "queen_lost": "Pérdida de dama",
}


def _issue_for_tag(tag: str, move_san: str, opponent_reply: str | None) -> str:
    move = move_san or "tu jugada"
    reply = f" con {opponent_reply}" if opponent_reply else ""
    templates = {
        "fork": f"Con {move} permitiste un ataque doble del rival{reply}.",
        "pin": f"Con {move} una pieza quedó clavada y dejó de defender correctamente{reply}.",
        "skewer": f"Con {move} quedaste expuesto a una enfilada{reply}.",
        "discovered_attack": f"Con {move} el rival activó un ataque descubierto{reply}.",
        "hanging_piece": f"Con {move} dejaste material capturable sin defensa adecuada{reply}.",
        "back_rank": f"Con {move} debilitaste la defensa de la última fila{reply}.",
        "mate": f"Con {move} apareció una secuencia de mate forzada{reply}.",
        "mate_threat": f"Con {move} el rival obtuvo una amenaza de mate{reply}.",
        "check": f"Con {move} no calculaste bien una secuencia con jaque{reply}.",
        "passed_pawn": f"Con {move} el rival creó o activó un peón pasado peligroso{reply}.",
    }
    return templates.get(tag, f"Con {move} se materializó un motivo táctico ({tag}){reply}.")


def _lesson_for_tag(tag: str) -> str:
    lessons = {
        "fork": "Antes de mover, revisa si una pieza rival puede atacar dos objetivos a la vez.",
        "pin": "Si una pieza queda clavada, reevalúa toda la cadena de defensas.",
        "skewer": "Mantén piezas valiosas fuera de la misma línea que otras más débiles.",
        "discovered_attack": "Cuando una pieza se mueve, calcula qué línea queda descubierta detrás.",
        "hanging_piece": "Antes de cada jugada, confirma que todas tus piezas siguen defendidas.",
        "back_rank": "Crea casillas de escape para tu rey antes de activar las torres.",
        "passed_pawn": "Un peón pasado exige contrajuego inmediato o bloqueo con piezas activas.",
        "mate": "Ante jaques forzados, calcula la secuencia completa antes de simplificar.",
        "mate_threat": "Prioriza cortar amenazas de mate antes de ganar material.",
        "check": "Tras un jaque forzado, calcula todas las respuestas obligatorias del rival.",
    }
    return lessons.get(
        tag,
        "Antes de jugar, calcula la respuesta más forzada del rival en la variante concreta.",
    )


def _material_from_tags(tags: list[str]) -> str:
    tag_set = set(tags)
    if "queen_lost" in tag_set or "mate" in tag_set:
        return MATERIAL_LOST_PIECE
    if "exchange_lost" in tag_set:
        return MATERIAL_LOST_EXCHANGE
    if tag_set & MATERIAL_TAGS:
        return MATERIAL_LOST_PAWN if "hanging_piece" not in tag_set else MATERIAL_LOST_PIECE
    return MATERIAL_NONE


@dataclass(frozen=True)
class TacticalInterpretation:
    pattern_id: str
    theme: str
    issue: str
    lesson_hint: str
    material_change: str
    tags: list[str]
    confidence: float

    @property
    def is_actionable(self) -> bool:
        return self.pattern_id not in {"", "normal", "tactical_oversight"} and self.confidence >= 0.55


def interpret_tactical_tags(
    tags: list[str],
    *,
    move_san: str,
    opponent_reply: str | None = None,
) -> TacticalInterpretation | None:
    if not tags:
        return None

    primary = primary_tactical_tag(tags)
    if primary is None:
        return None

    pattern_id = primary
    if "fork" in tags or "double_attack" in tags:
        pattern_id = "fork"
    elif "pin" in tags and "hanging_piece" in tags:
        pattern_id = "pin"

    confidence = 0.65
    if primary in {"fork", "mate", "pin", "skewer", "discovered_attack"}:
        confidence = 0.88
    if len(tags) >= 2 and tags[1] in MATERIAL_TAGS:
        confidence = min(0.95, confidence + 0.08)

    theme = THEME_ES.get(pattern_id, THEME_ES.get(primary, primary.replace("_", " ").title()))
    issue = _issue_for_tag(pattern_id, move_san, opponent_reply)
    if "fork" in tags and any(tag in MATERIAL_TAGS for tag in tags):
        issue = f"Un ataque doble ganó material tras {move_san or 'tu jugada'}."
    if "pin" in tags and "hanging_piece" in tags:
        issue = f"La pieza clavada dejó de defender otra pieza tras {move_san or 'tu jugada'}."

    return TacticalInterpretation(
        pattern_id=pattern_id,
        theme=theme,
        issue=issue,
        lesson_hint=_lesson_for_tag(pattern_id),
        material_change=_material_from_tags(tags),
        tags=tags,
        confidence=confidence,
    )
