# /app/src/db/repository/Analyzed_tacticals.py

import logging
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

    def save_analyzed_tactical_hash(self, game_id):
        with self.session_factory() as session:
            if session.query(Analyzed_tacticals).filter_by(game_id=game_id).first():
                return
            new_record = Analyzed_tacticals(game_id=game_id)
            session.add(new_record)
            session.commit()
