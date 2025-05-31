import streamlit as st
import os
import json
import chess
import chess.svg
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="Elite Training", layout="wide")
st.title("🎯 Elite Tactics Trainer")

TACTICS_DIR = Path("data/tactics/elite")

def load_exercises():
    exercises = []
    for file in TACTICS_DIR.glob("*.json"):
        with open(file) as f:
            data = json.load(f)
            data["file"] = file.name
            exercises.append(data)
    return exercises

exercises = load_exercises()

if not exercises:
    st.warning("No elite exercises found. Run generate_exercises_from_elite.py first.")
    st.stop()

# Filtros
with st.sidebar:
    st.header("🔍 Filters")
    all_tags = sorted({tag for ex in exercises for tag in ex.get("tags", [])})
    selected_tag = st.selectbox("Tag", ["Any"] + all_tags)

if selected_tag != "Any":
    exercises = [e for e in exercises if selected_tag in e.get("tags", [])]

exercise = st.selectbox("Choose an exercise", exercises, format_func=lambda e: f"{e['file']} - {e['tags']}")

# Mostrar ejercicio
fen = exercise["fen"]
board = chess.Board(fen)

st.subheader("🔲 Position")
st.image(chess.svg.board(board=board, width=400), use_column_width=True)

with st.expander("💡 Hint"):
    st.write(f"Suggested move: {exercise['move']}")

with st.expander("✅ Solution"):
    st.code(exercise['uci'], language="text")

st.caption(f"Exercise ID: {exercise['id']}  |  Source Game ID: {exercise['source_game_id']}")
