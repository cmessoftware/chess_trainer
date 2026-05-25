"""
Test completo de la capa de contexto competitivo con game_id específico
"""

import requests
import json
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:8000"
GAME_ID = "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb"

# Test credentials
TEST_USER = "admin"
TEST_PASSWORD = "admin123"


def get_access_token():
    """Login and get access token"""
    url = f"{BASE_URL}/api/auth/login"
    payload = {"username": TEST_USER, "password": TEST_PASSWORD}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login exitoso como {TEST_USER}")
            return token
        else:
            print(f"❌ Login fallido: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        return None


def test_competitive_context(
    game_id: str, player_color: str, player_elo: int, access_token: str
):
    """Test LLM report with competitive context layer"""

    print(f"\n{'='*100}")
    print(f"🎮 TEST: Competitive Context Layer")
    print(f"{'='*100}")
    print(f"Game ID: {game_id}")
    print(f"Player Color: {player_color}")
    print(f"Player ELO: {player_elo}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")

    # Prepare request
    url = f"{BASE_URL}/api/analysis/generate-llm-report"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "game_id": game_id,
        "player_color": player_color,
        "player_elo": player_elo,
    }

    print(f"📤 REQUEST:")
    print(f"POST {url}")
    print(f"Headers: Authorization: Bearer {access_token[:20]}...")
    print(json.dumps(payload, indent=2))
    print()

    try:
        # Make request
        print(f"⏳ Llamando al endpoint LLM...")
        response = requests.post(url, json=payload, headers=headers, timeout=120)

        print(f"\n📥 RESPONSE:")
        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            data = response.json()

            # First, print full response structure for debugging
            print(f"✅ SUCCESS - Report Generated")
            print(f"{'='*100}")
            print(f"\n📋 FULL RESPONSE STRUCTURE:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print(f"\n{'='*100}")

            # Extract key information

            # Report metadata
            if "metadata" in data:
                metadata = data["metadata"]
                print(f"\n📊 METADATA:")
                print(f"  - Game Result: {metadata.get('result', 'N/A')}")
                print(f"  - Player ELO: {metadata.get('player_elo', 'N/A')}")
                print(f"  - Opponent ELO: {metadata.get('opponent_elo', 'N/A')}")
                print(f"  - Total Moves: {metadata.get('total_moves', 'N/A')}")

            # Evidence pack
            if "evidence_pack" in data:
                evidence = data["evidence_pack"]
                print(f"\n🔬 EVIDENCE PACK:")
                print(
                    f"  - Top Errors: {len(evidence.get('top_error_moves', []))} moves"
                )

                if evidence.get("top_error_moves"):
                    print(f"\n  Top 3 Errors:")
                    for i, error in enumerate(
                        evidence.get("top_error_moves", [])[:3], 1
                    ):
                        print(
                            f"    {i}. Move #{error.get('move_number_chess', 'N/A')}: {error.get('error_type', 'N/A').upper()}"
                        )
                        print(
                            f"       - Stockfish Score: {error.get('stockfish_score', 'N/A')}"
                        )
                        print(f"       - Phase: {error.get('phase', 'N/A')}")
                        if "top_features" in error:
                            top_feat = error["top_features"][:2]
                            print(f"       - Top SHAP features: {', '.join(top_feat)}")

            # Competitive context (NEW!)
            if "competitive_context" in data:
                context = data["competitive_context"]
                print(f"\n⚔️ COMPETITIVE CONTEXT (NEW LAYER):")
                print(f"  - Result: {context.get('result', 'N/A')}")
                print(f"  - Critical Move: #{context.get('critical_move', 'N/A')}")
                print(f"  - Decisive Phase: {context.get('decisive_phase', 'N/A')}")

                # NEW METRICS
                print(f"\n  🎯 NEW METRICS:")
                decisive_swing = context.get("decisive_swing", 0)
                print(
                    f"  - Decisive Swing: {decisive_swing:.2f} (eval delta entre movimientos)"
                )

                loss_type = context.get("loss_type")
                if loss_type:
                    print(f"  - Loss Type: {loss_type}")
                    if loss_type == "single_blunder":
                        print(f"    → Derrota por UN error crítico")
                    else:
                        print(f"    → Derrota por acumulación de errores")

                first_material_loss = context.get("first_material_loss_move")
                if first_material_loss:
                    print(f"  - First Material Loss: Move #{first_material_loss}")

                conversion = context.get("conversion_quality")
                if conversion:
                    print(f"  - Conversion Quality: {conversion}")
                    if conversion == "clean":
                        print(f"    → Conversión limpia, mantuvo ventaja")
                    elif conversion == "stable":
                        print(f"    → Conversión estable, leves pérdidas")
                    else:
                        print(f"    → Conversión imprecisa, perdió ventaja")

                phase_errors = context.get("phase_error_distribution", {})
                if phase_errors:
                    print(f"  - Phase Error Distribution:")
                    for phase, count in phase_errors.items():
                        if count > 0:
                            print(f"    → {phase.capitalize()}: {count} errores")

            # LLM Report
            if "llm_report" in data:
                report = data["llm_report"]
                print(f"\n📝 LLM REPORT:")
                print(f"{'='*100}")
                print(report)
                print(f"{'='*100}")

            # Analysis
            print(f"\n🔍 ANALYSIS:")
            print(f"  1. ¿El reporte menciona el momento decisivo específico?")
            print(f"  2. ¿El reporte diferencia entre un blunder vs acumulación?")
            print(f"  3. ¿El reporte solo menciona fases con errores reales?")
            print(f"  4. ¿El reporte explica QUÉ pasó en el movimiento crítico?")
            print(f"  5. ¿El reporte adapta el tono según victoria/derrota?")

            print(f"\n{'='*100}")
            print(f"✅ TEST COMPLETADO")
            print(f"{'='*100}\n")

            return data

        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Request timeout (>120s)")
        print(f"   El LLM puede estar tardando mucho. Considera:")
        print(f"   - Verificar que OpenAI API key esté configurada")
        print(f"   - Aumentar el timeout")
        return None

    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to {BASE_URL}")
        print(f"   Verifica que el backend esté corriendo en puerto 8000")
        return None

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def main():
    """Run tests for both colors"""

    print(f"\n{'#'*100}")
    print(f"# COMPETITIVE CONTEXT LAYER - INTEGRATION TEST")
    print(f"# Game: {GAME_ID}")
    print(f"{'#'*100}\n")

    # Get access token
    print(f"🔐 Autenticando...")
    access_token = get_access_token()

    if not access_token:
        print(f"❌ No se pudo obtener access token. Abortando tests.")
        return

    print()

    # Test 1: White player
    print(f"\n{'▶'*50}")
    print(f"TEST 1: White Player (Novice ~1400-1500)")
    print(f"{'▶'*50}")
    result_white = test_competitive_context(GAME_ID, "white", 1450, access_token)

    # Test 2: Black player - TEMPORARILY DISABLED TO SAVE OPENAI TOKENS
    print(f"\n{'▶'*50}")
    print(f"TEST 2: Black Player (SKIPPED for token saving)")
    print(f"{'▶'*50}")
    result_black = None  # Temporarily skip
    # result_black = test_competitive_context(GAME_ID, "black", 1450, access_token)

    # Summary
    print(f"\n{'#'*100}")
    print(f"# TEST SUMMARY")
    print(f"{'#'*100}")
    print(f"White Test: {'✅ PASS' if result_white else '❌ FAIL'}")
    print(f"Black Test: {'✅ PASS' if result_black else '❌ FAIL'}")
    print(f"{'#'*100}\n")


if __name__ == "__main__":
    main()
