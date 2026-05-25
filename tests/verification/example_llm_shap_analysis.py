#!/usr/bin/env python3
"""
Ejemplo de análisis de SHAP con LLM usando los movimientos incluidos.

Muestra cómo:
1. Obtener SHAP values desde API
2. Formatear datos para LLM
3. Generar prompt con contexto de movimiento
4. (Opcionalmente) enviar a OpenAI/Claude

Requirements:
    pip install requests openai anthropic  # (opcional para LLM real)
"""

import requests
import json
from typing import List, Dict
from dataclasses import dataclass

# ========== CONFIGURACIÓN ==========
API_BASE_URL = "http://localhost:8000"
USERNAME = "test_admin"
PASSWORD = "test_password"

# Opcional: Configurar API keys para LLM real
OPENAI_API_KEY = None  # os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = None  # os.getenv("ANTHROPIC_API_KEY")


# ========== CLASES DE DATOS ==========
@dataclass
class ShapValue:
    """Representa un SHAP value con contexto de movimiento."""

    move_number: int
    move_san: str
    move_uci: str
    fen: str
    player_color: str  # 'white' o 'black'
    feature_name: str
    shap_value: float
    feature_value: float
    error_label: str


# ========== FUNCIONES DE API ==========
def login() -> str:
    """Obtiene token de autenticación."""
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    response.raise_for_status()
    return response.json()["token"]


def get_shap_values(game_id: str, token: str) -> List[ShapValue]:
    """Obtiene SHAP values para una partida."""
    response = requests.get(
        f"{API_BASE_URL}/api/analysis/shap/game/{game_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    data = response.json()

    # Convertir a objetos ShapValue
    shap_values = []
    for item in data.get("shap_values", []):
        shap_values.append(
            ShapValue(
                move_number=item["move_number"],
                move_san=item.get("move_san", "N/A"),
                move_uci=item.get("move_uci", "N/A"),
                fen=item.get("fen", "N/A"),
                player_color=item.get("player_color", "unknown"),
                feature_name=item["feature_name"],
                shap_value=item["shap_value"],
                feature_value=item["feature_value"],
                error_label=item["error_label"],
            )
        )

    return shap_values


# ========== ANÁLISIS Y FORMATO ==========
def group_by_move(shap_values: List[ShapValue]) -> Dict[int, List[ShapValue]]:
    """Agrupa SHAP values por número de jugada."""
    moves = {}
    for sv in shap_values:
        if sv.move_number not in moves:
            moves[sv.move_number] = []
        moves[sv.move_number].append(sv)
    return moves


def format_shap_for_llm(move_number: int, values: List[ShapValue]) -> str:
    """Formatea SHAP values de una jugada para prompt LLM."""
    # Ordenar por valor absoluto (mayor impacto primero)
    sorted_values = sorted(values, key=lambda x: abs(x.shap_value), reverse=True)

    # Tomar el primer elemento (todos tienen el mismo move_san, fen, etc.)
    first = sorted_values[0]

    # Emoji para el jugador
    player_emoji = "⚪" if first.player_color == "white" else "⚫"
    player_text = "Blancas" if first.player_color == "white" else "Negras"

    prompt = f"""
{player_emoji} **{player_text} - Jugada {move_number}: {first.move_san}** ({first.move_uci})
🎲 **Clasificación ML**: {first.error_label.upper()}

🏁 **Posición FEN**:
```
{first.fen}
```

📊 **SHAP Values** (impacto en la clasificación):
"""

    for i, sv in enumerate(sorted_values[:5], 1):  # Top 5 features
        direction = (
            "contribuye a BUENA jugada" if sv.shap_value > 0 else "contribuye a ERROR"
        )
        prompt += f"\n{i}. **{sv.feature_name}**: {sv.shap_value:+.4f} → {direction}"
        prompt += f"\n   Valor: {sv.feature_value:.2f}"

    if len(sorted_values) > 5:
        prompt += f"\n\n... y {len(sorted_values) - 5} features adicionales"

    return prompt


def generate_llm_prompt(move_number: int, values: List[ShapValue]) -> str:
    """Genera prompt completo para análisis LLM."""
    formatted_data = format_shap_for_llm(move_number, values)

    prompt = f"""Eres un maestro de ajedrez y analista de Machine Learning.

Analiza la siguiente jugada usando los SHAP values del modelo ML:

{formatted_data}

🤔 **Preguntas para analizar**:

1. ¿Por qué el modelo clasificó esta jugada como "{values[0].error_label.upper()}"?
2. ¿Qué features tienen mayor impacto (positivo/negativo)?
3. ¿Los SHAP values reflejan principios ajedrecísticos correctos?
4. ¿Hay contradicciones entre features? (e.g., alta movilidad pero pérdida material)
5. ¿Qué aprendizajes se pueden extraer para mejorar el juego?

Responde de forma clara y didáctica, conectando los valores SHAP con conceptos ajedrecísticos.
"""

    return prompt


# ========== EJECUCIÓN PRINCIPAL ==========
def main():
    """Flujo principal: obtener SHAP, formatear, mostrar prompt."""
    print("=" * 70)
    print("🤖 EJEMPLO: Análisis de SHAP con LLM (usando move context)")
    print("=" * 70)

    # Configuración
    GAME_ID = "cmess1315-vs-manuelfrp79-2024-08-18-00-15-00"  # Cambiar por game_id real

    print(f"\n1️⃣  Obteniendo token de autenticación...")
    token = login()
    print("✅ Token obtenido")

    print(f"\n2️⃣  Obteniendo SHAP values para game_id: {GAME_ID}...")
    shap_values = get_shap_values(GAME_ID, token)
    print(f"✅ {len(shap_values)} SHAP values obtenidos")

    print(f"\n3️⃣  Agrupando por jugada...")
    moves = group_by_move(shap_values)
    print(f"✅ {len(moves)} jugadas únicas")

    # Seleccionar una jugada interesante (la que más SHAP values contiene)
    target_move = max(moves.keys(), key=lambda k: len(moves[k]))
    target_values = moves[target_move]

    print(f"\n4️⃣  Generando prompt para LLM (jugada {target_move})...")
    llm_prompt = generate_llm_prompt(target_move, target_values)

    print("\n" + "=" * 70)
    print("📝 PROMPT PARA LLM:")
    print("=" * 70)
    print(llm_prompt)
    print("=" * 70)

    # Opcional: Enviar a OpenAI/Claude
    if OPENAI_API_KEY:
        print("\n5️⃣  Enviando a OpenAI GPT-4...")
        # response = openai.ChatCompletion.create(...)
        print("⚠️  Implementación pendiente (descomentar código)")
    else:
        print("\n💡 TIP: Configura OPENAI_API_KEY para enviar automáticamente")

    # Mostrar distribución de errores
    print("\n📊 Distribución de clasificaciones:")
    error_dist = {}
    for move_values in moves.values():
        label = move_values[0].error_label
        error_dist[label] = error_dist.get(label, 0) + 1

    for label, count in sorted(error_dist.items(), key=lambda x: -x[1]):
        pct = (count / len(moves)) * 100
        print(f"  {label}: {count} jugadas ({pct:.1f}%)")

    print("\n✅ Análisis completado!")
    print("\n💡 Para usar con LLM real:")
    print("   1. Copia el PROMPT generado arriba")
    print("   2. Pégalo en ChatGPT, Claude, o Gemini")
    print("   3. O configura API keys en este script para automatización")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error API: {e}")
        print(f"Response: {e.response.text if e.response else 'N/A'}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
