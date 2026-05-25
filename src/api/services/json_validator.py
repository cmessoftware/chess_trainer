"""
JSON Validator - Validación estructurada de análisis LLM

Valida el JSON estructurado generado por el LLM en el Paso 1,
antes de generar la narrativa pedagógica.

Arquitectura Doble Paso:
1. LLM genera JSON estructurado verificable
2. JSON Validator verifica hechos contra competitive_context
3. LLM genera narrativa basada SOLO en JSON validado

Esto elimina ~80% de alucinaciones vs validar texto libre.
"""

from typing import Dict, List


class JSONValidationError(Exception):
    """Excepción lanzada cuando el JSON estructurado viola reglas factuales"""

    pass


class StructuredAnalysisValidator:
    """
    Valida el análisis estructurado (JSON) del LLM contra datos reales
    """

    def __init__(self, competitive_context: Dict, evidence_pack: List[Dict]):
        """
        Args:
            competitive_context: Contexto competitivo calculado (source of truth)
            evidence_pack: Lista de movimientos con detalles
        """
        self.context = competitive_context
        self.engine = competitive_context.get("engine_analysis", {})
        self.evidence = evidence_pack
        self.evidence_moves = {e["move_number"] for e in evidence_pack}

    def validate_decisive_move(self, structured: Dict):
        """
        V3: Verifica que el decisive_move_used coincida con engine_decisive_move

        Raises:
            JSONValidationError: Si usa jugada decisiva incorrecta
        """
        decisive_move_claimed = structured.get("decisive_move_used")
        engine_decisive_move = self.engine.get("engine_decisive_move_chess")

        if decisive_move_claimed != engine_decisive_move:
            raise JSONValidationError(
                f"❌ Jugada decisiva incorrecta: afirma #{decisive_move_claimed} "
                f"pero engine precalculó #{engine_decisive_move}"
            )

    def validate_material_loss_claim(self, structured: Dict):
        """
        V4: Verifica que solo se afirme pérdida material si material_events no está vacío
        Y que el decisive_move tenga material_event asociado si material_loss_claimed=true

        Raises:
            JSONValidationError: Si inventa pérdida material
        """
        material_loss_claimed = structured.get("material_loss_claimed", False)
        material_events = self.engine.get("material_events", [])
        decisive_move = structured.get("decisive_move_used")

        # Regla 1: Solo puede afirmar pérdida material si hay eventos de material
        if material_loss_claimed and not material_events:
            raise JSONValidationError(
                f"❌ Pérdida material inventada: afirma material_loss_claimed=true "
                f"pero material_events está vacío (no hubo pérdida de piezas)"
            )
        
        # Regla 2 (V4): Si afirma material_loss, el decisive_move DEBE estar en material_events
        if material_loss_claimed and material_events:
            material_moves = {e["chess_notation_move"] for e in material_events}
            if decisive_move not in material_moves:
                raise JSONValidationError(
                    f"❌ Material loss inconsistente: afirma material_loss_claimed=true "
                    f"y decisive_move=#{decisive_move}, pero ese move NO tiene material_event. "
                    f"Material events reales: {sorted(material_moves)}"
                )

    def validate_phase_problems(self, structured: Dict):
        """
        V3: Verifica que solo se marquen problemas en fases con errores reales

        Raises:
            JSONValidationError: Si inventa errores en fase limpia
        """
        phase_distribution = self.engine.get("error_distribution", {})

        # Verificar apertura
        if structured.get("opening_problem_detected", False):
            if phase_distribution.get("opening", 0) == 0:
                raise JSONValidationError(
                    f"❌ Problema de apertura inventado: afirma opening_problem_detected=true "
                    f"pero no hubo errores en apertura. Distribución real: {phase_distribution}"
                )

        # Verificar middlegame
        if structured.get("middlegame_problem_detected", False):
            if phase_distribution.get("middlegame", 0) == 0:
                raise JSONValidationError(
                    f"❌ Problema de medio juego inventado: afirma middlegame_problem_detected=true "
                    f"pero no hubo errores en middlegame. Distribución real: {phase_distribution}"
                )

        # Verificar endgame
        if structured.get("endgame_problem_detected", False):
            if phase_distribution.get("endgame", 0) == 0:
                raise JSONValidationError(
                    f"❌ Problema de final inventado: afirma endgame_problem_detected=true "
                    f"pero no hubo errores en endgame. Distribución real: {phase_distribution}"
                )

    def validate_key_moves(self, structured: Dict):
        """
        Verifica que las jugadas mencionadas existan en el evidence_pack

        Raises:
            JSONValidationError: Si menciona jugadas inexistentes
        """
        key_moves = structured.get("key_moves_explained", [])

        for move in key_moves:
            if move not in self.evidence_moves:
                raise JSONValidationError(
                    f"❌ Jugada inexistente: menciona jugada #{move} "
                    f"pero no existe en evidence_pack. Jugadas disponibles: {sorted(self.evidence_moves)}"
                )

    def validate_error_type(self, structured: Dict):
        """
        V3: Verifica que el error_type sea consistente con engine_max_swing_cp

        Raises:
            JSONValidationError: Si tipo de error inconsistente
        """
        error_type = structured.get("error_type")
        max_swing_cp = self.engine.get("engine_max_swing_cp", 0)
        loss_type = self.context.get("loss_type")

        # Si afirma "single" debe haber swing >= 250 cp
        if error_type == "single" and max_swing_cp < 250:
            raise JSONValidationError(
                f"❌ Tipo de error inconsistente: afirma error_type='single' "
                f"pero max_swing={max_swing_cp} cp (debe ser >= 250 cp para single)"
            )

        # Si afirma "accumulated" pero loss_type indica single_blunder
        if error_type == "accumulated" and loss_type == "single_blunder":
            raise JSONValidationError(
                f"❌ Tipo de error inconsistente: afirma error_type='accumulated' "
                f"pero loss_type='{loss_type}' indica error único"
            )

    def validate_confidence(self, structured: Dict):
        """
        Verifica que el confidence score esté en rango válido

        Raises:
            JSONValidationError: Si confidence fuera de rango
        """
        confidence = structured.get("confidence")

        if confidence is not None:
            if not (0.0 <= confidence <= 1.0):
                raise JSONValidationError(
                    f"❌ Confidence fuera de rango: {confidence} (debe estar entre 0.0 y 1.0)"
                )

    def validate(self, structured: Dict) -> bool:
        """
        Ejecuta todas las validaciones sobre el JSON estructurado

        Args:
            structured: Análisis estructurado generado por el LLM

        Returns:
            True si pasa todas las validaciones

        Raises:
            JSONValidationError: Si falla alguna validación
        """
        # Ejecutar las 6 validaciones
        self.validate_decisive_move(structured)
        self.validate_material_loss_claim(structured)
        self.validate_phase_problems(structured)
        self.validate_key_moves(structured)
        self.validate_error_type(structured)
        self.validate_confidence(structured)

        return True


def validate_structured_analysis(
    structured: Dict, competitive_context: Dict, evidence_pack: List[Dict]
) -> bool:
    """
    Función helper para validar análisis estructurado

    Args:
        structured: JSON generado por LLM en Paso 1
        competitive_context: Contexto competitivo (source of truth)
        evidence_pack: Movimientos con detalles

    Returns:
        True si el análisis es válido

    Raises:
        JSONValidationError: Si el análisis contiene alucinaciones
    """
    validator = StructuredAnalysisValidator(competitive_context, evidence_pack)
    return validator.validate(structured)
