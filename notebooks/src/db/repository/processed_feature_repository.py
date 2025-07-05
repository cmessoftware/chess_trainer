# /app/src/db/repository/ProcessedFeatures_repository.py
import datetime
import logging

from sqlalchemy import insert
from db.db_utils import DBUtils
from db.session import get_session
from db.models.processed_features import Processed_features


logger = logging.getLogger(__name__)


class ProcessedFeaturesRepository:
    def __init__(self, session_factory=get_session):
        self.session_factory = session_factory
        self.session = self.session_factory()
        self.db_utils = DBUtils()

    def get_all(self):
        with self.session_factory() as session:
            rows = session.query(Processed_features).all()
            return [row.game_id for row in rows]

    def get_by_game_id(self, game_id):
        return self.session.query(Processed_features).filter(Processed_features.game_id == game_id).all()

    def save(self, processed_feature: Processed_features):
        with self.session_factory() as session:
            session.add(processed_feature)
            session.commit()

    def save_processed_hash(self, game_id: str):
        new_entry = Processed_features(
            game_id=game_id,
            date_processed=datetime.datetime.utcnow()
        )
        # Esto debe ser una instancia del modelo, no un str
        self.session.add(new_entry)
        self.session.commit()

    def save_many_processed_features(self, game_ids: list[str]):
        if not game_ids:
            return

        session = self.session_factory()
        try:
            rows = [{"game_id": gid} for gid in game_ids]

            stmt = insert(Processed_features).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=["game_id"])

            result = session.execute(stmt)
            session.commit()

            inserted = result.rowcount
            skipped = len(rows) - inserted
            logger.info(
                f"✅ Procesados insertados: {inserted}, ⏭️ Duplicados ignorados: {skipped}")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al insertar procesados en lote: {e}")
            raise e
        finally:
            session.close()
