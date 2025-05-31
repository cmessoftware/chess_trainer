import json
import streamlit as st
import sqlite3
import pandas as pd
import dotenv
import os
dotenv.load_dotenv() 

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

def ensure_tactical_exercises_table(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tactical_exercises (
            id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            move TEXT NOT NULL,
            uci TEXT NOT NULL,
            tags TEXT NOT NULL,  -- JSON string con la lista de tags
            source_game_id TEXT  -- puede venir del header o ser un hash
        );
    """)
    conn.commit()
    conn.close()


def save_tactic_to_db(tactic, db_path=DB_PATH):
    ensure_tactical_exercises_table
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO tactical_exercises (id, fen, move, uci, tags, source_game_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        tactic["id"],
        tactic["fen"],
        tactic["move"],
        tactic["uci"],
        json.dumps(tactic["tags"]),
        tactic.get("source_game_id"),
    ))
    conn.commit()
    conn.close()

def load_tactics_from_db():
    ensure_tactical_exercises_table(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tactical_exercises", conn)
    conn.close()
    return df

st.title("📤 Exportar ejercicios tácticos")

df = load_tactics_from_db()
st.dataframe(df)

col1, col2 = st.columns(2)
with col1:
    st.download_button("⬇ Exportar a CSV", df.to_csv(index=False), file_name="tactics.csv")

with col2:
    st.download_button("⬇ Exportar a JSON", df.to_json(orient="records", indent=2), file_name="tactics.json")
