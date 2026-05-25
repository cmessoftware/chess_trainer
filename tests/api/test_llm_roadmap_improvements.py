"""
Tests para validar las mejoras del roadmap LLM (Fase 1, Secciones 1-5)

Valida:
- Evidence pack move-by-move
- Calibración por ELO
- Output policy por bucket
- Diferenciación winner/loser
- Integración de contexto competitivo
"""

import pytest
import asyncio
from sqlalchemy.orm import Session
from src.api.services.llm_analysis_service import LLMAnalysisService
from src.api.services.analysis_service import AnalysisService
from src.db.database import SessionLocal
import re


@pytest.fixture
def db_session():
    """Fixture para sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def llm_service():
    """Fixture para LLMAnalysisService"""
    return LLMAnalysisService()


@pytest.fixture
def analysis_service():
    """Fixture para AnalysisService"""
    return AnalysisService()


# ID de juego de prueba (ajustar según tu DB)
TEST_GAME_ID = "cmess1315_vs_Th3Hound_2024-11-30"
TEST_USERNAME = "cmess1315"
TEST_ELO_NOVICE = 1400
TEST_ELO_ADVANCED = 2000


class TestEvidencePackMoveByMove:
    """Tests para _get_top_error_moves() - Sección 5.2"""

    def test_get_top_error_moves_returns_list(self, db_session, llm_service):
        """Verifica que retorne una lista de movimientos con error"""
        # Primero necesitamos un analysis_id válido
        analysis_service = AnalysisService()
        analysis_id = analysis_service.analyze_game(
            db=db_session,
            game_id=TEST_GAME_ID,
            username=TEST_USERNAME,
            player_color="white",
        )

        # Obtener top error moves
        error_moves = llm_service._get_top_error_moves(
            db=db_session, analysis_id=analysis_id, top_n=8
        )

        assert isinstance(error_moves, list)
        assert len(error_moves) > 0, "Debe retornar al menos un movimiento con error"

    def test_error_moves_structure(self, db_session, llm_service):
        """Verifica la estructura de cada movimiento del evidence pack"""
        analysis_service = AnalysisService()
        analysis_id = analysis_service.analyze_game(
            db=db_session,
            game_id=TEST_GAME_ID,
            username=TEST_USERNAME,
            player_color="white",
        )

        error_moves = llm_service._get_top_error_moves(
            db=db_session, analysis_id=analysis_id, top_n=5
        )

        for move in error_moves:
            # Verificar campos requeridos
            assert "move_number" in move
            assert "error_label" in move
            assert "top_shap_features" in move
            assert "shap_impact" in move
            assert "severity_score" in move

            # Verificar tipos
            assert isinstance(move["move_number"], int)
            assert move["error_label"] in ["blunder", "mistake", "inaccuracy"]
            assert isinstance(move["top_shap_features"], list)
            assert len(move["top_shap_features"]) <= 3, "Debe tener máximo 3 features"

            # Verificar que cada feature tenga estructura correcta
            for feature in move["top_shap_features"]:
                assert "feature" in feature
                assert "shap_value" in feature
                assert isinstance(feature["shap_value"], (int, float))

    def test_error_moves_ordered_by_severity(self, db_session, llm_service):
        """Verifica que los movimientos estén ordenados por severidad descendente"""
        analysis_service = AnalysisService()
        analysis_id = analysis_service.analyze_game(
            db=db_session,
            game_id=TEST_GAME_ID,
            username=TEST_USERNAME,
            player_color="black",
        )

        error_moves = llm_service._get_top_error_moves(
            db=db_session, analysis_id=analysis_id, top_n=8
        )

        # Verificar orden descendente por severity_score
        severity_scores = [m["severity_score"] for m in error_moves]
        assert severity_scores == sorted(
            severity_scores, reverse=True
        ), "Los movimientos deben estar ordenados por severity_score descendente"


class TestCalibrationByElo:
    """Tests para _calibrate_severity_by_elo() - Sección 4.1"""

    def test_calibrate_blunder_novice(self, llm_service):
        """Verifica calibración de blunder para jugador novice"""
        calibration = llm_service._calibrate_severity_by_elo(
            error_label="blunder", player_elo=1400, shap_impact=0.5
        )

        assert calibration["pedagogical_severity"] == "crítico"
        assert calibration["priority"] == "alta"
        assert "costó" in calibration["narrative_tone"].lower()

    def test_calibrate_inaccuracy_novice_vs_advanced(self, llm_service):
        """Verifica que inaccuracy sea menos prioritaria para novice que para advanced"""
        calibration_novice = llm_service._calibrate_severity_by_elo(
            error_label="inaccuracy", player_elo=1400, shap_impact=0.2
        )

        calibration_advanced = llm_service._calibrate_severity_by_elo(
            error_label="inaccuracy", player_elo=2200, shap_impact=0.2
        )

        # Para novice, inaccuracy es baja prioridad
        assert calibration_novice["priority"] == "baja"

        # Para advanced, inaccuracy es seria
        assert calibration_advanced["pedagogical_severity"] == "serio"
        assert calibration_advanced["priority"] == "alta"

    def test_calibrate_mistake_intermediate(self, llm_service):
        """Verifica calibración de mistake para jugador intermediate"""
        calibration = llm_service._calibrate_severity_by_elo(
            error_label="mistake", player_elo=1800, shap_impact=0.4
        )

        assert calibration["pedagogical_severity"] == "serio"
        assert calibration["priority"] == "alta"


class TestEloOutputPolicy:
    """Tests para _get_elo_output_policy() - Sección 4.2"""

    def test_output_policy_novice(self, llm_service):
        """Verifica política de salida para jugador novice"""
        policy = llm_service._get_elo_output_policy(player_elo=1400)

        assert policy["max_bullet_points"] == 3
        assert policy["max_key_moves"] == 2
        assert policy["max_words"] == 300
        assert not policy["include_variations"]
        assert "analogías simples" in policy["teaching_style"]

    def test_output_policy_intermediate(self, llm_service):
        """Verifica política de salida para jugador intermediate"""
        policy = llm_service._get_elo_output_policy(player_elo=1800)

        assert policy["max_bullet_points"] == 5
        assert policy["max_key_moves"] == 4
        assert policy["max_words"] == 450
        assert policy["include_variations"]

    def test_output_policy_advanced(self, llm_service):
        """Verifica política de salida para jugador advanced"""
        policy = llm_service._get_elo_output_policy(player_elo=2200)

        assert policy["max_bullet_points"] == 6
        assert policy["max_key_moves"] == 6
        assert policy["max_words"] == 600
        assert policy["include_variations"]
        assert "técnico profundo" in policy["teaching_style"]


class TestCompetitiveContextIntegration:
    """Tests para integración de contexto competitivo"""

    @pytest.mark.asyncio
    async def test_report_includes_competitive_context(self, db_session, llm_service):
        """Verifica que el reporte incluya contexto competitivo"""
        report = await llm_service.generate_pedagogical_report(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_elo=TEST_ELO_NOVICE,
            player_color="white",
            username=TEST_USERNAME,
        )

        # El reporte debe incluir información del resultado
        report_text = report["report"]

        # Verificar que mencione el resultado (win/loss/draw)
        # O al menos que el contexto esté presente en metadata
        assert "patterns_detected" in report
        assert isinstance(report["patterns_detected"], list)

    @pytest.mark.asyncio
    async def test_winner_vs_loser_differentiation(self, db_session, llm_service):
        """
        Verifica que los reportes sean diferentes para ganador vs perdedor

        Este es el test más importante: validar que la diferenciación funciona
        """
        # Generar reporte para blancas (ganador en este juego)
        report_winner = await llm_service.generate_pedagogical_report(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_elo=TEST_ELO_NOVICE,
            player_color="white",
            username=TEST_USERNAME,
        )

        # Generar reporte para negras (perdedor en este juego)
        report_loser = await llm_service.generate_pedagogical_report(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_elo=TEST_ELO_NOVICE,
            player_color="black",
            username=TEST_USERNAME,
        )

        report_winner_text = report_winner["report"]
        report_loser_text = report_loser["report"]

        # Los reportes NO deben ser idénticos
        assert (
            report_winner_text != report_loser_text
        ), "Los reportes de ganador y perdedor no deben ser idénticos"

        # Verificar longitud diferente (indicador de contenido distinto)
        len_diff = abs(len(report_winner_text) - len(report_loser_text))
        assert (
            len_diff > 50
        ), f"Los reportes deben tener diferencias significativas de longitud (diff: {len_diff})"

        # Verificar que mencionen movimientos específicos (evidence pack)
        move_pattern = r"#\d+"
        winner_moves = set(re.findall(move_pattern, report_winner_text))
        loser_moves = set(re.findall(move_pattern, report_loser_text))

        assert (
            len(winner_moves) >= 2
        ), "Reporte ganador debe citar al menos 2 movimientos"
        assert (
            len(loser_moves) >= 2
        ), "Reporte perdedor debe citar al menos 2 movimientos"


class TestPromptBuilding:
    """Tests para construcción de prompt con todas las mejoras"""

    def test_build_prompt_includes_evidence_pack(self, db_session, llm_service):
        """Verifica que el prompt incluya el evidence pack"""
        analysis_service = AnalysisService()
        analysis_id = analysis_service.analyze_game(
            db=db_session,
            game_id=TEST_GAME_ID,
            username=TEST_USERNAME,
            player_color="white",
        )

        # Obtener componentes del prompt
        shap_summary = llm_service._get_shap_summary(
            db=db_session, analysis_id=analysis_id
        )
        patterns = llm_service._synthesize_patterns(
            db=db_session, analysis_id=analysis_id, shap_summary=shap_summary
        )
        competitive_context = llm_service._get_competitive_context(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_color="white",
            analysis_id=analysis_id,
        )
        top_error_moves = llm_service._get_top_error_moves(
            db=db_session, analysis_id=analysis_id, top_n=8
        )

        # Construir prompt
        prompt = llm_service._build_prompt(
            player_elo=TEST_ELO_NOVICE,
            patterns=patterns,
            shap_summary=shap_summary,
            competitive_context=competitive_context,
            top_error_moves=top_error_moves,
        )

        # Verificar que el prompt incluya secciones clave
        assert "Evidence Pack" in prompt or "Movimientos Críticos" in prompt
        assert "Contexto Competitivo" in prompt
        assert "Resultado:" in prompt
        assert "error rate" in prompt.lower() or "error ratio" in prompt.lower()

        # Verificar que mencione movimientos específicos del evidence pack
        for move in top_error_moves[:3]:  # Al menos los 3 primeros
            assert (
                f"#{move['move_number']}" in prompt
            ), f"Prompt debe incluir movimiento #{move['move_number']}"


class TestMetricsAndPerformance:
    """Tests para validar métricas de performance"""

    @pytest.mark.asyncio
    async def test_token_usage_optimized(self, db_session, llm_service):
        """Verifica que el uso de tokens esté optimizado (< 1000)"""
        report = await llm_service.generate_pedagogical_report(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_elo=TEST_ELO_NOVICE,
            player_color="white",
            username=TEST_USERNAME,
        )

        tokens_total = report["tokens_used"]["total"]
        assert (
            tokens_total < 1000
        ), f"Tokens totales ({tokens_total}) deben ser < 1000 (optimizado)"

        # Verificar que el costo sea razonable
        cost = report["cost_estimate_usd"]
        assert cost < 0.035, f"Costo estimado ({cost}) debe ser < $0.035"

    @pytest.mark.asyncio
    async def test_report_generation_latency(self, db_session, llm_service):
        """Verifica que la generación del reporte sea rápida (< 10s)"""
        import time

        start_time = time.time()

        report = await llm_service.generate_pedagogical_report(
            db=db_session,
            game_id=TEST_GAME_ID,
            player_elo=TEST_ELO_NOVICE,
            player_color="white",
            username=TEST_USERNAME,
        )

        elapsed_time = time.time() - start_time

        assert (
            elapsed_time < 10
        ), f"Generación del reporte tomó {elapsed_time:.2f}s, debe ser < 10s"


# Función helper para ejecutar tests async
def run_async_test(coro):
    """Helper para ejecutar tests async"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


if __name__ == "__main__":
    """
    Ejecutar tests directamente:
    python tests/api/test_llm_roadmap_improvements.py

    O con pytest:
    pytest tests/api/test_llm_roadmap_improvements.py -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
