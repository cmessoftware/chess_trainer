# from dotenv import load_dotenv
# from db.models.games import Games
# from modules.tagging import detect_tags_from_game
# import os
# import json
# import sys

# from sqlalchemy import create_engine, Column, Integer, Text
# from sqlalchemy.orm import sessionmaker, declarative_base
# from sqlalchemy.exc import SQLAlchemyError

# # Permitir importar modules.* desde un script en src/scripts
# sys.path.insert(0, os.path.abspath(
#     os.path.join(os.path.dirname(__file__), '..')))


# load_dotenv()

# DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
# if not DB_URL:
#     raise FileNotFoundError("❌ Database URL not set in CHESS_TRAINER_DB_URL")

# engine = create_engine(DB_URL)
# Session = sessionmaker(bind=engine)
# Base = declarative_base()


# def apply_tags_to_all_games():
#     session = Session()
#     try:
#         games = session.query(Games).filter(Games.tags == None).all()
#         for game in games:
#             try:
#                 tags = detect_tags_from_game(game.pgn)
#                 game.tags = json.dumps(tags)
#             except Exception as e:
#                 print(f"⚠️ Error tagging game {game.game_id}: {e}")
#         session.commit()
#         print(f"✅ Tagged {len(games)} game(s).")
#     except SQLAlchemyError as e:
#         print(f"❌ Database error: {e}")
#         session.rollback()
#     finally:
#         session.close()


# if __name__ == "__main__":
#     apply_tags_to_all_games()

# 🚫 OBSOLETO

# Este script ha quedado obsoleto desde que los tags tácticos se manejan y almacenan
# por jugada en la tabla `features`. Ya no se utiliza el campo `tags` en `games`.

# Si se desea un resumen de tags por partida, considerar crear un nuevo script
# que agregue y consolide los tags desde `features`.

# Fecha de obsolescencia: 2025-06-06
# Autor: Sergio
# """

raise NotImplementedError(
    "Este script ha sido marcado como obsoleto. No debe ejecutarse.")
