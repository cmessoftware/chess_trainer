"""
Executor Service - Arquitectura Orquestada

Responsabilidad: Produce EVIDENCIA objetiva
- Ejecuta análisis desde múltiples fuentes
- Paraleliza operaciones independientes (ML + RAG)
- Ejecuta secuencialmente operaciones dependientes (Engine → Features)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, List, Optional

from .schemas import (
    AnalysisPlan,
    ExecutionResult,
    MLPrediction,
    RAGContext,
)

logger = logging.getLogger(__name__)


class ExecutorService:
    """
    Servicio de ejecución de análisis.

    Orquesta la producción de evidencia desde múltiples fuentes:
    - Stockfish (engine)
    - Feature extraction
    - ML models
    - RAG retrieval
    - Computer Vision (FEN extraction) - opcional
    """

    def __init__(
        self,
        engine_service: Optional[Any] = None,
        feature_service: Optional[Any] = None,
        ml_predictor: Optional[Any] = None,
        rag_service: Optional[Any] = None,
        cv_service: Optional[Any] = None,
    ):
        """
        Inicializa el servicio de ejecución.

        Args:
            engine_service: Servicio de análisis de Stockfish
            feature_service: Servicio de extracción de features
            ml_predictor: Predictor de errores ML
            rag_service: Servicio de recuperación RAG
            cv_service: Servicio de Computer Vision (opcional)
        """
        self.engine = engine_service
        self.features = feature_service
        self.ml = ml_predictor
        self.rag = rag_service
        self.cv = cv_service

        logger.info(
            f"[Executor] Inicializado con servicios: "
            f"engine={engine_service is not None}, "
            f"features={feature_service is not None}, "
            f"ml={ml_predictor is not None}, "
            f"rag={rag_service is not None}, "
            f"cv={cv_service is not None}"
        )

    async def execute(
        self, game: Any, plan: AnalysisPlan
    ) -> List[ExecutionResult]:
        """
        Ejecuta el plan de análisis y produce evidencia.

        Estrategia de paralelización:
        1. Engine + Features: Secuencial (Features dependen de Engine)
        2. ML + RAG: Paralelo (independientes)

        Args:
            game: Partida a analizar (debe tener .moves, .id, get_fen_at())
            plan: Plan generado por Planner

        Returns:
            Lista de ExecutionResult con evidencia de cada jugada

        Raises:
            ValueError: Si el game no tiene los métodos requeridos
        """
        logger.info(
            f"[Executor] Ejecutando plan: {len(plan.target_moves)} jugadas, "
            f"modos={plan.analysis_modes}"
        )

        # Validar game
        if not hasattr(game, "moves") or not hasattr(game, "id"):
            raise ValueError("Game must have 'moves' and 'id' attributes")

        if not hasattr(game, "get_fen_at"):
            raise ValueError("Game must have 'get_fen_at()' method")

        results = []
        start_time = datetime.now()

        for ply in plan.target_moves:
            move_start = datetime.now()

            try:
                result = await self._execute_move_analysis(game, plan, ply)
                results.append(result)

                logger.debug(
                    f"[Executor] Jugada (ply {ply}) completada en "
                    f"{(datetime.now() - move_start).total_seconds():.2f}s"
                )

            except Exception as e:
                logger.error(
                    f"[Executor] Error analizando jugada (ply {ply}): {e}",
                    exc_info=True,
                )
                # Continuar con siguiente jugada
                continue

        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[Executor] Completado: {len(results)}/{len(plan.target_moves)} "
            f"jugadas en {total_time:.2f}s"
        )

        return results

    async def _execute_move_analysis(
        self, game: Any, plan: AnalysisPlan, ply: int
    ) -> ExecutionResult:
        """
        Ejecuta análisis completo de una jugada.

        Args:
            game: Partida
            plan: Plan de análisis
            ply: Ply number de la jugada a analizar

        Returns:
            ExecutionResult con toda la evidencia
        """
        move_start = datetime.now()
        
        # Buscar el move por ply number
        move = None
        for m in game.moves:
            if hasattr(m, "ply") and m.ply == ply:
                move = m
                break
        
        if not move:
            raise ValueError(f"No se encontró move con ply={ply}")

        # ====================================================================
        # PASO 1: Engine Analysis (bloqueante)
        # ====================================================================
        engine_result = await self._run_engine_analysis(game, ply, plan)

        # ====================================================================
        # PASO  2: Feature Extraction (depende de engine)
        # ====================================================================
        features = self._extract_features(game, ply, engine_result)

        # ====================================================================
        # PASO 3: ML + RAG en paralelo (independientes)
        # ====================================================================
        ml_task = None
        rag_task = None

        if "ml" in plan.analysis_modes and self.ml is not None:
            ml_task = self._run_ml_prediction(features, engine_result)

        if "rag" in plan.analysis_modes and self.rag is not None:
            rag_task = self._run_rag_retrieval(game, ply)

        # Ejecutar en paralelo solo si hay tasks
        ml_result = None
        rag_result = None

        if ml_task or rag_task:
            tasks = []
            if ml_task:
                tasks.append(ml_task)
            if rag_task:
                tasks.append(rag_task)

            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Asignar resultados (mantener orden)
            result_idx = 0
            if ml_task:
                ml_result = (
                    parallel_results[result_idx]
                    if not isinstance(parallel_results[result_idx], Exception)
                    else None
                )
                result_idx += 1
            if rag_task:
                rag_result = (
                    parallel_results[result_idx]
                    if not isinstance(parallel_results[result_idx], Exception)
                    else None
                )

        # ====================================================================
        # PASO 4: Ensamblar resultado
        # ====================================================================
        execution_time = (datetime.now() - move_start).total_seconds()

        result = ExecutionResult(
            game_id=game.id,
            ply=ply,
            move_san=getattr(move, "move_san", getattr(move, "san", str(move))),
            fen_before=game.get_fen_at(ply),
            fen_after=game.get_fen_at(ply + 1),
            engine_eval_before=engine_result.get("eval_before", 0.0),
            engine_eval_after=engine_result.get("eval_after", 0.0),
            score_diff=engine_result.get("score_diff", 0.0),
            best_move=engine_result.get("best_move", ""),
            best_line=engine_result.get("best_line", []),
            features=features,
            tactical_tags=engine_result.get("tactical_tags", []),
            phase=self._determine_phase(ply, len(game.moves)),
            ml_prediction=ml_result,
            rag_context=rag_result,
            timestamp=datetime.now(),
            execution_time=execution_time,
        )

        return result

    async def _run_engine_analysis(
        self, game: Any, ply: int, plan: AnalysisPlan
    ) -> dict:
        """
        Ejecuta análisis de Stockfish.

        Args:
            game: Partida
            ply: Ply number de la jugada
            plan: Plan (tiene depth en options)

        Returns:
            dict con eval_before, eval_after, best_move, best_line, tactical_tags
        """
        if self.engine is None:
            logger.warning("[Executor] Engine service not available, using move data")
            # Si no hay engine service, intentar usar datos del move
            return self._extract_engine_data_from_move(game, ply)

        try:
            fen_before = game.get_fen_at(ply)

            # Call engine service to analyze position
            analysis = self.engine.analyze_position(fen_before)

            # Get eval_before from move data
            move = None
            for m in game.moves:
                if hasattr(m, "ply") and m.ply == ply:
                    move = m
                    break

            eval_before = getattr(move, "eval_before", 0.0) if move else 0.0
            eval_after = analysis.get("eval", 0.0)

            return {
                "eval_before": eval_before,
                "eval_after": eval_after,
                "score_diff": eval_after - eval_before,
                "best_move": analysis.get("best_move", ""),
                "best_line": analysis.get("best_line", []),
                "tactical_tags": analysis.get("tactical_tags", []),
            }

        except Exception as e:
            logger.error(f"[Executor] Error en engine analysis: {e}")
            return self._extract_engine_data_from_move(game, ply)

    def _extract_engine_data_from_move(self, game: Any, ply: int) -> dict:
        """
        Extrae datos de evaluación del move si están disponibles.
        
        Args:
            game: Partida
            ply: Ply number
            
        Returns:
            dict con eval_before, eval_after, score_diff, best_move, best_line, tactical_tags
        """
        # Buscar move por ply number
        move = None
        for m in game.moves:
            if hasattr(m, "ply") and m.ply == ply:
                move = m
                break
        
        if move:
            eval_before = getattr(move, "eval_before", 0.0)
            eval_after = getattr(move, "eval_after", 0.0)
            score_diff = eval_after - eval_before
            best_move = getattr(move, "best_move", "")
            move_san = getattr(move, "move_san", getattr(move, "san", ""))
            tactical_tags = getattr(move, "tactical_tags", [])
            
            return {
                "eval_before": eval_before,
                "eval_after": eval_after,
                "score_diff": score_diff,
                "best_move": best_move or move_san,
                "best_line": [best_move] if best_move else [move_san] if move_san else [],
                "tactical_tags": tactical_tags if isinstance(tactical_tags, list) else [],
            }
        
        # Fallback values
        return {
            "eval_before": 0.0,
            "eval_after": 0.0,
            "score_diff": 0.0,
            "best_move": "",
            "best_line": [],
            "tactical_tags": [],
        }

    async def _engine_analyze_position(
        self, game: Any, ply: int, fen_before: str, fen_after: str, depth: int
    ) -> dict:
        """
        Fallback: análisis de engine via move data.
        """
        return self._extract_engine_data_from_move(game, ply)

    def _extract_features(
        self, game: Any, ply: int, engine_result: dict
    ) -> dict:
        """
        Extrae features de la posición.

        Args:
            game: Partida
            ply: Ply number
            engine_result: Resultado del engine

        Returns:
            dict con features {feature_name: value}
        """
        if self.features is None:
            logger.warning("[Executor] Feature service not available")
            return {}

        try:
            fen = game.get_fen_at(ply)
            return self.features.extract_features(fen, engine_result)

        except Exception as e:
            logger.error(f"[Executor] Error en feature extraction: {e}")
            return {}

    async def _run_ml_prediction(
        self, features: dict, engine_result: dict
    ) -> Optional[MLPrediction]:
        """
        Ejecuta predicción ML de error.

        Args:
            features: Features extraídas
            engine_result: Resultado del engine

        Returns:
            MLPrediction o None si falla
        """
        if self.ml is None:
            return None

        try:
            return await self.ml.predict(features)

        except Exception as e:
            logger.error(f"[Executor] Error en ML prediction: {e}")
            return None

    async def _run_rag_retrieval(
        self, game: Any, ply: int
    ) -> Optional[RAGContext]:
        """
        Recupera contexto similar via RAG.

        Args:
            game: Partida
            ply: Ply number

        Returns:
            RAGContext o None si falla
        """
        if self.rag is None:
            return None

        try:
            return await self.rag.retrieve(game, ply)

        except Exception as e:
            logger.error(f"[Executor] Error en RAG retrieval: {e}")
            return None

    @staticmethod
    def _determine_phase(ply: int, total_moves: int) -> str:
        """
        Determina la fase de juego.

        Args:
            ply: Ply number de la jugada
            total_moves: Total de jugadas

        Returns:
            "opening" | "middlegame" | "endgame"
        """
        if ply < 15:
            return "opening"
        elif ply < 40 or ply < total_moves * 0.7:
            return "middlegame"
        else:
            return "endgame"
