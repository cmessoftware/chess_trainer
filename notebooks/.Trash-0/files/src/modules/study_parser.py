import chess.pgn
from io import StringIO


def extract_chapters(pgn_text: str):
    chapters = []
    pgn_io = StringIO(pgn_text)

    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
        chapters.append({
            "title": game.headers.get("Event", ""),
            "pgn": str(game),
            "tags": game.headers,
            "moves": game.board().variation_san(game.mainline_moves()),
        })
    return chapters
