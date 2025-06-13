import os
import dotenv
from sqlalchemy import create_engine, text


def main():
    dotenv.load_dotenv()
    # Ejemplo: postgresql://user:pass@localhost/dbname
    DB_URL = os.environ.get("DATABASE_URL")

    sql_script = """
    DELETE FROM games;
    DELETE FROM features;
    DELETE FROM analyzed_errors;
    DELETE FROM processed_features;
    """

    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(sql_script))
    print("✅ All tables cleaned successfully.")


if __name__ == "__main__":
    main()
