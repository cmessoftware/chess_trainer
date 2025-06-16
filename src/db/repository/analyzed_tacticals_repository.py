# /app/src/db/repository/Features_repository.py

import datetime
import logging
import pandas as pd
from sqlalchemy import insert
from db.models.analyzed_tacticals import Analyzed_tacticals
from db.db_utils import DBUtils
from db.session import get_session

logger = logging.getLogger(__name__)


class Analyzed_tacticalsRepository:
    def __init__(self, session_factory=get_session):
        self.session_factory = session_factory
        self.session = self.session_factory()
        self.db_utils = DBUtils()

    def get_all(self):
        return self.session.query(Analyzed_tacticals).all()

    def get_by_game_id(self, game_id):
        return self.session.query(Analyzed_tacticals).filter(Analyzed_tacticals.game_id == game_id).all()

    def get_by_game_and_move(self, game_id, move_number):
        return self.session.query(Analyzed_tacticals).filter_by(game_id=game_id, move_number=move_number).first()

    def add_Tacticals(self, tacticals: Analyzed_tacticals):
        self.session.add(tacticals)
        self.session.commit()

    def delete_by_game_id(self, game_id):
        self.session.query(Analyzed_tacticals).filter_by(
            game_id=game_id).delete()
        self.session.commit()

    def update_Features(self, tacticals_id, **kwargs):
        self.session.query(Analyzed_tacticals).filter_by(
            id=tacticals_id).update(kwargs)
        self.session.commit()

    def save_analyzed_tactical_hash(self, game_id: str):
        existing = self.session.query(
            Analyzed_tacticals).filter_by(game_id=game_id).first()
        if existing:
            logger.info(
                f"⏭️ Game {game_id} ya fue analizado, omitiendo inserción.")
            return

        try:
            analyzed_tactical_row = Analyzed_tacticals(
                game_id=game_id,
                date_analyzed=datetime.datetime.utcnow()
            )
            self.session.add(analyzed_tactical_row)
            self.session.commit()
            logger.info(f"✅ Análisis guardado para game_id {game_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"❌ Error al insertar análisis táctico para {game_id}: {e}")
            raise
