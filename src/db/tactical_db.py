# src/modules/tactical_db.py
import os
import json
from typing import Dict, List
from altair import Feature
import dotenv

from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, update
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from db.db_utils import DBUtils
from db.models.tactical_exercises import Tactical_exercises
dotenv.load_dotenv()

# Debe ser una URL de conexión de PostgreSQL
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

db_utils = DBUtils()


def init_tactical_exercises_table():
    Base.metadata.create_all(engine, tables=[Tactical_exercises.__table__])


def save_tactic_to_db(tactic, db_url=DB_URL):
    print(f"📝 Guardando táctica: {tactic['id']}")
    session = Session()
    try:
        obj = Tactical_exercises(
            id=tactic["id"],
            fen=tactic["fen"],
            move=tactic["move"],
            uci=tactic["uci"],
            tags=json.dumps(tactic["tags"]),
            source_game_id=tactic.get("source_game_id")
        )
        session.merge(obj)
        session.commit()
    except SQLAlchemyError as e:
        print(f"❌ Excepción al guardar táctica: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def bulk_import_tactics_from_json(folder_path="data/tactics"):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for i, tactic in enumerate(data):
                    if "id" not in tactic:
                        tactic["id"] = f"{filename[:-5]}_{i}"
                    save_tactic_to_db(tactic)
            elif isinstance(data, dict):
                if "id" not in data:
                    data["id"] = filename[:-5]
                save_tactic_to_db(data)
