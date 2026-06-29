"""Spanish coaching text from structured pattern matches."""

from __future__ import annotations

from coaching.diagnosis.material import material_change_label_es
from coaching.diagnosis.models import DiagnosisContext, PatternMatch


def build_issue(match: PatternMatch, context: DiagnosisContext) -> str:
    move = context.player_move_san
    piece = match.affected_piece or "una pieza"
    builders = {
        "hanging_piece": f"Con {move} dejaste {piece} sin defensa.",
        "undefended_pawn": f"El empuje {move} dejó {piece} capturable.",
        "loose_piece_after_pawn_push": (
            f"Al avanzar con {move}, {piece} perdió respaldo y quedó expuesta."
        ),
        "fork": f"Tras {move}, el rival ejecutó un ataque doble sobre {piece}.",
        "pin": f"Después de {move}, {piece} quedó clavada.",
        "skewer": f"La respuesta del rival clavó {piece} y ganó material.",
        "king_safety": f"Con {move} debilitaste la seguridad del rey.",
        "passive_rook": f"Con {move} la torre quedó pasiva y sin contrajuego.",
        "tactical_oversight": (
            f"Con {move} pasaste por alto una respuesta forzada concreta del rival."
        ),
    }
    return builders.get(match.pattern_id, builders["tactical_oversight"])


def build_consequence(
    match: PatternMatch,
    context: DiagnosisContext,
    material_change: str,
) -> str:
    if context.tactical_line:
        return f"La secuencia {context.tactical_line} aprovechó el error."
    if context.opponent_move_san:
        material_phrase = material_change_label_es(material_change)
        if material_change != "none":
            return (
                f"El rival respondió {context.opponent_move_san} y la posición "
                f"sufrió {material_phrase}."
            )
        return f"El rival respondió {context.opponent_move_san} y la iniciativa cambió de mano."
    if context.cp_loss >= 500:
        return "La posición pasó a una desventaja decisiva."
    if context.cp_loss >= 150:
        return "La posición cedió iniciativa o material."
    return "La coordinación de las piezas se debilitó."


def build_lesson_hint(match: PatternMatch, context: DiagnosisContext) -> str:
    lessons = {
        "hanging_piece": "Antes de mover, comprueba que ninguna pieza quede capturable sin defensa.",
        "undefended_pawn": (
            "Antes de empujar un peón, verifica que los peones avanzados sigan defendidos."
        ),
        "loose_piece_after_pawn_push": (
            "Al empujar un peón, revisa qué piezas dejan de estar defendidas."
        ),
        "fork": "Cuando el rival puede dar jaque y atacar otra pieza, calcula toda la secuencia.",
        "pin": "Si una pieza queda clavada, busca romper la clavada o retirar la pieza valiosa.",
        "skewer": "Antes de mover una pieza valiosa en línea, revisa ataques a través de ella.",
        "king_safety": "Antes de abrir la posición, confirma que tu rey no recibe jaques forzados.",
        "passive_rook": "En finales de torres, busca actividad antes de mover piezas a casillas pasivas.",
        "tactical_oversight": (
            f"Antes de jugar {context.player_move_san}, calcula la respuesta más forzada del rival."
        ),
    }
    return lessons.get(match.pattern_id, lessons["tactical_oversight"])
