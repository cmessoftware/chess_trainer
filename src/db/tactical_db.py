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
from pages.export_exercises import TacticalExercise
dotenv.load_dotenv()

# Debe ser una URL de conexión de PostgreSQL
DB_URL = os.environ.get("CHESS_TRAINER_DB")

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

db_utils = DBUtils(DB_URL)


def update_features_tags_and_score_diff(game_id: str, tags: List[Dict]):
    if not tags:
        return

    print(
        f"📝 Actualizando {len(tags)} etiquetas tácticas para la partida {game_id}...:")

    updated_count = 0
    failed_updates = []

    session = Session()
    try:
        for tag in tags:
            move_number = tag.get("move_number")
            player_color = tag.get("player_color")
            if player_color is None:
                print(f"❌ Tag sin player_color: {tag}")

            if db_utils.is_feature_in_db(game_id):
                print(
                    f"✅ Insertando etiqueta: {tag.get('tag')} para la jugada {move_number} del jugador {player_color}")

                stmt = (
                    update(Feature)
                    .where(
                        Feature.game_id == game_id,
                        Feature.move_number == move_number,
                        Feature.player_color == player_color
                    )
                    .values(
                        tags=tag.get("tag"),
                        score_diff=tag.get("score_diff")
                    )
                )
                result = session.execute(stmt)
                if result.rowcount == 0:
                    failed_updates.append((move_number, player_color))
                else:
                    updated_count += 1
            else:
                print(
                    f"❌ La partida {game_id} no existe en la base de datos. No se pueden insertar etiquetas.")
                session.rollback()
                session.close()
                return

        if failed_updates:
            print(f"⚠️ No se actualizaron las jugadas: {failed_updates}")

        if updated_count == 0:
            print(
                f"⚠️ No se encontraron jugadas para actualizar en la partida {game_id}.")
            session.rollback()
            session.close()
            return

        print(f"✅ {updated_count} etiquetas insertadas exitosamente para {game_id}")
        session.commit()
    except SQLAlchemyError as e:
        print(
            f"❌ Excepción al insertar etiquetas tácticas en la base de datos: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def init_tactical_exercises_table():
    Base.metadata.create_all(engine, tables=[TacticalExercise.__table__])


def save_tactic_to_db(tactic, db_url=DB_URL):
    print(f"📝 Guardando táctica: {tactic['id']}")
    session = Session()
    try:
        obj = TacticalExercise(
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
