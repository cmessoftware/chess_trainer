from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import math

# Crear la aplicación FastAPI
app = FastAPI(
    title="Chess Trainer API - Basic",
    description="API básica para testing",
    version="1.0.0",
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos simulados de partidas para testing
SAMPLE_GAMES = [
    {
        "id": 1,
        "white": "Magnus Carlsen",
        "black": "Hikaru Nakamura",
        "result": "1-0",
        "event": "Online Championship",
        "date": "2024-01-15",
        "eco": "E90",
        "white_elo": 2831,
        "black_elo": 2780,
        "round": 1,
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7"],
    },
    {
        "id": 2,
        "white": "Garry Kasparov",
        "black": "Anatoly Karpov",
        "result": "1/2-1/2",
        "event": "World Championship",
        "date": "1984-09-10",
        "eco": "D85",
        "white_elo": 2715,
        "black_elo": 2700,
        "round": 5,
        "moves": ["d4", "Nf6", "c4", "g6", "Nc3", "d5", "cxd5", "Nxd5"],
    },
    {
        "id": 3,
        "white": "Bobby Fischer",
        "black": "Boris Spassky",
        "result": "1-0",
        "event": "World Championship",
        "date": "1972-07-11",
        "eco": "B44",
        "white_elo": 2785,
        "black_elo": 2660,
        "round": 6,
        "moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6"],
    },
    {
        "id": 4,
        "white": "Viswanathan Anand",
        "black": "Vladimir Kramnik",
        "result": "0-1",
        "event": "Candidates Tournament",
        "date": "2014-03-18",
        "eco": "A05",
        "white_elo": 2770,
        "black_elo": 2787,
        "round": 3,
        "moves": ["Nf3", "Nf6", "g3", "g6", "Bg2", "Bg7", "O-O", "O-O"],
    },
    {
        "id": 5,
        "white": "Fabiano Caruana",
        "black": "Ding Liren",
        "result": "1/2-1/2",
        "event": "FIDE Grand Prix",
        "date": "2022-10-05",
        "eco": "C43",
        "white_elo": 2783,
        "black_elo": 2806,
        "round": 7,
        "moves": ["e4", "e5", "Nf3", "Nf6", "d4", "Nxe4", "Bd3", "d5"],
    },
    {
        "id": 6,
        "white": "Wesley So",
        "black": "Levon Aronian",
        "result": "1-0",
        "event": "Sinquefield Cup",
        "date": "2021-08-22",
        "eco": "D37",
        "white_elo": 2772,
        "black_elo": 2781,
        "round": 4,
        "moves": ["d4", "Nf6", "c4", "e6", "Nf3", "d5", "Nc3", "Be7"],
    },
]


@app.get("/games/search")
async def search_games(
    search: str = Query("", description="Término de búsqueda"),
    page: int = Query(1, description="Número de página", ge=1),
    page_size: int = Query(25, description="Elementos por página", ge=1, le=100),
    white: str = Query("", description="Filtro por jugador blancas"),
    black: str = Query("", description="Filtro por jugador negras"),
    event: str = Query("", description="Filtro por evento"),
    eco: str = Query("", description="Filtro por código ECO"),
    result: str = Query("", description="Filtro por resultado"),
):
    """Búsqueda de partidas con filtros y paginación"""

    # Simular búsqueda filtrando los datos
    filtered_games = SAMPLE_GAMES.copy()

    # Aplicar filtros
    if search:
        search_lower = search.lower()
        filtered_games = [
            game
            for game in filtered_games
            if (
                search_lower in game["white"].lower()
                or search_lower in game["black"].lower()
                or search_lower in game["event"].lower()
                or search_lower in game["eco"].lower()
            )
        ]

    if white:
        white_lower = white.lower()
        filtered_games = [
            game for game in filtered_games if white_lower in game["white"].lower()
        ]

    if black:
        black_lower = black.lower()
        filtered_games = [
            game for game in filtered_games if black_lower in game["black"].lower()
        ]

    if event:
        event_lower = event.lower()
        filtered_games = [
            game for game in filtered_games if event_lower in game["event"].lower()
        ]

    if eco:
        eco_upper = eco.upper()
        filtered_games = [game for game in filtered_games if eco_upper in game["eco"]]

    if result:
        filtered_games = [game for game in filtered_games if game["result"] == result]

    # Paginación
    total = len(filtered_games)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    games_page = filtered_games[start_idx:end_idx]

    return JSONResponse(
        status_code=200,
        content={
            "games": games_page,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        headers={"Content-Type": "application/json"},
    )


@app.get("/games/{game_id}")
async def get_game_by_id(game_id: int):
    """Obtener partida por ID"""
    for game in SAMPLE_GAMES:
        if game["id"] == game_id:
            return JSONResponse(
                status_code=200,
                content=game,
                headers={"Content-Type": "application/json"},
            )

    return JSONResponse(
        status_code=404,
        content={"error": True, "message": "Partida no encontrada"},
        headers={"Content-Type": "application/json"},
    )


@app.get("/games/{game_id}/pgn")
async def get_game_pgn(game_id: int):
    """Obtener PGN de una partida"""
    for game in SAMPLE_GAMES:
        if game["id"] == game_id:
            pgn = f"""[Event "{game['event']}"]
[Date "{game['date']}"]
[White "{game['white']}"]
[Black "{game['black']}"]
[Result "{game['result']}"]
[WhiteElo "{game['white_elo']}"]
[BlackElo "{game['black_elo']}"]
[ECO "{game['eco']}"]

{' '.join(game['moves'])} {game['result']}"""

            return JSONResponse(
                status_code=200,
                content={"pgn": pgn},
                headers={"Content-Type": "application/json"},
            )

    return JSONResponse(
        status_code=404,
        content={"error": True, "message": "Partida no encontrada"},
        headers={"Content-Type": "application/json"},
    )


@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Chess Trainer API - ¡Bienvenido!",
            "version": "1.0.0",
            "status": "active",
            "docs": "/docs",
        },
        headers={"Content-Type": "application/json"},
    )


@app.get("/health")
async def health_check():
    """Endpoint de salud"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "chess-trainer-api"},
        headers={"Content-Type": "application/json"},
    )


@app.get("/favicon.ico")
async def favicon():
    """Endpoint para favicon (evita errores 404)"""
    return JSONResponse(
        status_code=200,
        content={"message": "No favicon available"},
        headers={"Content-Type": "application/json"},
    )


# Endpoints temporales de chess sin dependencias
@app.get("/chess/test/games/{game_id}")
async def get_game_test(game_id: int):
    """Endpoint temporal para testing - Obtener partida sin auth"""
    if game_id == 1:
        return JSONResponse(
            status_code=200,
            content={
                "game_id": 1,
                "white": "Magnus Carlsen",
                "black": "Hikaru Nakamura",
                "result": "1-0",
                "event": "Online Championship",
                "site": "chess.com",
                "date": "2024-01-15",
                "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"],
            },
            headers={"Content-Type": "application/json"},
        )
    elif game_id == 2:
        return JSONResponse(
            status_code=200,
            content={
                "game_id": 2,
                "white": "Garry Kasparov",
                "black": "Anatoly Karpov",
                "result": "1/2-1/2",
                "event": "World Championship",
                "site": "Moscow",
                "date": "1984-09-10",
                "moves": ["d4", "Nf6", "c4", "g6", "Nc3"],
            },
            headers={"Content-Type": "application/json"},
        )
    else:
        return JSONResponse(
            status_code=404,
            content={"error": True, "message": "Partida no encontrada"},
            headers={"Content-Type": "application/json"},
        )


# Endpoints de autenticación simulados
@app.post("/auth/login")
async def login_test(body: dict):
    """Endpoint temporal para login - Autenticación simulada"""
    username = body.get("username", "")
    password = body.get("password", "")

    # Usuarios hardcodeados para testing
    users = {
        "admin": {"password": "admin123", "role": "admin", "user_id": 1},
        "analista": {"password": "analista123", "role": "analista", "user_id": 2},
        "usuario": {"password": "usuario123", "role": "usuario", "user_id": 3},
    }

    if username in users and users[username]["password"] == password:
        return JSONResponse(
            status_code=200,
            content={
                "access_token": f"fake-jwt-token-{username}-{hash(username)}",
                "token_type": "bearer",
                "user": {
                    "user_id": users[username]["user_id"],
                    "username": username,
                    "role": users[username]["role"],
                },
            },
            headers={"Content-Type": "application/json"},
        )
    else:
        return JSONResponse(
            status_code=401,
            content={"error": True, "message": "Credenciales inválidas"},
            headers={"Content-Type": "application/json"},
        )


@app.post("/auth/verify")
async def verify_token_test():
    """Endpoint temporal para verificar token - Siempre válido"""
    return JSONResponse(
        status_code=200,
        content={"valid": True, "message": "Token válido"},
        headers={"Content-Type": "application/json"},
    )


# Endpoints de chess que el frontend espera (además de los /test)
@app.get("/chess/games/{game_id}")
async def get_game_frontend(game_id: int):
    """Endpoint para que el frontend funcione - Redirige a test"""
    return await get_game_test(game_id)


@app.get("/chess/games/{game_id}/moves")
async def get_game_moves_frontend(game_id: int):
    """Endpoint para movimientos - Simulado"""
    if game_id == 1:
        return JSONResponse(
            status_code=200,
            content={"game_id": 1, "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"]},
            headers={"Content-Type": "application/json"},
        )
    elif game_id == 2:
        return JSONResponse(
            status_code=200,
            content={"game_id": 2, "moves": ["d4", "Nf6", "c4", "g6", "Nc3"]},
            headers={"Content-Type": "application/json"},
        )
    else:
        return JSONResponse(
            status_code=404,
            content={"error": True, "message": "Partida no encontrada"},
            headers={"Content-Type": "application/json"},
        )


@app.post("/chess/analyze")
async def analyze_frontend(body: dict):
    """Endpoint para análisis que el frontend espera"""
    return await analyze_test(body)


@app.post("/chess/games/{game_id}/validate-move")
async def validate_move_frontend(game_id: int, body: dict):
    """Endpoint para validar movimientos - Simulado"""
    move = body.get("move", "")
    valid_moves = ["e4", "d4", "Nf3", "Nc3", "Bd4"]

    return JSONResponse(
        status_code=200,
        content={
            "valid": move in valid_moves,
            "move": move if move in valid_moves else None,
            "message": (
                "Movimiento válido" if move in valid_moves else "Movimiento inválido"
            ),
        },
        headers={"Content-Type": "application/json"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main_basic:app", host="0.0.0.0", port=8000, reload=True)
