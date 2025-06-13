import sqlite3
import os
from dotenv import load_dotenv

from db.db_utils import DBUtils


def main():
    try:
        db = DBUtils()
        load_dotenv()
        db_path = os.environ.get("CHESS_TRAINER_DB_URL")
        db.init_db()
        print(f"✅ Base de datos creada correctamente en {db_path}")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        exit(1)


if __name__ == "__main__":
    main()
