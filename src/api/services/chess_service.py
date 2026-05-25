import chess
import chess.engine
import chess.pgn
import io
import psycopg2
import os
from models.schemas import GameResponse, AnalysisResponse, MoveValidationResponse
from typing import Optional, List, Dict, Any
import time
import logging


class ChessService:
    """
    Servicio para manejar lógica de ajedrez

    Incluye análisis, validación de movimientos y conexión a la DB
    """

    def __init__(self):
        self.engine_path = None  # TODO: Configurar ruta a Stockfish
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "chess_trainer_db",
            "user": "chess",
            "password": "chess_pass",
        }

    def _get_db_connection(self):
        """Crear conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logging.error(f"Error conectando a la base de datos: {e}")
            return None

    async def get_game(self, game_id: str) -> Optional[GameResponse]:
        """
        Obtener una partida de la base de datos PostgreSQL
        """
        conn = self._get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT game_id, pgn, white_player, white_elo, 
                           black_player, black_elo, result, eco, opening, source, date_played
                    FROM games 
                    WHERE game_id = %s
                """,
                    (game_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                # Parsear el PGN para obtener los movimientos
                moves = []
                if row[1]:  # pgn
                    try:
                        pgn_game = chess.pgn.read_game(io.StringIO(row[1]))
                        if pgn_game:
                            moves = [move.uci() for move in pgn_game.mainline_moves()]
                    except Exception as e:
                        logging.warning(f"Error parsing PGN for game {game_id}: {e}")

                return GameResponse(
                    game_id=row[0],
                    white=row[2] or "Unknown",
                    black=row[4] or "Unknown",
                    result=row[6] or "*",
                    event="Tournament",  # Default since we don't have event column
                    site="Unknown Site",  # Default since we don't have site column
                    date=str(row[10]) if row[10] else "Unknown Date",
                    moves=moves,
                    white_elo=row[3],
                    black_elo=row[5],
                    eco=row[7],
                    opening=row[8],
                    source=row[9],
                )
        finally:
            conn.close()

    async def get_games_list(
        self,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None,
        search: Optional[str] = None,
        user_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtener lista de partidas con paginación y búsqueda
        Si user_filter se proporciona, solo muestra partidas donde el usuario es un jugador
        """
        conn = self._get_db_connection()
        if not conn:
            return {"games": [], "total": 0, "limit": limit, "offset": offset}

        try:
            with conn.cursor() as cursor:
                # Query con filtro opcional por fuente y búsqueda
                where_conditions = []
                params = []

                if source:
                    where_conditions.append("source = %s")
                    params.append(source)

                if search:
                    where_conditions.append(
                        "(white_player ILIKE %s OR black_player ILIKE %s)"
                    )
                    search_pattern = f"%{search}%"
                    params.extend([search_pattern, search_pattern])

                # Filtro de usuario: solo partidas importadas por el usuario
                if user_filter:
                    where_conditions.append("imported_by = %s")
                    params.append(user_filter)

                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)

                # Contar total
                cursor.execute(f"SELECT COUNT(*) FROM games {where_clause}", params)
                total = cursor.fetchone()[0]

                # Obtener partidas con paginación
                cursor.execute(
                    f"""
                    SELECT game_id, white_player, black_player, white_elo, black_elo, 
                           result, eco, opening, source, date_played
                    FROM games 
                    {where_clause}
                    ORDER BY date_played DESC, game_id
                    LIMIT %s OFFSET %s
                """,
                    params + [limit, offset],
                )

                games = cursor.fetchall()

                games_list = []
                for game in games:
                    games_list.append(
                        {
                            "game_id": game[0],
                            "white_player": game[1],
                            "black_player": game[2],
                            "white_elo": game[3],
                            "black_elo": game[4],
                            "result": game[5],
                            "event": "Tournament",  # Default since we don't have event column
                            "site": "Unknown Site",  # Default since we don't have site column
                            "date": str(game[9]) if game[9] else "Unknown Date",
                            "eco": game[6],
                            "opening": game[7],
                            "source": game[8],
                        }
                    )

                return {
                    "games": games_list,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
        finally:
            conn.close()

    async def get_sources(self) -> List[str]:
        """
        Obtener todas las fuentes de partidas disponibles
        """
        conn = self._get_db_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT DISTINCT source FROM games WHERE source IS NOT NULL ORDER BY source"
                )
                sources = cursor.fetchall()
                return [source[0] for source in sources]
        finally:
            conn.close()

    async def get_game_moves(self, game_id: str) -> List[str]:
        """
        Obtener solo los movimientos de una partida
        """
        game = await self.get_game(game_id)
        return game.moves if game else []

    async def analyze_position(self, fen: str, depth: int = 10) -> AnalysisResponse:
        """
        Analizar una posición usando Stockfish
        """
        start_time = time.time()

        try:
            # TODO: Integrar con Stockfish real
            # Por ahora simulamos análisis

            board = chess.Board(fen)

            # Análisis simulado
            best_move = None
            evaluation = 0.0

            if board.legal_moves:
                # Tomar el primer movimiento legal como "mejor" (placeholder)
                best_move = str(list(board.legal_moves)[0])
                evaluation = 0.1  # Evaluación simulada

            analysis_time = time.time() - start_time

            return AnalysisResponse(
                fen=fen,
                best_move=best_move,
                evaluation=evaluation,
                depth=depth,
                analysis_time=analysis_time,
            )

        except Exception as e:
            logging.error(f"Error en análisis: {e}")
            return AnalysisResponse(
                fen=fen,
                best_move=None,
                evaluation=None,
                depth=depth,
                analysis_time=time.time() - start_time,
            )

    async def validate_move(
        self, game_id: int, move_str: str
    ) -> MoveValidationResponse:
        """
        Validar un movimiento en el contexto de una partida
        """
        try:
            # Obtener la partida
            game = await self.get_game(game_id)
            if not game:
                return MoveValidationResponse(
                    valid=False, move=None, message="Partida no encontrada"
                )

            # Recrear la posición actual
            board = chess.Board()
            for move in game.moves:
                try:
                    board.push_san(move)
                except chess.ValueError:
                    # Si hay un error en los movimientos guardados
                    break

            # Validar el movimiento propuesto
            try:
                parsed_move = board.parse_san(move_str)
                if parsed_move in board.legal_moves:
                    return MoveValidationResponse(
                        valid=True, move=move_str, message="Movimiento válido"
                    )
                else:
                    return MoveValidationResponse(
                        valid=False,
                        move=move_str,
                        message="Movimiento ilegal en esta posición",
                    )
            except chess.ValueError:
                return MoveValidationResponse(
                    valid=False,
                    move=move_str,
                    message="Notación de movimiento inválida",
                )

        except Exception as e:
            logging.error(f"Error validando movimiento: {e}")
            return MoveValidationResponse(
                valid=False, move=move_str, message="Error interno validando movimiento"
            )

    async def validate_move_simple(self, move_str: str) -> MoveValidationResponse:
        """
        Validar un movimiento de ajedrez sin contexto de partida específica
        Útil para validación general de notación
        """
        try:
            # Crear tablero inicial
            board = chess.Board()

            # Intentar parsear el movimiento
            try:
                # Primero intentar como SAN (e4, Nf3, etc.)
                parsed_move = board.parse_san(move_str)
                return MoveValidationResponse(
                    valid=True, move=move_str, message="Notación de movimiento válida"
                )
            except chess.ValueError:
                try:
                    # Intentar como UCI (e2e4, g1f3, etc.)
                    parsed_move = chess.Move.from_uci(move_str)
                    if parsed_move in board.legal_moves:
                        return MoveValidationResponse(
                            valid=True, move=move_str, message="Movimiento UCI válido"
                        )
                    else:
                        return MoveValidationResponse(
                            valid=False,
                            move=move_str,
                            message="Movimiento UCI inválido para posición inicial",
                        )
                except chess.ValueError:
                    return MoveValidationResponse(
                        valid=False,
                        move=move_str,
                        message="Notación de movimiento no reconocida (use SAN o UCI)",
                    )

        except Exception as e:
            logging.error(f"Error validando movimiento simple: {e}")
            return MoveValidationResponse(
                valid=False, move=move_str, message="Error interno validando movimiento"
            )
