# /app/src/db/repository/Analyzed_tacticals.py

import logging
from sqlalchemy import insert, select
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

    def get_analysis_coverage_by_source(self, source: str):
        """Get analysis coverage statistics for a specific source."""
        from db.models.games import Games
        import sqlalchemy

        with self.session_factory() as session:
            stmt = select(
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Games.game_id)).label('total'),
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Analyzed_tacticals.game_id)).label('analyzed')
            ).select_from(
                Games
            ).outerjoin(
                Analyzed_tacticals, Games.game_id == Analyzed_tacticals.game_id
            ).where(Games.source == source)

            result = session.execute(stmt).fetchone()
            total = result.total
            analyzed = result.analyzed
            percentage = (analyzed / total * 100) if total > 0 else 0

            return {
                'total': total,
                'analyzed': analyzed,
                'percentage': percentage
            }

    def get_analysis_coverage(self):
        """Get analysis coverage statistics for all sources."""
        from db.models.games import Games
        import sqlalchemy

        with self.session_factory() as session:
            stmt = select(
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Games.game_id)).label('total'),
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Analyzed_tacticals.game_id)).label('analyzed')
            ).select_from(
                Games
            ).outerjoin(
                Analyzed_tacticals, Games.game_id == Analyzed_tacticals.game_id
            )

            result = session.execute(stmt).fetchone()
            total = result.total
            analyzed = result.analyzed
            percentage = (analyzed / total * 100) if total > 0 else 0

            return {
                'total': total,
                'analyzed': analyzed,
                'percentage': percentage
            }

    def get_total_analyzed_count(self):
        """Get total number of analyzed games."""
        with self.session_factory() as session:
            return session.query(Analyzed_tacticals).count()

    def get_coverage_by_source(self):
        """Get analysis coverage by source."""
        from db.models.games import Games
        import sqlalchemy

        with self.session_factory() as session:
            stmt = select(
                Games.source,
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Games.game_id)).label('total_games'),
                sqlalchemy.func.count(sqlalchemy.distinct(
                    Analyzed_tacticals.game_id)).label('analyzed_games')
            ).select_from(
                Games
            ).outerjoin(
                Analyzed_tacticals, Games.game_id == Analyzed_tacticals.game_id
            ).where(Games.source.is_not(None)).group_by(Games.source)

            result = session.execute(stmt).fetchall()
            coverage_data = []

            for row in result:
                source = row.source
                total = row.total_games
                analyzed = row.analyzed_games
                coverage_pct = (analyzed / total * 100) if total > 0 else 0

                coverage_data.append({
                    'source': source,
                    'total_games': total,
                    'analyzed_games': analyzed,
                    'coverage_percentage': coverage_pct
                })

            return coverage_data
