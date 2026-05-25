"""
LLM Analysis Service - Arquitectura Doble Paso (JSON → Narrativa)
Genera feedback pedagógico adaptado al ELO usando análisis estructurado verificable
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.services.analysis_service import AnalysisService
from api.services.prompt_validator import PromptValidator, PromptValidationError
from api.services.json_validator import (
    StructuredAnalysisValidator,
    JSONValidationError,
)
from db.models.analysis_results import AnalysisResult
from db.models.move_shap_values import MoveShapValue
from db.models.games import Games
from db.models.features import Features


class LLMAnalysisService:
    """
    Servicio para generar análisis pedagógico usando LLM

    Fase 1: Prompt hardcodeado con adaptación básica por ELO
    """

    def __init__(self):
        """Inicializa el cliente de OpenAI"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY no encontrada en variables de entorno. "
                "Por favor configura tu API key en el archivo .env"
            )

        self.client = AsyncOpenAI(api_key=api_key)
        self.analysis_service = AnalysisService()

    def _get_shap_summary(self, db: Session, analysis_id: int) -> Dict:
        """
        Obtiene resumen SHAP del análisis desde la base de datos

        Args:
            db: Sesión de base de datos
            analysis_id: ID del análisis

        Returns:
            Dict con resumen del análisis y top features SHAP
        """
        # Obtener análisis
        analysis = (
            db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        )

        if not analysis:
            raise ValueError(f"Análisis con ID {analysis_id} no encontrado")

        # Obtener valores SHAP para este análisis
        shap_values = (
            db.query(MoveShapValue)
            .filter(MoveShapValue.analysis_id == analysis_id)
            .all()
        )

        # Calcular feature importance agregada (suma absoluta de SHAP values)
        feature_importance = {}
        for sv in shap_values:
            if sv.feature_name not in feature_importance:
                feature_importance[sv.feature_name] = 0.0
            feature_importance[sv.feature_name] += abs(sv.shap_value)

        # Top 5 features más importantes
        top_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Construir resumen
        summary = {
            "analysis_id": analysis_id,
            "game_id": analysis.game_id,
            "total_moves": analysis.total_moves or 0,
            "error_level": analysis.error_level,
            "blunder_count": analysis.blunder_count or 0,
            "mistake_count": analysis.mistake_count or 0,
            "inaccuracy_count": analysis.inaccuracy_count or 0,
            "good_move_count": analysis.good_move_count or 0,
            "average_centipawn_loss": analysis.average_centipawn_loss or 0.0,
            "top_features": [
                {"feature": name, "importance": importance}
                for name, importance in top_features
            ],
        }

        return summary

    def _get_top_error_moves(
        self, db: Session, analysis_id: int, top_n: int = 8
    ) -> List[Dict]:
        """
        Obtiene los movimientos con errores más críticos, con sus SHAP values específicos

        Implementa Sección 5.2 del roadmap: evidence pack move-by-move

        Args:
            db: Sesión de base de datos
            analysis_id: ID del análisis
            top_n: Número máximo de movimientos a retornar

        Returns:
            Lista de movimientos con error, ordenados por severidad
            Cada movimiento incluye:
            - move_number: Número del movimiento
            - error_label: blunder/mistake/inaccuracy
            - top_shap_features: Top 3-5 features que explican esta jugada
            - shap_impact: Impacto total SHAP para este move
        """
        # Query movimientos con error (excluye 'good')
        shap_moves = (
            db.query(MoveShapValue)
            .filter(
                MoveShapValue.analysis_id == analysis_id,
                MoveShapValue.error_label.in_(["blunder", "mistake", "inaccuracy"]),
            )
            .all()
        )

        if not shap_moves:
            return []

        # Agrupar por move_number para calcular SHAP total e identificar top features
        moves_dict = {}
        for sv in shap_moves:
            move_num = sv.move_number
            if move_num not in moves_dict:
                moves_dict[move_num] = {
                    "move_number": move_num,
                    "error_label": sv.error_label,
                    "features": [],
                }

            # Agregar feature con su SHAP value
            moves_dict[move_num]["features"].append(
                {"feature": sv.feature_name, "shap_value": abs(sv.shap_value)}
            )

        # Procesar cada movimiento
        error_moves = []
        for move_data in moves_dict.values():
            # Ordenar features por impacto SHAP (absoluto)
            sorted_features = sorted(
                move_data["features"], key=lambda x: x["shap_value"], reverse=True
            )

            # Top 3 features más influyentes para este movimiento
            top_features = sorted_features[:3]

            # Calcular impacto total SHAP para este movimiento
            total_shap_impact = sum(f["shap_value"] for f in sorted_features)

            # Ponderación de severidad para ordenamiento
            severity_weight = {"blunder": 3.0, "mistake": 2.0, "inaccuracy": 1.0}

            # Calcular número de movimiento en notación estándar de ajedrez
            # move_number es secuencial (1, 2, 3... para cada jugada individual)
            # Convertir a notación estándar (1. e4, 1... d6, 2. d4, etc.)
            chess_move_number = (move_data["move_number"] + 1) // 2

            error_moves.append(
                {
                    "move_number": move_data["move_number"],
                    "chess_move_number": chess_move_number,
                    "error_label": move_data["error_label"],
                    "top_shap_features": top_features,
                    "shap_impact": round(total_shap_impact, 3),
                    "severity_score": total_shap_impact
                    * severity_weight.get(move_data["error_label"], 1.0),
                }
            )

        # Ordenar por severity_score (severidad * impacto SHAP)
        error_moves_sorted = sorted(
            error_moves, key=lambda x: x["severity_score"], reverse=True
        )

        # Retornar top N movimientos más críticos
        return error_moves_sorted[:top_n]

    def _get_competitive_context(
        self, db: Session, game_id: str, player_color: str, analysis_id: int
    ) -> Dict:
        """
        Obtiene contexto competitivo enriquecido: resultado, comparación vs oponente,
        momento crítico, swing evaluativo, pérdida material, conversión, y distribución por fase

        Implementa mejoras del documento ChessTrainer_Competitive_Context_Layer.md

        Args:
            db: Sesión de base de datos
            game_id: ID de la partida
            player_color: Color del jugador ("white" o "black")
            analysis_id: ID del análisis del jugador

        Returns:
            Dict con contexto competitivo diferencial enriquecido
        """
        # Obtener datos de la partida
        game = db.query(Games).filter(Games.game_id == game_id).first()

        if not game:
            return {}

        # Determinar resultado desde perspectiva del jugador
        result = game.result  # "1-0", "0-1", "1/2-1/2"
        player_result = "draw"
        if result == "1-0":  # Ganan blancas
            player_result = "win" if player_color == "white" else "loss"
        elif result == "0-1":  # Ganan negras
            player_result = "loss" if player_color == "white" else "win"

        # Obtener análisis del jugador
        player_analysis = (
            db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        )

        # Calcular error ratio del jugador
        player_total_moves = player_analysis.total_moves or 1
        player_errors = (
            (player_analysis.blunder_count or 0)
            + (player_analysis.mistake_count or 0)
            + (player_analysis.inaccuracy_count or 0)
        )
        player_error_ratio = player_errors / player_total_moves

        # Intentar obtener análisis del oponente (color opuesto)
        opponent_color_int = 0 if player_color == "white" else 1
        opponent_analysis = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.game_id == game_id)
            .join(
                MoveShapValue,
                MoveShapValue.analysis_id == AnalysisResult.id,
            )
            .first()
        )

        # Si no hay análisis del oponente, usar estimación básica
        opponent_error_ratio = 0.2  # Default
        if opponent_analysis and opponent_analysis.id != analysis_id:
            opp_total = opponent_analysis.total_moves or 1
            opp_errors = (
                (opponent_analysis.blunder_count or 0)
                + (opponent_analysis.mistake_count or 0)
                + (opponent_analysis.inaccuracy_count or 0)
            )
            opponent_error_ratio = opp_errors / opp_total

        # ============================================================
        # ARQUITECTURA V3: Precálculo del Engine Analysis
        # ============================================================
        player_color_int = 0 if player_color == "white" else 1
        features_player = (
            db.query(Features)
            .filter(
                Features.game_id == game_id, Features.player_color == player_color_int
            )
            .order_by(Features.move_number)
            .all()
        )

        # Calcular top_swings (V3: precalculado por engine, no por LLM)
        # IMPORTANTE: Excluir primeras movidas (apertura temprana) y requerir errores etiquetados
        top_swings = []
        all_swings = []  # Para fallback si no hay swings >= 50 cp
        
        if (
            len(features_player) > 5
        ):  # Al menos 5 movidas para tener datos significativos
            for i in range(1, len(features_player)):
                feature = features_player[i]
                prev_score = features_player[i - 1].score_diff or 0
                curr_score = feature.score_diff or 0
                delta_cp = int((curr_score - prev_score) * 100)  # centipawns

                # Excluir primeras 3 movidas (apertura temprana, no puede ser decisiva)
                chess_move_num = (feature.move_number + 1) // 2
                if chess_move_num <= 3:
                    continue

                # Priorizar swings etiquetados como errores
                is_error = feature.error_label in ["blunder", "mistake", "inaccuracy"]

                swing_data = {
                    "move": feature.move_number,
                    "chess_notation_move": chess_move_num,
                    "delta_cp": delta_cp,
                    "from_cp": int(prev_score * 100),
                    "to_cp": int(curr_score * 100),
                    "phase": feature.phase or "middlegame",
                    "error_label": feature.error_label or "none",
                    "is_error": is_error,
                }

                # Guardar todos los swings para fallback
                all_swings.append(swing_data)

                # Solo considerar swings significativos (al menos 50 cp de cambio) para top_swings
                if abs(delta_cp) >= 50:
                    top_swings.append(swing_data)

        # Si NO hay swings >= 50 cp, usar el mayor swing disponible (sin umbral)
        if not top_swings and all_swings:
            print(f"⚠️ No hay swings >= 50 cp, usando fallback: mayor swing disponible")
            # Ordenar por magnitud y tomar el mayor
            all_swings.sort(key=lambda x: -abs(x["delta_cp"]))
            top_swings = all_swings[:5]  # Top 5 swings sin umbral

        # Ordenar por magnitud de swing (mayor impacto primero)
        # Priorizar errores etiquetados sobre swings no etiquetados
        top_swings.sort(key=lambda x: (not x["is_error"], -abs(x["delta_cp"])))
        top_swings = top_swings[:5]  # Solo top 5 swings

        # Engine decisive move (el de mayor swing)
        decisive_move = None
        decisive_move_chess = None
        decisive_swing = 0.0
        decisive_phase = None
        max_single_error_impact = 0.0

        if top_swings:
            decisive_move = top_swings[0]["move"]
            decisive_move_chess = top_swings[0]["chess_notation_move"]
            decisive_swing = abs(top_swings[0]["delta_cp"]) / 100.0
            decisive_phase = top_swings[0]["phase"]

            # Calcular máximo impacto de error individual
            for swing in top_swings:
                if swing["error_label"] in ["blunder", "mistake"]:
                    max_single_error_impact = max(
                        max_single_error_impact, abs(swing["delta_cp"]) / 100.0
                    )

        # ============================================================
        # MEJORA 2: Tipo de pérdida (single_blunder vs accumulated_errors)
        # ============================================================
        loss_type = None
        if player_result == "loss":
            # Si hay un error con swing > 2.0, es single_blunder
            if max_single_error_impact > 2.0:
                loss_type = "single_blunder"
            else:
                loss_type = "accumulated_errors"

        # ============================================================
        # V6.3: Material events FIX - Calcular balance real desde PGN
        # ============================================================
        material_events = []
        first_material_loss_move = None

        print("\n🔍 Calculando material_events desde PGN (V6.3)...")
        
        # Obtener TODOS los features del juego (ambos jugadores)
        all_features = (
            db.query(Features)
            .filter(Features.game_id == game_id)
            .order_by(Features.move_number)
            .all()
        )
        
        i = 0
        while i < len(all_features) - 1:
            current = all_features[i]
            next_move = all_features[i + 1]
            
            # Calcular cambio de balance DESPUÉS de este move
            current_balance = current.material_balance or 0
            next_balance = next_move.material_balance or 0
            balance_change = next_balance - current_balance
            
            # Convertir a perspectiva del jugador (blancas: + es bueno, negras: - es bueno)
            if player_color == "white":
                player_change = balance_change
            else:
                player_change = -balance_change  # Invertir para negras
            
            # ¿Este move tiene captura?
            has_capture = 'x' in current.move_san
            is_player_move = current.player_color == player_color_int
            
            # CASO 1: Secuencia de intercambio (captura + recaptura)
            if has_capture and i + 1 < len(all_features) and 'x' in next_move.move_san:
                # Hay intercambio: move i captura, move i+1 recaptura
                # Calcular balance neto del intercambio completo
                balance_before = current_balance
                balance_after_trade = all_features[i + 2].material_balance if i + 2 < len(all_features) else next_balance
                
                # Balance neto desde perspectiva del jugador
                if player_color == "white":
                    net_change = balance_after_trade - balance_before
                else:
                    net_change = -(balance_after_trade - balance_before)
                
                # ¿Quién inició el intercambio?
                initiator_is_player = is_player_move
                
                # Si el jugador inició y perdió material neto → mal intercambio
                if initiator_is_player and net_change < -2.0:
                    chess_move = (current.move_number + 1) // 2
                    print(f"   Intercambio desfavorable: Move #{chess_move} ({current.move_san}), pérdida neta={abs(net_change):.1f}")
                    material_events.append({
                        "move": current.move_number,
                        "chess_notation_move": chess_move,
                        "type": "bad_trade",
                        "value_lost": abs(net_change),
                        "phase": current.phase or "middlegame",
                    })
                    
                    if first_material_loss_move is None:
                        first_material_loss_move = chess_move
                
                # Si el oponente inició y el jugador respondió perdiendo → pérdida en recaptura
                elif not initiator_is_player and net_change < -2.0:
                    # El jugador recapturó pero perdió material neto
                    chess_move = (next_move.move_number + 1) // 2
                    print(f"   Recaptura desfavorable: Move #{chess_move} ({next_move.move_san}), pérdida neta={abs(net_change):.1f}")
                    material_events.append({
                        "move": next_move.move_number,
                        "chess_notation_move": chess_move,
                        "type": "bad_recapture",
                        "value_lost": abs(net_change),
                        "phase": next_move.phase or "middlegame",
                    })
                    
                    if first_material_loss_move is None:
                        first_material_loss_move = chess_move
                
                # Saltar el intercambio completo (ya procesado)
                i += 2
                continue
            
            # CASO 2: Captura simple (sin recaptura inmediata)
            elif has_capture:
                # Captura sin respuesta inmediata
                # Si es del oponente y empeoró mi balance → me capturaron
                if not is_player_move and player_change < -2.0:
                    chess_move = (current.move_number + 1) // 2
                    print(f"   Captura del oponente: Move #{chess_move} ({current.move_san}), pérdida={abs(player_change):.1f}")
                    material_events.append({
                        "move": current.move_number,
                        "chess_notation_move": chess_move,
                        "type": "piece_captured",
                        "value_lost": abs(player_change),
                        "phase": current.phase or "middlegame",
                    })
                    
                    if first_material_loss_move is None:
                        first_material_loss_move = chess_move
            
            # CASO 3: Pérdida sin captura (pieza dejada hanging)
            elif not has_capture and player_change < -2.0:
                # Material perdido sin que haya captura visible en este move
                # Podría ser que el move anterior del oponente capturó
                if i > 0 and 'x' in all_features[i - 1].move_san:
                    # El oponente capturó en el move anterior
                    prev_move = all_features[i - 1]
                    chess_move = (prev_move.move_number + 1) // 2
                    
                    # Verificar que no fue ya reportado
                    already_reported = any(e["chess_notation_move"] == chess_move for e in material_events)
                    
                    if not already_reported:
                        print(f"   Pieza perdida (captura detectada retroactivamente): Move #{chess_move} ({prev_move.move_san}), pérdida={abs(player_change):.1f}")
                        material_events.append({
                            "move": prev_move.move_number,
                            "chess_notation_move": chess_move,
                            "type": "piece_hanging",
                            "value_lost": abs(player_change),
                            "phase": prev_move.phase or "middlegame",
                        })
                        
                        if first_material_loss_move is None:
                            first_material_loss_move = chess_move
            
            i += 1
        
        if not material_events:
            print(f"   ✅ No se detectaron pérdidas significativas de material")
        else:
            print(f"   ⚠️ Total material_events: {len(material_events)}")
            for event in material_events:
                print(f"      - Move #{event['chess_notation_move']}: {event['type']} (-{event['value_lost']:.1f} puntos)")

        # ============================================================
        # PRIORIDAD MATERIAL: Si el decisive_move tiene swing insignificante pero hay material_events,
        # usar el primer material_event como decisivo (más pedagógico)
        # ============================================================
        if material_events and decisive_swing < 0.5:  # Si swing < 50 cp (insignificante)
            print(f"⚠️ Decisive move actual tiene swing insignificante ({decisive_swing:.2f}), pero hay pérdida material")
            print(f"   Reemplazando decisive_move con primer material_event...")
            
            first_material = material_events[0]
            decisive_move = first_material["move"]
            decisive_move_chess = first_material["chess_notation_move"]
            decisive_phase = first_material["phase"]
            decisive_swing = first_material["value_lost"]  # Usar valor material como "swing"
            
            print(f"✅ Nuevo decisive_move: #{decisive_move_chess} (pérdida material: {decisive_swing:.1f} puntos)")

        # ============================================================
        # MEJORA 4: Calidad de conversión (solo para ganadores)
        # ============================================================
        conversion_quality = None
        if player_result == "win" and len(features_player) > 5:
            # Detectar primera ventaja significativa (score_diff > 1.5)
            advantage_established = None
            max_advantage = 0
            min_after_advantage = float("inf")

            for f in features_player:
                score = f.score_diff or 0
                if score > 1.5 and advantage_established is None:
                    advantage_established = f.move_number
                    max_advantage = score
                elif advantage_established is not None:
                    max_advantage = max(max_advantage, score)
                    min_after_advantage = min(min_after_advantage, score)

            # Evaluar calidad de conversión
            if advantage_established is not None and min_after_advantage != float(
                "inf"
            ):
                advantage_drop = max_advantage - min_after_advantage
                if advantage_drop < 0.5:
                    conversion_quality = "clean"
                elif advantage_drop < 1.0:
                    conversion_quality = "stable"
                else:
                    conversion_quality = "unstable"

        # ============================================================
        # MEJORA 5: Distribución de errores por fase
        # ============================================================
        phase_error_distribution = {"opening": 0, "middlegame": 0, "endgame": 0}

        for f in features_player:
            if f.error_label in ["blunder", "mistake", "inaccuracy"]:
                phase_key = f.phase or "middlegame"
                if phase_key in phase_error_distribution:
                    phase_error_distribution[phase_key] += 1

        # ============================================================
        # Momento crítico alternativo (si no hay swing evaluativo, usar material o SHAP)
        # ============================================================
        if decisive_move is None:
            # FALLBACK 1: Si hay material_events, usar el primero
            if material_events:
                print(f"⚠️ No hay swings, usando FALLBACK MATERIAL: pérdida de {material_events[0]['value_lost']:.1f} puntos")
                first_material = material_events[0]
                decisive_move = first_material["move"]
                decisive_move_chess = first_material["chess_notation_move"]
                decisive_phase = first_material["phase"]
                decisive_swing = first_material["value_lost"]
                print(f"✅ Decisive move (material): #{decisive_move_chess}")
            
            # FALLBACK 2: Si no hay material, usar SHAP
            else:
                print(f"⚠️ No hay decisive_move de swings ni material, usando fallback SHAP...")
                shap_moves = (
                    db.query(MoveShapValue)
                    .filter(MoveShapValue.analysis_id == analysis_id)
                    .all()
                )

                max_impact = 0
                for sv in shap_moves:
                    if abs(sv.shap_value) > max_impact and sv.error_label in [
                        "blunder",
                        "mistake",
                    ]:
                        max_impact = abs(sv.shap_value)
                        decisive_move = sv.move_number
                        decisive_move_chess = (sv.move_number + 1) // 2  # Convertir a notación de ajedrez
                        decisive_swing = abs(sv.shap_value)
                        # Buscar fase del move en features
                        for f in features_player:
                            if f.move_number == sv.move_number:
                                decisive_phase = f.phase or "middlegame"
                                break
                
                if decisive_move is not None:
                    print(f"✅ SHAP fallback: jugada decisiva #{decisive_move_chess} (SHAP impact: {max_impact:.2f})")
        
        # ============================================================
        # FALLBACK ABSOLUTO: Si ni swings, ni material, ni SHAP encontraron nada, usar movimiento del medio
        # ============================================================
        if decisive_move is None and len(features_player) > 5:
            print(f"⚠️ FALLBACK ABSOLUTO: No se encontró jugada decisiva, usando movimiento del medio de la partida")
            mid_index = len(features_player) // 2
            decisive_move = features_player[mid_index].move_number
            decisive_move_chess = (decisive_move + 1) // 2
            decisive_phase = features_player[mid_index].phase or "middlegame"
            decisive_swing = 0.0  # No hay swing calculado
            print(f"   Usando jugada #{decisive_move_chess} como decisiva (movimiento {mid_index}/{len(features_player)})")

        # ============================================================
        # MEJORA V2: Material delta en el momento decisivo
        # ============================================================
        material_delta_at_decisive_move = 0.0
        if decisive_move is not None:
            # Buscar el feature correspondiente al decisive_move
            decisive_feature = next(
                (f for f in features_player if f.move_number == decisive_move), None
            )
            if decisive_feature and decisive_feature.material_balance is not None:
                material_delta_at_decisive_move = decisive_feature.material_balance

        # ============================================================
        # V3: Engine Analysis (datos estructurados precalculados)
        # ============================================================
        engine_analysis = {
            "top_swings": top_swings,
            "engine_decisive_move": decisive_move,
            "engine_decisive_move_chess": decisive_move_chess,
            "engine_max_swing_cp": int(decisive_swing * 100) if decisive_swing else 0,
            "material_events": material_events,
            "error_distribution": phase_error_distribution,
        }

        # Construir contexto enriquecido
        context = {
            # Datos básicos
            "result": player_result,
            "player_color": player_color,  # V5: Agregar player_color
            "player_error_ratio": round(player_error_ratio, 2),
            "opponent_error_ratio": round(opponent_error_ratio, 2),
            "error_ratio_delta": round(player_error_ratio - opponent_error_ratio, 2),
            # V3: Engine analysis precalculado
            "engine_analysis": engine_analysis,
            # Momento decisivo
            "critical_move": decisive_move_chess,
            "decisive_phase": decisive_phase or "middlegame",
            # MEJORAS del documento v1
            "decisive_swing": round(decisive_swing, 2),
            "loss_type": loss_type,
            "first_material_loss_move": first_material_loss_move,
            "conversion_quality": conversion_quality,
            "phase_error_distribution": phase_error_distribution,
            # MEJORA V2: Material delta
            "material_delta_at_decisive_move": round(
                material_delta_at_decisive_move, 2
            ),
        }

        return context

    def _synthesize_patterns(
        self, db: Session, analysis_id: int, shap_summary: Dict
    ) -> List[Dict]:
        """
        Sintetiza patrones pedagógicos desde datos SHAP crudos

        Args:
            db: Sesión de base de datos
            analysis_id: ID del análisis
            shap_summary: Resumen SHAP con features

        Returns:
            Lista de patrones detectados con evidencia concreta
        """
        patterns = []

        # Obtener valores SHAP por movimiento para análisis detallado
        shap_moves = (
            db.query(MoveShapValue)
            .filter(MoveShapValue.analysis_id == analysis_id)
            .all()
        )

        # Organizar por movimiento
        moves_data = {}
        for sv in shap_moves:
            if sv.move_number not in moves_data:
                moves_data[sv.move_number] = {}
            moves_data[sv.move_number][sv.feature_name] = {
                "shap_value": sv.shap_value,
                "feature_value": sv.feature_value,
                "error_label": sv.error_label,
            }

        # **PATRÓN 1: Cede iniciativa (opponent_mobility alto)**
        opponent_mobility_values = [
            sv.shap_value
            for sv in shap_moves
            if sv.feature_name == "opponent_mobility" and abs(sv.shap_value) > 0.1
        ]
        if len(opponent_mobility_values) >= 3:
            avg_mobility = sum(abs(v) for v in opponent_mobility_values) / len(
                opponent_mobility_values
            )
            affected_moves = [
                sv.move_number
                for sv in shap_moves
                if sv.feature_name == "opponent_mobility" and abs(sv.shap_value) > 0.1
            ]
            patterns.append(
                {
                    "pattern": "cede_iniciativa",
                    "description": "Jugadas que permiten alta movilidad al oponente",
                    "severity": "high" if avg_mobility > 0.2 else "medium",
                    "evidence": {
                        "affected_moves": affected_moves[:5],
                        "frequency": len(opponent_mobility_values),
                        "avg_impact": round(avg_mobility, 3),
                    },
                    "recommendation": "Busca jugadas que restrinjan las opciones del rival. Pregúntate: ¿esta jugada le da libertad a mi oponente?",
                }
            )

        # **PATRÓN 2: Pérdida material (material_balance negativo)**
        material_losses = [
            (sv.move_number, sv.shap_value)
            for sv in shap_moves
            if sv.feature_name == "material_balance"
            and sv.shap_value < -0.15
            and sv.error_label in ["blunder", "mistake"]
        ]
        if material_losses:
            worst_move = min(material_losses, key=lambda x: x[1])
            # Convertir move_number secuencial a notación estándar de ajedrez
            worst_move_chess = (worst_move[0] + 1) // 2
            patterns.append(
                {
                    "pattern": "error_material",
                    "description": "Jugadas que resultan en pérdida de material",
                    "severity": "critical",
                    "evidence": {
                        "critical_move": worst_move[0],
                        "impact": round(worst_move[1], 3),
                        "total_occurrences": len(material_losses),
                    },
                    "recommendation": f"Revisa el movimiento #{worst_move_chess}. Antes de mover, verifica: ¿está mi pieza protegida? ¿puede ser capturada?",
                }
            )

        # **PATRÓN 3: Errores en apertura (move_number_global bajo + error)**
        opening_errors = [
            sv.move_number
            for sv in shap_moves
            if sv.feature_name == "move_number_global"
            and sv.feature_value < 15
            and sv.error_label in ["mistake", "inaccuracy"]
        ]
        if len(opening_errors) >= 2:
            patterns.append(
                {
                    "pattern": "perdida_tiempos_apertura",
                    "description": "Errores en la fase de apertura (primeros 15 movimientos)",
                    "severity": "medium",
                    "evidence": {
                        "affected_moves": opening_errors[:3],
                        "count": len(opening_errors),
                    },
                    "recommendation": "Enfócate en: 1) Desarrollar piezas rápidamente, 2) Controlar el centro, 3) Enrocar pronto.",
                }
            )

        # **PATRÓN 4: Juego pasivo (self_mobility bajo)**
        low_mobility = [
            sv.move_number
            for sv in shap_moves
            if sv.feature_name == "self_mobility"
            and sv.shap_value < -0.1
            and sv.error_label != "good"
        ]
        if len(low_mobility) >= 4:
            patterns.append(
                {
                    "pattern": "juego_pasivo",
                    "description": "Movimientos que reducen tus propias opciones",
                    "severity": "medium",
                    "evidence": {
                        "affected_moves": low_mobility[:5],
                        "frequency": len(low_mobility),
                    },
                    "recommendation": "Busca jugadas activas que aumenten tus opciones. Pregúntate: ¿esta jugada me da más o menos libertad?",
                }
            )

        # **PATRÓN 5: Problemas de control del centro**
        center_control_issues = [
            sv.move_number
            for sv in shap_moves
            if sv.feature_name == "is_center_controlled"
            and abs(sv.shap_value) > 0.1
            and sv.error_label in ["mistake", "inaccuracy"]
        ]
        if len(center_control_issues) >= 2:
            patterns.append(
                {
                    "pattern": "control_centro_debil",
                    "description": "Jugadas que no disputan o pierden control del centro",
                    "severity": "medium",
                    "evidence": {
                        "affected_moves": center_control_issues[:3],
                        "count": len(center_control_issues),
                    },
                    "recommendation": "El centro es clave. Intenta ocuparlo con peones (e4, d4) o controlarlo con piezas.",
                }
            )

        # Ordenar patrones por severidad
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        patterns.sort(key=lambda p: severity_order.get(p["severity"], 99))

        return patterns

    def _get_elo_context(self, elo: int) -> Dict[str, str]:
        """
        Obtiene contexto pedagógico según el ELO del jugador

        Args:
            elo: Rating ELO del jugador

        Returns:
            Dict con focus_areas y language_level
        """
        if elo < 1200:
            return {
                "focus_areas": "material, tácticas básicas, seguridad de piezas",
                "language_level": "simple y didáctico, usando analogías básicas",
                "severity": "solo errores graves (blunders y mistakes claros)",
            }
        elif elo < 1700:
            return {
                "focus_areas": "desarrollo, iniciativa, coordinación de piezas, tácticas intermedias",
                "language_level": "conceptos posicionales claros, terminología estándar",
                "severity": "errores significativos (blunders, mistakes, inaccuracies importantes)",
            }
        elif elo < 2100:
            return {
                "focus_areas": "estructura de peones, planes a medio plazo, profilaxis, juego posicional",
                "language_level": "terminología técnica precisa, análisis profundo",
                "severity": "todos los errores detectados, incluyendo imprecisiones sutiles",
            }
        else:
            return {
                "focus_areas": "optimización fina, precisión dinámica, cálculo profundo",
                "language_level": "notación algebraica completa, análisis experto",
                "severity": "perfeccionismo: incluso las imprecisiones más pequeñas son relevantes",
            }

    def _calibrate_severity_by_elo(
        self, error_label: str, player_elo: int, shap_impact: float
    ) -> Dict[str, any]:
        """
        Calibra la severidad de un error según el ELO del jugador

        Implementa Sección 4.1 del roadmap: Calibration post-modelo

        Regla general:
        - Para jugadores bajos (< 1600): Solo blunders y mistakes graves importan pedagógicamente
        - Para jugadores intermedios (1600-2000): Mistakes e inaccuracies relevantes
        - Para jugadores altos (2000+): Todas las imprecisiones son importantes

        Args:
            error_label: Etiqueta del error (blunder/mistake/inaccuracy/good)
            player_elo: Rating ELO del jugador
            shap_impact: Impacto SHAP total del movimiento

        Returns:
            Dict con severidad calibrada y tono narrativo
        """
        # Matriz de calibración por ELO
        if player_elo < 1600:
            # Novice/Intermediate: Focus en errores graves
            calibration = {
                "blunder": {
                    "pedagogical_severity": "crítico",
                    "narrative_tone": "Este error te costó la partida",
                    "priority": "alta",
                },
                "mistake": {
                    "pedagogical_severity": (
                        "serio" if shap_impact > 0.3 else "moderado"
                    ),
                    "narrative_tone": (
                        "Error importante que debes evitar"
                        if shap_impact > 0.3
                        else "Jugada imprecisa"
                    ),
                    "priority": "alta" if shap_impact > 0.3 else "media",
                },
                "inaccuracy": {
                    "pedagogical_severity": "bajo",
                    "narrative_tone": (
                        "Pequeña imprecisión, no prioritaria"
                        if shap_impact < 0.2
                        else "Jugada mejorable"
                    ),
                    "priority": "baja",
                },
            }
        elif player_elo < 2000:
            # Intermediate/Advanced: Buscar precisión
            calibration = {
                "blunder": {
                    "pedagogical_severity": "crítico",
                    "narrative_tone": "Error grave que un jugador de tu nivel debe evitar",
                    "priority": "alta",
                },
                "mistake": {
                    "pedagogical_severity": "serio",
                    "narrative_tone": "Error posicional significativo",
                    "priority": "alta",
                },
                "inaccuracy": {
                    "pedagogical_severity": "moderado",
                    "narrative_tone": "Imprecisión que afecta tu posición",
                    "priority": "media",
                },
            }
        else:
            # Advanced/Expert: Perfeccionismo
            calibration = {
                "blunder": {
                    "pedagogical_severity": "inaceptable",
                    "narrative_tone": "Error crítico en tu nivel",
                    "priority": "crítica",
                },
                "mistake": {
                    "pedagogical_severity": "grave",
                    "narrative_tone": "Error técnico que debe corregirse",
                    "priority": "alta",
                },
                "inaccuracy": {
                    "pedagogical_severity": "serio",
                    "narrative_tone": "Imprecisión relevante para tu nivel",
                    "priority": "alta",
                },
            }

        # Retornar calibración o default si el label no está
        return calibration.get(
            error_label,
            {
                "pedagogical_severity": "desconocido",
                "narrative_tone": "Requiere revisión",
                "priority": "media",
            },
        )

    def _build_structured_analysis_deterministic(
        self, competitive_context: Dict, player_elo: int
    ) -> Dict:
        """
        V4: Genera análisis estructurado (JSON) de forma 100% determinística desde backend
        
        El LLM YA NO elige hechos. Todo se calcula desde engine_analysis precalculado.
        Esto elimina 100% de alucinaciones en datos estructurales.
        
        Args:
            competitive_context: Contexto con engine_analysis precalculado
            player_elo: ELO del jugador (para calibración)
            
        Returns:
            Dict con análisis estructurado verificable
        """
        engine = competitive_context.get("engine_analysis", {})
        result = competitive_context.get("result", "unknown")
        
        # DECISIVO: Extraer del backend (NO del LLM)
        decisive_move = engine.get("engine_decisive_move_chess")
        max_swing_cp = engine.get("engine_max_swing_cp", 0)
        material_events = engine.get("material_events", [])
        error_distribution = engine.get("error_distribution", {})
        
        # ERROR_TYPE: Basado en swing (regla determinística)
        if max_swing_cp >= 250:
            error_type = "single"
        else:
            error_type = "accumulated"
        
        # MATERIAL_LOSS: SOLO true si hay material_events
        material_loss_claimed = len(material_events) > 0
        
        # PHASE_PROBLEMS: SOLO true si hay errores en esa fase
        opening_problem = error_distribution.get("opening", 0) > 0
        middlegame_problem = error_distribution.get("middlegame", 0) > 0
        endgame_problem = error_distribution.get("endgame", 0) > 0
        
        # CONFIDENCE: Calibrado por resultado y consistencia
        if result == "loss" and error_type == "single":
            confidence = 0.90  # Alta confianza: un error causó la derrota
        elif result == "loss" and error_type == "accumulated":
            confidence = 0.75  # Media: múltiples factores
        elif result == "win":
            confidence = 0.70  # Menor: la victoria enmascara errores
        else:
            confidence = 0.85  # Empate
        
        # Construir JSON estructurado (determinístico)
        structured = {
            "decisive_move_used": decisive_move,
            "error_type": error_type,
            "material_loss_claimed": material_loss_claimed,
            "opening_problem_detected": opening_problem,
            "middlegame_problem_detected": middlegame_problem,
            "endgame_problem_detected": endgame_problem,
            "confidence": confidence,
        }
        
        print(f"\n🔧 V4 - JSON ESTRUCTURADO (100% DETERMINÍSTICO):")
        print(f"   decisive_move_used: {decisive_move}")
        print(f"   error_type: {error_type} (swing: {max_swing_cp} cp)")
        print(f"   material_loss_claimed: {material_loss_claimed} ({len(material_events)} events)")
        print(f"   phase_problems: opening={opening_problem}, middle={middlegame_problem}, end={endgame_problem}")
        print(f"   confidence: {confidence:.2f}")
        
        return structured

    def _build_facts_pack(
        self, competitive_context: Dict, structured_analysis: Dict, player_elo: int
    ) -> Dict:
        """
        V5: Construye FACTS_PACK con datos filtrados y limpios
        
        CAMBIO CLAVE: Filtra top_swings con delta_cp = 0 o muy bajo (< 50).
        Esto evita que el LLM mencione "cambios de 0 centipawns".
        
        Args:
            competitive_context: Contexto con engine_analysis
            structured_analysis: JSON estructurado validado
            player_elo: ELO del jugador
            
        Returns:
            FACTS_PACK con datos ground truth limpios
        """
        engine = competitive_context.get("engine_analysis", {})
        result = competitive_context.get("result", "unknown")
        
        # Extraer datos básicos
        decisive_move_chess = engine.get("engine_decisive_move_chess")
        decisive_move_ply = engine.get("engine_decisive_move")
        max_swing_cp = engine.get("engine_max_swing_cp", 0)
        material_events = engine.get("material_events", [])
        error_distribution = engine.get("error_distribution", {})
        
        # ⚠️ FILTRADO CRÍTICO: Remover top_swings inútiles
        top_swings_raw = engine.get("top_swings", [])
        top_swings_filtered = [
            s for s in top_swings_raw 
            if abs(s.get("delta_cp", 0)) >= 50  # Threshold: mínimo 50 cp
        ]
        
        print(f"\n🧹 V5 - FILTRADO DE SWINGS:")
        print(f"   Swings crudos: {len(top_swings_raw)}")
        print(f"   Swings filtrados (|delta| >= 50): {len(top_swings_filtered)}")
        
        # Evento decisivo detallado
        decisive_event = None
        if decisive_move_chess and decisive_move_ply:
            # Buscar details del evento decisivo en material_events o top_swings
            material_event = next(
                (e for e in material_events if e["chess_notation_move"] == decisive_move_chess),
                None
            )
            
            if material_event:
                decisive_event = {
                    "chess_move": decisive_move_chess,
                    "ply": decisive_move_ply,
                    "type": material_event["type"],
                    "value_lost": material_event["value_lost"],
                    "phase": material_event["phase"],
                }
            else:
                # Buscar en swings filtrados
                swing_event = next(
                    (s for s in top_swings_filtered if s["chess_notation_move"] == decisive_move_chess),
                    None
                )
                if swing_event:
                    decisive_event = {
                        "chess_move": decisive_move_chess,
                        "ply": decisive_move_ply,
                        "type": "evaluative_swing",
                        "delta_cp": swing_event["delta_cp"],
                        "phase": swing_event["phase"],
                    }
        
        # Construir FACTS_PACK
        facts_pack = {
            "player_color": competitive_context.get("player_color", "unknown"),
            "player_elo": player_elo,
            "result": result,
            "decisive_event": decisive_event,
            "material_events": material_events,
            "top_swings": top_swings_filtered[:3],  # Solo top 3 swings relevantes
            "error_distribution": error_distribution,
            "structured_analysis": structured_analysis,
        }
        
        print(f"✅ FACTS_PACK construido:")
        print(f"   Evento decisivo: {decisive_event}")
        print(f"   Material events: {len(material_events)}")
        print(f"   Top swings relevantes: {len(facts_pack['top_swings'])}")
        
        return facts_pack

    def _get_elo_output_policy(self, player_elo: int) -> Dict[str, any]:
        """
        Define la política de salida (formato, longitud, estructura) según ELO

        Implementa Sección 4.2 del roadmap: Output Policy por bucket

        Args:
            player_elo: Rating ELO del jugador

        Returns:
            Dict con reglas de formato y estructura del reporte
        """
        if player_elo < 1600:
            # Novice/Intermediate: Simple y accionable
            return {
                "max_bullet_points": 3,
                "max_key_moves": 2,
                "include_variations": False,
                "teaching_style": "analogías simples, reglas heurísticas claras",
                "max_words": 300,
                "format_rules": [
                    "Máximo 3 recomendaciones",
                    "Al menos 2 jugadas específicas citadas",
                    "1 hábito de entrenamiento sugerido",
                ],
            }
        elif player_elo < 2000:
            # Intermediate/Advanced: Balance entre teoría y práctica
            return {
                "max_bullet_points": 5,
                "max_key_moves": 4,
                "include_variations": True,
                "teaching_style": "conceptos posicionales + variantes cortas",
                "max_words": 450,
                "format_rules": [
                    "3-5 recomendaciones priorizadas",
                    "Al menos 4 jugadas específicas citadas",
                ],
            }
        else:
            # Advanced/Expert: Profundidad técnica
            return {
                "max_bullet_points": 6,
                "max_key_moves": 6,
                "include_variations": True,
                "teaching_style": "análisis técnico profundo, profilaxis",
                "max_words": 600,
                "format_rules": [
                    "Análisis exhaustivo de errores críticos",
                    "Mínimo 6 jugadas específicas referenciadas",
                ],
            }

    # ============================================================
    # ARQUITECTURA DOBLE PASO: JSON → Validación → Narrativa
    # ============================================================

    def _build_structured_prompt(
        self,
        player_elo: int,
        shap_summary: Dict,
        competitive_context: Dict,
        top_error_moves: List[Dict],
    ) -> str:
        """
        V3: PASO 1 - Genera prompt para análisis estructurado usando engine_analysis precalculado

        El LLM NO decide hechos estructurales. Solo los usa para generar JSON.

        Args:
            player_elo: ELO del jugador
            shap_summary: Resumen del análisis SHAP
            competitive_context: Contexto competitivo (incluye engine_analysis)
            top_error_moves: Evidence pack

        Returns:
            Prompt optimizado v3 (reducido ~40% tokens)
        """
        # Extraer engine_analysis precalculado
        engine = competitive_context.get("engine_analysis", {})
        result = competitive_context.get("result", "unknown")

        top_swings = engine.get("top_swings", [])
        engine_decisive_move = engine.get("engine_decisive_move_chess")
        engine_max_swing_cp = engine.get("engine_max_swing_cp", 0)
        material_events = engine.get("material_events", [])
        error_distribution = engine.get("error_distribution", {})

        # Construir top swings compacto
        swings_text = "\n".join(
            [
                f"  Move #{s['chess_notation_move']}: {s['delta_cp']:+d} cp (phase: {s['phase']})"
                for s in top_swings[:3]  # Solo top 3
            ]
        )

        # Material events compacto
        material_text = "None"
        if material_events:
            material_text = "\n".join(
                [
                    f"  Move #{e['chess_notation_move']}: -{e['value_lost']:.1f} material"
                    for e in material_events[:2]  # Solo primeros 2
                ]
            )

        prompt = f"""Analyze chess game strictly using precomputed engine data.

**ENGINE ANALYSIS (PRECOMPUTED):**

Result: {result.upper()}
Player ELO: {player_elo}

Top swings (centipawns):
{swings_text}

Engine decisive move: #{engine_decisive_move} (swing: {engine_max_swing_cp} cp)

Material events:
{material_text}

Error distribution:
- Opening: {error_distribution.get('opening', 0)}
- Middlegame: {error_distribution.get('middlegame', 0)}
- Endgame: {error_distribution.get('endgame', 0)}

**OUTPUT (JSON only):**

{{
  "decisive_move_used": {engine_decisive_move},
  "error_type": "single" | "accumulated",
  "material_loss_claimed": true | false,
  "opening_problem_detected": true | false,
  "middlegame_problem_detected": true | false,
  "endgame_problem_detected": true | false,
  "confidence": 0.0-1.0
}}

**HARD RULES:**

1. decisive_move_used MUST be {engine_decisive_move} (engine precomputed)
2. material_loss_claimed = true ONLY if material_events not empty
3. error_type = "single" if max_swing >= 250 cp, else "accumulated"
4. *_problem_detected = true ONLY if error_distribution[phase] > 0
5. confidence <= 0.85 (unless mate detected)
6. DO NOT invent data beyond engine_analysis

Return JSON only."""

        return prompt

    def _build_narrative_prompt(
        self,
        player_elo: int,
        shap_summary: Dict,
        competitive_context: Dict,
        top_error_moves: List[Dict],
        structured_analysis: Dict,
    ) -> str:
        """
        V3: PASO 2 - Genera prompt para narrativa usando JSON validado y engine_analysis

        El LLM solo explica, no decide. Tokens reducidos ~30%.

        Args:
            player_elo: ELO del jugador
            shap_summary: Resumen del análisis SHAP
            competitive_context: Contexto competitivo (incluye engine_analysis)
            top_error_moves: Evidence pack
            structured_analysis: JSON validado del Paso 1

        Returns:
            Prompt optimizado v3 para narrativa
        """
        elo_context = self._get_elo_context(player_elo)
        output_policy = self._get_elo_output_policy(player_elo)

        # Extraer datos
        result = competitive_context.get("result", "unknown")
        engine = competitive_context.get("engine_analysis", {})

        decisive_move = structured_analysis["decisive_move_used"]
        error_type = structured_analysis["error_type"]
        material_loss = structured_analysis["material_loss_claimed"]
        opening_problem = structured_analysis["opening_problem_detected"]
        middlegame_problem = structured_analysis["middlegame_problem_detected"]
        endgame_problem = structured_analysis["endgame_problem_detected"]

        # Top swings del engine (para contexto)
        top_swings = engine.get("top_swings", [])
        swings_context = "\n".join(
            [
                f"  Move #{s['chess_notation_move']}: {s['delta_cp']:+d} cp"
                for s in top_swings[:3]
            ]
        )

        # Construir restricciones dinámicas
        material_events_list = engine.get("material_events", [])
        restrictions = "\n❌ RESTRICCIONES CRÍTICAS (ANTI-ALUCINACIÓN):\n"

        if not material_loss:
            restrictions += "- ⛔ ABSOLUTAMENTE PROHIBIDO mencionar: 'perdiste una pieza', 'pérdida material', 'perdiste el caballo', 'perdiste la torre', etc.\n"
            restrictions += (
                "- ⛔ ABSOLUTAMENTE PROHIBIDO mencionar cualquier pieza perdida\n"
            )
            restrictions += "- Describir ÚNICAMENTE como error posicional/estratégico/táctico/evaluativo\n"
            restrictions += f"- DATO VERIFICADO: material_loss_claimed = false (NO hubo pérdida de piezas > 2 peones)\n"
            restrictions += f"- DATO VERIFICADO: material_events = [] (lista vacía, sin pérdidas detectadas)\n"

        if not opening_problem:
            restrictions += "- NO discutir errores de apertura\n"

        if not middlegame_problem:
            restrictions += "- NO discutir errores de medio juego\n"

        if not endgame_problem:
            restrictions += "- NO discutir errores de final\n"

        # Obtener detalles del swing decisivo para contexto más rico
        decisive_swing_detail = ""
        if top_swings:
            decisive = top_swings[0]
            swing_cp = abs(decisive["delta_cp"])
            error_type_label = decisive["error_label"]
            phase_label = decisive["phase"]

            if error_type_label == "blunder":
                error_desc = "un error grave (blunder)"
            elif error_type_label == "mistake":
                error_desc = "un error significativo (mistake)"
            elif error_type_label == "inaccuracy":
                error_desc = "una imprecisión"
            else:
                error_desc = "un cambio en la evaluación"

            decisive_swing_detail = f"\nJugada #{decisive_move}: {error_desc} en {phase_label}, cambio de {swing_cp} centipawns"

        # Instrucción según resultado
        if result == "win":
            outcome_instr = f"GANASTE esta partida. El análisis identifica la jugada #{decisive_move} como el momento más crítico. Explica cómo tu juego compensó este momento y qué fortalezas te permitieron ganar."
        elif result == "loss":
            if error_type == "single":
                outcome_instr = f"PERDISTE por un error decisivo en la jugada #{decisive_move}. Explica específicamente qué pasó en ese momento (cambio evaluativo de {engine.get('engine_max_swing_cp', 0)} cp) y cómo evitarlo."
            else:
                outcome_instr = f"PERDISTE por acumulación de errores. La jugada #{decisive_move} fue el momento más crítico. Explica el patrón de errores que llevó a la derrota."
        else:
            outcome_instr = f"EMPATE. La jugada #{decisive_move} fue el momento más crítico de la partida. Explica las oportunidades que pudiste aprovechar mejor."

        prompt = f"""Genera reporte pedagógico de ajedrez EN ESPAÑOL basado en análisis validado.

⚠️ CRÍTICO: TODO EL REPORTE DEBE ESTAR EN ESPAÑOL. NO uses inglés bajo ninguna circunstancia.

**CONTEXTO DE LA PARTIDA:**
- Resultado: {result.upper()}
- ELO del jugador: {player_elo}
- Tipo de error: {error_type}{decisive_swing_detail}

**ANÁLISIS VALIDADO (JSON):**
```json
{json.dumps(structured_analysis, indent=2, ensure_ascii=False)}
```

**SWINGS DEL ENGINE (los 3 momentos más críticos):**
{swings_context}

**EVENTOS DE MATERIAL (verificado por engine):**
{f"- Pérdidas de piezas detectadas: {len(material_events_list)}" if material_events_list else "- NO hubo pérdidas significativas de material (> 2 peones)"}
{f"- Jugadas con pérdida: {[e['chess_notation_move'] for e in material_events_list]}" if material_events_list else ""}

{restrictions}

**INSTRUCCIONES:**
1. {outcome_instr}
2. Nivel objetivo: {elo_context['language_level']}
3. Áreas de enfoque: {elo_context['focus_areas']}
4. Máximo palabras: {output_policy['max_words']}
5. SÉ ESPECÍFICO: Explica QUÉ pasó en la jugada #{decisive_move}, no uses frases genéricas
6. NO inventar hechos más allá del análisis validado
7. ⚠️ CRÍTICO: Respeta ABSOLUTAMENTE las restricciones sobre material

**PROHIBIDO (frases genéricas y alucinaciones):**
❌ "errores acumulados a lo largo de la partida"
❌ "mejor coordinación de piezas"
❌ "desarrollo armonioso"
❌ "control del centro" (sin citar jugada específica)
❌ Si material_loss_claimed = false: NO MENCIONAR pérdida de piezas bajo NINGUNA circunstancia

**REQUERIDO (análisis específico):**
✅ "En la jugada #{decisive_move}, en el {structured_analysis.get('middlegame_problem_detected') and 'medio juego' or 'final'}, [descripción específica]"
✅ Citar el cambio evaluativo en centipawns
✅ Mencionar la fase concreta (apertura/medio juego/final)

**FORMATO DE SALIDA (Markdown EN ESPAÑOL):**

## 📊 Diagnóstico
(2-3 oraciones específicas sobre la jugada #{decisive_move}: qué pasó, impacto evaluativo, consecuencias)

## 🎯 Acciones Concretas
({output_policy['max_bullet_points']} recomendaciones CONCRETAS con jugadas citadas)

## ✅ Fortaleza Detectada
(1 aspecto positivo CONCRETO con fase o jugada específica)

RECUERDA: Escribe TODO en español. Sé ESPECÍFICO y CONCRETO. NO uses frases genéricas."""

        return prompt

    def _build_v5_narrative_prompt(self, facts_pack: Dict, player_elo: int) -> str:
        """
        V5: Genera prompt usando FACTS_PACK con datos filtrados
        
        MEJORA CLAVE vs V4:
        - top_swings ya vienen filtrados (sin delta_cp = 0)
        - HARD RULES explícitas sobre no inventar swings
        - Formato estructurado: Hechos vs Interpretación
        - Validación interna obligatoria
        
        Args:
            facts_pack: Paquete de datos ground truth filtrados
            player_elo: ELO del jugador
            
        Returns:
            Prompt V5 con FACTS_PACK explícito
        """
        elo_context = self._get_elo_context(player_elo)
        output_policy = self._get_elo_output_policy(player_elo)
        
        # Extraer datos del FACTS_PACK
        player_color = facts_pack["player_color"]
        result = facts_pack["result"]
        decisive_event = facts_pack["decisive_event"]
        material_events = facts_pack["material_events"]
        top_swings = facts_pack["top_swings"]
        structured = facts_pack["structured_analysis"]
        
        # Formatear evento decisivo
        if decisive_event:
            if decisive_event.get("type") == "evaluative_swing":
                event_desc = f"Movida {decisive_event['chess_move']} (ply {decisive_event['ply']}): Swing evaluativo de {decisive_event['delta_cp']:+d} cp en {decisive_event['phase']}"
            else:
                event_desc = f"Movida {decisive_event['chess_move']} (ply {decisive_event['ply']}): {decisive_event['type']} de {decisive_event.get('value_lost', 0):.1f} puntos en {decisive_event['phase']}"
        else:
            event_desc = "Dato no disponible en FACTS_PACK"
        
        # Formatear material_events
        material_desc = ""
        if material_events:
            material_desc = "Otros eventos materiales:\n"
            for e in material_events:
                material_desc += f"  - Movida {e['chess_notation_move']} (ply {e['move']}): {e['type']} de {e['value_lost']:.1f} puntos en {e['phase']}\n"
        else:
            material_desc = "No hay pérdidas materiales registradas (> 2 peones)"
        
        # Formatear top_swings (YA FILTRADOS en V5)
        swings_desc = ""
        if top_swings:
            swings_desc = "Swings relevantes (|delta| >= 50 cp):\n"
            for s in top_swings:
                swings_desc += f"  - Movida {s['chess_notation_move']} (ply {s['move']}): {s['delta_cp']:+d} cp ({s['error_label']}, {s['phase']})\n"
        else:
            swings_desc = "No hay swings evaluativos relevantes (todos |delta| < 50 cp)"
        
        # Construir FACTS_PACK para el prompt
        facts_json = json.dumps(facts_pack, indent=2, ensure_ascii=False)
        
        # Instrucciones según resultado
        if result == "win":
            outcome_context = f"GANASTE esta partida. A pesar del evento decisivo identificado, tu juego compensó y lograste la victoria. Explica fortalezas concretas que permitieron ganar."
        elif result == "loss":
            outcome_context = f"PERDISTE esta partida. El evento decisivo fue determinante para el resultado. Explica específicamente qué pasó y cómo evitarlo."
        else:
            outcome_context = f"EMPATE. El evento decisivo fue un punto crítico donde pudiste aprovechar mejor. Explica oportunidades específicas."
        
        prompt = f"""Genera reporte pedagógico de ajedrez EN ESPAÑOL basado ÚNICAMENTE en FACTS_PACK.

⚠️ CRÍTICO: TODO debe estar EN ESPAÑOL. NO uses inglés.

## ROLE
Sos un analista de ajedrez y explicador pedagógico, pero **solo** podés usar los datos en FACTS_PACK.
No inventes jugadas, pérdidas, swings, ni evaluaciones.

## INPUT - FACTS_PACK (Ground Truth)
```json
{facts_json}
```

## HARD RULES (OBLIGATORIAS)

1. **Si `top_swings` está vacío o todos tienen `delta_cp` bajo (< 50):**
   - ❌ NO hables de "cambios evaluativos", "puntos de inflexión por centipawns", o "cambio de X centipawns"
   - ✅ Enfócate SOLO en eventos materiales si existen

2. **Solo podés afirmar "pérdida de material en movida X":**
   - ✅ Si existe un `material_event` para esa movida (por `chess_notation_move`)
   - ❌ Nunca inventes pérdidas sin respaldo en FACTS_PACK

3. **Si falta un dato:**
   - Escribí: **"Dato no disponible en FACTS_PACK"**

4. **Formato de movidas:**
   - Reportá como: **"Movida N (ply P)"** usando los valores de FACTS_PACK

5. **NO generalidades sin respaldo:**
   - ❌ "control del centro", "coordinación", "desarrollo" (sin features/SHAP que lo soporten)

## CONTEXTO DE LA PARTIDA
- Color analizado: {player_color}
- ELO: {player_elo}
- Resultado: {result.upper()}
- Nivel objetivo: {elo_context['language_level']}
- Áreas de enfoque: {elo_context['focus_areas']}

{outcome_context}

## EVENTO DECISIVO (de FACTS_PACK)
{event_desc}

## OTROS DATOS (de FACTS_PACK)
{material_desc}

{swings_desc}

## OUTPUT FORMAT (Spanish, Markdown)

### 📌 Hechos (Ground truth)
- Color analizado: [del FACTS_PACK]
- ELO: [del FACTS_PACK]
- Evento decisivo: [citar textual de FACTS_PACK]
- Otros eventos materiales: [listar si existen, sino "ninguno"]
- Swings relevantes: [listar si existen con |delta| >= 50, sino "ninguno detectado"]

### 🧠 Interpretación (con límites)
(2-3 oraciones explicando QUÉ significa el evento decisivo para un jugador de este ELO.
Si no hay swings relevantes, aclarar: "No se detectaron cambios evaluativos significativos (< 50 cp), 
por lo que el análisis se enfoca en [eventos materiales / otro aspecto respaldado]")

### 🎯 Acciones concretas (máximo {output_policy['max_bullet_points']})
(Recomendaciones ESPECÍFICAS y CHEQUEABLES. Ejemplos:
- "En situaciones como movida X, verificar..." 
- "Antes de mover, chequear piezas desprotegidas en..."
NO frases genéricas como "mejorar coordinación")

### ✅ 1 fortaleza real
(Basada SOLO en FACTS_PACK. Si el jugador ganó a pesar del error, explicar qué permitió la recuperación.
Si no hay dato explícito, inferir CONSERVADORAMENTE del resultado. Ejemplo:
"Lograste ganar a pesar del evento decisivo, lo que sugiere resiliencia en la fase final")

### 🧪 Validación interna
Lista de afirmaciones del reporte y el campo de FACTS_PACK que la respalda:
- Afirmación 1: [cita del reporte] → Respaldo: facts_pack.decisive_event.chess_move = X
- Afirmación 2: [cita del reporte] → Respaldo: facts_pack.material_events[0].value_lost = Y
(Incluir al menos 3 validaciones)

## PROHIBIDO (Anti-alucinación)
❌ "cambio evaluativo de 0 centipawns" (no tiene sentido)
❌ "pérdida de material" sin material_event en FACTS_PACK
❌ Mencionar jugadas no listadas en FACTS_PACK
❌ Generalidades sin respaldo (control, coordinación, etc.)

## REQUERIDO
✅ Citar jugadas como "Movida X (ply Y)" con valores de FACTS_PACK
✅ Si no hay swings relevantes, DECIRLO explícitamente
✅ Basar CADA afirmación en FACTS_PACK
✅ Incluir sección de validación interna

RECUERDA: Todo en español. Solo hechos de FACTS_PACK. Sé específico y verificable."""

        return prompt

    def _build_v6_narrative_prompt(self, facts_pack: Dict, player_elo: int) -> str:
        """
        V6: Genera prompt PEDAGÓGICO (menos técnico/forense que V5)
        
        MEJORA CLAVE vs V5:
        - Sin jerga técnica (no "ply", "Ground truth", "FACTS_PACK" en output)
        - Tono conversacional (párrafos, no bullets técnicos)
        - Sin "Validación interna" en output (solo para debugging)
        - Más natural: "En la jugada 7..." en lugar de "Movida 7 (ply 13):"
        - Enfoque pedagógico según nivel ELO
        
        Args:
            facts_pack: Paquete de datos ground truth filtrados
            player_elo: ELO del jugador
            
        Returns:
            Prompt V6 conversacional y pedagógico
        """
        elo_context = self._get_elo_context(player_elo)
        output_policy = self._get_elo_output_policy(player_elo)
        
        # Extraer datos del FACTS_PACK
        player_color = facts_pack["player_color"]
        player_color_es = "blancas" if player_color == "white" else "negras"
        result = facts_pack["result"]
        decisive_event = facts_pack["decisive_event"]
        material_events = facts_pack["material_events"]
        top_swings = facts_pack["top_swings"]
        
        # Descripción natural del evento decisivo
        if decisive_event:
            move_num = decisive_event['chess_move']
            phase_es = {
                "opening": "la apertura",
                "middlegame": "el medio juego",
                "endgame": "el final"
            }.get(decisive_event.get('phase', 'middlegame'), "la partida")
            
            if decisive_event.get("type") == "evaluative_swing":
                event_desc = f"un cambio importante en la evaluación durante {phase_es} (jugada {move_num})"
            else:
                value =decisive_event.get('value_lost', 0)
                if value >= 5:
                    piece_desc = "una pieza valiosa"
                elif value >= 3:
                    piece_desc = "una pieza menor"
                else:
                    piece_desc = "material"
                event_desc = f"la pérdida de {piece_desc} en la jugada {move_num} durante {phase_es}"
        else:
            event_desc = "un momento crítico en la partida"
        
        # Contar eventos materiales adicionales
        other_material = [e for e in material_events if e['chess_notation_move'] != decisive_event.get('chess_move')] if decisive_event else material_events
        
        # Contexto según resultado
        if result == "win":
            outcome_intro = "A pesar de este momento difícil, lograste ganar la partida."
            outcome_focus = "recuperarte y aprovechar las oportunidades que se presentaron después"
        elif result == "loss":
            outcome_intro = "Lamentablemente, este momento fue determinante para el resultado final."
            outcome_focus = "reconocer y evitar situaciones similares en futuras partidas"
        else:
            outcome_intro = "La partida terminó en empate."
            outcome_focus = "haber aprovechado mejor este momento para inclinar la balanza a tu favor"
        
        # Construir FACTS_PACK para validación interna (no va al output)
        facts_json = json.dumps(facts_pack, indent=2, ensure_ascii=False)
        
        prompt = f"""Genera un reporte de ajedrez EN ESPAÑOL con tono PEDAGÓGICO y CONVERSACIONAL.

⚠️ CRÍTICO: Debe ser amigable, NO técnico. NO uses jerga como "ply", "cp", "ground truth".

## DATOS DISPONIBLES (para uso interno, NO copiar al reporte)
```json
{facts_json}
```

## CONTEXTO
- Jugaste con: {player_color_es}
- Tu nivel: {player_elo} ELO
- Resultado: {result.upper()}
- Momento crítico: {event_desc}
- {outcome_intro}

## REGLAS ESTRICTAS (Anti-alucinación)
1. **Si no hay swings relevantes (|delta| >= 50):**
   - ❌ NO menciones "cambios evaluativos" ni "centipawns"
   - ✅ Enfócate en la pérdida de material

2. **Solo menciona pérdida de material SI:**
   - ✅ Existe un material_event para esa jugada
   - ❌ NUNCA inventes pérdidas

3. **Formato natural:**
   - ✅ "En la jugada 7..." (no "Movida 7 (ply 13):")
   - ✅ "Durante la apertura..." (no "phase: opening")
   - ✅ "Perdiste una pieza..." (no "material_event: piece_loss de 3.0 puntos")

## OBJETIVO PEDAGÓGICO
Nivel ELO {player_elo}:
- Lenguaje: {elo_context['language_level']}
- Enfoque: {elo_context['focus_areas']}
- Meta: {outcome_focus}

## FORMATO DE SALIDA (Markdown, EN ESPAÑOL)

## 📊 ¿Qué pasó en esta partida?
(2-3 párrafos conversacionales explicando:
- Contexto: qué fue lo más importante que pasó
- SOLO si hay swings relevantes: mencionar cambio evaluativo de forma natural
- Si NO hay swings: explicar que el momento crítico fue la pérdida de material
- Impacto: cómo esto influyó en el resultado
- Usar tono empático y pedagógico, NO técnico)

## 🎯 ¿Qué puedes mejorar?
({output_policy['max_bullet_points']} recomendaciones CONCRETAS y ACCIONABLES:
- Usar lenguaje natural: "En situaciones como la de la jugada X, antes de mover..."
- Evitar frases genéricas: NO "mejorar la coordinación", SÍ "antes de mover, verifica..."
- Ser específico: mencionar jugadas exactas si están en los datos
- Tono motivador: "Para la próxima...", "Intenta...")

## ✅ ¿Qué hiciste bien?
(1 fortaleza REAL basada en los datos:
- Si ganaste a pesar del error: resiliencia, recuperación
- Si empataste: manejo de la presión
- Si perdiste pero jugaste bien después: aprendizaje, no repetición de errores
- Tono positivo y motivador)

## PROHIBICIONES ESTRICTAS
❌ NO usar: "ply", "cp", "centipawns", "delta", "swing", "ground truth", "FACTS_PACK"
❌ NO formato técnico: "Movida X (ply Y): type Z de N puntos"
❌ NO sección "Validación interna" (es para debugging, no para el usuario)
❌ NO mencionar pérdida de material sin respaldo en los datos
❌ NO mencionar cambios evaluativos Si no hay swings relevantes

## EJEMPLO DE TONO CORRECTO
✅ "En la jugada 7, durante la apertura, perdiste una pieza menor..."
✅ "Este fue el momento más crítico de la partida..."
✅ "Para evitar esto en el futuro, intenta..."

## EJEMPLO DE TONO INCORRECTO
❌ "Evento decisivo: Movida 7 (ply 13): piece_loss de 3.0 puntos en opening"
❌ "Se produjo un cambio evaluativo de 0 centipawns..." (sin sentido)
❌ "Validación interna: Afirmación 1 → facts_pack.X..." (técnico/debugging)

RECUERDA: 
- Tono amigable y pedagógico
- Sin jerga técnica
- Basado 100% en los datos disponibles
- Máximo {output_policy['max_words']} palabras"""

        return prompt

    def _build_prompt(
        self,
        player_elo: int,
        patterns: List[Dict],
        shap_summary: Dict,
        competitive_context: Dict,
        top_error_moves: List[Dict],
    ) -> str:
        """
        Construye el prompt estructurado para el LLM usando patrones sintetizados y contexto competitivo

        Implementa Sección 5.2 del roadmap: Evidence pack move-by-move

        Args:
            player_elo: Rating ELO del jugador
            patterns: Lista de patrones detectados (ya sintetizados)
            shap_summary: Resumen básico del análisis
            competitive_context: Contexto competitivo (resultado, comparación vs oponente)
            top_error_moves: Top movimientos con error específicos (evidence pack)

        Returns:
            Prompt optimizado para GPT-4
        """
        elo_context = self._get_elo_context(player_elo)
        output_policy = self._get_elo_output_policy(player_elo)

        # Construir evidence pack move-by-move (Sección 5.2)
        evidence_moves_text = ""
        if top_error_moves:
            evidence_moves_text = "\n**Movimientos Críticos (Evidence Pack):**\n"
            for idx, move in enumerate(
                top_error_moves[: output_policy["max_key_moves"]], 1
            ):
                top_features_str = ", ".join(
                    [f"{f['feature']}" for f in move["top_shap_features"]]
                )
                # Usar chess_move_number (notación estándar) en lugar de move_number (secuencial)
                display_move_num = move.get("chess_move_number", move["move_number"])
                evidence_moves_text += f"""
{idx}. **Movimiento #{display_move_num}** → {move['error_label'].upper()}
   - Features críticos: {top_features_str}
   - Impacto SHAP: {move['shap_impact']}
"""

        # Construir lista de patrones para el prompt
        patterns_text = ""
        for idx, p in enumerate(patterns[:3], 1):  # Solo top 3 patrones
            patterns_text += f"""
{idx}. **{p['description']}** (Severidad: {p['severity']})
   - Recomendación: {p['recommendation']}
"""

        # Calcular métricas básicas
        total_moves = shap_summary.get("total_moves", 0)
        blunder_count = shap_summary.get("blunder_count", 0)
        mistake_count = shap_summary.get("mistake_count", 0)

        # Extraer contexto competitivo
        result = competitive_context.get("result", "unknown")
        player_error_ratio = competitive_context.get("player_error_ratio", 0)
        opponent_error_ratio = competitive_context.get("opponent_error_ratio", 0)
        error_delta = competitive_context.get("error_ratio_delta", 0)
        critical_move = competitive_context.get("critical_move")
        decisive_swing = competitive_context.get("decisive_swing", 0)
        decisive_phase = competitive_context.get("decisive_phase", "middlegame")
        loss_type = competitive_context.get("loss_type")
        first_material_loss = competitive_context.get("first_material_loss_move")
        conversion_quality = competitive_context.get("conversion_quality")
        phase_errors = competitive_context.get("phase_error_distribution", {})
        material_delta = competitive_context.get("material_delta_at_decisive_move", 0)

        # Determinar tono según resultado
        result_emoji = {"win": "🏆", "loss": "❌", "draw": "⚖️"}.get(result, "❓")

        # Construir contexto competitivo enriquecido para el prompt
        comp_context_text = f"""
**Resultado:** {result_emoji} {result.upper()}
**Tu error rate:** {player_error_ratio:.1%} | **Oponente:** {opponent_error_ratio:.1%} | **Delta:** {error_delta:+.1%}
"""
        if critical_move:
            comp_context_text += f"**Momento crítico:** Movimiento #{critical_move} (Fase: {decisive_phase}, Swing: {decisive_swing})\n"

        # Agregar métricas específicas según resultado
        if result == "loss" and loss_type:
            loss_desc = (
                "un error decisivo"
                if loss_type == "single_blunder"
                else "acumulación de imprecisiones"
            )
            comp_context_text += f"**Tipo de derrota:** {loss_desc}\n"

        if first_material_loss:
            comp_context_text += (
                f"**Primera pérdida material:** Movimiento #{first_material_loss}\n"
            )

        if result == "win" and conversion_quality:
            conversion_desc = {
                "clean": "conversión limpia",
                "stable": "conversión estable",
                "unstable": "conversión imprecisa",
            }.get(conversion_quality, conversion_quality)
            comp_context_text += f"**Calidad de conversión:** {conversion_desc}\n"

        # Distribución de errores por fase (para evitar generalización)
        if phase_errors:
            phase_summary = ", ".join(
                [
                    f"{phase.capitalize()}: {count}"
                    for phase, count in phase_errors.items()
                    if count > 0
                ]
            )
            if phase_summary:
                comp_context_text += f"**Errores por fase:** {phase_summary}\n"

        # Adaptar instrucciones según resultado y contexto
        if result == "win":
            outcome_instruction = "GANASTE. Identifica qué compensó tus errores. Refuerza patrones exitosos."
            if conversion_quality:
                outcome_instruction += f" Tu conversión fue {conversion_quality} - analiza cómo mantuviste/perdiste ventaja."
        elif result == "loss":
            outcome_instruction = "PERDISTE. Identifica el factor decisivo de la derrota. Prioriza la corrección más urgente."
            if loss_type == "single_blunder":
                outcome_instruction += f" Derrota por UN error crítico en el movimiento #{critical_move} - analiza qué alternativa tenías."
            elif loss_type == "accumulated_errors":
                outcome_instruction += (
                    " Derrota por acumulación - identifica el patrón repetitivo."
                )
        else:
            outcome_instruction = (
                "EMPATE. Identifica oportunidades perdidas para ganar."
            )

        # Instrucciones sobre distribución de errores por fase
        phase_instruction = ""
        if phase_errors:
            phases_with_errors = [
                phase for phase, count in phase_errors.items() if count > 0
            ]
            if phases_with_errors:
                phase_instruction = f"Los errores ocurrieron en: {', '.join(phases_with_errors)}. NO menciones fases sin errores."

        # ============================================================
        # MEJORA V2: Reglas anti-alucinación estrictas
        # ============================================================
        # Determinar si está prohibido hablar de pérdida material
        forbid_material_language = material_delta >= -1.0

        # Construir reglas anti-alucinación
        anti_hallucination_rules = """
🚨 **REGLAS ANTI-ALUCINACIÓN (OBLIGATORIAS):**

❌ **PROHIBIDO inventar pérdida material:**
"""
        if forbid_material_language:
            anti_hallucination_rules += """   - Material delta en momento decisivo: 0 puntos
   - NO puedes afirmar: "perdiste una pieza", "pérdida material", "te costó material"
   - Solo describir como: error posicional, estratégico, exposición del rey, pérdida de coordinación
"""
        else:
            anti_hallucination_rules += f"""   - Material delta en momento decisivo: {material_delta:.1f} puntos
   - PUEDES mencionar pérdida material SOLO si es significativa (< -1.0)
"""

        anti_hallucination_rules += f"""
❌ **PROHIBIDO frases genéricas sin jugada:**
   - NO: "controla el centro", "mejora la apertura", "limita la movilidad"
   - SÍ: "En la jugada #{critical_move}, perdiste el control del centro porque..."

❌ **PROHIBIDO inventar blunders:**
   - Solo puedes llamar "blunder" a jugadas explícitamente marcadas como BLUNDER en Evidence Pack
   - Verifica error_label antes de afirmar

❌ **PROHIBIDO hablar de fases sin errores:**
   - {phase_instruction if phase_instruction else "Solo menciona fases donde ocurrieron errores"}

✅ **OBLIGATORIO mencionar:**
   - Movimiento decisivo #{critical_move}
   - QUÉ cambió en la posición (swing: {decisive_swing:.1f} puntos)
   - Tipo de error específico (no genérico)

⚠️ **NOTA:** Este reporte será validado automáticamente. Violaciones causarán rechazo.
"""

        prompt = f"""Eres un entrenador de ajedrez. Genera un informe específico y diferenciado por resultado.

**Jugador:** ELO {player_elo} | **Movimientos:** {total_moves} | **Errores graves:** {blunder_count + mistake_count}

**Contexto Competitivo:**
{comp_context_text}
{evidence_moves_text}
**Patrones Detectados:**
{patterns_text}

{anti_hallucination_rules}

**Instrucciones PEDAGÓGICAS:**
1. {outcome_instruction}
2. Usa lenguaje {elo_context['language_level']}
3. Enfócate en: {elo_context['focus_areas']}
4. Estilo: {output_policy['teaching_style']}
5. OBLIGATORIO: Cita al menos {output_policy['max_key_moves']} movimientos específicos del Evidence Pack
6. Máximo {output_policy['max_words']} palabras
7. El momento decisivo fue en {decisive_phase} (movimiento #{critical_move}) - EXPLICA QUÉ PASÓ en esa jugada
8. ADAPTA el tono al resultado: {"refuerza logros" if result == "win" else "corrige errores críticos" if result == "loss" else "optimiza precisión"}

**Formato (Markdown):**

## 📊 Diagnóstico
(problema principal o fortaleza decisiva según resultado - cita movimiento #{critical_move})

## 🎯 Acciones Concretas
({output_policy['max_bullet_points']} recomendaciones máximo, cada una citando jugadas del Evidence Pack)

## ✅ Fortaleza Detectada
(1 aspecto positivo concreto)

Sé directo y específico. Evita relleno. Respeta las REGLAS ANTI-ALUCINACIÓN."""

        return prompt

    async def generate_pedagogical_report(
        self,
        db: Session,
        game_id: str,
        player_elo: int,
        player_color: str,
        username: str,
        analysis_id: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Genera un informe pedagógico completo usando LLM

        Args:
            db: Sesión de base de datos
            game_id: ID del juego a analizar
            player_elo: Rating ELO del jugador
            player_color: Color del jugador ("white" o "black")
            username: Usuario que solicita el análisis
            analysis_id: ID de análisis existente (opcional, si no se ejecuta nuevo)

        Returns:
            Dict con el informe generado y metadata
        """
        try:
            # Si no hay analysis_id, ejecutar análisis ML primero
            if not analysis_id:
                print(
                    f"🔬 Ejecutando análisis ML para game {game_id} (jugador: {player_color})..."
                )
                analysis_id = self.analysis_service.analyze_game(
                    db=db, game_id=game_id, username=username, player_color=player_color
                )
                print(f"✅ Análisis completado: ID {analysis_id}")

            # Obtener resumen SHAP del análisis
            shap_summary = self._get_shap_summary(db=db, analysis_id=analysis_id)

            # Sintetizar patrones pedagógicos desde SHAP
            print(f"🔍 Sintetizando patrones pedagógicos...")
            patterns = self._synthesize_patterns(
                db=db, analysis_id=analysis_id, shap_summary=shap_summary
            )
            print(f"✅ Detectados {len(patterns)} patrones")

            # Obtener movimientos con errores específicos (evidence pack)
            print(f"📋 Obteniendo evidence pack (top error moves)...")
            top_error_moves = self._get_top_error_moves(
                db=db, analysis_id=analysis_id, top_n=8
            )
            print(f"✅ Identificados {len(top_error_moves)} movimientos críticos")

            # Obtener contexto competitivo (resultado, comparación vs oponente)
            print(f"⚔️ Obteniendo contexto competitivo...")
            competitive_context = self._get_competitive_context(
                db=db,
                game_id=game_id,
                player_color=player_color,
                analysis_id=analysis_id,
            )
            print(f"   Resultado: {competitive_context.get('result', 'N/A')}")
            print(
                f"   Error ratio jugador: {competitive_context.get('player_error_ratio', 0):.2f}"
            )
            print(
                f"   Error ratio oponente: {competitive_context.get('opponent_error_ratio', 0):.2f}"
            )

            # ============================================================
            # V4: PASO 1 - Generar análisis estructurado (100% DETERMINÍSTICO - SIN LLM)
            # ============================================================
            print("🔬 V4 - PASO 1: Generando análisis estructurado (DETERMINÍSTICO - SIN LLM)...")
            
            # Generar JSON directamente desde backend (NO usar LLM)
            structured_analysis = self._build_structured_analysis_deterministic(
                competitive_context=competitive_context,
                player_elo=player_elo
            )
            
            print("✅ JSON estructurado generado (0 tokens LLM usados)")

            # ============================================================
            # VALIDACIÓN V3: Verificar JSON contra engine_analysis precalculado
            # ============================================================
            print(f"🔍 VALIDACIÓN V3: Verificando análisis estructurado...")
            validator = StructuredAnalysisValidator(
                competitive_context=competitive_context, evidence_pack=top_error_moves
            )

            try:
                validator.validate(structured_analysis)
                print(
                    f"✅ Validación exitosa: análisis estructurado es factualmente correcto"
                )
                validation_passed = True
                validation_warning = None

            except JSONValidationError as ve:
                # El JSON del LLM contradice el engine_analysis (alucinación detectada)
                print(f"❌ VALIDACIÓN FALLIDA: {str(ve)}")
                print(f"   JSON generado: {json.dumps(structured_analysis, indent=2)}")

                validation_passed = False
                validation_warning = str(ve)

                # V3: No ajustamos nada automáticamente, el engine_analysis es la verdad
                # Si falla validación, lanzamos error para forzar corrección del prompt
                raise ValueError(
                    f"Análisis estructurado no pasó validación V3: {str(ve)}"
                )

            # ============================================================
            # PASO 2: Generar narrativa pedagógica basada en JSON validado
            # ============================================================
            print(
                f"📝 PASO 2: Generando narrativa pedagógica basada en JSON validado..."
            )

            # Logging de restricciones de material
            material_loss_in_json = structured_analysis.get(
                "material_loss_claimed", False
            )
            material_events_count = len(
                competitive_context.get("engine_analysis", {}).get(
                    "material_events", []
                )
            )
            print(f"   material_loss_claimed (JSON): {material_loss_in_json}")
            print(f"   material_events detectados: {material_events_count}")
            if not material_loss_in_json:
                print(
                    f"   ⚠️ RESTRICCIÓN ACTIVA: NO mencionar pérdida de material en narrativa"
                )

            # ============================================================
            # V6: Construir FACTS_PACK con datos filtrados
            # ============================================================
            print(f"🔬 V6: Construyendo FACTS_PACK con datos filtrados...")
            
            facts_pack = self._build_facts_pack(
                competitive_context=competitive_context,
                structured_analysis=structured_analysis,
                player_elo=player_elo
            )

            # V6: Usar prompt PEDAGÓGICO (menos técnico/forense)
            narrative_prompt = self._build_v6_narrative_prompt(
                facts_pack=facts_pack,
                player_elo=player_elo
            )

            print(
                f"   Tokens estimados (paso 2): ~{len(narrative_prompt.split())*1.3:.0f}"
            )

            # Llamar a GPT-4 para narrativa final
            narrative_response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un entrenador de ajedrez AMIGABLE y PEDAGÓGICO. Genera reportes EN ESPAÑOL con tono CONVERSACIONAL (no técnico/forense). Explica conceptos de forma clara y motivadora. Nunca uses jerga técnica (ply, cp, delta, ground truth). IMPORTANTE: Responde ÚNICAMENTE en español.",
                    },
                    {"role": "user", "content": narrative_prompt},
                ],
                temperature=0.7,  # Más alto para narrativa natural
                max_tokens=700,  # V5: Aumentado para incluir validación interna completa
                top_p=0.9,
            )

            report_content = narrative_response.choices[0].message.content
            print(f"✅ Narrativa generada ({len(report_content)} caracteres)")

            # Validación post-generación: Detectar alucinaciones de material
            if not material_loss_in_json:
                material_keywords = [
                    "perdiste una pieza",
                    "pérdida material",
                    "te costó material",
                    "perdió material",
                    "perdiste el caballo",
                    "perdiste la torre",
                    "perdiste el alfil",
                    "perdiste la dama",
                    "perdiste un peón",
                ]
                found_material_mentions = [
                    kw for kw in material_keywords if kw in report_content.lower()
                ]

                if found_material_mentions:
                    print(
                        f"❌ ALUCINACIÓN DETECTADA: Se mencionó pérdida de material cuando material_loss_claimed = false"
                    )
                    print(f"   Palabras encontradas: {found_material_mentions}")
                    print(f"   Rechazando reporte y regenerando...")
                    raise ValueError(
                        f"Narrativa mencionó pérdida de material cuando JSON dice material_loss_claimed = false. "
                        f"Palabras detectadas: {found_material_mentions}"
                    )
                else:
                    print(
                        f"✅ Validación post-generación: No se mencionó material (correcto, material_loss_claimed = false)"
                    )

            # Calcular tokens totales (V4: solo paso 2, paso 1 es determinístico)
            total_tokens_used = narrative_response.usage.total_tokens
            total_prompt_tokens = narrative_response.usage.prompt_tokens
            total_completion_tokens = narrative_response.usage.completion_tokens

            # Opción 2: Lanzar error y rechazar el reporte
            # raise HTTPException(
            #     status_code=500,
            #     detail=f"Reporte generado no pasó validación: {str(ve)}"
            # )

            # Por ahora, solo loggeamos y agregamos warning
            # En producción, se podría implementar regeneración automática

            # Metadata del informe V3 (incluyendo engine_analysis y structured_analysis)
            result = {
                "analysis_id": analysis_id,
                "game_id": game_id,
                "player_elo": player_elo,
                "report": report_content,
                "engine_analysis": competitive_context.get(
                    "engine_analysis", {}
                ),  # V3: Engine precalculado
                "structured_analysis": structured_analysis,  # JSON validado
                "validation_passed": validation_passed,
                "validation_warning": validation_warning,
                "patterns_detected": [
                    {
                        "pattern": p["pattern"],
                        "description": p["description"],
                        "severity": p["severity"],
                    }
                    for p in patterns
                ],
                "tokens_used": {
                    "prompt": total_prompt_tokens,
                    "completion": total_completion_tokens,
                    "total": total_tokens_used,
                    "paso_1_tokens": 0,  # V4+: Determinístico, sin LLM
                    "paso_2_tokens": narrative_response.usage.total_tokens,
                },
                "model": narrative_response.model,
                "cost_estimate_usd": total_tokens_used
                * 0.00003,  # GPT-4: $0.03/1K tokens
                "generated_at": datetime.now().isoformat(),
                "architecture_version": "v6.2_trade_analysis",  # V6.2: Análisis de intercambios y secuencias
            }

            print(
                f"✅ Informe generado exitosamente (ARQUITECTURA V6.2: Trade Sequence Analysis)"
            )
            print(
                f"   Tokens usados (paso 1): 0 (determinístico, sin LLM)"
            )
            print(f"   Tokens usados (paso 2): {narrative_response.usage.total_tokens}")
            print(
                f"   Tokens totales: {result['tokens_used']['total']}"
            )
            print(f"   Costo estimado: ${result['cost_estimate_usd']:.4f}")
            print(
                f"   Engine decisive move: #{competitive_context.get('engine_analysis', {}).get('engine_decisive_move_chess')}"
            )
            print(f"   Top swings filtrados: {len(facts_pack.get('top_swings', []))} (|delta| >= 50 cp)")
            print(
                f"   Validación JSON: {'✅ PASSED' if validation_passed else '❌ FAILED'}"
            )

            return result

        except Exception as e:
            print(f"❌ Error generando informe LLM: {str(e)}")
            raise

    async def generate_batch_reports(
        self, db: Session, game_ids: list[str], player_elo: int, username: str
    ) -> list[Dict]:
        """
        Genera informes para múltiples partidas en batch

        Args:
            db: Sesión de base de datos
            game_ids: Lista de IDs de juegos
            player_elo: Rating ELO del jugador
            username: Usuario que solicita el análisis

        Returns:
            Lista de informes generados
        """
        reports = []

        for i, game_id in enumerate(game_ids, 1):
            print(f"\n{'='*60}")
            print(f"🎯 Procesando game {i}/{len(game_ids)}: {game_id[:12]}...")
            print(f"{'='*60}")

            try:
                report = await self.generate_pedagogical_report(
                    db=db, game_id=game_id, player_elo=player_elo, username=username
                )
                reports.append(report)

            except Exception as e:
                print(f"⚠️ Error en game {game_id}: {str(e)}")
                reports.append(
                    {"game_id": game_id, "error": str(e), "status": "failed"}
                )

        # Resumen final
        successful = sum(1 for r in reports if "error" not in r)
        total_cost = sum(
            r.get("cost_estimate_usd", 0) for r in reports if "cost_estimate_usd" in r
        )
        total_tokens = sum(
            r.get("tokens_used", {}).get("total", 0)
            for r in reports
            if "tokens_used" in r
        )

        print(f"\n{'='*60}")
        print(f"📊 RESUMEN BATCH")
        print(f"{'='*60}")
        print(f"✅ Exitosos: {successful}/{len(game_ids)}")
        print(f"💰 Costo total: ${total_cost:.4f}")
        print(f"🔢 Tokens totales: {total_tokens:,}")
        print(f"{'='*60}\n")

        return reports
