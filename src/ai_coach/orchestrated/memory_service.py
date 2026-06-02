"""
Memory Service - Arquitectura Orquestada

Responsabilidad: Persistencia y aprendizaje ACUMUL ADO
- Guarda análisis por jugada (move_analyses)
- Actualiza patrones de jugador (player_patterns)
- Soporta dual write con feature flags para migración gradual
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import EnrichedResult, PlayerPatterns

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Servicio de persistencia y patrones de jugador.

    Responsabilidades:
    - Guardar análisis por jugada (tabla move_analyses)
    - Agregar patrones del jugador (tabla player_patterns)
    - Clustering de errores (futuro)
    - Proveer historial para personalización

    Feature Flags:
    - ENABLE_DUAL_WRITE: Escribe tanto en v1.0 (moves) como v2.0 (move_analyses)
    - PREFER_VERSION: Controla de qué versión leer ("v1.0" | "v2.0")
    """

    def __init__(self, db_session: AsyncSession):
        """
        Inicializa el servicio de memoria.

        Args:
            db_session: Sesión de base de datos SQLAlchemy asíncrona
        """
        self.db = db_session

        # Feature Flags (desde environment o config)
        self.enable_dual_write = os.getenv("ENABLE_DUAL_WRITE", "true").lower() == "true"
        self.prefer_version = os.getenv("PREFER_VERSION", "v2.0")

        logger.info(
            f"[Memory] Inicializado con dual_write={self.enable_dual_write}, "
            f"prefer_version={self.prefer_version}"
        )

    async def store_move_analysis(
        self, game_id: str, player_id: int, enriched_result: EnrichedResult
    ) -> None:
        """
        Guarda análisis de una jugada con toda la metadata.

        Args:
            game_id: ID de la partida (UUID)
            player_id: ID del jugador
            enriched_result: Resultado enriquecido con explicación y crítica

        Raises:
            Exception: Si falla la inserción en DB
        """
        try:
            # Escribir a move_analyses (v2.0)
            await self._store_v2_move_analysis(game_id, player_id, enriched_result)

            # Si dual_write está activo, escribir también a moves (v1.0)
            if self.enable_dual_write:
                await self._store_v1_move_legacy(game_id, player_id, enriched_result)

            logger.debug(
                f"[Memory] Guardado análisis: game={game_id}, "
                f"ply={enriched_result.execution_result.ply}"
            )

        except Exception as e:
            logger.error(f"[Memory] Error guardando move_analysis: {e}", exc_info=True)
            raise

    async def _store_v2_move_analysis(
        self, game_id: str, player_id: int, enriched_result: EnrichedResult
    )-> None:
        """Guarda en tabla move_analyses (esquema v2.0)."""
        exec_result = enriched_result.execution_result
        critic_result = enriched_result.critic_result

        # Preparar campos JSONB
        ml_contributing_features = None
        if exec_result.ml_prediction:
            ml_contributing_features = exec_result.ml_prediction.contributing_features

        rag_similar_positions = None
        if exec_result.rag_context:
            rag_similar_positions = exec_result.rag_context.similar_positions

        rag_book_excerpts = None
        if exec_result.rag_context:
            rag_book_excerpts = exec_result.rag_context.book_excerpts

        rag_total_retrieved = 0
        if exec_result.rag_context:
            rag_total_retrieved = exec_result.rag_context.total_retrieved

        rag_relevance_scores = None
        if exec_result.rag_context and exec_result.rag_context.relevance_scores:
            rag_relevance_scores = exec_result.rag_context.relevance_scores

        # Preparar critic_issues como JSONB
        critic_issues = [
            {
                "rule_name": issue.rule_name,
                "severity": issue.severity,
                "message": issue.message,
                "context": issue.context,
            }
            for issue in critic_result.issues
        ]

        # SQL Insert
        query = text("""
            INSERT INTO move_analyses (
                game_id, player_id, ply, move_san,
                fen_before, fen_after,
                engine_eval_before, engine_eval_after, score_diff,
                best_move, best_line,
                features, tactical_tags, phase,
                ml_predicted_error, ml_confidence, ml_risk_score, ml_contributing_features,
                rag_similar_positions, rag_book_excerpts, rag_total_retrieved, rag_relevance_scores,
                explanation,
                is_consistent, critic_confidence, critic_issues,
                critic_passed_rules, critic_failed_rules,
                created_at, execution_time, version
            ) VALUES (
                :game_id, :player_id, :ply, :move_san,
                :fen_before, :fen_after,
                :engine_eval_before, :engine_eval_after, :score_diff,
                :best_move, :best_line,
                :features, :tactical_tags, :phase,
                :ml_predicted_error, :ml_confidence, :ml_risk_score, :ml_contributing_features,
                :rag_similar_positions, :rag_book_excerpts, :rag_total_retrieved, :rag_relevance_scores,
                :explanation,
                :is_consistent, :critic_confidence, :critic_issues,
                :critic_passed_rules, :critic_failed_rules,
                :created_at, :execution_time, :version
            )
        """)

        await self.db.execute(
            query,
            {
                "game_id": game_id,
                "player_id": player_id,
                "ply": exec_result.ply,
                "move_san": exec_result.move_san,
                "fen_before": exec_result.fen_before,
                "fen_after": exec_result.fen_after,
                "engine_eval_before": exec_result.engine_eval_before,
                "engine_eval_after": exec_result.engine_eval_after,
                "score_diff": exec_result.score_diff,
                "best_move": exec_result.best_move,
                "best_line": exec_result.best_line,
                "features": exec_result.features,
                "tactical_tags": exec_result.tactical_tags,
                "phase": exec_result.phase,
                "ml_predicted_error": (
                    exec_result.ml_prediction.predicted_error
                    if exec_result.ml_prediction
                    else None
                ),
                "ml_confidence": (
                    exec_result.ml_prediction.confidence
                    if exec_result.ml_prediction
                    else None
                ),
                "ml_risk_score": (
                    exec_result.ml_prediction.risk_score
                    if exec_result.ml_prediction
                    else None
                ),
                "ml_contributing_features": ml_contributing_features,
                "rag_similar_positions": rag_similar_positions,
                "rag_book_excerpts": rag_book_excerpts,
                "rag_total_retrieved": rag_total_retrieved,
                "rag_relevance_scores": rag_relevance_scores,
                "explanation": enriched_result.explanation,
                "is_consistent": critic_result.is_consistent,
                "critic_confidence": critic_result.confidence,
                "critic_issues": critic_issues,
                "critic_passed_rules": critic_result.passed_rules,
                "critic_failed_rules": critic_result.failed_rules,
                "created_at": datetime.now(),
                "execution_time": exec_result.execution_time,
                "version": "v2.0",
            },
        )

        await self.db.commit()

    async def _store_v1_move_legacy(
        self, game_id: str, player_id: int, enriched_result: EnrichedResult
    ) -> None:
        """
        Guarda también en tabla moves (esquema v1.0 legacy).
        Solo se usa durante migración gradual con dual write.
        """
        logger.debug(f"[Memory] Dual write to v1.0 moves table (legacy)")

        # TODO: Implementar escritura a tabla moves legacy
        # Por ahora, log placeholder
        pass

    async def update_player_patterns(
        self, player_id: int, analysis_results: List[EnrichedResult]
    ) -> None:
        """
        Actualiza patrones agregados del jugador.

        Calcula:
        - Frecuencia de tipos de error
        - Temas tácticos recurrentes
        - Fases de juego débiles
        - Tendencias temporales

        Args:
            player_id: ID del jugador
            analysis_results: Lista de resultados enriquecidos del análisis

        Raises:
            Exception: Si falla la actualización
        """
        try:
            if not analysis_results:
                logger.warning(
                    f"[Memory] No hay resultados para actualizar patrones de player {player_id}"
                )
                return

            # Calcular estadísticas
            stats = self._compute_player_statistics(analysis_results)

            # Upsert a player_patterns
            await self._upsert_player_patterns(player_id, stats)

            logger.info(
                f"[Memory] Actualizado patrones de player {player_id}: "
                f"{stats['total_moves_analyzed']} movimientos"
            )

        except Exception as e:
            logger.error(
                f"[Memory] Error actualizando player_patterns: {e}", exc_info=True
            )
            raise

    def _compute_player_statistics(
        self, results: List[EnrichedResult]
    ) -> Dict[str, Any]:
        """
        Calcula estadísticas agregadas del jugador.

        Args:
            results: Resultados de análisis

        Returns:
            dict con estadísticas calculadas
        """
        total_moves = len(results)

        # Distribución de errores
        error_counts = {"good": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0}
        for result in results:
            if result.execution_result.ml_prediction:
                error_type = result.execution_result.ml_prediction.predicted_error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        error_distribution = {
            error: count / total_moves for error, count in error_counts.items()
        }

        # Tácticas frecuentes
        tactic_counts: Dict[str, int] = {}
        for result in results:
            for tactic in result.execution_result.tactical_tags:
                tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1

        frequent_tactics = [
            {"tactic": tactic, "count": count}
            for tactic, count in sorted(
                tactic_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Errores por fase
        phase_errors = {"opening": 0, "middlegame": 0, "endgame": 0}
        phase_counts = {"opening": 0, "middlegame": 0, "endgame": 0}

        for result in results:
            phase = result.execution_result.phase
            phase_counts[phase] += 1

            if result.execution_result.ml_prediction:
                error = result.execution_result.ml_prediction.predicted_error
                if error in ["inaccuracy", "mistake", "blunder"]:
                    phase_errors[phase] += 1

        phase_error_rates = {
            phase: (phase_errors[phase] / phase_counts[phase] if phase_counts[phase] > 0 else 0.0)
            for phase in phase_errors
        }

        # Fases débiles (error_rate > 0.15)
        weak_phases = [
            phase for phase, rate in phase_error_rates.items() if rate > 0.15
        ]

        # Tendencia de mejora (placeholder - requiere análisis temporal)
        improvement_trend = 0.0

        # Error rate reciente
        recent_avg_error_rate = 1.0 - error_distribution.get("good", 0.0)

        return {
            "total_moves_analyzed": total_moves,
            "error_distribution": error_distribution,
            "frequent_tactics": frequent_tactics,
            "weak_phases": weak_phases,
            "phase_error_rates": phase_error_rates,
            "improvement_trend": improvement_trend,
            "recent_avg_error_rate": recent_avg_error_rate,
        }

    async def _upsert_player_patterns(
        self, player_id: int, stats: Dict[str, Any]
    ) -> None:
        """
        Inserta o actualiza patrones del jugador en la tabla player_patterns.

        Args:
            player_id: ID del jugador
            stats: Estadísticas calculadas
        """
        query = text("""
            INSERT INTO player_patterns (
                player_id,
                total_moves_analyzed,
                error_distribution,
                frequent_tactics,
                weak_phases,
                phase_error_rates,
                improvement_trend,
                recent_avg_error_rate,
                last_updated
            ) VALUES (
                :player_id,
                :total_moves_analyzed,
                :error_distribution,
                :frequent_tactics,
                :weak_phases,
                :phase_error_rates,
                :improvement_trend,
                :recent_avg_error_rate,
                :last_updated
            )
            ON CONFLICT (player_id)
            DO UPDATE SET
                total_moves_analyzed = player_patterns.total_moves_analyzed + EXCLUDED.total_moves_analyzed,
                error_distribution = EXCLUDED.error_distribution,
                frequent_tactics = EXCLUDED.frequent_tactics,
                weak_phases = EXCLUDED.weak_phases,
                phase_error_rates = EXCLUDED.phase_error_rates,
                improvement_trend = EXCLUDED.improvement_trend,
                recent_avg_error_rate = EXCLUDED.recent_avg_error_rate,
                last_updated = EXCLUDED.last_updated
        """)

        await self.db.execute(
            query,
            {
                "player_id": player_id,
                "total_moves_analyzed": stats["total_moves_analyzed"],
                "error_distribution": stats["error_distribution"],
                "frequent_tactics": stats["frequent_tactics"],
                "weak_phases": stats["weak_phases"],
                "phase_error_rates": stats["phase_error_rates"],
                "improvement_trend": stats["improvement_trend"],
                "recent_avg_error_rate": stats["recent_avg_error_rate"],
                "last_updated": datetime.now(),
            },
        )

        await self.db.commit()

    async def get_player_patterns(
        self, player_id: int, lookback_days: int = 30
    ) -> Optional[PlayerPatterns]:
        """
        Recupera patrones del jugador de los últimos N días.

        Args:
            player_id: ID del jugador
            lookback_days: Ventana de tiempo (días)

        Returns:
            PlayerPatterns o None si no hay datos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            query = text("""
                SELECT * FROM player_patterns
                WHERE player_id = :player_id
                AND last_updated >= :cutoff_date
            """)

            result = await self.db.execute(
                query, {"player_id": player_id, "cutoff_date": cutoff_date}
            )

            row = result.fetchone()

            if not row:
                logger.warning(
                    f"[Memory] No player_patterns found for player {player_id}"
                )
                return None

            # Construir PlayerPatterns
            patterns = PlayerPatterns(
                player_id=row.player_id,
                total_games_analyzed=0,  # TODO: Calcular desde move_analyses
                total_moves_analyzed=row.total_moves_analyzed,
                error_distribution=row.error_distribution,
                frequent_tactics=row.frequent_tactics,
                weak_phases=row.weak_phases,
                phase_error_rates=row.phase_error_rates,
                improvement_trend=row.improvement_trend,
                recent_avg_error_rate=row.recent_avg_error_rate,
                error_clusters=[],  # TODO: Implementar clustering
                last_updated=row.last_updated,
            )

            return patterns

        except Exception as e:
            logger.error(f"[Memory] Error obteniendo player_patterns: {e}", exc_info=True)
            return None
