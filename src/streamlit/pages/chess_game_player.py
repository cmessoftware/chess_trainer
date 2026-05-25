"""
🎮 Chess Game Player - Integrated Game Browser + Interactive Board
Selector de partidas integrado con tablero interactivo

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from components.chess_board_clean_fixed import get_clean_chess_visualizer


def main():
    st.set_page_config(page_title="🎮 Chess Game Player", page_icon="♟️", layout="wide")

    st.markdown("# 🎮 Chess Game Player")
    st.markdown("**Selector de partidas + Tablero interactivo**")
    st.markdown("---")

    # Sample games database (later will connect to PostgreSQL)
    sample_games = [
        {
            "id": 1,
            "white": "Magnus Carlsen",
            "black": "Fabiano Caruana",
            "result": "1-0",
            "date": "2024-03-15",
            "event": "World Championship",
            "pgn": """[Event "World Championship"]
[Site "Dubai"]
[Date "2024.03.15"]
[White "Magnus Carlsen"]
[Black "Fabiano Caruana"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 O-O 8. c3 d6 9. h3 Bb7 10. d4 Re8 11. Nbd2 Bf8 12. Bc2 exd4 13. cxd4 c5 1-0""",
        },
        {
            "id": 2,
            "white": "Ding Liren",
            "black": "Ian Nepomniachtchi",
            "result": "0-1",
            "date": "2024-02-20",
            "event": "Candidates Tournament",
            "pgn": """[Event "Candidates Tournament"]
[Site "Madrid"]
[Date "2024.02.20"]
[White "Ding Liren"]
[Black "Ian Nepomniachtchi"]
[Result "0-1"]

1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3 O-O 6. Be2 e5 7. O-O Nc6 8. d5 Ne7 9. Nd2 a5 10. a3 Nd7 11. Rb1 f5 12. b4 axb4 13. axb4 fxe4 14. Ndxe4 Nf5 0-1""",
        },
        {
            "id": 3,
            "white": "Hikaru Nakamura",
            "black": "Wesley So",
            "result": "1/2-1/2",
            "date": "2024-01-10",
            "event": "Speed Chess Championship",
            "pgn": """[Event "Speed Chess Championship"]
[Site "Chess.com"]
[Date "2024.01.10"]
[White "Hikaru Nakamura"]
[Black "Wesley So"]
[Result "1/2-1/2"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be3 e6 7. f3 b5 8. Qd2 Bb7 9. O-O-O Nbd7 10. h4 Rc8 11. Kb1 h6 12. g4 Ne5 13. Be2 Qc7 14. Rhg1 Be7 15. g5 hxg5 16. hxg5 Nh7 17. Rh1 Rxh1 18. Rxh1 Nxg5 1/2-1/2""",
        },
    ]

    # Sidebar for game selection
    with st.sidebar:
        st.markdown("### 🎯 Seleccionar Partida")

        selected_game_index = st.selectbox(
            "Elegir partida:",
            range(len(sample_games)),
            format_func=lambda x: f"{sample_games[x]['white']} vs {sample_games[x]['black']} ({sample_games[x]['result']})",
            key="game_selector",
        )

        selected_game = sample_games[selected_game_index]

        st.markdown("---")
        st.markdown("**📋 Información de la Partida:**")
        st.markdown(f"**⚪ Blancas:** {selected_game['white']}")
        st.markdown(f"**⚫ Negras:** {selected_game['black']}")
        st.markdown(f"**🏆 Resultado:** {selected_game['result']}")
        st.markdown(f"**📅 Fecha:** {selected_game['date']}")
        st.markdown(f"**🏟️ Evento:** {selected_game['event']}")

        st.markdown("---")
        st.markdown("**✨ Controles del Tablero:**")
        st.markdown("🖱️ Click para ver info")
        st.markdown("🎮 Navegación con botones")
        st.markdown("♟️ Sigue movimientos reales")
        st.markdown("📊 Contador de jugadas")

    # Main area for chess board
    st.markdown(f"### ♟️ {selected_game['white']} vs {selected_game['black']}")

    # Board options
    col1, col2 = st.columns([4, 1])

    with col2:
        st.markdown("**⚙️ Opciones:**")
        board_width = st.select_slider(
            "Tamaño tablero", options=[350, 400, 450, 500, 550], value=450
        )

        show_controls = st.checkbox("🎮 Controles navegación", value=True)
        flip_board = st.checkbox("🔄 Ver desde negras", value=False)

        # Load game button
        if st.button("🔄 Recargar Partida", type="primary"):
            st.rerun()

    with col1:
        # Render interactive chess board with selected game
        chess_visualizer = get_clean_chess_visualizer()
        if chess_visualizer and selected_game["pgn"]:
            chess_visualizer.render_chess_board(
                pgn_text=selected_game["pgn"],
                width=board_width,
                show_controls=show_controls,
                flip_board=flip_board,
                game_id=f"game_{selected_game['id']}",
            )
        else:
            st.error("❌ Error al cargar la partida seleccionada")

    # Footer with game details
    with st.expander("📝 Ver PGN completo", expanded=False):
        st.code(selected_game["pgn"], language="text")


if __name__ == "__main__":
    main()
