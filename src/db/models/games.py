# db/models/games.py
from sqlalchemy import Column, String
from db.database import Base
from db.session import get_schema


class Games(Base):
    __tablename__ = "games"
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    pgn = Column(String)
    site = Column(String)
    event = Column(String)
    date = Column(String)
    white_player = Column(String)
    white_elo = Column(String)  # New: White player's Elo
    black_player = Column(String)
    black_elo = Column(String)  # New
    result = Column(String)
    eco = Column(String)              # New: ECO code
    opening = Column(String)          # New: opening description
    # New: PGN source --> for example, personal, novice, lichess elite, stockfish test, etc.
    source = Column(String)
