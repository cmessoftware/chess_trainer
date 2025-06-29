import json
import streamlit as st
import pandas as pd
import dotenv
import os
from db.postgres_utils import execute_postgres_query, read_postgres_sql

dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")


def ensure_tactical_exercises_table():
    """Create tactical_exercises table if it doesn't exist"""
    query = """
    CREATE TABLE IF NOT EXISTS tactical_exercises (
        id TEXT PRIMARY KEY,
        fen TEXT NOT NULL,
        move TEXT NOT NULL,
        uci TEXT NOT NULL,
        tags TEXT NOT NULL,
        source_game_id TEXT
    );
    """
    execute_postgres_query(query, fetch=False)


def save_tactic_to_db(tactic):
    ensure_tactical_exercises_table()
    query = """
        INSERT INTO tactical_exercises (id, fen, move, uci, tags, source_game_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            fen = EXCLUDED.fen,
            move = EXCLUDED.move,
            uci = EXCLUDED.uci,
            tags = EXCLUDED.tags,
            source_game_id = EXCLUDED.source_game_id
    """
    execute_postgres_query(query, (
        tactic["id"],
        tactic["fen"],
        tactic["move"],
        tactic["uci"],
        json.dumps(tactic["tags"]),
        tactic.get("source_game_id"),
    ), fetch=False)


def load_tactics_from_db():
    ensure_tactical_exercises_table()
    return read_postgres_sql("SELECT * FROM tactical_exercises")


st.title("📤 Exportar ejercicios tácticos")

df = load_tactics_from_db()
st.dataframe(df)

col1, col2 = st.columns(2)
with col1:
    st.download_button("⬇ Exportar a CSV", df.to_csv(
        index=False), file_name="tactics.csv")

with col2:
    st.download_button("⬇ Exportar a JSON", df.to_json(
        orient="records", indent=2), file_name="tactics.json")
