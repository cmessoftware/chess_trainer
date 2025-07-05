import chess
import chess.pgn
from io import StringIO

class StudyGenerator:
    def __init__(self, repo):
        self.repo = repo

    def generate_positions_from_pgn(self, study_id: str, pgn: str):
        game = chess.pgn.read_game(StringIO(pgn))
        if not game:
            raise ValueError("No se pudo parsear la partida PGN")

        board = game.board()
        sequence = []

        for move in game.mainline_moves():
            board.push(move)
            fen = board.fen()
            position_data = {
                "fen": fen,
                "comment": "",
                "is_critical": False
            }
            sequence.append(position_data)

        # Guardar en base de datos
        study = self.repo.get_study_by_id(study_id)
        study['position_sequence'] = sequence
        self.repo.save_study(study)

        return sequence
