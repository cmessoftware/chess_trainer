import streamlit as st
import chess
import chess.svg
import streamlit.components.v1 as components
from chess.svg import Arrow
import chess.engine

def evaluate_position_with_stockfish(board, engine_path="engines/stockfish", depth=15,multipv=1):
    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        info = engine.analyse(board, chess.engine.Limit(depth=depth),multipv=multipv)
        score = info["score"].white() if board.turn == chess.WHITE else info["score"].black()
        best_move = info.get("pv", [None])[0]
        return score, best_move

def show_interactive_line_viewer(fen, lines, tactic_id="default", feedback_mode=False):
    if not lines:
        st.info("No hay líneas para mostrar.")
        return

    selected_index = st.selectbox("Elegí línea", range(len(lines)), format_func=lambda i: f"Línea #{i+1}")
    selected_line = lines[selected_index]["moves"]

    key_index = f"{tactic_id}_line_{selected_index}_index"
    if key_index not in st.session_state:
        st.session_state[key_index] = 0

    current_index = st.session_state[key_index]
    board = chess.Board(fen)
    last_move = None

    for i in range(current_index):
        try:
            last_move = board.push_san(selected_line[i])
        except Exception:
            break

    arrows = []
    if last_move:
        arrows = [Arrow(last_move.from_square, last_move.to_square)]

    svg = chess.svg.board(board, arrows=arrows, size=600)
    components.html(svg, height=400)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("←", key=f"{key_index}_back") and current_index > 0:
            st.session_state[key_index] -= 1
    with col2:
        if st.button("→", key=f"{key_index}_next") and current_index < len(selected_line):
            st.session_state[key_index] += 1
