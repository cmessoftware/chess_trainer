# db_utils_sqlalchemy.py

import hashlib
import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
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
