"""
Script para hacer predicciones en tiempo real con el modelo entrenado
Procedimiento completo usando MLflow
"""

import sys
import logging
from pathlib import Path
import chess
import chess.engine
import mlflow

# Añadir path de src
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.chess_error_predictor import ChessErrorPredictor
from modules.features_generator import extract_features_from_position
from modules.stockfish_analysis import get_engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTimeChessPredictor:
    """
    Predictor en tiempo real para análisis de jugadas de ajedrez
    """

    def __init__(self, model_name="ChessErrorClassifier", version="latest"):
        """Inicializar predictor con modelo desde MLflow"""
        self.predictor = ChessErrorPredictor()
        self.engine = None

        # Cargar modelo desde MLflow
        if not self.predictor.load_model(model_name=model_name, version=version):
            logger.error(
                "No se pudo cargar el modelo. Asegúrate de haber entrenado uno primero."
            )
            raise ValueError("Modelo no disponible")

        logger.info("✅ Predictor en tiempo real inicializado")

    def setup_engine(self, depth=15):
        """Configurar motor Stockfish"""
        try:
            self.engine, _ = get_engine(depth)
            logger.info("✅ Motor Stockfish configurado")
            return True
        except Exception as e:
            logger.error(f"❌ Error configurando Stockfish: {e}")
            return False

    def analyze_position(self, fen, move_uci, get_real_score=True):
        """
        Analizar una posición y predecir el tipo de error

        Args:
            fen: Posición en formato FEN
            move_uci: Jugada en formato UCI (ej: "e2e4")
            get_real_score: Si obtener evaluación real con Stockfish

        Returns:
            dict: Análisis completo con predicción y evaluación real
        """
        try:
            # Crear tablero desde FEN
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)

            if move not in board.legal_moves:
                return {"error": "Jugada ilegal"}

            # Extraer features de la posición
            features = extract_features_from_position(board, move)

            # Predicción del modelo
            prediction = self.predictor.predict_move_error(features)

            result = {
                "fen": fen,
                "move_uci": move_uci,
                "move_san": board.san(move),
                "predicted_error": prediction["predicted_error"],
                "confidence": prediction["confidence"],
                "probabilities": prediction["probabilities"],
                "features_used": features,
            }

            # Evaluación real con Stockfish (opcional)
            if get_real_score and self.engine:
                try:
                    # Evaluar antes de la jugada
                    info_before = self.engine.analyse(
                        board, chess.engine.Limit(depth=15)
                    )
                    score_before = info_before["score"].relative.score(mate_score=10000)

                    # Hacer la jugada y evaluar
                    board.push(move)
                    info_after = self.engine.analyse(
                        board, chess.engine.Limit(depth=15)
                    )
                    score_after = info_after["score"].relative.score(mate_score=10000)

                    # Calcular diferencia real
                    real_score_diff = (
                        abs(score_after - score_before)
                        if score_before and score_after
                        else None
                    )

                    # Clasificación real basada en Stockfish
                    if real_score_diff is not None:
                        if real_score_diff <= 50:
                            real_error = "good"
                        elif real_score_diff <= 150:
                            real_error = "inaccuracy"
                        elif real_score_diff <= 500:
                            real_error = "mistake"
                        else:
                            real_error = "blunder"
                    else:
                        real_error = "unknown"

                    result.update(
                        {
                            "stockfish_evaluation": {
                                "score_before": score_before,
                                "score_after": score_after,
                                "score_diff": real_score_diff,
                                "real_error_classification": real_error,
                                "prediction_correct": prediction["predicted_error"]
                                == real_error,
                            }
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error en evaluación Stockfish: {e}")
                    result["stockfish_evaluation"] = {"error": str(e)}

            return result

        except Exception as e:
            logger.error(f"Error analizando posición: {e}")
            return {"error": str(e)}

    def analyze_game_moves(self, pgn_string, max_moves=None):
        """
        Analizar todas las jugadas de una partida

        Args:
            pgn_string: Partida en formato PGN
            max_moves: Máximo número de jugadas a analizar

        Returns:
            list: Lista de análisis por jugada
        """
        try:
            import chess.pgn
            import io

            # Parsear PGN
            game = chess.pgn.read_game(io.StringIO(pgn_string))
            if not game:
                return {"error": "PGN inválido"}

            board = game.board()
            moves_analysis = []
            move_count = 0

            for move in game.mainline_moves():
                if max_moves and move_count >= max_moves:
                    break

                # Analizar la jugada
                fen = board.fen()
                analysis = self.analyze_position(fen, move.uci(), get_real_score=True)

                analysis.update(
                    {
                        "move_number": move_count + 1,
                        "player": "white" if board.turn else "black",
                    }
                )

                moves_analysis.append(analysis)
                board.push(move)
                move_count += 1

            # Estadísticas del análisis
            if moves_analysis:
                predictions = [
                    m["predicted_error"]
                    for m in moves_analysis
                    if "predicted_error" in m
                ]
                correct_predictions = [
                    m["stockfish_evaluation"]["prediction_correct"]
                    for m in moves_analysis
                    if "stockfish_evaluation" in m
                    and "prediction_correct" in m["stockfish_evaluation"]
                ]

                stats = {
                    "total_moves_analyzed": len(moves_analysis),
                    "error_distribution": {
                        error: predictions.count(error)
                        for error in ["good", "inaccuracy", "mistake", "blunder"]
                    },
                    "prediction_accuracy": (
                        sum(correct_predictions) / len(correct_predictions)
                        if correct_predictions
                        else None
                    ),
                }
            else:
                stats = {"total_moves_analyzed": 0}

            return {"moves_analysis": moves_analysis, "game_statistics": stats}

        except Exception as e:
            logger.error(f"Error analizando partida: {e}")
            return {"error": str(e)}

    def close(self):
        """Cerrar recursos"""
        if self.engine:
            self.engine.quit()
            logger.info("Motor Stockfish cerrado")


def demo_prediction():
    """Demostración del sistema de predicción"""
    logger.info("=== DEMO: PREDICCIÓN EN TIEMPO REAL ===")

    # Inicializar predictor
    predictor = RealTimeChessPredictor()
    predictor.setup_engine()

    # Ejemplo 1: Analizar una jugada específica
    logger.info("\\n1. Análisis de jugada específica:")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Posición inicial
    move = "e2e4"  # Apertura común

    result = predictor.analyze_position(fen, move)
    logger.info(f"FEN: {fen}")
    logger.info(f"Jugada: {move}")
    logger.info(f"Predicción: {result['predicted_error']}")
    logger.info(f"Confianza: {result['confidence']:.4f}")

    # Ejemplo 2: Analizar una partida completa (primeras 10 jugadas)
    logger.info("\\n2. Análisis de partida completa:")
    sample_pgn = """
    [Event "Sample Game"]
    [White "Player1"]
    [Black "Player2"]
    
    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
    """

    game_analysis = predictor.analyze_game_moves(sample_pgn, max_moves=5)

    if "moves_analysis" in game_analysis:
        logger.info(
            f"Jugadas analizadas: {game_analysis['game_statistics']['total_moves_analyzed']}"
        )
        logger.info("Distribución de errores predichos:")
        for error, count in game_analysis["game_statistics"][
            "error_distribution"
        ].items():
            logger.info(f"  {error}: {count}")

        if game_analysis["game_statistics"]["prediction_accuracy"]:
            logger.info(
                f"Precisión de predicciones: {game_analysis['game_statistics']['prediction_accuracy']:.4f}"
            )

    predictor.close()
    logger.info("\\n✅ Demo completada")


if __name__ == "__main__":
    demo_prediction()
