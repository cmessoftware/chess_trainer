"""
🎯 Interactive Chess Board Component
Componente reutilizable de tablero de ajedrez interactivo para toda la aplicación

Features:
- Drag & Drop interactivo
- Navegación por partidas PGN
- Integración con explorador de partidas
- Múltiples modos de visualización
- Sin dependencias de CDN externos

Author: Chess Trainer Frontend Team
Date: January 16, 2026
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from src.components.chess_board_standalone import get_standalone_chess_visualizer


class InteractiveChessBoard:
    """Componente reutilizable de tablero de ajedrez interactivo"""

    def __init__(self):
        self.visualizer = get_standalone_chess_visualizer()

    def render_game_viewer(
        self,
        pgn_data: str,
        game_info: Optional[Dict[str, Any]] = None,
        width: int = 450,
        show_controls: bool = True,
        show_game_info: bool = True,
        container_key: Optional[str] = None,
    ) -> None:
        """
        Renderizar visor de partida completo con información del juego

        Args:
            pgn_data: Datos PGN de la partida
            game_info: Información adicional del juego (white, black, result, etc.)
            width: Ancho del tablero
            show_controls: Mostrar controles de navegación
            show_game_info: Mostrar información del juego
            container_key: Clave única para el contenedor
        """

        # Contenedor principal
        with st.container():
            if show_game_info and game_info:
                self._render_game_info(game_info)

            # Renderizar tablero interactivo
            self.visualizer.render_chess_board(
                pgn_text=pgn_data,
                width=width,
                show_controls=show_controls,
                game_id=container_key or f"game_viewer_{id(game_info)}",
            )

            # Controles adicionales si es necesario
            if show_controls:
                self._render_additional_controls(pgn_data, game_info)

    def render_position_analyzer(
        self,
        fen: str,
        width: int = 400,
        allow_moves: bool = True,
        position_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Renderizar analizador de posición

        Args:
            fen: Posición FEN
            width: Ancho del tablero
            allow_moves: Permitir hacer movimientos
            position_info: Información adicional de la posición
        """

        with st.container():
            if position_info:
                st.markdown(f"**Posición:** {position_info.get('title', 'Análisis')}")
                if position_info.get("description"):
                    st.markdown(position_info["description"])

            # Crear PGN simplificado para la posición
            simple_pgn = f"""[SetUp "1"]
[FEN "{fen}"]

*"""

            self.visualizer.render_chess_board(
                pgn_text=simple_pgn,
                width=width,
                show_controls=False,
                game_id=f"position_analyzer_{fen[:10]}",
            )

            if allow_moves:
                st.info(
                    "💡 Haz clic en las piezas para ver movimientos posibles, o arrastra para mover"
                )

    def render_game_selector(
        self, games_list: List[Dict[str, Any]], on_game_selected: callable = None
    ) -> Optional[Dict[str, Any]]:
        """
        Renderizar selector de partidas con vista previa

        Args:
            games_list: Lista de partidas disponibles
            on_game_selected: Callback cuando se selecciona una partida

        Returns:
            Partida seleccionada o None
        """

        if not games_list:
            st.warning("No hay partidas disponibles")
            return None

        st.markdown("### 🎮 Seleccionar Partida")

        # Crear opciones para el selectbox
        game_options = []
        for i, game in enumerate(games_list):
            white = game.get("white", "Desconocido")
            black = game.get("black", "Desconocido")
            result = game.get("result", "*")
            date = game.get("date", "")

            option_text = f"{white} vs {black} ({result})"
            if date:
                option_text += f" - {date}"

            game_options.append(option_text)

        # Selector de partida
        selected_index = st.selectbox(
            "Elegir partida:",
            range(len(game_options)),
            format_func=lambda x: game_options[x],
            key="game_selector",
        )

        if selected_index is not None:
            selected_game = games_list[selected_index]

            # Mostrar vista previa
            col1, col2 = st.columns([2, 1])

            with col1:
                if selected_game.get("pgn"):
                    self.render_game_viewer(
                        pgn_data=selected_game["pgn"],
                        game_info=selected_game,
                        width=350,
                        show_controls=True,
                        show_game_info=False,
                    )
                else:
                    st.warning("No hay datos PGN para esta partida")

            with col2:
                self._render_game_info(selected_game, compact=True)

                # Botón para seleccionar
                if st.button(
                    "📋 Usar esta partida", type="primary", key="select_game_btn"
                ):
                    if on_game_selected:
                        on_game_selected(selected_game)
                    return selected_game

        return None

    def _render_game_info(
        self, game_info: Dict[str, Any], compact: bool = False
    ) -> None:
        """Renderizar información del juego"""

        if compact:
            st.markdown(f"**⚪ Blancas:** {game_info.get('white', 'Desconocido')}")
            st.markdown(f"**⚫ Negras:** {game_info.get('black', 'Desconocido')}")
            st.markdown(f"**🏆 Resultado:** {game_info.get('result', 'Sin resultado')}")

            if game_info.get("date"):
                st.markdown(f"**📅 Fecha:** {game_info['date']}")
            if game_info.get("event"):
                st.markdown(f"**🏟️ Evento:** {game_info['event']}")

        else:
            # Información completa
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Jugador Blanco", game_info.get("white", "Desconocido"))
                if game_info.get("white_elo"):
                    st.caption(f"ELO: {game_info['white_elo']}")

            with col2:
                st.metric("Jugador Negro", game_info.get("black", "Desconocido"))
                if game_info.get("black_elo"):
                    st.caption(f"ELO: {game_info['black_elo']}")

            with col3:
                st.metric("Resultado", game_info.get("result", "Sin resultado"))
                if game_info.get("termination"):
                    st.caption(f"Terminación: {game_info['termination']}")

            # Información adicional
            info_items = []
            if game_info.get("event"):
                info_items.append(f"**Evento:** {game_info['event']}")
            if game_info.get("site"):
                info_items.append(f"**Lugar:** {game_info['site']}")
            if game_info.get("date"):
                info_items.append(f"**Fecha:** {game_info['date']}")
            if game_info.get("round"):
                info_items.append(f"**Ronda:** {game_info['round']}")
            if game_info.get("opening"):
                info_items.append(f"**Apertura:** {game_info['opening']}")

            if info_items:
                st.markdown(" | ".join(info_items))

    def _render_additional_controls(
        self, pgn_data: str, game_info: Optional[Dict[str, Any]]
    ) -> None:
        """Renderizar controles adicionales"""

        with st.expander("🔧 Controles Adicionales", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📋 Copiar PGN", key="copy_pgn"):
                    st.code(pgn_data, language="text")
                    st.success("PGN mostrado arriba")

            with col2:
                if st.button("📊 Analizar Partida", key="analyze_game"):
                    st.info("🚧 Función de análisis próximamente")

            with col3:
                if st.button("💾 Guardar Partida", key="save_game"):
                    st.info("🚧 Función de guardado próximamente")


# Singleton instance
_interactive_chess_board = None


def get_interactive_chess_board() -> InteractiveChessBoard:
    """Obtener instancia del tablero interactivo"""
    global _interactive_chess_board
    if _interactive_chess_board is None:
        _interactive_chess_board = InteractiveChessBoard()
    return _interactive_chess_board
