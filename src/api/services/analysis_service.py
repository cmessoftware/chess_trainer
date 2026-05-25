# api/services/analysis_service.py
"""
Analysis Service - Servicio para análisis ML de partidas con persistencia SHAP.

Responsabilidades:
- Ejecutar análisis ML sobre partidas
- Calcular SHAP values con ShapService
- Persistir resultados en analysis_results
- Persistir SHAP values en move_shap_values
- Actualizar agregados en player_feature_importance
- Proveer datos para dashboard React
"""
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import pandas as pd
import numpy as np

from db.models.analysis_results import AnalysisResult
from db.models.move_shap_values import MoveShapValue
from db.models.player_feature_importance import PlayerFeatureImportance
from db.models.features import Features
from db.models.games import Games
from api.services.shap_service import ShapService


class AnalysisService:
    """
    Servicio para análisis ML + SHAP con persistencia en base de datos.

    Workflow:
    1. Obtener features de partida (desde tabla features)
    2. Ejecutar predicción ML
    3. Calcular SHAP values
    4. Persistir en analysis_results + move_shap_values
    5. Actualizar player_feature_importance
    """

    def __init__(self):
        """Inicializar servicio con ShapService"""
        self.shap_service = ShapService()

        # Mapeo de error_label a clasificación global
        self.error_mapping = {
            "blunder": "blunder_prone",
            "mistake": "mistake_prone",
            "inaccuracy": "accurate",
            "good_move": "excellent",
        }

    def analyze_game(
        self, db: Session, game_id: str, username: str, player_color: str = "white"
    ) -> int:
        """
        Analizar partida completa con ML + SHAP y persistir resultados.

        Args:
            db: Sesión de base de datos SQLAlchemy
            game_id: ID de la partida a analizar
            username: Usuario para el cual se analiza (puede != imported_by)
            player_color: Color del jugador a analizar ("white" o "black")

        Returns:
            analysis_id: ID del registro en analysis_results

        Raises:
            ValueError: Si no hay features para la partida

        Example:
            >>> analysis_id = analysis_service.analyze_game(db, "abc123", "user1", "white")
            >>> print(f"Análisis completado: {analysis_id}")
        """
        # Convertir player_color a int (1=white, 0=black)
        color_int = 1 if player_color.lower() == "white" else 0

        # 1. Verificar si ya existe análisis reciente (cache)
        existing = (
            db.query(AnalysisResult)
            .filter(
                and_(
                    AnalysisResult.game_id == game_id,
                    AnalysisResult.username == username,
                    AnalysisResult.analyzed_at > datetime.now() - timedelta(days=7),
                )
            )
            .first()
        )

        if existing:
            print(f"♻️  Análisis existente encontrado (ID: {existing.id})")
            return existing.id

        # 2. Obtener features de la partida SOLO del jugador especificado
        features_rows = (
            db.query(Features)
            .filter(
                and_(Features.game_id == game_id, Features.player_color == color_int)
            )
            .all()
        )

        print(
            f"🎯 Analizando {len(features_rows)} movimientos del jugador {player_color}"
        )

        if not features_rows:
            raise ValueError(f"No se encontraron features para game_id={game_id}")

        # Convertir a DataFrame - SEPARAR features numéricas de contexto
        features_numeric = pd.DataFrame(
            [
                {
                    "material_balance": f.material_balance,
                    "material_total": f.material_total,
                    "num_pieces": f.num_pieces,
                    "branching_factor": f.branching_factor,
                    "self_mobility": f.self_mobility,
                    "opponent_mobility": f.opponent_mobility,
                    "move_number_global": f.move_number_global,
                    "is_center_controlled": f.is_center_controlled,
                    "score_diff": f.score_diff,
                    # Add more numeric features as needed
                }
                for f in features_rows
            ]
        )

        # Contexto del movimiento (NO enviar a SHAP, solo para persistencia)
        context_df = pd.DataFrame(
            [
                {
                    "move_san": f.move_san,
                    "move_uci": f.move_uci,
                    "fen": f.fen,
                    "player_color": (
                        "white" if f.player_color == 1 else "black"
                    ),  # Convertir 1/0 a string
                }
                for f in features_rows
            ]
        )

        # 3. Predecir error_labels con modelo ML (solo features numéricas)
        error_labels = []
        try:
            print(
                f"🔬 Prediciendo error_labels para {len(features_rows)} movimientos..."
            )
            error_labels = self.shap_service.predict_error_labels(features_numeric)
            print(f"✅ Error labels predichos: {len(error_labels)} predicciones")

            # Debug: mostrar distribución
            from collections import Counter

            label_counts = Counter(error_labels)
            print(f"📊 Distribución de errores predichos: {dict(label_counts)}")

        except Exception as e:
            print(f"❌ Error prediciendo error_labels: {e}")
            import traceback

            traceback.print_exc()
            # Fallback: todos "good"
            error_labels = ["good"] * len(features_rows)

        # 4. Calcular SHAP values (solo features numéricas)
        shap_values = None
        base_value = None

        try:
            print(
                f"🔬 Iniciando cálculo de SHAP values para {len(features_rows)} movimientos..."
            )
            shap_values, base_value = self.shap_service.calculate_shap_values(
                features_numeric  # ← Solo features numéricas, sin contexto
            )
            print(f"✅ SHAP values calculados exitosamente: shape={shap_values.shape}")
        except Exception as e:
            print(f"❌ Error crítico calculando SHAP: {e}")
            print(f"📋 Stack trace:")
            import traceback

            traceback.print_exc()
            print(
                f"⚠️  Continuando análisis SIN valores SHAP (dashboard tendrá datos limitados)"
            )
            # Fallback: análisis sin SHAP
            shap_values = None

        # 5. Generar métricas de análisis (usando error_labels predichos)
        error_counts = self._count_predicted_errors(error_labels)
        error_level = self._classify_error_level(error_counts, len(features_rows))
        confidence = (
            self._calculate_confidence(shap_values) if shap_values is not None else None
        )

        # 6. Persistir en analysis_results
        analysis_result = AnalysisResult(
            game_id=game_id,
            username=username,
            error_level=error_level,
            prediction_confidence=confidence,
            total_moves=len(features_rows),
            blunder_count=error_counts.get("blunder", 0),
            mistake_count=error_counts.get("mistake", 0),
            inaccuracy_count=error_counts.get("inaccuracy", 0),
            good_move_count=error_counts.get("good_move", 0),
            average_centipawn_loss=self._calculate_avg_centipawn_loss(features_rows),
            accuracy_percentage=self._calculate_accuracy_percentage(
                error_counts, len(features_rows)
            ),
        )

        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)

        print(f"✅ Análisis persistido: analysis_id={analysis_result.id}")

        # 7. Persistir SHAP values por jugada (si existen)
        if shap_values is not None:
            try:
                print(f"💾 Persistiendo SHAP values en move_shap_values...")
                print(f"   - features_numeric shape: {features_numeric.shape}")
                print(
                    f"   - features_numeric columns: {features_numeric.columns.tolist()}"
                )
                print(f"   - context_df shape: {context_df.shape}")
                print(f"   - shap_values shape: {shap_values.shape}")

                self._persist_move_shap_values(
                    db,
                    analysis_result.id,
                    shap_values,
                    features_numeric.columns.tolist(),
                    features_numeric,
                    context_df,  # ← Agregar contexto separado
                    error_labels,  # Pasar error_labels predichos
                )
            except Exception as e:
                print(f"❌ Error persistiendo SHAP values: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(
                f"⏭️  SHAP values no disponibles - saltando persistencia en move_shap_values"
            )

        # 8. Actualizar agregados de jugador
        if shap_values is not None:
            try:
                print(f"📊 Actualizando player_feature_importance para {username}...")
                self._update_player_feature_importance(
                    db, username, shap_values, features_numeric.columns.tolist()
                )
            except Exception as e:
                print(f"❌ Error actualizando feature importance: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(
                f"⏭️  SHAP values no disponibles - saltando actualización de player_feature_importance"
            )

        return analysis_result.id

    def get_error_distribution(
        self, db: Session, username: str, days: int = 30
    ) -> Dict[str, int]:
        """
        Obtener distribución de errores del usuario (últimos N días).

        Returns:
            Dict con {blunder, mistake, inaccuracy, good}
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        results = (
            db.query(AnalysisResult)
            .filter(
                and_(
                    AnalysisResult.username == username,
                    AnalysisResult.analyzed_at >= cutoff_date,
                )
            )
            .all()
        )

        if not results:
            return {"blunder": 0, "mistake": 0, "inaccuracy": 0, "good": 0}

        # Agregar conteos
        total_blunders = sum(r.blunder_count or 0 for r in results)
        total_mistakes = sum(r.mistake_count or 0 for r in results)
        total_inaccuracies = sum(r.inaccuracy_count or 0 for r in results)
        total_good = sum(r.good_move_count or 0 for r in results)

        return {
            "blunder": total_blunders,
            "mistake": total_mistakes,
            "inaccuracy": total_inaccuracies,
            "good": total_good,
        }

    def get_error_temporal_trend(
        self, db: Session, username: str, days: int = 90, interval_days: int = 7
    ) -> List[Dict]:
        """
        Obtener evolución temporal de errores (agrupado por semanas).

        Returns:
            Lista de {date, blunder_rate, mistake_rate, inaccuracy_rate, accuracy}
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        results = (
            db.query(AnalysisResult)
            .filter(
                and_(
                    AnalysisResult.username == username,
                    AnalysisResult.analyzed_at >= cutoff_date,
                )
            )
            .order_by(AnalysisResult.analyzed_at)
            .all()
        )

        if not results:
            return []

        # Agrupar por intervalos de fecha
        trends = []
        current_interval_start = cutoff_date

        while current_interval_start <= datetime.now():
            interval_end = current_interval_start + timedelta(days=interval_days)

            interval_results = [
                r
                for r in results
                if current_interval_start <= r.analyzed_at < interval_end
            ]

            if interval_results:
                total_moves = sum(r.total_moves or 0 for r in interval_results)
                total_blunders = sum(r.blunder_count or 0 for r in interval_results)
                total_mistakes = sum(r.mistake_count or 0 for r in interval_results)
                total_inaccuracies = sum(
                    r.inaccuracy_count or 0 for r in interval_results
                )

                if total_moves > 0:
                    trends.append(
                        {
                            "date": current_interval_start.strftime("%Y-%m-%d"),
                            "blunder_rate": round(
                                (total_blunders / total_moves) * 100, 2
                            ),
                            "mistake_rate": round(
                                (total_mistakes / total_moves) * 100, 2
                            ),
                            "inaccuracy_rate": round(
                                (total_inaccuracies / total_moves) * 100, 2
                            ),
                            "accuracy": round(
                                (
                                    1
                                    - (
                                        total_blunders
                                        + total_mistakes
                                        + total_inaccuracies
                                    )
                                    / total_moves
                                )
                                * 100,
                                2,
                            ),
                        }
                    )

            current_interval_start = interval_end

        return trends

    def get_global_feature_importance(
        self, db: Session, username: str, top_k: int = 10
    ) -> List[Dict]:
        """
        Obtener top features más importantes para el usuario (SHAP agregado).

        Returns:
            Lista de {feature_name, mean_abs_shap_value, total_samples}
        """
        feature_importance = (
            db.query(PlayerFeatureImportance)
            .filter(PlayerFeatureImportance.username == username)
            .all()
        )

        if not feature_importance:
            return []

        # Convertir a lista de dicts
        importance_list = [
            {
                "feature_name": fi.feature_name,
                "mean_abs_shap_value": fi.mean_abs_shap_value,
                "mean_shap_value": fi.mean_shap_value,
                "total_samples": fi.total_samples,
            }
            for fi in feature_importance
        ]

        # Ordenar por magnitud absoluta
        importance_list.sort(key=lambda x: x["mean_abs_shap_value"], reverse=True)

        return importance_list[:top_k]

    def get_move_shap_explanation(
        self, db: Session, game_id: str, move_number: int
    ) -> Dict:
        """
        Obtener explicación SHAP para una jugada específica.

        Returns:
            Dict con {move_number, error_level, top_features: [...]}
        """
        # Obtener analysis_result para esta partida
        analysis = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.game_id == game_id)
            .order_by(desc(AnalysisResult.analyzed_at))
            .first()
        )

        if not analysis:
            raise ValueError(f"No se encontró análisis para game_id={game_id}")

        # Obtener SHAP values de esta jugada
        shap_values = (
            db.query(MoveShapValue)
            .filter(
                and_(
                    MoveShapValue.analysis_id == analysis.id,
                    MoveShapValue.move_number == move_number,
                )
            )
            .all()
        )

        if not shap_values:
            return {
                "move_number": move_number,
                "error_level": "unknown",
                "top_features": [],
            }

        # Ordenar por magnitud absoluta
        shap_values.sort(key=lambda x: abs(x.shap_value), reverse=True)

        # Top 3-5 features
        top_features = [
            {
                "feature": sv.feature_name,
                "impact": sv.shap_value,
                "value": sv.feature_value,
            }
            for sv in shap_values[:5]
        ]

        # Obtener error_label de la feature original
        feature = (
            db.query(Features)
            .filter(
                and_(Features.game_id == game_id, Features.move_number == move_number)
            )
            .first()
        )

        error_level = (
            feature.error_label if feature and feature.error_label else "unknown"
        )

        return {
            "move_number": move_number,
            "error_level": error_level,
            "top_features": top_features,
        }

    # ========================
    # Helper Methods (Private)
    # ========================

    def _count_errors(self, features_rows: List[Features]) -> Dict[str, int]:
        """Contar errores por tipo (desde features.error_label - deprecated)"""
        counts = {"blunder": 0, "mistake": 0, "inaccuracy": 0, "good_move": 0}

        for f in features_rows:
            label = f.error_label or "good_move"
            if label in counts:
                counts[label] += 1
            else:
                counts["good_move"] += 1  # Default

        return counts

    def _count_predicted_errors(self, error_labels: List[str]) -> Dict[str, int]:
        """Contar errores por tipo desde predicciones ML"""
        counts = {"blunder": 0, "mistake": 0, "inaccuracy": 0, "good_move": 0}

        for label in error_labels:
            # Normalizar variaciones
            if label in ["good", "excellent", "book"]:
                counts["good_move"] += 1
            elif label in counts:
                counts[label] += 1
            else:
                counts["good_move"] += 1  # Default

        return counts

    def _classify_error_level(self, error_counts: Dict, total_moves: int) -> str:
        """Clasificar nivel global de error basado en distribución"""
        if total_moves == 0:
            return "unknown"

        blunder_rate = error_counts.get("blunder", 0) / total_moves
        mistake_rate = error_counts.get("mistake", 0) / total_moves

        if blunder_rate > 0.15:
            return "blunder_prone"
        elif mistake_rate > 0.25:
            return "mistake_prone"
        elif (blunder_rate + mistake_rate) < 0.10:
            return "excellent"
        else:
            return "accurate"

    def _calculate_confidence(self, shap_values: np.ndarray) -> float:
        """Calcular confianza basada en consistencia de SHAP values"""
        # Usar desviación estándar de SHAP como proxy de confianza
        # Menor std = mayor confianza
        std_shap = float(np.std(shap_values))  # Convertir a Python native float
        confidence = max(0.0, min(1.0, 1.0 - std_shap))
        return float(confidence)  # Asegurar tipo nativo

    def _calculate_avg_centipawn_loss(self, features_rows: List[Features]) -> float:
        """Calcular pérdida promedio en centipawns"""
        score_diffs = [
            abs(f.score_diff or 0) for f in features_rows if f.score_diff is not None
        ]
        return sum(score_diffs) / len(score_diffs) if score_diffs else 0.0

    def _calculate_accuracy_percentage(
        self, error_counts: Dict, total_moves: int
    ) -> float:
        """Calcular porcentaje de precisión"""
        if total_moves == 0:
            return 0.0

        errors = (
            error_counts.get("blunder", 0)
            + error_counts.get("mistake", 0)
            + error_counts.get("inaccuracy", 0)
        )
        accuracy = ((total_moves - errors) / total_moves) * 100
        return round(accuracy, 2)

    def _persist_move_shap_values(
        self,
        db: Session,
        analysis_id: int,
        shap_values: np.ndarray,
        feature_names: List[str],
        features_numeric: pd.DataFrame,  # ← Solo features numéricas
        context_df: pd.DataFrame,  # ← Contexto separado (move_san, move_uci, fen, player_color)
        error_labels: List[str],
    ):
        """Persistir SHAP values por jugada en move_shap_values (con error_label y contexto)"""
        move_shap_records = []

        for move_idx, shap_row in enumerate(shap_values):
            error_label = (
                error_labels[move_idx] if move_idx < len(error_labels) else "good"
            )

            # Extraer contexto del movimiento desde DataFrame separado
            move_san = context_df.iloc[move_idx]["move_san"]
            move_uci = context_df.iloc[move_idx]["move_uci"]
            fen = context_df.iloc[move_idx]["fen"]
            player_color = context_df.iloc[move_idx]["player_color"]

            for feat_idx, shap_val in enumerate(shap_row):
                feature_name = feature_names[feat_idx]
                feature_value = features_numeric.iloc[move_idx, feat_idx]

                # Manejar valores None/NaN (usar 0.0 como default)
                if feature_value is None or pd.isna(feature_value):
                    feature_value = 0.0
                else:
                    feature_value = float(feature_value)

                move_shap_records.append(
                    MoveShapValue(
                        analysis_id=analysis_id,
                        move_number=move_idx + 1,  # 1-indexed
                        feature_name=feature_name,
                        shap_value=float(shap_val),
                        feature_value=feature_value,
                        error_label=error_label,  # Predicción ML
                        move_san=move_san,  # Notación del movimiento
                        move_uci=move_uci,  # UCI notation
                        fen=fen,  # Posición FEN
                        player_color=player_color,  # Color del jugador ('white'/'black')
                    )
                )

        db.bulk_save_objects(move_shap_records)
        db.commit()
        print(
            f"✅ {len(move_shap_records)} SHAP values persistidos (con error_label y contexto)"
        )

    def _update_player_feature_importance(
        self,
        db: Session,
        username: str,
        shap_values: np.ndarray,
        feature_names: List[str],
    ):
        """Actualizar agregados de feature importance para el jugador"""
        aggregated = self.shap_service.aggregate_shap_by_player(
            shap_values, feature_names
        )

        period_end = date.today()
        period_start = period_end - timedelta(days=30)  # Ventana de 30 días

        for feature_name, stats in aggregated.items():
            # Buscar registro existente
            existing = (
                db.query(PlayerFeatureImportance)
                .filter(
                    and_(
                        PlayerFeatureImportance.username == username,
                        PlayerFeatureImportance.feature_name == feature_name,
                        PlayerFeatureImportance.period_start == period_start,
                        PlayerFeatureImportance.period_end == period_end,
                    )
                )
                .first()
            )

            if existing:
                # Actualizar con promedio ponderado
                total_samples_new = existing.total_samples + stats["total_samples"]
                weight_old = existing.total_samples / total_samples_new
                weight_new = stats["total_samples"] / total_samples_new

                existing.mean_shap_value = (
                    existing.mean_shap_value * weight_old
                    + stats["mean_shap_value"] * weight_new
                )
                existing.mean_abs_shap_value = (
                    existing.mean_abs_shap_value * weight_old
                    + stats["mean_abs_shap_value"] * weight_new
                )
                existing.total_samples = total_samples_new
                existing.updated_at = datetime.now()
            else:
                # Crear nuevo registro
                new_importance = PlayerFeatureImportance(
                    username=username,
                    feature_name=feature_name,
                    mean_shap_value=stats["mean_shap_value"],
                    mean_abs_shap_value=stats["mean_abs_shap_value"],
                    total_samples=stats["total_samples"],
                    period_start=period_start,
                    period_end=period_end,
                )
                db.add(new_importance)

        db.commit()
        print(f"✅ Feature importance actualizado para {username}")
