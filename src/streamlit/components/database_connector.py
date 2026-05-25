"""
🗃️ Database Connector for Streamlit Frontend
Provides database connectivity and query methods for Chess Trainer frontend.

Author: Chess Trainer Frontend Team
Date: 2026-01-15
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from db.postgres_utils import PostgreSQLConnection

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass


class DatabaseConnector:
    """
    Centralized database connector for Streamlit frontend.
    Provides cached queries and pagination for optimal performance.
    """

    def __init__(self):
        """Initialize database connection."""
        try:
            self.pg_conn = PostgreSQLConnection()
            self._connection_tested = False
        except Exception as e:
            st.error(f"❌ Error inicializando conexión a base de datos: {e}")
            self.pg_conn = None

    def test_connection(self) -> bool:
        """
        Test database connection and cache result.

        Returns:
            bool: True if connection is successful
        """
        if self._connection_tested:
            return self.pg_conn is not None

        try:
            if self.pg_conn is None:
                return False

            # Test with simple query
            result = self.pg_conn.execute_query(
                "SELECT COUNT(*) as total FROM games LIMIT 1"
            )

            if result and len(result) > 0:
                self._connection_tested = True
                return True
            else:
                return False

        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")
            return False

    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def get_database_stats(_self) -> Dict[str, int]:
        """
        Get general database statistics.

        Returns:
            dict: Database statistics
        """
        if not _self.test_connection():
            return {}

        try:
            stats = {}

            # Total games
            result = _self.pg_conn.execute_query(
                "SELECT COUNT(*) as total FROM games"
            )
            stats["total_games"] = result[0]["total"] if result else 0

            # Total features
            result = _self.pg_conn.execute_query(
                "SELECT COUNT(*) as total FROM features"
            )
            stats["total_features"] = result[0]["total"] if result else 0

            # Total analyzed tacticals
            result = _self.pg_conn.execute_query(
                "SELECT COUNT(*) as total FROM analyzed_tacticals"
            )
            stats["total_tacticals"] = result[0]["total"] if result else 0

            # Unique players
            result = _self.pg_conn.execute_query(
                """SELECT COUNT(DISTINCT player) as unique_players 
                   FROM (
                       SELECT white_player as player FROM games 
                       UNION 
                       SELECT black_player as player FROM games
                   ) as all_players"""
            )
            stats["unique_players"] = result[0]["unique_players"] if result else 0

            return stats

        except Exception as e:
            st.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}

    def get_games_paginated(
        self,
        page: int = 1,
        per_page: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[pd.DataFrame, int]:
        """
        Get paginated games from database.

        Args:
            page: Page number (1-based)
            per_page: Results per page
            filters: Dictionary of filters

        Returns:
            Tuple of (DataFrame, total_count)
        """
        if not self.test_connection():
            return pd.DataFrame(), 0

        try:
            # Build WHERE clause from filters
            where_conditions = []
            params = []

            if filters:
                if filters.get("player"):
                    where_conditions.append(
                        "(white_player ILIKE %s OR black_player ILIKE %s)"
                    )
                    params.extend([f"%{filters['player']}%", f"%{filters['player']}%"])

                if filters.get("min_rating"):
                    where_conditions.append("(white_elo >= %s OR black_elo >= %s)")
                    params.extend([filters["min_rating"], filters["min_rating"]])

                if filters.get("max_rating"):
                    where_conditions.append("(white_elo <= %s OR black_elo <= %s)")
                    params.extend([filters["max_rating"], filters["max_rating"]])

                if filters.get("result"):
                    where_conditions.append("result = %s")
                    params.append(filters["result"])

                if filters.get("date_from"):
                    where_conditions.append("date_played >= %s")
                    params.append(filters["date_from"])

                if filters.get("date_to"):
                    where_conditions.append("date_played <= %s")
                    params.append(filters["date_to"])

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as count
                FROM games 
                {where_clause}
            """

            result = self.pg_conn.execute_query(
                count_query, params
            )
            total_count = result[0]["count"] if result else 0

            # Get paginated results
            offset = (page - 1) * per_page

            games_query = f"""
                SELECT 
                    game_id,
                    white_player,
                    black_player,
                    white_elo,
                    black_elo,
                    result,
                    date_played,
                    opening,
                    time_control,
                    source
                FROM games 
                {where_clause}
                ORDER BY date_played DESC, game_id DESC
                LIMIT %s OFFSET %s
            """

            params.extend([per_page, offset])

            result = self.pg_conn.execute_query(
                games_query, params
            )

            if result:
                # Convert list of dicts to DataFrame
                df = pd.DataFrame(result)
                return df, total_count
            else:
                return pd.DataFrame(), total_count

        except Exception as e:
            st.error(f"❌ Error obteniendo partidas: {e}")
            return pd.DataFrame(), 0

    def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific game.

        Args:
            game_id: Game identifier

        Returns:
            dict: Game details or None
        """
        if not self.test_connection():
            return None

        try:
            query = """
                SELECT 
                    game_id, white_player, black_player,
                    white_elo, black_elo, result,
                    date_played, opening, eco,
                    time_control, source, pgn, created_at
                FROM games 
                WHERE game_id = %s
            """

            result = self.pg_conn.execute_query(query, [game_id])

            if result:
                # Result is already a dictionary
                return result[0]
            else:
                return None

        except Exception as e:
            st.error(f"❌ Error obteniendo detalles del juego: {e}")
            return None

    @st.cache_data(ttl=600)  # Cache por 10 minutos
    def get_unique_players(_self, limit: int = 100) -> List[str]:
        """
        Get list of unique player names for search suggestions.

        Args:
            limit: Maximum number of players to return

        Returns:
            list: Player names
        """
        if not _self.test_connection():
            return []

        try:
            query = """
                SELECT DISTINCT player, COUNT(*) as game_count
                FROM (
                    SELECT white_player as player FROM games 
                    UNION ALL 
                    SELECT black_player as player FROM games
                ) as all_players
                WHERE player IS NOT NULL AND player != ''
                GROUP BY player
                ORDER BY game_count DESC, player ASC
                LIMIT %s
            """

            result = _self.pg_conn.execute_query(query, [limit])

            if result:
                return [row["player"] for row in result]
            else:
                return []

        except Exception as e:
            st.error(f"❌ Error obteniendo lista de jugadores: {e}")
            return []

    def search_games(self, query: str, limit: int = 10) -> pd.DataFrame:
        """
        Search games by text query (players, opening, etc.).

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            DataFrame: Search results
        """
        if not self.test_connection() or not query.strip():
            return pd.DataFrame()

        try:
            search_query = f"%{query}%"

            sql = """
                SELECT 
                    game_id, white_player, black_player,
                    white_elo, black_elo, result,
                    date_played, opening
                FROM games 
                WHERE 
                    white_player ILIKE %s OR 
                    black_player ILIKE %s OR 
                    opening ILIKE %s
                ORDER BY date_played DESC
                LIMIT %s
            """

            result = self.pg_conn.execute_query(
                sql,
                [search_query, search_query, search_query, limit]
            )

            if result:
                # Convert list of dicts to DataFrame  
                df = pd.DataFrame(result)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            st.error(f"❌ Error en búsqueda: {e}")
            return pd.DataFrame()

    def export_games_to_pgn(self, game_ids: List[str]) -> str:
        """
        Export selected games to PGN format.

        Args:
            game_ids: List of game IDs to export

        Returns:
            str: PGN content
        """
        if not self.test_connection() or not game_ids:
            return ""

        try:
            placeholders = ", ".join(["%s"] * len(game_ids))
            query = f"""
                SELECT 
                    white_player, black_player, result,
                    date_played, opening, pgn
                FROM games 
                WHERE game_id IN ({placeholders})
                ORDER BY date_played DESC
            """

            result = self.pg_conn.execute_query(query, game_ids)

            if not result:
                return ""

            pgn_content = []

            for row in result:
                # Extract data from dictionary
                white_player = row.get('white_player')
                black_player = row.get('black_player')
                result_str = row.get('result')
                date_played = row.get('date_played')
                opening_name = row.get('opening')
                moves_text = row.get('pgn')

                # Format date (date_played is already a string)
                date_str = date_played if date_played else "????.??.??"

                # Create PGN headers
                pgn_headers = [
                    f'[Event "Chess Trainer Export"]',
                    f'[Site "Chess Trainer"]',
                    f'[Date "{date_str}"]',
                    f'[Round "-"]',
                    f'[White "{white_player or "Unknown"}"]',
                    f'[Black "{black_player or "Unknown"}"]',
                    f'[Result "{result_str or "*"}"]',
                ]

                if opening_name:
                    pgn_headers.append(f'[Opening "{opening_name}"]')

                pgn_headers.append("")  # Empty line after headers

                # Add moves
                if moves_text:
                    pgn_headers.append(moves_text)
                else:
                    pgn_headers.append("*")

                pgn_headers.append("")  # Empty line between games

                pgn_content.extend(pgn_headers)

            return "\n".join(pgn_content)

        except Exception as e:
            st.error(f"❌ Error exportando PGN: {e}")
            return ""


# Singleton instance for caching
@st.cache_resource
def get_database_connector():
    """Get cached database connector instance."""
    return DatabaseConnector()


def display_connection_status():
    """Display database connection status in sidebar."""
    db = get_database_connector()

    if db.test_connection():
        st.sidebar.success("✅ Conectado a PostgreSQL")

        # Show basic stats
        stats = db.get_database_stats()
        if stats:
            st.sidebar.metric("Partidas", f"{stats.get('total_games', 0):,}")
            st.sidebar.metric("Características", f"{stats.get('total_features', 0):,}")
            st.sidebar.metric("Jugadores", f"{stats.get('unique_players', 0):,}")
    else:
        st.sidebar.error("❌ Sin conexión a BD")
        st.sidebar.info("💡 Verifica que PostgreSQL esté corriendo")
