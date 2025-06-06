import os
import sqlite3
import dotenv

def main():
    dotenv.load_dotenv()
    DB_PATH = os.environ.get("CHESS_TRAINER_DB")

    sql_script = """
    DELETE FROM games;
    DELETE FROM features;
    DELETE FROM analyzed_errors;
    DELETE FROM processed_games;
    DELETE FROM sqlite_sequence
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    
    print("✅ All tables cleaned successfully.")

if __name__ == "__main__":
    main()
