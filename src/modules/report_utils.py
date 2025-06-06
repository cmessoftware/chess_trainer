import os
import chess
from modules.feature_engineering import is_center_controlled, is_pawn_endgame


def extract_features_from_position(board, move):
    values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25,
        chess.ROOK: 5, chess.QUEEN: 9
    }

    fen = board.fen()
    move_san = board.san(move)
    move_uci = move.uci()
    player_color = chess.WHITE if board.turn else chess.BLACK
    move_number = board.fullmove_number
    has_castling_rights = int(board.has_castling_rights(player_color))
    is_repetition = int(board.is_repetition())

    legal_before = list(board.legal_moves)
    self_mobility = len(legal_before)

    material = sum(
        values.get(piece.piece_type, 0) * (1 if piece.color else -1)
        for piece in board.piece_map().values()
    )
    material_total = sum(values.get(p.piece_type, 0) for p in board.piece_map().values())
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
        "is_pawn_endgame": is_pawn_endgame(board)
    }



def generate_features_from_game(game):
    rows = []

    # Inicializar el tablero según headers
    setup = game.headers.get("SetUp", "0")
    fen = game.headers.get("FEN")
    
    if setup == "1" and fen:
        try:
            board = chess.Board(fen)
        except Exception as e:
            print(f"⚠️ FEN inválido en headers: {fen} -> {e}")
            return []
    else:
        board = chess.Board()  # posición inicial estándar

    for move in game.mainline_moves():
        if not board.is_legal(move):
            print(f"⚠️ Movimiento ilegal: {move} en {board.fen()}")
            return []

        try:
            row = extract_features_from_position(board, move)
            rows.append(row)
            board.push(move)
        except Exception as e:
            print(f"⚠️ Error inesperado con {move}: {e}")
            return []

    return rows



def check_pgn_headers(directory):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith(".pgn"):
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    setup = game.headers.get("SetUp", "0")
                    fen = game.headers.get("FEN", None)
                    if setup == "1" and fen:
                        results.append((filename, game.headers.get("Event", ""), fen))
    return results

# Usalo así:
# resultados = check_pgn_headers("data/games")
# for archivo, evento, fen in resultados:
#     print(f"🎯 Juego con FEN en {archivo} ({evento}): {fen}")
