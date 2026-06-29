"""Convert SHAP explanations into supporting phrases (never expose SHAP jargon)."""

from __future__ import annotations

from typing import Any

FEATURE_PHRASES: dict[str, str] = {
    "king_safety": "la seguridad del rey pesó mucho en el error",
    "self_mobility": "la poca movilidad de tus piezas fue determinante",
    "opponent_mobility": "la actividad creciente del rival influyó en la evaluación",
    "center_control": "el control del centro fue clave en la posición",
    "branching_factor": "había muchas respuestas forzadas por calcular",
    "material_total": "el balance material cambió de forma importante",
    "num_pieces": "la simplificación de piezas marcó la tendencia",
    "has_castling_rights": "los derechos de enroque influyeron en la evaluación",
    "is_pawn_endgame": "la estructura de peones en el final fue relevante",
    "move_number": "la fase de la partida condicionó la evaluación",
    "player_elo": "el nivel esperado del jugador contrastó con la jugada",
}


def _impact_map(explanation: dict[str, Any]) -> dict[str, float]:
    impacts: dict[str, float] = {}
    for bucket in ("top_positive_features", "top_negative_features"):
        for item in explanation.get(bucket) or []:
            feature = str(item.get("feature", ""))
            if not feature or feature.startswith("opening_"):
                continue
            impacts[feature] = impacts.get(feature, 0.0) + abs(float(item.get("impact", 0.0)))
    return impacts


def interpret_shap(explanation: dict[str, Any], *, min_impact: float = 0.04) -> list[str]:
    impacts = _impact_map(explanation)
    if not impacts:
        return []

    ranked = sorted(impacts.items(), key=lambda item: item[1], reverse=True)
    phrases: list[str] = []
    for feature, impact in ranked:
        if impact < min_impact:
            continue
        phrase = FEATURE_PHRASES.get(feature)
        if phrase and phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) >= 2:
            break
    return phrases
