"""
Análisis del reporte LLM para verificar mejoras del contexto competitivo
"""

import re

# Reporte obtenido del test
REPORT_WHITE = """## 📊 Diagnóstico

A pesar de tu victoria, tu juego presentó un margen de mejora importante en dos áreas críticas: el control del centro y la restricción de la movilidad de las piezas del oponente. En el movimiento #8, por ejemplo, tu jugada permitió un alto grado de libertad a tu rival, una situación que deberías evitar en el futuro.

## 🎯 Acciones Concretas

1. **Restringe la movilidad del oponente:** En el movimiento #8, tu blunder permitió al oponente una mayor movilidad, lo cual pudo haber costado caro. Pregúntate: ¿esta jugada le da libertad a mi oponente? Trata de limitar sus opciones.

2. **Controla el centro:** En el movimiento #33, perdiste control del centro, lo que permitió a tu oponente ganar terreno. Intenta ocuparlo con peones (e4, d4) o controlarlo con piezas. Recuerda, el centro es clave.

3. **Evita errores en la apertura:** Enfócate en desarrollar piezas rápidamente, controlar el centro, y enrocar pronto. En tus primeros 15 movimientos, evita errores que permitan al oponente ganar ventaja.

## ✅ Fortaleza Detectada

A pesar de los errores, lograste una victoria, lo que indica que tu capacidad de recuperación es sólida. Además, tu error rate es solo ligeramente mayor que el de tu oponente (+1.0%), lo que sugiere que, a pesar de los errores graves, mantienes un nivel de juego competitivo. Continúa trabajando en tus fortalezas mientras abordas estas áreas de mejora."""


def analyze_competitive_context_improvements(report: str):
    """
    Analiza el reporte para verificar que las mejoras del contexto competitivo
    están funcionando correctamente
    """

    print("\n" + "=" * 100)
    print("🔬 ANÁLISIS DE MEJORAS - CONTEXTO COMPETITIVO")
    print("=" * 100 + "\n")

    results = {}

    # MEJORA 1: Momento decisivo específico (swing evaluativo)
    print("1️⃣ MOMENTO DECISIVO ESPECÍFICO (Swing Evaluativo)")
    print("-" * 100)

    move_mentions = re.findall(r"movimiento #(\d+)", report.lower())
    if move_mentions:
        print(
            f"✅ PASS: Menciona movimientos específicos: {', '.join(['#' + m for m in move_mentions])}"
        )
        results["specific_moves"] = True

        # Verificar si explica QUÉ pasó en esos movimientos
        explanations = []
        for match in re.finditer(
            r"movimiento #(\d+)[^.]*([^.]+\.)", report.lower(), re.IGNORECASE
        ):
            move_num = match.group(1)
            explanation = match.group(2).strip()
            explanations.append(f"  - Movimiento #{move_num}: {explanation}")

        if explanations:
            print("✅ PASS: Explica QUÉ pasó en los movimientos:")
            for exp in explanations:
                print(exp)
            results["explains_what_happened"] = True
        else:
            print("⚠️ WARNING: Menciona movimientos pero no explica claramente qué pasó")
            results["explains_what_happened"] = False
    else:
        print("❌ FAIL: NO menciona movimientos específicos")
        results["specific_moves"] = False
        results["explains_what_happened"] = False

    print()

    # MEJORA 2: Diferenciación de tipo de derrota (single_blunder vs accumulated)
    print("2️⃣ TIPO DE ERROR (single_blunder vs accumulated_errors)")
    print("-" * 100)

    has_blunder_mention = "blunder" in report.lower()
    has_single_error_mention = re.search(
        r"(error cr[ií]tico|blunder único|un solo error)", report.lower()
    )
    has_accumulated_mention = re.search(
        r"(acumulaci[oó]n|varios errores|múltiples)", report.lower()
    )

    if has_blunder_mention:
        print(f"✅ PASS: Menciona 'blunder' explícitamente")
        results["mentions_blunder"] = True

        if has_single_error_mention:
            print(f"✅ PASS: Identifica como error único/crítico")
            results["identifies_single_error"] = True
        elif has_accumulated_mention:
            print(f"✅ PASS: Identifica como acumulación de errores")
            results["identifies_accumulated_error"] = True
        else:
            print(
                f"⚠️ PARTIAL: Menciona blunder pero no clarifica si es único o acumulado"
            )
            results["identifies_single_error"] = False
            results["identifies_accumulated_error"] = False
    else:
        print("⚠️ WARNING: NO menciona 'blunder' explícitamente")
        results["mentions_blunder"] = False

    print()

    # MEJORA 3: Distribución de errores por fase (opening/middlegame/endgame)
    print("3️⃣ DISTRIBUCIÓN POR FASE (NO inventar fases sin errores)")
    print("-" * 100)

    phase_mentions = {
        "apertura": "apertura" in report.lower() or "opening" in report.lower(),
        "medio juego": "medio juego" in report.lower()
        or "middlegame" in report.lower(),
        "final": "final" in report.lower() or "endgame" in report.lower(),
    }

    mentioned_phases = [
        phase for phase, mentioned in phase_mentions.items() if mentioned
    ]

    if mentioned_phases:
        print(f"✅ PASS: Menciona fases específicas: {', '.join(mentioned_phases)}")
        results["mentions_phases"] = True

        # Verificar si relaciona errores con fases específicas
        if re.search(r"(en la apertura|en el medio juego|en el final)", report.lower()):
            print(f"✅ PASS: Relaciona errores con fases específicas")
            results["relates_errors_to_phases"] = True
        else:
            print(
                f"⚠️ PARTIAL: Menciona fases pero no las relaciona claramente con errores"
            )
            results["relates_errors_to_phases"] = False
    else:
        print(
            "⚠️ INFO: NO menciona fases específicas (puede ser correcto si no hubo errores por fase)"
        )
        results["mentions_phases"] = False
        results["relates_errors_to_phases"] = False

    print()

    # MEJORA 4: Adaptación al resultado (victoria/derrota)
    print("4️⃣ ADAPTACIÓN AL RESULTADO (tono según victoria/derrota)")
    print("-" * 100)

    has_victory_mention = re.search(
        r"(victoria|ganaste|lograste ganar|a pesar de.*victoria)", report.lower()
    )
    has_defeat_mention = re.search(r"(derrota|perdiste|caíste)", report.lower())

    if has_victory_mention:
        print(f"✅ PASS: Reconoce VICTORIA y adapta tono")
        results["recognizes_victory"] = True

        # Verificar si menciona fortalezas en victoria
        if re.search(r"(fortaleza|capacidad|habilidad|bien hecho)", report.lower()):
            print(f"✅ PASS: Resalta fortalezas en victoria")
            results["highlights_strengths"] = True
        else:
            print(f"⚠️ PARTIAL: Reconoce victoria pero no resalta fortalezas")
            results["highlights_strengths"] = False

    elif has_defeat_mention:
        print(f"✅ PASS: Reconoce DERROTA y adapta tono")
        results["recognizes_defeat"] = True
    else:
        print("⚠️ WARNING: NO reconoce claramente victoria ni derrota")
        results["recognizes_victory"] = False
        results["recognizes_defeat"] = False

    print()

    # MEJORA 5: Calidad de conversión (para victorias)
    print("5️⃣ CALIDAD DE CONVERSIÓN (para victorias)")
    print("-" * 100)

    if has_victory_mention:
        conversion_mentions = re.search(
            r"(conversión|mantuviste.*ventaja|recuperación|capacidad de mantener)",
            report.lower(),
        )
        if conversion_mentions:
            print(f"✅ PASS: Analiza calidad de conversión de ventaja")
            results["analyzes_conversion"] = True
        else:
            print(
                f"⚠️ PARTIAL: Victoria reconocida pero no analiza conversión de ventaja"
            )
            results["analyzes_conversion"] = False
    else:
        print(f"ℹ️ INFO: No aplica (no es victoria)")
        results["analyzes_conversion"] = None

    print()

    # RESUMEN FINAL
    print("\n" + "=" * 100)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 100 + "\n")

    total_checks = sum(1 for v in results.values() if v is not None)
    passed_checks = sum(1 for v in results.values() if v is True)

    print(f"Total checks: {passed_checks}/{total_checks}")
    print(f"Pass rate: {(passed_checks/total_checks*100):.1f}%\n")

    print("Estado por mejora:")
    print(
        f"  1. Momento decisivo específico: {'✅' if results.get('specific_moves') and results.get('explains_what_happened') else '❌'}"
    )
    print(
        f"  2. Tipo de error identificado: {'✅' if results.get('mentions_blunder') else '⚠️'}"
    )
    print(
        f"  3. Distribución por fase: {'✅' if results.get('relates_errors_to_phases') else '⚠️'}"
    )
    print(
        f"  4. Adaptación al resultado: {'✅' if results.get('recognizes_victory') or results.get('recognizes_defeat') else '❌'}"
    )
    print(
        f"  5. Calidad de conversión: {'✅' if results.get('analyzes_conversion') else 'N/A' if results.get('analyzes_conversion') is None else '⚠️'}"
    )

    print("\n" + "=" * 100)

    overall_success = passed_checks / total_checks >= 0.7  # 70% pass rate

    if overall_success:
        print(
            "🎉 ÉXITO: Las mejoras del contexto competitivo están funcionando correctamente"
        )
    else:
        print("⚠️ REVISAR: Algunas mejoras no se reflejan claramente en el reporte")

    print("=" * 100 + "\n")

    return results, overall_success


if __name__ == "__main__":
    print("\n" + "#" * 100)
    print("# VERIFICACIÓN: Competitive Context Layer Improvements")
    print("# Game: aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb")
    print("# Player: WHITE (Winner)")
    print("#" * 100)

    results, success = analyze_competitive_context_improvements(REPORT_WHITE)

    exit(0 if success else 1)
