"""
📋 Games Browser - Chess Trainer Frontend
Browse and manage chess games stored in PostgreSQL database.

Features:
- Paginated games table
- Advanced filtering (player, rating, date, result)
- Game details viewer
- Search functionality
- Export to PGN
- Real-time database statistics

Author: Chess Trainer Frontend Team
Date: 2026-01-15
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Import components with proper path handling
try:
    from components.database_connector import (
        get_database_connector,
        display_connection_status,
    )
    from components.chess_board_clean_fixed import get_clean_chess_visualizer
except ImportError:
    # Fallback for different execution contexts
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    from components.database_connector import (
        get_database_connector,
        display_connection_status,
    )
    from components.chess_board_clean_fixed import get_clean_chess_visualizer


def apply_custom_css():
    """Apply custom CSS for better UI."""
    st.markdown(
        """
    <style>
    .game-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .player-white {
        font-weight: bold;
        color: #333;
    }
    .player-black {
        font-weight: bold;
        color: #666;
    }
    .game-result {
        font-weight: bold;
        font-size: 1.2em;
    }
    .result-white-win { color: #28a745; }
    .result-black-win { color: #dc3545; }
    .result-draw { color: #6c757d; }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_filters_section() -> Dict[str, Any]:
    """Create and return filter controls."""
    st.markdown("### 🔍 Filtros de Búsqueda")

    with st.container():
        # Create columns for filters
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("👤 Jugadores")

            # Get player suggestions from database
            db = get_database_connector()
            players = db.get_unique_players(limit=50)

            player_filter = st.selectbox(
                "Buscar jugador",
                options=[""] + players,
                help="Selecciona un jugador o deja vacío para ver todos",
            )

            # Alternative text input for manual search
            player_manual = st.text_input(
                "O busca manualmente",
                placeholder="Escribe nombre del jugador...",
                help="Busca por nombre (parcial)",
            )

            # Use manual input if provided, otherwise use selectbox
            final_player = (
                player_manual.strip() if player_manual.strip() else player_filter
            )

        with col2:
            st.subheader("📊 Rating")

            min_rating = st.number_input(
                "Rating mínimo",
                min_value=0,
                max_value=3000,
                value=None,
                step=100,
                help="Rating mínimo (cualquier jugador)",
            )

            max_rating = st.number_input(
                "Rating máximo",
                min_value=0,
                max_value=3000,
                value=None,
                step=100,
                help="Rating máximo (cualquier jugador)",
            )

            result_filter = st.selectbox(
                "Resultado",
                options=["", "1-0", "0-1", "1/2-1/2", "*"],
                help="Filtrar por resultado de la partida",
            )

        with col3:
            st.subheader("📅 Fechas")

            date_from = st.date_input(
                "Desde", value=None, help="Fecha de inicio (opcional)"
            )

            date_to = st.date_input("Hasta", value=None, help="Fecha final (opcional)")

            # Quick date filters
            st.write("**Filtros rápidos:**")
            col_today, col_week, col_month = st.columns(3)

            with col_today:
                if st.button("Hoy", help="Partidas de hoy"):
                    st.session_state.date_from = datetime.now().date()
                    st.session_state.date_to = datetime.now().date()

            with col_week:
                if st.button("Semana", help="Últimos 7 días"):
                    st.session_state.date_from = (
                        datetime.now() - timedelta(days=7)
                    ).date()
                    st.session_state.date_to = datetime.now().date()

            with col_month:
                if st.button("Mes", help="Último mes"):
                    st.session_state.date_from = (
                        datetime.now() - timedelta(days=30)
                    ).date()
                    st.session_state.date_to = datetime.now().date()

    # Use session state for dates if set
    final_date_from = st.session_state.get("date_from", date_from)
    final_date_to = st.session_state.get("date_to", date_to)

    # Build filters dictionary
    filters = {}

    if final_player:
        filters["player"] = final_player
    if min_rating:
        filters["min_rating"] = min_rating
    if max_rating:
        filters["max_rating"] = max_rating
    if result_filter:
        filters["result"] = result_filter
    if final_date_from:
        filters["date_from"] = final_date_from
    if final_date_to:
        filters["date_to"] = final_date_to

    # Clear filters button
    col_clear, col_apply, col_export = st.columns([1, 1, 1])

    with col_clear:
        if st.button("🗑️ Limpiar filtros", help="Resetear todos los filtros"):
            # Clear session state
            for key in ["date_from", "date_to"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    with col_apply:
        st.write("")  # Spacer
        active_filters = len([f for f in filters.values() if f])
        st.info(f"📊 {active_filters} filtros activos")

    return filters


def display_games_table(df: pd.DataFrame, total_count: int, page: int, per_page: int):
    """Display games in a formatted table with pagination."""
    if df.empty:
        st.warning("🔍 No se encontraron partidas con los filtros aplicados.")
        return

    # Display pagination info
    start_idx = (page - 1) * per_page + 1
    end_idx = min(page * per_page, total_count)

    st.info(f"📊 Mostrando partidas {start_idx}-{end_idx} de {total_count:,} total")

    # Format dataframe for display
    display_df = df.copy()

    # Format columns
    if "date_played" in display_df.columns:
        display_df["date_played"] = pd.to_datetime(
            display_df["date_played"]
        ).dt.strftime("%Y-%m-%d")

    # Rename columns for display
    column_renames = {
        "game_id": "ID",
        "white_player": "⚪ Blancas",
        "black_player": "⚫ Negras",
        "white_elo": "ELO ⚪",
        "black_elo": "ELO ⚫",
        "result": "Resultado",
        "date_played": "Fecha",
        "opening_name": "Apertura",
        "time_control": "Control",
        "source": "Fuente",
    }

    display_df = display_df.rename(columns=column_renames)

    # Display table with selection
    st.markdown("**📋 Tabla de Partidas - Selecciona una fila para ver opciones**")

    selected_indices = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-row",
        on_select="rerun",
        key=f"games_table_{page}",
    ).selection.rows

    # Handle row selection for details
    if selected_indices:
        selected_game_ids = [df.iloc[idx]["game_id"] for idx in selected_indices]

        # Show selection info and buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"✅ {len(selected_game_ids)} partida(s) seleccionada(s)")

        with col2:
            if st.button(
                "♟️ Ver Partida", type="primary", disabled=len(selected_game_ids) != 1
            ):
                if len(selected_game_ids) == 1:
                    st.session_state.selected_game_id = selected_game_ids[0]
                    st.rerun()

        with col3:
            if st.button("📤 Exportar PGN", disabled=len(selected_game_ids) == 0):
                export_games_to_pgn(selected_game_ids)
    else:
        st.markdown("---")
        st.info(
            "💡 **Instrucciones:** Haz clic en una fila de la tabla para seleccionar una partida y ver el tablero interactivo"
        )


def display_pagination_controls(total_count: int, page: int, per_page: int):
    """Display pagination controls."""
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    if total_pages <= 1:
        return page

    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⬅️ Primera", disabled=page <= 1):
            st.session_state.current_page = 1
            st.rerun()

    with col2:
        if st.button("← Anterior", disabled=page <= 1):
            st.session_state.current_page = max(1, page - 1)
            st.rerun()

    with col3:
        new_page = st.number_input(
            f"Página (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=page,
            key="page_input",
        )

        if new_page != page:
            st.session_state.current_page = new_page
            st.rerun()

    with col4:
        if st.button("Siguiente →", disabled=page >= total_pages):
            st.session_state.current_page = min(total_pages, page + 1)
            st.rerun()

    with col5:
        if st.button("Última ➡️", disabled=page >= total_pages):
            st.session_state.current_page = total_pages
            st.rerun()

    return page


def display_game_details(game_id: str):
    """Display detailed view of a specific game."""
    db = get_database_connector()
    game_data = db.get_game_details(game_id)

    if not game_data:
        st.error(f"❌ No se encontró la partida {game_id}")
        return

    st.markdown(f"## 🎯 Detalles de Partida: `{game_id}`")

    # Game header
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("⚪ Jugador Blancas", game_data["white_player"] or "Unknown")
        st.metric("📊 Rating Blancas", game_data["white_elo"] or "N/A")

    with col2:
        result = game_data["result"] or "*"
        result_color = {"1-0": "🟢", "0-1": "🔴", "1/2-1/2": "🟡", "*": "⚪"}.get(
            result, "⚪"
        )

        st.metric("🏆 Resultado", f"{result_color} {result}")
        st.metric("📅 Fecha", game_data["date_played"] or "Unknown")

    with col3:
        st.metric("⚫ Jugador Negras", game_data["black_player"] or "Unknown")
        st.metric("📊 Rating Negras", game_data["black_elo"] or "N/A")

    # Game information
    st.markdown("### 📋 Información de la Partida")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(f"**🎯 Apertura:** {game_data.get('opening') or 'N/A'}")
        st.write(f"**⏱️ Control de tiempo:** {game_data.get('time_control') or 'N/A'}")
        st.write(f"**📁 Fuente:** {game_data.get('source') or 'N/A'}")

    with info_col2:
        st.write(f"**🏷️ ECO:** {game_data.get('eco') or 'N/A'}")
        st.write(f"**📅 Fecha creación:** {game_data.get('created_at') or 'N/A'}")

    # Interactive Chess Board - Versión Mejorada
    pgn_text = game_data.get("pgn")
    if pgn_text:
        st.markdown("### ♟️ Tablero Interactivo - Navegación por Jugadas")

        # Board options
        board_col1, board_col2 = st.columns([3, 1])

        with board_col2:
            st.markdown("**⚙️ Opciones del Tablero:**")
            board_width = st.select_slider(
                "Tamaño tablero",
                options=[350, 400, 450, 500, 550],
                value=450,
                key=f"board_width_{game_id}",
            )

            show_controls = st.checkbox(
                "🎮 Controles navegación", value=True, key=f"show_controls_{game_id}"
            )

            flip_board = st.checkbox(
                "🔄 Ver desde negras", value=False, key=f"flip_board_{game_id}"
            )

            st.markdown("---")
            st.markdown("**✨ Funciones Disponibles:**")
            st.markdown("🖱️ Click para info de casillas")
            st.markdown("🎮 Navegación real por jugadas")
            st.markdown("📊 Contador de posición actual")
            st.markdown("♟️ Sigue movimientos reales")

            # Game info summary
            st.markdown("---")
            st.markdown("**📋 Info Partida:**")
            st.markdown(f"**⚪:** {game_data.get('white_player', 'N/A')[:15]}")
            st.markdown(f"**⚫:** {game_data.get('black_player', 'N/A')[:15]}")
            st.markdown(f"**🏆:** {game_data.get('result', '*')}")

        with board_col1:
            # Render con el nuevo componente mejorado
            chess_visualizer = get_clean_chess_visualizer()
            if chess_visualizer:
                chess_visualizer.render_chess_board(
                    pgn_text=pgn_text,
                    width=board_width,
                    show_controls=show_controls,
                    flip_board=flip_board,
                    game_id=f"db_game_{game_id}",
                )
            else:
                st.error("❌ Error al cargar el tablero interactivo")

        # PGN text (collapsible)
        with st.expander("📝 Ver PGN completo", expanded=False):
            st.code(pgn_text, language="text")
    else:
        st.warning("⚠️ No hay movimientos disponibles para esta partida")

    # Remove the old moves section since we now have the interactive board
    # Final position section removed as it's now handled by the board

    # Actions
    st.markdown("### 🔧 Acciones")

    col_back, col_pgn = st.columns(2)

    with col_back:
        if st.button("← Volver a la lista"):
            if "selected_game_id" in st.session_state:
                del st.session_state.selected_game_id
            st.rerun()

    with col_pgn:
        if st.button("📤 Exportar PGN"):
            export_games_to_pgn([game_id])


def export_games_to_pgn(game_ids: list):
    """Export selected games to PGN format."""
    db = get_database_connector()
    pgn_content = db.export_games_to_pgn(game_ids)

    if pgn_content:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chess_trainer_export_{timestamp}.pgn"

        st.download_button(
            label="📥 Descargar PGN",
            data=pgn_content,
            file_name=filename,
            mime="text/plain",
            help=f"Descargar {len(game_ids)} partidas en formato PGN",
        )

        st.success(f"✅ Preparado para descargar {len(game_ids)} partidas")

        # Show preview
        with st.expander("👁️ Preview del PGN"):
            preview = pgn_content[:1000]
            if len(pgn_content) > 1000:
                preview += "\n\n... (contenido truncado)"
            st.code(preview, language="text")
    else:
        st.error("❌ Error generando PGN")


def main():
    """Main games browser interface."""
    st.set_page_config(
        page_title="Games Browser - Chess Trainer", page_icon="📋", layout="wide"
    )

    apply_custom_css()

    st.title("📋 Explorador de Partidas")
    st.markdown(
        "Visualiza y gestiona todas las partidas almacenadas en la base de datos."
    )

    # Sidebar with connection status
    display_connection_status()

    # Check if viewing game details
    if st.session_state.get("selected_game_id"):
        display_game_details(st.session_state["selected_game_id"])
        return

    # Initialize pagination
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # Create filters
    filters = create_filters_section()

    # Pagination settings
    st.markdown("### ⚙️ Configuración de Vista")
    col_per_page, col_info = st.columns([1, 2])

    with col_per_page:
        per_page = st.selectbox(
            "Partidas por página",
            options=[25, 50, 100, 200],
            index=1,  # Default to 50
            help="Número de partidas a mostrar por página",
        )

    with col_info:
        st.info("💡 Usa los filtros arriba para encontrar partidas específicas")

    # Get database connection
    db = get_database_connector()

    if not db.test_connection():
        st.error("❌ No se puede conectar a la base de datos")
        st.info("💡 Verifica que PostgreSQL esté corriendo con Docker Compose")
        return

    # Load games with pagination
    page = st.session_state.current_page

    with st.spinner("🔄 Cargando partidas..."):
        df, total_count = db.get_games_paginated(
            page=page, per_page=per_page, filters=filters
        )

    # Display results
    st.markdown("### 📊 Resultados")

    if total_count == 0:
        st.warning("🔍 No hay partidas en la base de datos.")
        st.info("💡 Importa algunos archivos PGN para empezar.")
        return

    # Display games table
    display_games_table(df, total_count, page, per_page)

    # Pagination controls
    display_pagination_controls(total_count, page, per_page)


if __name__ == "__main__":
    main()
