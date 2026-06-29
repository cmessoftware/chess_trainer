"""Translate feature columns into chess language (V5 — no raw feature names)."""

from __future__ import annotations

import pandas as pd

LOW_MOBILITY = 8
HIGH_OPPONENT_MOBILITY = 14


def _float_value(row: pd.Series, name: str, default: float = 0.0) -> float:
    if name not in row.index:
        return default
    value = row.get(name)
    if value is None or pd.isna(value):
        return default
    return float(value)


def interpret_features(row: pd.Series) -> list[str]:
    phrases: list[str] = []

    self_mobility = _float_value(row, "self_mobility")
    opponent_mobility = _float_value(row, "opponent_mobility")
    king_safety = _float_value(row, "king_safety")
    center = _float_value(row, "center_control")

    if self_mobility <= LOW_MOBILITY:
        phrases.append("tus piezas tuvieron pocas casillas activas")
    if opponent_mobility >= HIGH_OPPONENT_MOBILITY:
        phrases.append("las piezas del rival ganaron actividad")
    if king_safety < -1.0:
        phrases.append("la seguridad del rey empeoró")
    elif king_safety > 1.0:
        phrases.append("el rey quedó relativamente expuesto")

    if center < -0.5:
        phrases.append("perdiste control del centro")
    elif center > 0.5:
        phrases.append("cediste influencia central")

    if int(_float_value(row, "is_low_mobility")) == 1:
        phrases.append("una o más piezas quedaron muy limitadas")
    if int(_float_value(row, "is_center_controlled")) == 0 and center <= 0:
        phrases.append("el centro dejó de estar bien controlado")
    if int(_float_value(row, "is_pawn_endgame")) == 1:
        phrases.append("la posición entró en un final de peones")

    return phrases[:3]
