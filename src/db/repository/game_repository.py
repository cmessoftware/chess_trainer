# db/repository/game_repository.py

from io import StringIO
import os
import sqlite3
from pathlib import Path
import chess
import dotenv

from db.db_utils import get_game_id_by_game
dotenv.load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB", "data/chess_trainer.db")


class GameRepository:
    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_all_games(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pgn FROM games")
            rows = cursor.fetchall()
        
        games = []
        for (pgn_text,) in rows:
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is not None:
                games.append(game)

        return games
    
     
    def get_games_not_analyzed(self, analyzed_hashes: set):
        """
        Devuelve partidas cuya ID (hash) no esté en analyzed_hashes.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            placeholder = ','.join('?' for _ in analyzed_hashes) or "''"
            query = f"SELECT game_id, pgn FROM games WHERE game_id NOT IN ({placeholder})"
            cursor.execute(query, tuple(analyzed_hashes))
            rows =  cursor.fetchall()
        
        games = []
        for (pgn_text,) in rows:
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is not None:
                games.append(game)

        return games
    
    def get_game_by_id(self, game_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT game_id, pgn FROM games WHERE game_id = ?", (game_id,))
            return cursor.fetchone()
        
    def get_game_id_by_game(self, game):
        """
        Obtiene el ID de una partida dada.
        """
        game_hash = get_game_id_by_game(game)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT game_id FROM games WHERE game_id = ?", (game_hash,))
            row = cursor.fetchone()
            return row[0] if row else None
