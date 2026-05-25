"""
🎯 Chess Board Demo Page
Test page for the Chess Board Visualizer component

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from components.chess_board_fixed import get_chess_visualizer
from components.chess_board_simple import get_simple_chess_visualizer
from components.chess_board_standalone import get_standalone_chess_visualizer


def main():
    st.set_page_config(
        page_title="Chess Board Demo - Chess Trainer", page_icon="♟️", layout="wide"
    )

    st.title("♟️ Chess Board Visualizer - Demo")
    st.markdown("---")
    # Selector de versión
    version = st.selectbox(
        "📋 Seleccionar versión del visualizador:",
        [
            "Versión Autónoma (Sin CDN)",
            "Versión Simple (Recomendada)",
            "Versión Avanzada",
        ],
        index=0,
        help="La versión autónoma no depende de librerías externas y siempre funciona",
    )

    if "Autónoma" in version:
        chess_visualizer = get_standalone_chess_visualizer()
        version_info = "🛡️ Versión completamente autónoma sin dependencias de CDN"
    elif "Simple" in version:
        chess_visualizer = get_simple_chess_visualizer()
        version_info = "🛡️ Versión simple con múltiples CDNs de respaldo"
    else:
        chess_visualizer = get_chess_visualizer()
        version_info = "⚡ Versión avanzada con todas las funciones"

    st.info(f"**Versión activa:** {version_info}")

    # Botón para limpiar caché
    if st.button("🔄 Forzar Recarga (limpiar caché)", type="secondary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    # Sample PGN for testing
    sample_pgn = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2023.06.15"]
[Round "-"]
[White "PlayerWhite"]
[Black "PlayerBlack"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7 14. Bg5 b4 15. Nb1 h6 16. Bh4 c5 17. dxe5 Nxe4 18. Bxe7 Qxe7 19. exd6 Qf6 20. Nbd2 Nxd6 21. Nc4 Nxc4 22. Bxc4 Nb6 23. Ne5 Rae8 24. Qf3 Qxf3 25. Nxf3 Rxe1+ 26. Rxe1 c4 27. Re7 Bc8 28. Bd5 Rd8 29. Bxc4 Nxc4 30. Rc7 Na5 31. b3 Rd1+ 32. Kh2 Rd2 33. Rxc8+ Kh7 34. Ra8 Nc6 35. Ra6 Ne5 36. Nxe5 1-0"""

    # Demo options
    st.sidebar.title("⚙️ Demo Options")

    demo_mode = st.sidebar.selectbox(
        "Select Demo Mode", ["Complete Game", "Custom PGN", "Position Only"]
    )

    if demo_mode == "Complete Game":
        st.markdown("### 🎮 Complete Game Demo")
        st.markdown("Navigate through a complete Spanish Opening game:")

        chess_visualizer.render_chess_board(
            pgn_text=sample_pgn,
            game_id="demo_game",
            width=450,
            show_controls=True,
            flip_board=False,
        )

        st.markdown("**Features demonstrated:**")
        st.markdown("- ⏮️ Navigate to start/end of game")
        st.markdown("- ⏪⏩ Move forward/backward through moves")
        st.markdown("- 🔄 Flip board perspective")
        st.markdown("- ⌨️ Keyboard navigation (arrow keys, home, end)")
        st.markdown("- 📱 Responsive design")

    elif demo_mode == "Custom PGN":
        st.markdown("### ✏️ Custom PGN Demo")

        custom_pgn = st.text_area("Enter your PGN:", value=sample_pgn, height=150)

        board_options_col1, board_options_col2 = st.columns(2)

        with board_options_col1:
            board_size = st.select_slider(
                "Board Size", options=[300, 350, 400, 450, 500, 550], value=400
            )

        with board_options_col2:
            flip_perspective = st.checkbox("Flip Board (Black perspective)")

        if custom_pgn.strip():
            chess_visualizer.render_chess_board(
                pgn_text=custom_pgn,
                game_id="custom_demo",
                width=board_size,
                show_controls=True,
                flip_board=flip_perspective,
            )
        else:
            st.warning("Please enter a PGN to visualize")

    elif demo_mode == "Position Only":
        st.markdown("### 🏁 Static Position Demo")

        fen_examples = {
            "Starting Position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "Scholar's Mate": "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
            "Endgame": "8/8/8/8/8/3k4/3P4/3K4 w - - 0 1",
            "Custom": "",
        }

        selected_example = st.selectbox(
            "Choose a position example:", list(fen_examples.keys())
        )

        if selected_example == "Custom":
            fen_string = st.text_input(
                "Enter FEN string:",
                placeholder="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            )
        else:
            fen_string = fen_examples[selected_example]
            st.code(fen_string, language="text")

        position_size = st.slider("Position Size", 250, 500, 350)
        position_flip = st.checkbox("Flip Position")

        if fen_string:
            if hasattr(chess_visualizer, "render_static_position"):
                chess_visualizer.render_static_position(
                    fen=fen_string, width=position_size, flip_board=position_flip
                )
            else:
                st.info("Position-only rendering not available in this version")

    # Technical information
    st.markdown("---")
    st.markdown("### 🔧 Technical Information")

    tech_info_col1, tech_info_col2 = st.columns(2)

    with tech_info_col1:
        st.markdown("**Libraries Used:**")
        st.markdown("- Chess.js - Move generation and validation")
        st.markdown("- Chessboard.js - Interactive board rendering")
        st.markdown("- Streamlit Components - Integration")

    with tech_info_col2:
        st.markdown("**Planned Enhancements:**")
        st.markdown("- 🎯 Arrow highlighting for moves")
        st.markdown("- 📊 Position evaluation display")
        st.markdown("- 🔍 Move analysis integration")
        st.markdown("- ⚡ Engine analysis overlay")

    st.markdown("---")
    st.info(
        "💡 This demo shows the basic functionality. The complete integration is available in the Games Browser."
    )


if __name__ == "__main__":
    main()
