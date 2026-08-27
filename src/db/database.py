import os
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Only test connection if not in test environment.
# Do not print the server version on success: it looks like a CLI finished
# when a script only imported this module.
if not os.environ.get("PYTEST_CURRENT_TEST"):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Database connection test failed: {e}")
        # Don't fail on import, just warn
