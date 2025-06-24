# db/repository/game_repository.py

from io import StringIO
import os
import chess
import dotenv
from sqlalchemy import select, not_
from db.models.games import Games  # You must have this model defined
from db.session import get_session  # Function that returns a SQLAlchemy session

dotenv.load_dotenv()


class GamesRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all_games(self):
        with self.session_factory() as session:
            engine = session.get_bind()
            stmt = select(Games)
            games = session.execute(stmt).scalars().all()
            # self.db_utils.print_sql_query(stmt, engine)
            return games  # list of Games ORM objects

    def get_games_by_pagination(self, offset: int = 0, limit: int = 10):
        """
        Retrieves a list of games using pagination.
        :param offset: Number of games to skip.
        :param limit: Maximum number of games to return.
        :return: List of Games objects.
        """
        with self.session_factory() as session:
            engine = session.get_bind()
            stmt = select(Games).offset(offset).limit(limit)
            games = session.execute(stmt).scalars().all()
            # self.db_utils.print_sql_query(stmt, engine)
            return games

    def get_games_by_pagination_not_analyzed(self, analyzed_hashes: set, offset: int = 0, limit: int = 10):
        """
        Returns games whose ID (hash) is not in analyzed_hashes, paginated.
        """
        with self.session_factory() as session:
            if analyzed_hashes:
                stmt = select(Games.pgn).where(not_(Games.game_id.in_(analyzed_hashes)))
            else:
                stmt = select(Games.pgn)

            stmt = stmt.offset(offset).limit(limit)
            games = session.execute(stmt).scalars().all()
        return games

    def get_games_not_analyzed(self, analyzed_hashes: set):
        """
        Returns games whose ID (hash) is not in analyzed_hashes.
        """
        with self.session_factory() as session:
            try:
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
            except Exception as e:
                    session.rollback()
                    raise e
    
    
    def get_pgn_text_by_id(self, game_id):
        with self.session_factory() as session:
            try:
                stmt = select(Games.pgn).where(Games.game_id == game_id)
                return session.execute(stmt).scalar_one_or_none()
            except Exception as e:
                session.rollback()
                raise e

    def get_game_by_id(self, game_id):
        with self.session_factory() as session:
            row = session.execute(
                select(Games.game_id, Games.pgn).where(
                    Games.game_id == game_id)
            ).scalar().first()
            return row

    def game_exists(self, game_id: str) -> bool:
        return self.session.query(Games).filter(Games.game_id == game_id).first() is not None

    def save_game(self, game_data: dict):
        game = Games(**game_data)
        self.session.add(game)
        self.commit()

    def commit(self):
        self.session.commit()

    def close(self):
        self.session.close()

    def is_game_in_db(self, game_id: str) -> bool:
        """
        Checks if a game with the given game_id exists in the database.
        :param game_id: Unique identifier for the game.
        :return: True if the game exists, False otherwise.
        """
        with self.session_factory() as session:
            stmt = select(Games).where(Games.game_id == game_id)
            result = session.execute(stmt).first()
            return result is not None
