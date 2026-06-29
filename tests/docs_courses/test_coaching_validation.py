"""Tests for post-LLM coaching response validation (V3)."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.coaching_validation import validate_coaching_response


def _critical_moves() -> list[dict]:
    return [
        {
            "move_number": 21,
            "player_move": "21. c4",
            "opponent_reply": "21... Nxe5",
            "issue": "peón indefenso",
            "lesson_hint": "calcula capturas",
            "context_pgn": "pgn",
            "phase": "middlegame",
            "severity": "blunder",
        },
        {
            "move_number": 29,
            "player_move": "29. f4",
            "issue": "debilita el rey",
            "lesson_hint": "no abrir sin necesidad",
            "context_pgn": "pgn",
            "phase": "endgame",
            "severity": "mistake",
        },
    ]


def test_validate_coaching_response_accepts_compliant_text():
    text = """
### Resumen breve

Jugaste una apertura sólida y el medio juego fue equilibrado. El final exigió más precisión.

### Lecciones principales

#### Lección: Errores tácticos evitables
En el medio juego perdiste material por no ver capturas.

#### Lección: Comprensión posicional
Varias jugadas mejoraron la coordinación rival.

### Momentos clave

- Jugada del alumno: 21. c4
  Respuesta rival: 21... Nxe5
  Peón avanzado sin defensa.

- Jugada del alumno: 29. f4
  Debilita la estructura del rey.

### Plan de entrenamiento
- Verifica defensas antes de empujar
- practica finales
- repasa apertura
"""
    result = validate_coaching_response(text, _critical_moves())
    assert result.ok
    assert not result.extra_move_numbers


def test_validate_coaching_response_rejects_extra_moves():
    text = """
### Resumen breve
Resumen sin jugadas concretas.

### Lecciones principales
#### Lección: Una
Texto.

#### Lección: Dos
Texto.

### Momentos clave
- Jugada del alumno: 6. Nc3
- Jugada del alumno: 21. c4
- Jugada del alumno: 29. f4

### Plan de entrenamiento
- uno
"""
    result = validate_coaching_response(text, _critical_moves())
    assert not result.ok
    assert 6 in result.extra_move_numbers


def test_validate_coaching_response_rejects_wrong_entry_count():
    text = """
### Resumen breve
Resumen.

### Lecciones principales
#### Lección: Una
Texto.

#### Lección: Dos
Texto.

### Momentos clave
- Jugada del alumno: 21. c4

### Plan de entrenamiento
- uno
"""
    result = validate_coaching_response(text, _critical_moves())
    assert not result.ok
    assert any("Expected 2" in error for error in result.errors)


def test_validate_coaching_response_allows_consequence_followup_moves():
    moves = [
        {
            "move_number": 6,
            "player_move": "6. N1c3",
            "opponent_reply": "6...Nd4",
            "issue": "ceguera táctica",
            "lesson_hint": "calcula antes de jugar",
            "context_pgn": "4. Nxd4 4...e5 5. Nb5 5...Nf6 6. N1c3 6...Nd4 7. Nxd4 7...exd4",
            "consequence": "La secuencia 6...Nd4 7. Nxd4 7...exd4 aprovechó el error.",
            "phase": "apertura",
            "severity": "error grave",
        }
    ]
    text = """
### Resumen breve
Apertura tensa sin detallar jugadas aún.

### Lecciones principales
#### Lección: Ceguera táctica
Hubo un error forzado temprano.

### Momentos clave

- Jugada del alumno: 6. N1c3
  Respuesta rival: 6...Nd4
  La secuencia 6...Nd4 7. Nxd4 7...exd4 aprovechó el error.

### Plan de entrenamiento
- calcula antes de jugar
"""
    result = validate_coaching_response(text, moves)
    assert result.ok
    assert 7 not in result.extra_move_numbers
