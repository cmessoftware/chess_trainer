"""
Análisis del reporte LLM V2 para verificar mejoras anti-alucinación
"""

import re

# Nuevo reporte con mejoras V2
REPORT_V2_WHITE = """## 📊 Diagnóstico
A pesar de la victoria, tu partida tuvo varios momentos de tensión. En particular, el movimiento #33 fue crítico. A pesar de que no hubo una pérdida material (swing: 0.0), cometiste un error estratégico que pudo haber sido fatal. El error estuvo en permitir al oponente un alto grado de movilidad, lo que le dio mayor libertad para maniobrar sus piezas.

## 🎯 Acciones Concretas
1. **Restringe la movilidad del oponente**: En el movimiento #33, permitiste a tu oponente demasiada libertad. Considera jugadas que limiten las opciones de tu oponente y lo obliguen a jugar de manera defensiva.

2. **Mejora tu apertura**: En el movimiento #8 cometiste un error grave que te costó la ventaja inicial. Trata de enfocarte en desarrollar tus piezas rápidamente, controlar el centro y enrocar pronto.

3. **Controla el centro**: En varios movimientos, incluyendo el #8 y #33, no disputaste o perdiste control del centro. El centro es clave en el ajedrez, intenta ocuparlo con peones o controlarlo con tus piezas.

## ✅ Fortaleza Detectada
A pesar de los errores, tu victoria se debió a tu habilidad para mantener la calma en momentos de presión y realizar movimientos decisivos. Continúa trabajando en tus fortalezas y corrigiendo tus debilidades para seguir mejorando. Recuerda que en el ajedrez, cada partida es una oportunidad para aprender y crecer."""


def analyze_v2_improvements(report: str):
    """
    Analiza el reporte V2 para verificar que las mejoras anti-alucinación funcionan
    """

    print("\n" + "=" * 100)
    print("🔬 ANÁLISIS REPORTE V2 - Mejoras Anti-Alucinación")
    print("=" * 100 + "\n")

    issues = []
    improvements = []

    # VERIFICACIÓN 1: ¿Menciona material_delta correctamente?
    print("1️⃣ MATERIAL DELTA")
    print("-" * 100)

    if "no hubo una pérdida material (swing: 0.0)" in report.lower():
        print("⚠️ PROBLEMA: Reporte dice 'swing: 0.0' - esto es incorrecto")
        print(
            "   El swing evaluativo debería ser > 0 (pérdida de evaluación, no material)"
        )
        print("   SUGERENCIA: El LLM confunde 'material_delta' con 'decisive_swing'")
        issues.append("Confusión entre material_delta y decisive_swing")
    else:
        print("✅ PASS: No menciona swing 0.0 incorrectamente")
        improvements.append("Material delta mencionado correctamente")

    print()

    # VERIFICACIÓN 2: ¿Usa frases genéricas SIN jugadas?
    print("2️⃣ FRASES GENÉRICAS")
    print("-" * 100)

    generic_phrases_pattern = [
        (r"controla el centro(?!\s+(?:en|movimiento|jugada))", "Controla el centro"),
        (r"mejora tu apertura(?!\s+(?:en|movimiento|jugada))", "Mejora tu apertura"),
        (
            r"restringe la movilidad(?!\s+(?:en|movimiento|jugada))",
            "Restringe la movilidad",
        ),
    ]

    found_generic = False
    for pattern, phrase in generic_phrases_pattern:
        if re.search(pattern, report.lower()):
            print(f"⚠️ ENCONTRADO: '{phrase}' sin contexto de jugada específica")
            issues.append(f"Frase genérica: {phrase}")
            found_generic = True

    if not found_generic:
        print("✅ PASS: No se encontraron frases genéricas sin contexto")
        improvements.append("Evita frases genéricas")

    print()

    # VERIFICACIÓN 3: ¿Menciona movimientos específicos?
    print("3️⃣ MOVIMIENTOS ESPECÍFICOS")
    print("-" * 100)

    move_mentions = re.findall(r"movimiento #(\d+)", report.lower())
    if move_mentions:
        print(
            f"✅ PASS: Menciona movimientos específicos: {', '.join(['#' + m for m in set(move_mentions)])}"
        )
        improvements.append(
            f"Menciona {len(set(move_mentions))} movimientos específicos"
        )
    else:
        print(f"❌ FAIL: NO menciona movimientos específicos")
        issues.append("No menciona movimientos")

    print()

    # VERIFICACIÓN 4: ¿Explica QUÉ pasó en movimientos?
    print("4️⃣ EXPLICACIONES CONTEXTUALES")
    print("-" * 100)

    # Buscar explicaciones después de mencionar movimientos
    explanations = []
    for move in set(move_mentions):
        # Buscar contexto alrededor del movimiento
        match = re.search(
            rf"movimiento #?{move}[^.]*?([^.]+\.)", report.lower(), re.IGNORECASE
        )
        if match:
            explanation = match.group(1).strip()
            print(f"  - Movimiento #{move}: {explanation}")
            explanations.append(explanation)

    if explanations:
        print(f"\n✅ PASS: Proporciona {len(explanations)} explicaciones contextuales")
        improvements.append(f"{len(explanations)} explicaciones detalladas")
    else:
        print(f"\n⚠️ PARTIAL: Menciona movimientos pero sin explicaciones claras")

    print()

    # VERIFICACIÓN 5: ¿Evita inventar pérdida material?
    print("5️⃣ PÉRDIDA MATERIAL")
    print("-" * 100)

    material_claims = re.findall(
        r"(perdiste una pieza|pérdida material|te costó|perdiste material)",
        report.lower(),
    )

    if material_claims:
        print(f"⚠️ ENCONTRADO: Menciones de pérdida material: {material_claims}")
        print(f"   ¿Hay evidencia de material_delta < -1.0?")
        issues.append(f"Menciona pérdida material: {material_claims}")
    else:
        print("✅ PASS: No menciona pérdida material incorrectamente")
        print("   Describe error como estratégico/posicional")
        improvements.append("Evita inventar pérdida material")

    print()

    # RESUMEN
    print("\n" + "=" * 100)
    print("📊 RESUMEN - REPORTE V2")
    print("=" * 100 + "\n")

    print(f"✅ MEJORAS ({len(improvements)}):")
    for imp in improvements:
        print(f"  + {imp}")

    print(f"\n⚠️ PROBLEMAS DETECTADOS ({len(issues)}):")
    for issue in issues:
        print(f"  - {issue}")

    print("\n" + "=" * 100)

    # Evaluación general
    if len(issues) == 0:
        print("🎉 EXCELENTE: Reporte V2 cumple todas las reglas anti-alucinación")
    elif len(issues) <= 2:
        print(
            "✅ BUENO: Reporte V2 tiene mejoras significativas, pocos problemas restantes"
        )
    else:
        print("⚠️ REVISAR: Reporte V2 aún tiene varios problemas de alucinación")

    print("=" * 100 + "\n")

    return improvements, issues


if __name__ == "__main__":
    print("\n" + "#" * 100)
    print("# ANÁLISIS REPORTE V2 - Con Mejoras Anti-Alucinación")
    print("# Game: aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb")
    print("# Player: WHITE (Winner, 1450 ELO)")
    print("#" * 100)

    improvements, issues = analyze_v2_improvements(REPORT_V2_WHITE)

    exit(0 if len(issues) <= 2 else 1)
