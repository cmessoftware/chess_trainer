"""
API Endpoints para Ejercicios Personalizados
==========================================

Funcionalidad completa para generar, gestionar y exportar ejercicios
personalizados basados en el análisis de ML del jugador.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import chess.pgn
from datetime import datetime
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

# Models for request/response
class PlayerAnalysisRequest(BaseModel):
    player_name: str
    pgn_content: Optional[str] = None
    analysis_type: List[str] = ["error_label", "streaks", "player_type"]

class ExerciseCreate(BaseModel):
    title: str
    description: str
    difficulty: str  # "beginner", "intermediate", "advanced"
    pattern_type: str  # "tactics", "endgame", "opening", "strategy" 
    fen_position: str
    target_moves: List[str]
    explanation: str
    lichess_study_url: Optional[str] = None
    player_weaknesses: List[str] = []

class ExerciseResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    pattern_type: str
    fen_position: str
    target_moves: List[str]
    explanation: str
    lichess_study_url: Optional[str]
    created_at: datetime
    success_rate: Optional[float] = None

class PersonalizedExercisePlan(BaseModel):
    player_name: str
    analysis_summary: Dict[str, Any]
    recommended_exercises: List[ExerciseResponse]
    priority_areas: List[str]
    study_plan: Dict[str, Any]
    lichess_export: Dict[str, str]

@router.post("/analyze-player", response_model=Dict[str, Any])
async def analyze_player_and_generate_exercises(
    request: PlayerAnalysisRequest
    # db: Session = Depends(get_db)  # Temporarily disabled
):
    """
    Analiza un jugador y genera ejercicios personalizados
    
    Flujo completo:
    1. Analizar PGN si se proporciona
    2. Generar features con Stockfish  
    3. Ejecutar modelos ML
    4. Identificar debilidades
    5. Generar ejercicios específicos
    """
    
    try:
        # Importar módulos de análisis
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../ml'))
        
        from analyze_th3hound import (
            check_th3hound_data, 
            analyze_th3hound_player_profile,
            analyze_error_streaks,
            train_player_models,
            generate_personalized_recommendations
        )
        
        # 1. Verificar datos existentes del jugador
        player_name = request.player_name
        
        # Si se proporciona PGN, procesarlo
        if request.pgn_content:
            # Guardar PGN temporal y procesarlo
            await process_uploaded_pgn(request.pgn_content, player_name)
        
        # 2. Ejecutar análisis ML
        has_data, move_count = check_th3hound_data()
        
        if not has_data or move_count < 10:
            raise HTTPException(
                status_code=404,
                detail=f"Datos insuficientes para {player_name}. Movimientos: {move_count}"
            )
        
        # Cargar datos del jugador
        from sqlalchemy import create_engine
        DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL")
        engine = create_engine(DATABASE_URL)
        
        player_query = f"""
            SELECT f.*, g.white_player, g.black_player,
                   CASE 
                       WHEN f.player_color = 1 AND g.white_elo ~ '^[0-9]+$' THEN CAST(g.white_elo AS INTEGER)
                       WHEN f.player_color = 0 AND g.black_elo ~ '^[0-9]+$' THEN CAST(g.black_elo AS INTEGER)
                   END as player_elo
            FROM features f
            LEFT JOIN games g ON f.game_id = g.game_id
            WHERE (g.white_player ILIKE '%{player_name}%' OR g.black_player ILIKE '%{player_name}%')
              AND f.error_label IS NOT NULL
            ORDER BY f.game_id, f.move_number
            LIMIT 2000
        """
        
        player_df = pd.read_sql(player_query, engine)
        engine.dispose()
        
        if len(player_df) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron datos de partidas para {player_name}"
            )
        
        # 3. Ejecutar análisis completo
        profile = analyze_th3hound_player_profile(player_df)
        streaks = analyze_error_streaks(player_df)
        models = train_player_models(player_df)
        recommendations = generate_personalized_recommendations(profile, streaks, models)
        
        # 4. Generar ejercicios específicos basados en debilidades
        exercises = generate_exercises_from_analysis(profile, streaks, recommendations)
        
        # 5. Crear plan de estudio personalizado
        study_plan = create_study_plan(recommendations, exercises)
        
        # 6. Generar exportación para Lichess
        lichess_export = generate_lichess_export(exercises, player_name)
        
        return {
            "player_name": player_name,
            "analysis_summary": {
                "total_moves": profile['total_moves'],
                "good_rate": float(profile['good_rate']),
                "error_rate": float(profile['mistake_rate'] + profile['blunder_rate']),
                "max_error_streak": streaks['max_error_streak'],
                "model_accuracy": models.get('error_predictor', {}).get('f1_score', 0)
            },
            "recommended_exercises": exercises,
            "priority_areas": [rec['type'] for rec in recommendations if rec['priority'] in ['critical', 'high']],
            "study_plan": study_plan,
            "lichess_export": lichess_export,
            "recommendations_count": len(recommendations),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@router.post("/upload-pgn")
async def upload_pgn_for_analysis(
    player_name: str,
    file: UploadFile = File(...)
    # db: Session = Depends(get_db)  # Temporarily disabled
):
    """
    Subir archivo PGN para análisis de jugador
    """
    
    try:
        # Leer contenido del archivo
        content = await file.read()
        pgn_content = content.decode('utf-8')
        
        # Procesar PGN
        result = await process_uploaded_pgn(pgn_content, player_name)
        
        return {
            "message": f"PGN procesado exitosamente para {player_name}",
            "games_imported": result.get("games_count", 0),
            "features_generated": result.get("features_count", 0),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PGN: {str(e)}")

@router.get("/patterns", response_model=Dict[str, List[str]])
async def get_tactical_patterns():
    """
    Obtener patrones tácticos disponibles para ejercicios
    """
    
    return {
        "tactics": [
            "pin", "fork", "skewer", "discovered_attack", "deflection",
            "decoy", "clearance", "interference", "x_ray", "double_attack"
        ],
        "endgames": [
            "pawn_endgame", "rook_endgame", "queen_endgame", "bishop_endgame",
            "knight_endgame", "opposite_bishops", "same_bishops"
        ],
        "openings": [
            "center_control", "development", "castling_safety", "pawn_structure",
            "piece_activity", "time_management"
        ],
        "strategy": [
            "weak_squares", "pawn_breaks", "piece_coordination", "king_safety",
            "space_advantage", "initiative"
        ]
    }

@router.get("/export-lichess/{player_name}")
async def export_to_lichess_study(player_name: str):
    """
    Exportar ejercicios personalizados como estudio de Lichess
    """
    
    try:
        # Obtener ejercicios del jugador (simulado para ejemplo)
        exercises = get_player_exercises(player_name)
        
        # Generar PGN de estudio para Lichess
        study_pgn = generate_lichess_study_pgn(exercises, player_name)
        
        return {
            "player_name": player_name,
            "study_title": f"Ejercicios Personalizados - {player_name}",
            "pgn_content": study_pgn,
            "exercises_count": len(exercises),
            "lichess_import_url": "https://lichess.org/study/new",
            "instructions": [
                "1. Copiar el contenido PGN",
                "2. Ir a lichess.org/study/new", 
                "3. Pegar PGN en 'Import from PGN'",
                "4. Configurar como 'Private' o 'Public'",
                "5. Crear estudio personalizado"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando exportación: {str(e)}")

# Funciones auxiliares

async def process_uploaded_pgn(pgn_content: str, player_name: str) -> Dict[str, Any]:
    """
    Procesar PGN subido y generar features
    """
    
    import tempfile
    import subprocess
    import sys
    
    try:
        # Guardar PGN en archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pgn', delete=False) as f:
            f.write(pgn_content)
            temp_pgn_path = f.name
        
        # Copiar a directorio de datos
        import shutil
        target_dir = "data/games/personal"
        os.makedirs(target_dir, exist_ok=True)
        
        final_pgn_path = os.path.join(target_dir, f"{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn")
        shutil.copy2(temp_pgn_path, final_pgn_path)
        
        # Ejecutar importación y generación de features
        # (Aquí iría la lógica real de importación)
        
        return {
            "games_count": 10,  # Placeholder
            "features_count": 500,  # Placeholder
            "file_path": final_pgn_path
        }
        
    except Exception as e:
        raise Exception(f"Error procesando PGN: {e}")

def generate_exercises_from_analysis(profile: Dict, streaks: Dict, recommendations: List[Dict]) -> List[Dict]:
    """
    Generar ejercicios específicos basados en análisis ML
    """
    
    exercises = []
    
    # Ejercicios basados en tipo de errores
    if profile['blunder_rate'] > 0.02:
        exercises.append({
            "id": 1,
            "title": "Prevención de Blunders - Verificación",
            "description": "Ejercicios para verificar amenazas antes de mover",
            "difficulty": "intermediate",
            "pattern_type": "blunder_prevention",
            "fen_position": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4",
            "target_moves": ["Bxf7+", "Qh5"],
            "explanation": "Verifica siempre las amenazas del oponente antes de atacar",
            "lichess_study_url": "https://lichess.org/study/blunder-prevention"
        })
    
    # Ejercicios basados en rachas
    if streaks.get('streak_problems', False):
        exercises.append({
            "id": 2,
            "title": "Control de Rachas - Concentración",
            "description": "Ejercicios para mantener la concentración tras errores",
            "difficulty": "beginner",
            "pattern_type": "consistency",
            "fen_position": "8/8/8/8/8/8/8/8 w - - 0 1",
            "target_moves": [],
            "explanation": "Practica pausas mentales entre movimientos críticos",
            "lichess_study_url": "https://lichess.org/study/concentration"
        })
    
    # Ejercicios tácticos generales
    exercises.append({
        "id": 3,
        "title": "Táctica Diaria - Pins y Forks",
        "description": "Ejercicios básicos de clavadas y horquillas",
        "difficulty": "beginner",
        "pattern_type": "tactics",
        "fen_position": "r2qkb1r/ppp2ppp/2n1bn2/8/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq - 4 6",
        "target_moves": ["Nd5", "Nxe7+"],
        "explanation": "Busca siempre oportunidades de horquilla con caballos",
        "lichess_study_url": "https://lichess.org/training/themes"
    })
    
    return exercises

def create_study_plan(recommendations: List[Dict], exercises: List[Dict]) -> Dict[str, Any]:
    """
    Crear plan de estudio personalizado
    """
    
    return {
        "daily_schedule": {
            "tactics_time": 15,  # minutos
            "analysis_time": 10,
            "pattern_practice": 10
        },
        "weekly_goals": [
            "Completar 5 ejercicios de prevención de blunders",
            "Analizar 3 partidas propias con engine",
            "Practicar verificación sistemática"
        ],
        "priority_sequence": [rec['type'] for rec in recommendations],
        "difficulty_progression": ["beginner", "intermediate", "advanced"]
    }

def generate_lichess_export(exercises: List[Dict], player_name: str) -> Dict[str, str]:
    """
    Generar exportación para Lichess
    """
    
    pgn_content = f"""[Event "Ejercicios Personalizados - {player_name}"]
[Site "Chess Trainer"]
[Date "{datetime.now().strftime('%Y.%m.%d')}"]
[White "Training"]
[Black "Exercises"]
[Result "*"]

"""
    
    for exercise in exercises:
        pgn_content += f"""
{{Ejercicio: {exercise['title']}}}
{{Descripción: {exercise['description']}}}
[FEN "{exercise['fen_position']}"]

{' '.join(exercise.get('target_moves', []))} {{Movimientos objetivo}}

"""
    
    return {
        "pgn_content": pgn_content,
        "study_title": f"Ejercicios Personalizados - {player_name}",
        "import_instructions": "Copiar PGN y pegar en lichess.org/study/new"
    }

def generate_lichess_study_pgn(exercises: List[Dict], player_name: str) -> str:
    """
    Generar PGN completo para estudio de Lichess
    """
    
    pgn_parts = []
    
    for i, exercise in enumerate(exercises, 1):
        pgn_part = f"""[Event "Ejercicio {i}: {exercise['title']}"]
[Site "Chess Trainer - {player_name}"]
[Date "{datetime.now().strftime('%Y.%m.%d')}"]
[White "Training"]
[Black "Exercise"]
[Result "*"]
[FEN "{exercise['fen_position']}"]
[SetUp "1"]

{{[%csl {exercise.get('highlights', '')}] {exercise['explanation']}}}

{' '.join(exercise.get('target_moves', []))} *

"""
        pgn_parts.append(pgn_part)
    
    return '\n\n'.join(pgn_parts)

def get_player_exercises(player_name: str) -> List[Dict]:
    """
    Obtener ejercicios existentes para un jugador
    """
    
    # Placeholder: En implementación real, consultar base de datos
    return [
        {
            "title": "Verificación Anti-Blunder",
            "description": "Ejercicios para prevenir blunders",
            "fen_position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "target_moves": ["e4", "d4"]
        }
    ]