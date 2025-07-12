# reset_tables.py

import os
import dotenv
from sqlalchemy import create_engine, MetaData
from db.database import Base  # ✅ Usa el Base ya definido globalmente
from db.models.games import Games
from db.models.features import Features
from db.session import get_schema

dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
engine = create_engine(DB_URL)


def reset_tables():
    schema = get_schema()
    metadata = MetaData(schema=schema)
    metadata.reflect(bind=engine, only=["games", "features"])

    print("🔁 Borrando tablas si existen...")
    Features.__table__.drop(engine, checkfirst=True)
    Games.__table__.drop(engine, checkfirst=True)

    print("🧱 Recreando tablas...")
    Base.metadata.create_all(
        engine, tables=[Games.__table__, Features.__table__])

    print("✅ Tablas recreadas exitosamente.")


if __name__ == "__main__":
    reset_tables()
