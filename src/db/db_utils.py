# db_utils_sqlalchemy.py
from sqlalchemy.dialects import postgresql
import hashlib
import os
from sqlalchemy import (
    Engine, Select, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import dotenv

from db.models.games import Games
from db.models.processed_features import Processed_features

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
                return {c.name: getattr(game, c.name) for c in Games.__table__.columns}
            return None

    @staticmethod
    def was_game_already_processed(game_hash):
        with Session() as session:
            return session.query(Processed_features).filter_by(game_id=game_hash).first() is not None

    @staticmethod
    def mark_game_as_processed(game_hash):
        with Session() as session:
            if not session.query(Processed_features).filter_by(game_id=game_hash).first():
                session.add(Processed_features(game_id=game_hash))
                session.commit()

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
