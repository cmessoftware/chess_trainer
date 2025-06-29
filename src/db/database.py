import os
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone())
