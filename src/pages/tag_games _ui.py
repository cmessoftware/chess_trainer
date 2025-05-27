import os
import sqlite3
import streamlit as st
import json
import chess.pgn
import io
from dotenv import load_dotenv
from modules.tagging import detect_tags_from_game


load_dotenv()
DB_PATH = os.environ.get("CHESS_TRAINER_DB")

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")

st.set_page_config(page_title="Auto Tag Games", layout="wide")
st.title("🏷 Etiquetado automático de partidas")

def tag_games(limit=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, pgn FROM games WHERE tags IS NULL LIMIT ?", (limit,))
    rows = cursor.fetchall()
    total = len(rows)

    progress = st.progress(0, text="Aplicando etiquetas...")

    for i, (gid, pgn) in enumerate(rows):
        try:
            tags = detect_tags_from_game(pgn)
            tag_str = json.dumps(tags)
            cursor.execute("UPDATE games SET tags = ? WHERE id = ?", (tag_str, gid))
        except Exception as e:
            st.warning(f"⚠️ Error tagging game {gid}: {e}")
        progress.progress((i + 1) / total, text=f"Partida {i + 1} de {total}")
    conn.commit()
    conn.close()
    st.success(f"✅ Etiquetado completo: {total} partida(s) procesadas.")

if st.button("🏷 Ejecutar etiquetado automático"):
    tag_games(limit=1000)
