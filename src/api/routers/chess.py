from fastapi import APIRouter, HTTPException, Request, Query
from models.schemas import (
    GameResponse,
    GamesListResponse,
    AnalysisRequest,
    AnalysisResponse,
    MoveValidationRequest,
    MoveValidationResponse,
)
from services.chess_service import ChessService
from typing import Optional
import logging

router = APIRouter()

# Instancia del servicio de ajedrez
chess_service = ChessService()


@router.get("/games", response_model=GamesListResponse)
async def get_games_list(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    Obtener lista de partidas con paginación y filtros
    Usuarios no-admin solo ven partidas donde son jugadores
    """
    # Obtener usuario desde request.state (viene del middleware JWT)
    user = getattr(request.state, "user", {})
    username = user.get("username", "")
    roles = user.get("roles", [])

    logging.info(f"Usuario {username} (roles: {roles}) solicitando lista de partidas")

    # Determinar si el usuario necesita filtro
    # Admin y analyst pueden ver todas las partidas
    # Analyst tiene permisos como 'stats_viewer' o 'analysis_board'
    user_filter = None
    is_admin_or_analyst = (
        "admin" in roles or "stats_viewer" in roles or "analysis_board" in roles
    )

    if not is_admin_or_analyst:
        # Usuarios básicos solo ven sus propias partidas
        user_filter = username
        logging.info(f"Aplicando filtro de usuario: {user_filter}")
    else:
        logging.info(f"Usuario {username} puede ver TODAS las partidas (admin/analyst)")

    try:
        games_data = await chess_service.get_games_list(
            limit=limit,
            offset=offset,
            source=source,
            search=search,
            user_filter=user_filter,
        )
        return GamesListResponse(**games_data)
    except Exception as e:
        logging.error(f"Error obteniendo lista de partidas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/games/sources")
async def get_game_sources(request: Request):
    """
    Obtener todas las fuentes de partidas disponibles
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(f"Usuario {user['username']} solicitando fuentes de partidas")

    try:
        sources = await chess_service.get_sources()
        return {"sources": sources}
    except Exception as e:
        logging.error(f"Error obteniendo fuentes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, request: Request):
    """
    Obtener una partida específica por ID
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(f"Usuario {user['username']} solicitando partida {game_id}")

    try:
        game = await chess_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        return game
    except Exception as e:
        logging.error(f"Error obteniendo partida {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/games/{game_id}/moves")
async def get_game_moves(game_id: str, request: Request):
    """
    Obtener los movimientos de una partida
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(
        f"Usuario {user['username']} solicitando movimientos de partida {game_id}"
    )

    try:
        moves = await chess_service.get_game_moves(game_id)
        return {"game_id": game_id, "moves": moves}
    except Exception as e:
        logging.error(f"Error obteniendo movimientos de partida {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo movimientos")


@router.post("/position-analysis", response_model=AnalysisResponse)
async def analyze_position(analysis_request: AnalysisRequest, request: Request):
    """
    Analizar una posición de ajedrez usando el motor
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(f"Usuario {user['username']} solicitando análisis de posición")

    # Verificar permisos (solo admin y analista pueden usar el análisis)
    if user["role"] not in ["admin", "analista"]:
        raise HTTPException(status_code=403, detail="Sin permisos para análisis")

    try:
        analysis = await chess_service.analyze_position(
            analysis_request.fen, analysis_request.depth
        )
        return analysis
    except Exception as e:
        logging.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail="Error en el análisis")


@router.post("/validate-move", response_model=MoveValidationResponse)
async def validate_move_simple(move_request: MoveValidationRequest, request: Request):
    """
    Validar un movimiento de ajedrez (versión simple)
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(f"Usuario {user['username']} validando movimiento")

    try:
        validation = await chess_service.validate_move_simple(move_request.move)
        return validation
    except Exception as e:
        logging.error(f"Error validando movimiento: {e}")
        raise HTTPException(status_code=500, detail="Error validando movimiento")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_position(analysis_request: AnalysisRequest, request: Request):
    """
    Analizar una posición de ajedrez usando el motor
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(f"Usuario {user['username']} solicitando análisis de posición")

    # Verificar permisos (solo admin y analista pueden usar el análisis)
    if user["role"] not in ["admin", "analista"]:
        raise HTTPException(status_code=403, detail="Sin permisos para análisis")

    try:
        analysis = await chess_service.analyze_position(
            analysis_request.fen, analysis_request.depth
        )
        return analysis
    except Exception as e:
        logging.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail="Error en el análisis")


@router.post("/games/{game_id}/validate-move", response_model=MoveValidationResponse)
async def validate_move(
    game_id: int, move_request: MoveValidationRequest, request: Request
):
    """
    Validar un movimiento en una partida específica
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})
    logging.info(
        f"Usuario {user['username']} validando movimiento en partida {game_id}"
    )

    try:
        validation = await chess_service.validate_move(game_id, move_request.move)
        return validation
    except Exception as e:
        logging.error(f"Error validando movimiento: {e}")
        raise HTTPException(status_code=500, detail="Error validando movimiento")


# =======================================
# ENDPOINTS TEMPORALES PARA TESTING SIN AUTH
# =======================================


@router.get("/test/games/{game_id}", response_model=GameResponse)
async def get_game_no_auth(game_id: int):
    """
    Endpoint temporal para testing - Obtener partida sin autenticación
    """
    logging.info(f"[TEST] Solicitando partida {game_id} sin autenticación")

    try:
        game = await chess_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        return game
    except Exception as e:
        logging.error(f"Error obteniendo partida {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/test/analyze", response_model=AnalysisResponse)
async def analyze_position_no_auth(analysis_request: AnalysisRequest):
    """
    Endpoint temporal para testing - Análisis sin autenticación
    """
    logging.info(f"[TEST] Solicitando análisis sin autenticación")

    try:
        analysis = await chess_service.analyze_position(
            analysis_request.fen, analysis_request.depth
        )
        return analysis
    except Exception as e:
        logging.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail="Error en el análisis")
