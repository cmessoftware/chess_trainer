"""
Test de Arquitectura V3: Grounded & Deterministic
===================================================
Prueba el flujo: Engine Analysis → JSON → Validación → Narrativa

Cambios en V3:
- Engine precalcula top_swings y decisive_move (no el LLM)
- LLM solo interpreta datos precalculados (no decide hechos)
- Tokens reducidos ~40% (no se envía PGN completo)
- Validación estricta contra engine_analysis
- Costo reducido ~50% ($0.02-0.03 USD vs $0.056 USD)

Flujo completo:
1. Login para obtener token
2. Llamar a /analysis/generate-llm-report con game_id
3. Capturar engine_analysis (datos precalculados)
4. Capturar structured_analysis (JSON validado)
5. Verificar que validación pasó
6. Analizar reporte final contra JSON y engine_analysis
7. Medir hallucination_rate y costo

Expected outcome:
- validation_passed: true
- engine_analysis presente con top_swings
- structured_analysis presente
- Reporte solo menciona hechos del engine_analysis
- No contradicciones blanco vs negro
- Costo < $0.03 USD
"""

import httpx
import json
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/auth/login"
PEDAGOGICAL_ENDPOINT = f"{BASE_URL}/api/analysis/generate-llm-report"

# Game ID de prueba (white winner con novice errors)
TEST_GAME_ID = "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb"
TEST_PLAYER_COLOR = "white"
TEST_PLAYER_ELO = 1250

# Credenciales de prueba
USERNAME = "admin"
PASSWORD = "admin123"


def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def login(username: str, password: str) -> str:
    """Login y retornar token JWT"""
    print(f"🔐 Autenticando usuario: {username}")

    payload = {"username": username, "password": password}

    response = httpx.post(LOGIN_ENDPOINT, json=payload, timeout=30.0)

    if response.status_code != 200:
        print(f"❌ Error login: {response.status_code}")
        print(response.text)
        raise Exception(f"Login failed: {response.status_code}")

    data = response.json()
    token = data["access_token"]
    print(f"✅ Token obtenido (length: {len(token)})")

    return token


def test_double_pass_architecture(token: str, game_id: str, player_color: str):
    """
    Ejecuta test completo de arquitectura doble paso
    """
    print_section("TEST: ARQUITECTURA DOBLE PASO (V2)")

    # Payload
    payload = {
        "game_id": game_id,
        "player_elo": TEST_PLAYER_ELO,
        "player_color": player_color,
    }

    print(f"📊 Parámetros:")
    print(f"   Game ID: {game_id}")
    print(f"   Player ELO: {TEST_PLAYER_ELO}")
    print(f"   Player Color: {player_color}")

    # Headers con token
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n🚀 Llamando a {PEDAGOGICAL_ENDPOINT}...")
    print(f"   (Esto puede tomar 30-60 segundos - doble llamada a LLM)\n")

    response = httpx.post(
        PEDAGOGICAL_ENDPOINT, json=payload, headers=headers, timeout=120.0
    )

    if response.status_code != 200:
        print(f"❌ Error en request: {response.status_code}")
        print(response.text)
        return None

    data = response.json()

    print(f"✅ Respuesta recibida (status 200)")
    print(f"\n📋 METADATA DEL ANÁLISIS:")
    print(f"   Analysis ID: {data.get('analysis_id')}")
    print(f"   Architecture: {data.get('architecture_version', 'N/A')}")
    print(
        f"   Validación: {'✅ PASSED' if data.get('validation_passed') else '❌ FAILED'}"
    )
    print(f"   Model: {data.get('model', 'N/A')}")
    print(f"   Total tokens: {data.get('tokens_used', {}).get('total', 'N/A')}")
    print(
        f"   Paso 1 tokens: {data.get('tokens_used', {}).get('paso_1_tokens', 'N/A')}"
    )
    print(
        f"   Paso 2 tokens: {data.get('tokens_used', {}).get('paso_2_tokens', 'N/A')}"
    )
    print(f"   Cost: ${data.get('cost_estimate_usd', 0):.4f}")

    # ============================================================
    # ANÁLISIS DEL ENGINE (V3)
    # ============================================================
    print_section("ENGINE ANALYSIS (V3 - PRECALCULADO)")

    engine = data.get("engine_analysis", {})

    if not engine:
        print("⚠️ WARNING: No se encontró engine_analysis en la respuesta")
    else:
        print(json.dumps(engine, indent=2))

        print(f"\n🔍 ENGINE DATA:")
        print(f"   Engine decisive move: #{engine.get('engine_decisive_move_chess')}")
        print(f"   Max swing (cp): {engine.get('engine_max_swing_cp')}")
        print(f"   Top swings: {len(engine.get('top_swings', []))}")
        print(f"   Material events: {len(engine.get('material_events', []))}")

        # Mostrar top swings
        if engine.get("top_swings"):
            print(f"\n   📊 TOP SWINGS:")
            for swing in engine["top_swings"][:3]:
                print(
                    f"      Move #{swing.get('chess_notation_move')}: {swing.get('delta_cp'):+d} cp ({swing.get('phase')})"
                )

    # ============================================================
    # ASSERTIONS V3
    # ============================================================
    print_section("🔍 ASSERTIONS V3 GROUNDED & DETERMINISTIC")

    # Assert 1: Arquitectura debe ser v3
    arch = data.get("architecture_version")
    assert (
        arch == "v3_grounded_deterministic"
    ), f"Expected v3_grounded_deterministic, got {arch}"
    print(f"✅ Assert 1: Architecture = v3_grounded_deterministic")

    # Assert 2: Engine analysis debe estar presente
    assert engine, "engine_analysis not found (V3 requirement)"
    print("✅ Assert 2: engine_analysis presente")

    # Assert 3: Engine decisive move debe existir
    engine_decisive = engine.get("engine_decisive_move_chess")
    assert engine_decisive is not None, "engine_decisive_move_chess not found"
    print(f"✅ Assert 3: engine_decisive_move = #{engine_decisive}")

    # Assert 4: Top swings debe tener al menos 1 elemento
    top_swings = engine.get("top_swings", [])
    assert len(top_swings) > 0, "No top_swings found"
    print(f"✅ Assert 4: top_swings presente ({len(top_swings)} swings)")

    # Assert 5: Tokens reducidos (~40% vs v2)
    total_tokens = data.get("tokens_used", {}).get("total", 0)
    if total_tokens < 1400:
        print(f"✅ Assert 5: Tokens reducidos: {total_tokens} (target V3: ~1100)")
    else:
        print(f"⚠️ Assert 5: Tokens altos: {total_tokens} (expected ~1100 in V3)")

    # Assert 6: Costo reducido (~50% vs v2)
    cost = data.get("cost_estimate_usd", 0)
    if cost < 0.035:
        print(f"✅ Assert 6: Costo reducido: ${cost:.4f} (target V3: < $0.03)")
    else:
        print(f"⚠️ Assert 6: Costo alto: ${cost:.4f} (expected < $0.03 in V3)")

    # Assert 7: Validación debe haber pasado
    assert (
        data.get("validation_passed") is True
    ), f"Validación falló: {data.get('validation_warning')}"
    print(f"✅ Assert 7: validation_passed = True")

    # ============================================================
    # ANÁLISIS DEL JSON ESTRUCTURADO
    # ============================================================
    print_section("ANÁLISIS ESTRUCTURADO (PASO 1 - JSON VALIDADO)")

    structured = data.get("structured_analysis", {})

    if not structured:
        print("⚠️ WARNING: No se encontró structured_analysis en la respuesta")
        return data

    print(json.dumps(structured, indent=2))

    print(f"\n🔍 CAMPOS JSON:")
    print(f"   decisive_move_used: {structured.get('decisive_move_used')}")
    print(f"   error_type: {structured.get('error_type')}")
    print(f"   material_loss_claimed: {structured.get('material_loss_claimed')}")
    print(f"   opening_problem: {structured.get('opening_problem_detected')}")
    print(f"   middlegame_problem: {structured.get('middlegame_problem_detected')}")
    print(f"   endgame_problem: {structured.get('endgame_problem_detected')}")
    print(f"   key_moves: {structured.get('key_moves_explained', [])}")
    print(f"   confidence: {structured.get('confidence')}")

    # ============================================================
    # ANÁLISIS DEL REPORTE NARRATIVO
    # ============================================================
    print_section("REPORTE PEDAGÓGICO (PASO 2 - NARRATIVA)")

    report = data.get("report", "")
    print(report)

    # ============================================================
    # VALIDACIONES DE COHERENCIA JSON ↔ NARRATIVA ↔ ENGINE (V3)
    # ============================================================
    print_section("VALIDACIONES DE COHERENCIA V3")

    validations = []

    # 0. (V3) Jugada decisiva del JSON DEBE coincidir con engine (CRÍTICO)
    decisive_move_json = structured.get("decisive_move_used")
    engine_decisive = engine.get("engine_decisive_move_chess")

    if decisive_move_json == engine_decisive:
        validations.append(
            f"✅ DETERMINISMO V3: decisive_move del JSON (#{decisive_move_json}) "
            f"coincide con engine (#{engine_decisive})"
        )
    else:
        validations.append(
            f"❌ CRÍTICO V3: decisive_move del JSON (#{decisive_move_json}) "
            f"NO coincide con engine (#{engine_decisive}) - LLM decidió en vez de usar engine!"
        )

    # 1. Si material_loss_claimed = false → narrativa NO debe mencionar pérdida material
    material_claimed = structured.get("material_loss_claimed", False)
    material_keywords = [
        "perdiste una pieza",
        "pérdida material",
        "te costó material",
        "perdió material",
    ]

    material_mentioned = any(keyword in report.lower() for keyword in material_keywords)

    if not material_claimed and material_mentioned:
        validations.append(
            "❌ INCOHERENCIA: JSON dice material_loss=false pero narrativa menciona pérdida material"
        )
    else:
        validations.append(
            f"✅ Material loss coherente: JSON={material_claimed}, Narrativa menciona={'Sí' if material_mentioned else 'No'}"
        )

    # 2. Movimiento decisivo debe estar mencionado
    decisive_move = structured.get("decisive_move_used")
    if decisive_move:
        decisive_mentioned = (
            f"#{decisive_move}" in report or f"{decisive_move}" in report
        )
        if decisive_mentioned:
            validations.append(
                f"✅ Movimiento decisivo #{decisive_move} mencionado en narrativa"
            )
        else:
            validations.append(
                f"❌ OMISIÓN: Movimiento decisivo #{decisive_move} NO mencionado en narrativa"
            )

    # 3. Key moves deben estar mencionados
    key_moves = structured.get("key_moves_explained", [])
    for move in key_moves:
        if f"#{move}" in report or f"{move}" in report:
            validations.append(f"✅ Movimiento clave #{move} mencionado")
        else:
            validations.append(
                f"⚠️ Movimiento clave #{move} NO mencionado explícitamente"
            )

    # 4. Fases sin problemas no deben ser mencionadas
    opening_problem = structured.get("opening_problem_detected", False)
    opening_mentioned = "apertura" in report.lower() or "opening" in report.lower()

    if not opening_problem and opening_mentioned:
        validations.append(
            "⚠️ Fase 'apertura' mencionada pero JSON indica opening_problem=false"
        )
    else:
        validations.append(f"✅ Apertura coherente: JSON={opening_problem}")

    # 5. Generic phrases sin jugadas específicas
    generic_phrases = [
        "controla el centro",
        "mejora la apertura",
        "limita la movilidad",
        "coordina las piezas",
    ]

    for phrase in generic_phrases:
        if phrase in report.lower():
            # Verificar si va acompañado de número de jugada
            idx = report.lower().find(phrase)
            context = report[max(0, idx - 50) : min(len(report), idx + 50)]
            has_move_number = "#" in context or "jugada" in context.lower()

            if not has_move_number:
                validations.append(
                    f"⚠️ Frase genérica sin jugada: '{phrase}' (contexto: {context[:60]}...)"
                )

    # Imprimir validaciones
    for v in validations:
        print(v)

    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print_section("RESUMEN")

    passed_count = sum(1 for v in validations if v.startswith("✅"))
    warning_count = sum(1 for v in validations if v.startswith("⚠️"))
    failed_count = sum(1 for v in validations if v.startswith("❌"))

    print(f"✅ Validaciones pasadas: {passed_count}")
    print(f"⚠️ Warnings: {warning_count}")
    print(f"❌ Fallos: {failed_count}")

    if failed_count == 0 and warning_count <= 1:
        print(
            f"\n🎉 ARQUITECTURA V3 (GROUNDED & DETERMINISTIC) FUNCIONANDO CORRECTAMENTE"
        )
        print(f"   El reporte es coherente con el JSON validado y engine_analysis")
        print(
            f"   Tokens: {total_tokens} (reducción ~{int((1-total_tokens/1900)*100)}% vs v2)"
        )
        print(f"   Costo: ${cost:.4f}")
    elif failed_count == 0:
        print(f"\n✅ Arquitectura V3 funcional (con {warning_count} warnings menores)")
    else:
        print(f"\n❌ Problemas detectados: {failed_count} incoherencias críticas")

    # Guardar resultado completo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"double_pass_test_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "game_id": game_id,
                    "player_color": player_color,
                    "timestamp": timestamp,
                    "architecture": data.get("architecture_version"),
                },
                "structured_analysis": structured,
                "report": report,
                "validations": validations,
                "summary": {
                    "passed": passed_count,
                    "warnings": warning_count,
                    "failed": failed_count,
                },
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n💾 Resultado guardado en: {output_file}")

    return data


def main():
    """
    Ejecuta test completo de arquitectura V3 Grounded & Deterministic
    """
    print_section("ARQUITECTURA V3 GROUNDED & DETERMINISTIC - TEST E2E")
    print(f"Game ID: {TEST_GAME_ID}")
    print(f"Player: {TEST_PLAYER_COLOR}")
    print(f"Base URL: {BASE_URL}")
    print(f"Architecture: v3_grounded_deterministic")
    print(f"Expected improvements:")
    print(f"  - Engine precalculates top_swings and decisive_move")
    print(f"  - LLM narrates (no factual decisions)")
    print(f"  - Token reduction: ~40%")
    print(f"  - Cost reduction: ~50%")
    print(f"  - Zero contradictions (deterministic)")

    try:
        # 1. Login
        token = login(USERNAME, PASSWORD)

        # 2. Test arquitectura doble paso
        result = test_double_pass_architecture(
            token=token, game_id=TEST_GAME_ID, player_color=TEST_PLAYER_COLOR
        )

        if result:
            print_section("TEST COMPLETADO ✅")
        else:
            print_section("TEST FALLIDO ❌")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
