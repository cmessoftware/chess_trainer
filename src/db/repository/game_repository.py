# db/repository/game_repository.py

from io import StringIO
import os
from pathlib import Path
import chess
import dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select, not_
from db.db_utils import DBUtils
from db.models.games import Games  # Debes tener este modelo definido
from db.session import get_session  # Función que retorna una sesión SQLAlchemy

dotenv.load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB", "data/chess_trainer.db")


class GameRepository:
    def __init__(self, session_factory=get_session):
        self.session_factory = session_factory
        self.db_utils = DBUtils()

    def get_all_games(self):
        with self.session_factory() as session:
            engine = session.get_bind()
            stmt = select(Games)
            games = session.execute(stmt).scalars().all()
            self.db_utils.print_sql_query(stmt, engine)
            print(f"🔢 Total partidas recuperadas: {len(games)}")
            return games  # lista de objetos Games del ORM

    def get_games_not_analyzed(self, analyzed_hashes: set):
        """
        Devuelve partidas cuya ID (hash) no esté en analyzed_hashes.
        """
        with self.session_factory() as session:
            if analyzed_hashes:
                stmt = select(Games.pgn).where(
                    not_(Games.game_id.in_(analyzed_hashes)))
            else:
                stmt = select(Games.pgn)
            games_rows = session.execute(stmt).scalars().all()
        games = []
        for pgn_text in games_rows:
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is not None:
                games.append(game)
        return games

    def get_game_by_id(self, game_id):
        with self.session_factory() as session:
            row = session.execute(
                select(Games.game_id, Games.pgn).where(
                    Games.game_id == game_id)
            ).first()
            return row

    def get_game_id_by_game(self, game):
        """
        Obtiene el ID de una partida dada.
        """
        game_hash = self.db_utils.get_game_id_by_game(game)
        with self.session_factory() as session:
            row = session.execute(
                select(Games.game_id).where(Games.game_id == game_hash)
            ).first()
            return row[0] if row else None
