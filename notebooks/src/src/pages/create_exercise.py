import streamlit as st
import streamlit_chess
import chess
import json
from pathlib import Path

def show():
    st.title("Crear nuevo ejercicio táctico")
    fen = st.text_input("FEN inicial", value=chess.STARTING_FEN)
    board = chess.Board(fen)
    result = streamlit_chess.chessboard("Tablero", fen=fen)
    current_fen = result.get("fen", fen)

    title = st.text_input("Título", "Nuevo ejercicio")
    side_to_move = st.selectbox("Lado al mover", ["white", "black"])
    tags = st.text_input("Etiquetas", "táctica,mate")
    num_lines = st.number_input("Cantidad de líneas", 1, 5, 1)
    lines = []

    for i in range(num_lines):
        moves = st.text_input(f"Línea #{i+1} (SAN)", key=f"line{i}")
        comment = st.text_input(f"Comentario línea #{i+1}", key=f"c{i}")
        lines.append({"moves": moves.split(), "comment": comment})

    if st.button("Guardar"):
        data = {
            "fen": current_fen,
            "title": title,
            "side_to_move": side_to_move,
            "tags": tags.split(","),
            "lines": lines
        }
        Path("data/tactics").mkdir(parents=True, exist_ok=True)
        with open(f"data/tactics/{title.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        st.success("Ejercicio guardado")
