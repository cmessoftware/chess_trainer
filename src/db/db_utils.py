# db_utils_sqlalchemy.py
from io import StringIO
import chess
import pandas as pd
from sqlalchemy.dialects import postgresql
import hashlib
import os
from sqlalchemy import (
    Engine, Select, create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import dotenv

from db.models.games import Games
from db.models.processed_games import Processed_games

dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class DBUtils:
    @staticmethod
    def init_db():
        Base.metadata.create_all(engine)

    @staticmethod
    def compute_game_id(game):
        return hashlib.md5(str(game).encode('utf-8')).hexdigest()

    @staticmethod
    def is_game_in_db(game_id):
        with Session() as session:
            return session.query(Games).filter_by(game_id=game_id).first() is not None

    @staticmethod
    def get_game_by_id(game_id):
        with Session() as session:
            game = session.query(Games).filter_by(game_id=game_id).first()
            if game:
                return {c.name: getattr(game, c.name) for c in Game.__table__.columns}
            return None

    @staticmethod
    def was_game_already_processed(game_hash):
        with Session() as session:
            return session.query(Processed_games).filter_by(game_id=game_hash).first() is not None

    @staticmethod
    def mark_game_as_processed(game_hash):
        with Session() as session:
            if not session.query(Processed_games).filter_by(game_id=game_hash).first():
                session.add(Processed_games(game_id=game_hash))
                session.commit()

    def process_game_from_db(self, game):
        print(
            f"Procesando juego desde la base de datos... {game.headers.get('White', 'Desconocido')} vs {game.headers.get('Black', 'Desconocido')}")
        rows = []
        pgn_io = StringIO()
        game.accept(chess.pgn.StringExporter(
            headers=True, variations=True, comments=True))
        pgn_str = str(game)
        # Debe ser una función que genere el hash único
        game_id = self.get_game_id(game)
        features = self.extract_features(game, game_id)
        rows.append(features)

        if not rows:
            print("⚠️ No se extrajeron features.")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        return df

    def get_game_id(self, game):
        # Lógica para generar el hash único o identificador del juego
        # Usualmente basado en PGN o metadatos clave
        exporter = chess.pgn.StringExporter(
            headers=True, variations=False, comments=False)
        pgn_str = game.accept(exporter)
        import hashlib
        return hashlib.sha256(pgn_str.encode("utf-8")).hexdigest()

    def extract_features(self, game, game_id):
        # Extrae features básicas como ejemplo
        return {
            "game_id": game_id,
            "site": game.headers.get("Site", ""),
            "event": game.headers.get("Event", ""),
            "date": game.headers.get("Date", ""),
            "white_player": game.headers.get("White", ""),
            "black_player": game.headers.get("Black", ""),
            "result": game.headers.get("Result", ""),
            "num_moves": len(list(game.mainline_moves()))
        }

    @staticmethod
    def print_sql_query(statement: Select, engine: Engine = None, show_params: bool = True):
        """
        Imprime la consulta SQL generada por SQLAlchemy.

        Args:
            statement (Select): El objeto de consulta SQLAlchemy.
            engine (Engine, optional): Motor de SQLAlchemy (para dialecto y binding).
            show_params (bool): Si se deben mostrar los parámetros por separado.

        Ejemplo:
            stmt = select(Games.game_id).where(Games.result == '1-0')
            print_sql_query(stmt, engine)
        """
        dialect = postgresql.dialect()
        if engine:
            compiled = statement.compile(engine, compile_kwargs={
                                         "literal_binds": not show_params})
        else:
            compiled = statement.compile(dialect=dialect, compile_kwargs={
                                         "literal_binds": not show_params})

        print("🔎 SQL generado:")
        print(compiled)

        if show_params:
            print("🧾 Parámetros:")
            print(compiled.params)
