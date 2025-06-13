from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import dotenv
import os
dotenv.load_dotenv()


DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL")

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={
                           "check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_schema():
    return "public" if engine.dialect.name == "postgresql" else None


def get_session():
    return SessionLocal()
