"""
♟️ Chess Board Test - Interactive Chess Board Demo
Simple and clean test without database dependencies.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from components.chess_board_clean import get_clean_chess_visualizer


def main():
    st.set_page_config(
        page_title="🏆 Tablero Interactivo - Test", page_icon="♟️", layout="wide"
    )

    # Header más compacto
    st.markdown("# ♟️ Tablero Interactivo")

    # Test PGN (sample game)
    sample_pgn = """[Event "Test Game"]
[Site "Test"]
[Date "2026.01.16"]
[White "Player 1"]
[Black "Player 2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Bb7 10. d4 Re8"""

    # Columnas para layout compacto
    col1, col2 = st.columns([4, 1])

    with col2:
        st.markdown("**⚙️ Opciones:**")
        board_width = st.select_slider(
            "Tamaño tablero", options=[350, 400, 450, 500], value=400
        )

        show_controls = st.checkbox("🎮 Controles", value=True)
        flip_board = st.checkbox("🔄 Girar tablero", value=False)

        st.markdown("---")
        st.markdown("**✨ Funciones:**")
        st.markdown("🖱️ Click seleccionar")
        st.markdown("🔥 Drag & Drop")
        st.markdown("💡 Movimientos válidos")

    with col1:
        # Renderizar tablero directamente sin log
        chess_visualizer = get_clean_chess_visualizer()
        if chess_visualizer:
            # Suprimir logs con un contenedor limpio
            with st.container():
                chess_visualizer.render_chess_board(
                    pgn_text=sample_pgn,
                    width=board_width,
                    show_controls=show_controls,
                    flip_board=flip_board,
                    game_id="clean_test_board",
                )
        else:
            st.error("❌ Error al cargar el tablero")

    # Footer compacto
    st.markdown("---")
    st.markdown(
        "🏆 **Status:** ✅ Tablero funcionando | 🎯 **Drag & Drop:** Habilitado"
    )


if __name__ == "__main__":
    main()
