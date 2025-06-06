from typing import Dict, List
import chess.pgn
import io
from pathlib import Path
import hashlib
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.environ.get("CHESS_TRAINER_DB")


# 🔁 Cargar desde string PGN
def load_pgn_from_string(pgn_str):
    return chess.pgn.read_game(io.StringIO(pgn_str))

# 📄 Cargar primer juego de un archivo
def load_pgn_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return chess.pgn.read_game(f)

# 📄📄 Cargar todos los juegos de un archivo
def load_multiple_games_from_file(path):
    games = []
    with open(path, "r", encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            games.append(game)
    return games

def get_game_hash(game):
    """
    Genera un hash único para una partida PGN.
    Incluye headers y movimientos para evitar reprocesar duplicados.
    """
    headers = "".join(f"{k}:{v}" for k, v in sorted(game.headers.items()))
    moves = " ".join(move.uci() for move in game.mainline_moves())
    game_str = headers + moves
    return hashlib.sha256(game_str.encode("utf-8")).hexdigest()

#Cargas las partidas desde una base de datos

def load_all_games_from_db():
    if not DB_PATH or not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"❌ No se encontró la base de datos: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT pgn FROM games")
    rows = cursor.fetchall()
    conn.close()

    all_games = []
    for pgn_str, in rows:
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if game:
            all_games.append(game)
    
    if not all_games:
        print("❌ No se encontraron partidas en la base de datos.")
        return []
    # Verificar si se cargaron partidas
    print(f"🔍 Cargadas {len(all_games)} partidas desde la base de datos.")
    return all_games



# 📁📄📄 Cargar todos los juegos de todos los .pgn en una carpeta
def load_all_games_from_dir(directory):
    all_games = []
    pgn_files = Path(directory).rglob("*.pgn")
    for pgn_path in sorted(pgn_files):
        games = load_multiple_games_from_file(pgn_path)
        all_games.extend(games)
    
    print(f"🔍 Cargados {len(all_games)} juegos de {directory}")
    return all_games

# 🧠 Compatibilidad con el viejo nombre
def parse_pgn_file(path):
    return load_multiple_games_from_file(path)


def pgn_to_position_sequence(pgn_text: str, critical_fens: List[str] = None) -> List[Dict]:
    """
    Convierte un PGN en una secuencia de posiciones con FENs y marca las críticas.

    :param pgn_text: Contenido completo del PGN como string
    :param critical_fens: Lista opcional de FENs consideradas críticas
    :return: Lista de diccionarios con 'fen', 'comment' y 'is_critical'
    """
    critical_fens = set(critical_fens or [])
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()
    position_sequence = []

    for move in game.mainline_moves():
        fen_before_move = board.fen()
        is_critical = fen_before_move in critical_fens
        position_sequence.append({
            "fen": fen_before_move,
            "comment": "",
            "is_critical": is_critical
        })
        board.push(move)

    # Agregar la posición final si se desea
    position_sequence.append({
        "fen": board.fen(),
        "comment": "",
        "is_critical": board.fen() in critical_fens
    })

    return position_sequence


# 📝 Extraer posiciones (FENs) de todas las jugadas
def load_pgn_positions(path):
    positions = []
    with open(path, 'r') as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                positions.append(board.fen())
    return positions

# 🔄 Serializar a string PGN
def game_to_string(game):
    out = io.StringIO()
    print(game, file=out)
    return out.getvalue()

# 💾 Guardar juego PGN a archivo
def save_game_to_file(game, path):
    with open(path, "w", encoding="utf-8") as f:
        print(game, file=f)

def count_mainline_moves(game):
    return len(list(game.mainline_moves()))

def count_all_moves_with_variants(game):
    def recursive_count(node):
        count = len(node.variations)
        for variation in node.variations:
            count += recursive_count(variation)
        return count

    return recursive_count(game)

import chess.pgn

def extract_all_moves_with_variants(game):
    moves = []

    def recurse(node, move_number=1, variant_depth=0, board=None):
        if board is None:
            board = node.board()

        for var in node.variations:
            new_board = board.copy()
            new_board.push(var.move)
            moves.append({
                "move_number": move_number,
                "variant_depth": variant_depth,
                "san": board.san(var.move),
                "uci": var.move.uci(),
                "fen": board.fen()
            })
            recurse(var, move_number + 1, variant_depth + 1, new_board)

    recurse(game)
    return moves

def get_game_headers(game):
    headers = {}
    for key, value in game.headers.items():
        headers[key] = value
    return headers
