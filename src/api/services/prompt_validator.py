"""
PromptValidator - Guardrail para salida del LLM

Valida que los reportes generados por el LLM respeten el competitive_context
y no inventen hechos que no estén en el evidence_pack.

Implementa las reglas anti-alucinación del documento v2:
- No inventar pérdida material
- No citar jugadas inexistentes
- No inventar blunders
- No hablar de fases sin errores
- Citar el momento decisivo
"""

import re
from typing import Dict, List


class PromptValidationError(Exception):
    """Excepción lanzada cuando el reporte LLM viola las reglas de validación"""

    pass


class PromptValidator:
    """
    Valida la salida del LLM contra el competitive_context y evidence_pack
    """

    def __init__(self, competitive_context: Dict, evidence_pack: List[Dict]):
        """
        Args:
            competitive_context: Diccionario con contexto competitivo calculado
            evidence_pack: Lista de movimientos con detalles (move_number, error_label, etc)
        """
        self.context = competitive_context
        self.evidence = evidence_pack

        # Crear índice de movimientos para búsqueda rápida
        self.evidence_moves = {e["move_number"]: e for e in evidence_pack}

    # ============================================================
    # 1️⃣ Validar jugadas citadas existen en evidence
    # ============================================================
    def validate_moves_exist(self, report_text: str):
        """
        Verifica que todas las jugadas mencionadas en el reporte
        existan en el evidence_pack.

        Raises:
            PromptValidationError: Si se menciona una jugada inexistente
        """
        # Buscar patrones como "movimiento #8", "jugada 21", "en la jugada #33"
        mentioned_moves = re.findall(
            r"(?:movimiento|jugada)\s+#?(\d+)", report_text.lower()
        )

        for move_str in mentioned_moves:
            move = int(move_str)
            if move not in self.evidence_moves:
                raise PromptValidationError(
                    f"❌ VALIDACIÓN FALLIDA: El reporte menciona jugada inexistente: #{move}. "
                    f"Jugadas disponibles: {sorted(self.evidence_moves.keys())}"
                )

    # ============================================================
    # 2️⃣ Validar afirmaciones de pérdida material
    # ============================================================
    def validate_material_claims(self, report_text: str):
        """
        Verifica que solo se mencione pérdida material si realmente ocurrió
        (material_delta_at_decisive_move < -1.0)

        Raises:
            PromptValidationError: Si se inventa pérdida material
        """
        material_delta = self.context.get("material_delta_at_decisive_move", 0)

        # Palabras clave que indican pérdida material
        material_keywords = [
            "perdiste una pieza",
            "pérdida material",
            "perdió material",
            "ganó material",
            "perdiste material",
            "costó una pieza",
            "perdiste un peón",
            "perdiste una torre",
            "perdiste un alfil",
            "perdiste un caballo",
            "perdiste la dama",
        ]

        # Si no hubo pérdida material significativa (>1 punto)
        if material_delta >= -1.0:
            for keyword in material_keywords:
                if keyword in report_text.lower():
                    raise PromptValidationError(
                        f"❌ VALIDACIÓN FALLIDA: El reporte afirma '{keyword}' pero "
                        f"material_delta={material_delta:.2f} (no hubo pérdida material significativa). "
                        f"Debe describirse como error posicional/estratégico."
                    )

    # ============================================================
    # 3️⃣ Validar afirmaciones de BLUNDER
    # ============================================================
    def validate_blunder_claims(self, report_text: str):
        """
        Verifica que solo se etiquete como BLUNDER jugadas que
        realmente tienen error_label == "BLUNDER" en el evidence.

        Raises:
            PromptValidationError: Si se inventa un blunder
        """
        # Obtener jugadas realmente etiquetadas como BLUNDER
        blunder_moves_real = {
            e["move_number"]
            for e in self.evidence
            if e.get("error_label", "").upper() == "BLUNDER"
        }

        # Buscar menciones de blunder en el reporte con número de jugada
        # Ej: "movimiento #8 fue un blunder", "blunder en la jugada 21"
        mentioned_blunders = re.findall(
            r"(?:movimiento|jugada)\s+#?(\d+)[^.]*?blunder", report_text.lower()
        )

        for move_str in mentioned_blunders:
            move = int(move_str)
            if move not in blunder_moves_real:
                raise PromptValidationError(
                    f"❌ VALIDACIÓN FALLIDA: Se afirmó BLUNDER en jugada #{move} pero no está "
                    f"etiquetada como tal. Blunders reales: {sorted(blunder_moves_real)}. "
                    f"Error real: {self.evidence_moves.get(move, {}).get('error_label', 'N/A')}"
                )

    # ============================================================
    # 4️⃣ Validar afirmaciones sobre fases del juego
    # ============================================================
    def validate_phase_claims(self, report_text: str):
        """
        Verifica que solo se mencionen errores en fases donde realmente ocurrieron
        (phase_error_distribution > 0)

        Raises:
            PromptValidationError: Si se inventan errores en una fase limpia
        """
        phase_distribution = self.context.get("phase_error_distribution", {})

        # Mapeo de nombres de fase
        phase_keywords = {
            "apertura": ["apertura", "opening"],
            "middlegame": ["medio juego", "middlegame", "medio-juego"],
            "endgame": ["final", "endgame"],
        }

        # Verificar cada fase
        for phase_key, keywords in phase_keywords.items():
            error_count = phase_distribution.get(phase_key, 0)

            # Si no hubo errores en esta fase
            if error_count == 0:
                for keyword in keywords:
                    # Buscar patrones como "errores en la apertura", "en la apertura cometiste"
                    pattern = rf"(?:error|blunder|mistake|imprecisión|imprecision).*?(?:en|de)\s+(?:la\s+)?{keyword}"
                    if re.search(pattern, report_text.lower()):
                        raise PromptValidationError(
                            f"❌ VALIDACIÓN FALLIDA: Se mencionan errores en {phase_key} pero "
                            f"no existen según contexto. Distribución real: {phase_distribution}"
                        )

    # ============================================================
    # 5️⃣ Validar que se cite el momento decisivo
    # ============================================================
    def validate_decisive_move_cited(self, report_text: str):
        """
        Verifica que el reporte mencione explícitamente el momento decisivo
        (critical_move del competitive_context)

        Raises:
            PromptValidationError: Si no se menciona el momento decisivo
        """
        decisive_move = self.context.get("critical_move")

        if decisive_move:
            # Buscar el número de jugada en el texto
            move_pattern = rf"(?:movimiento|jugada)\s+#?{decisive_move}(?:\D|$)"  # Seguido de no-dígito
            if not re.search(move_pattern, report_text.lower()):
                raise PromptValidationError(
                    f"❌ VALIDACIÓN FALLIDA: El reporte NO menciona el momento decisivo "
                    f"(jugada #{decisive_move}). Esto es obligatorio."
                )

    # ============================================================
    # Ejecutar validación completa
    # ============================================================
    def validate(self, report_text: str) -> bool:
        """
        Ejecuta todas las validaciones en secuencia.

        Args:
            report_text: Texto del reporte generado por el LLM

        Returns:
            True si pasa todas las validaciones

        Raises:
            PromptValidationError: Si falla alguna validación
        """
        # Ejecutar las 5 validaciones
        self.validate_moves_exist(report_text)
        self.validate_material_claims(report_text)
        self.validate_blunder_claims(report_text)
        self.validate_phase_claims(report_text)
        self.validate_decisive_move_cited(report_text)

        return True


# ============================================================
# Función helper para uso rápido
# ============================================================
def validate_llm_report(
    report_text: str, competitive_context: Dict, evidence_pack: List[Dict]
) -> bool:
    """
    Función helper para validar un reporte LLM.

    Args:
        report_text: Texto del reporte generado por el LLM
        competitive_context: Contexto competitivo calculado
        evidence_pack: Lista de movimientos con detalles

    Returns:
        True si el reporte pasa todas las validaciones

    Raises:
        PromptValidationError: Si falla alguna validación
    """
    validator = PromptValidator(competitive_context, evidence_pack)
    return validator.validate(report_text)
