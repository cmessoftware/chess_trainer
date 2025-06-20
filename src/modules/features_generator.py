import chess

from modules.feature_engineering import is_center_controlled, is_pawn_endgame
from modules.pgn_utils import get_game_id


def extract_features_from_position(board, move):
    values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9
    }

    fen = board.fen()
    move_san = board.san(move)
    move_uci = move.uci()
    player_color = int(chess.WHITE) if board.turn else int(chess.BLACK)
    move_number = board.fullmove_number
    has_castling_rights = int(board.has_castling_rights(player_color))
    is_repetition = int(board.is_repetition())

    legal_before = list(board.legal_moves)
    self_mobility = len(legal_before)

    material = sum(
        values.get(piece.piece_type, 0) * (1 if piece.color else -1)
        for piece in board.piece_map().values()
    )
    material_total = sum(values.get(p.piece_type, 0)
                         for p in board.piece_map().values())
    num_pieces = sum(1 for p in board.piece_map().values()
                     if p.piece_type not in [chess.KING, chess.PAWN])

    # No hacemos board.push(move) aquí
    board_push_sim = board.copy()
    board_push_sim.push(move)
    opponent_mobility = len(list(board_push_sim.legal_moves))
    branching_factor = self_mobility + opponent_mobility

    piece_count = len(board.piece_map())
    phase = (
        "opening" if piece_count >= 24 else
        "middlegame" if piece_count >= 12 else
        "endgame"
    )
    is_low_mobility = int(self_mobility <= 5)

    return {
        "fen": fen,
        "move_san": move_san,
        "move_uci": move_uci,
        "material_balance": material,
        "material_total": material_total,
        "num_pieces": num_pieces,
        "branching_factor": branching_factor,
        "self_mobility": self_mobility,
        "opponent_mobility": opponent_mobility,
        "phase": phase,
        "player_color": player_color,
        "has_castling_rights": has_castling_rights,
        "move_number": move_number,
        "is_repetition": is_repetition,
        "is_low_mobility": is_low_mobility,
        "is_center_controlled": int(is_center_controlled(board, player_color)),
        "is_pawn_endgame": is_pawn_endgame(board),
    }


def create_metadata_feature_row(game_id: str, meta: dict) -> dict:
    """
    Creates a feature row with move_number = 0 and player_color = 'none' that contains general game metadata.
    Useful for storing contextual information even if no moves have been processed.

    :param game_id: Unique game ID.
    :param headers: Dictionary with PGN headers.
    :return: Dictionary compatible with the Features model.
    """
    return {
        "game_id": meta["game_id"],
        "move_number": 0,
        "player_color": "meta",
        "fen": None,
        "move_san": None,
        "move_uci": None,
        "material_balance": None,
        "material_total": None,
        "num_pieces": None,
        "branching_factor": None,
        "self_mobility": None,
        "opponent_mobility": None,
        "phase": None,
        "has_castling_rights": None,
        # MIGRATED-TODO: Implement global move number in features table failed
        "move_number_global": None,
        "is_repetition": None,
        "is_low_mobility": None,
        "is_center_controlled": None,
        "is_pawn_endgame": None,
        "score_diff": None,
        "site": meta.get("site", ""),
        "event": meta.get("event", ""),
        "date": meta.get("date", ""),
        "white_player": meta.get("white_player", ""),
        "black_player": meta.get("black_player", ""),
        "result": meta.get("result", ""),
        "num_moves": meta.get("num_moves", 0),
        "is_stockfish_test": False
    }


def generate_features_from_game(game, game_id=None, is_stockfish_test=False):
    rows = []

    # Inicializar el tablero
    setup = game.headers.get("SetUp", "0")
    fen = game.headers.get("FEN")

    if setup == "1" and fen:
        try:
            board = chess.Board(fen)
        except Exception as e:
            print(f"⚠️ FEN inválido en headers: {fen} -> {e}")
            return []
    else:
        board = chess.Board()

    if game_id is None:
        game_id = get_game_id(game)

    for move in game.mainline_moves():
        if not board.is_legal(move):
            print(f"⚠️ Movimiento ilegal: {move} en {board.fen()}")
            return []

        try:
            row = extract_features_from_position(board, move)

            row.update({
                "game_id": game_id,
                "site": game.headers.get("Site"),
                "event": game.headers.get("Event"),
                "date": game.headers.get("Date"),
                "white_player": game.headers.get("White"),
                "black_player": game.headers.get("Black"),
                "result": game.headers.get("Result"),
                "num_moves": game.end().board().fullmove_number,
                "is_stockfish_test": is_stockfish_test
            })

            rows.append(row)
            board.push(move)
        except Exception as e:
            print(f"⚠️ Error inesperado con {move}: {e}")
            return []

    return rows
