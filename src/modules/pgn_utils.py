from typing import Dict, List
import chess.pgn
from chess.pgn import StringExporter
import io
from pathlib import Path
from typing import Tuple

from nbconvert import ScriptExporter

# Validate pgn text


def is_valid_pgn(pgn_text: str) -> Tuple[bool, chess.pgn.Game]:
    """
    Checks if the PGN text is valid.
    Returns True if valid, False otherwise.
    """
    try:
        parsed_game = chess.pgn.read_game(io.StringIO(pgn_text))

        if not parsed_game or not isinstance(parsed_game, chess.pgn.Game):
            print("⚠️ Could not parse PGN or it is not a valid Game.")
            return False, None

        headers = parsed_game.headers
        critical_headers = ["Event", "Site",
                            "Date", "White", "Black", "Result"]
        if not all(h in headers and headers[h].strip() for h in critical_headers):
            print(f"⚠️ Missing critical headers in the game: {headers}")
            return False, None
        return True, parsed_game
    except Exception as e:
        print(f"⚠️ Error validating PGN: {e}")
        return False, None


# 🔁 Load from PGN string
def load_pgn_from_string(pgn_str):
    return chess.pgn.read_game(io.StringIO(pgn_str))

# 📄 Load first game from a file


def load_pgn_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return chess.pgn.read_game(f)

# 📄📄 Load all games from a file


def load_multiple_games_from_file(path):
    games = []
    with open(path, "r", encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            games.append(game)
    return games


def split_pgn_file_by_games(pgn_text: str, games_per_chunk: int = 10):
    """
    Split a PGN string into chunks of N games (as strings).
    Each chunk is a list of complete PGN games.

    Args:
        pgn_text (str): Entire content of a PGN file as a single string.
        games_per_chunk (int): Number of games per yielded chunk.

    Yields:
        List[str]: A list of PGN strings (one per game) in each chunk.
    """

    """
    Split a PGN string (or Game object) into chunks of N games.
    """
    import io
    import chess.pgn

    # Convierte si es objeto Game
    if isinstance(pgn_text, chess.pgn.Game):
        output = io.StringIO()
        pgn_text = pgn_text.accept(StringExporter(
            headers=True, variations=True, comments=True))

    if not isinstance(pgn_text, str):
        raise TypeError(f"Expected pgn_text to be str, got {type(pgn_text)}")

    # Split the PGN by double newlines between games
    raw_games = pgn_text.strip().split("\n\n[")
    normalized_games = []

    for i, game_text in enumerate(raw_games):
        if i == 0:
            normalized_games.append(game_text.strip())
        else:
            normalized_games.append("[{}".format(game_text.strip()))

    # Yield in chunks
    for i in range(0, len(normalized_games), games_per_chunk):
        yield normalized_games[i:i + games_per_chunk]


def parse_games_from_orm(orm_games):
    """
    Transforms a list of ORM Games objects into a list of tuples (game_id, chess.pgn.Game)

    Parameters:
    orm_games (List[Games]): List of Games ORM objects

    Returns:
    List[Tuple[str, chess.pgn.Game]]: List of tuples with game_id and parsed PGN object
    """
    parsed = []
    for g in orm_games:
        try:
            pgn_text = g.pgn
            if not pgn_text:
                continue
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if game is not None:
                parsed.append((g.game_id, game))
        except Exception as e:
            print(f"⚠️ Error parsing game_id={g.game_id}: {e}")
    return parsed


def extract_features_from_game(game, game_id):
    # Extract basic features as an example
    return {
        "game_id": game_id,
        "site": game.headers.get("Site", ""),
        "event": game.headers.get("Event", ""),
        "date": game.headers.get("Date", ""),
        "white_player": game.headers.get("White", ""),
        "black_player": game.headers.get("Black", ""),
        "result": game.headers.get("Result", ""),
        "num_moves": len(list(game.mainline_moves()))
    }


def count_moves(game: chess.pgn.Game) -> int:
    return sum(1 for _ in game.mainline_moves())


def get_game_id(game):
    try:
        # Logic to generate a unique hash or game identifier
        # Usually based on PGN or key metadata
        exporter = chess.pgn.StringExporter(
            headers=True, variations=False, comments=False)
        pgn_str = game.accept(exporter)
        import hashlib
        return hashlib.sha256(pgn_str.encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"⚠️ Error getting game ID: {e}")
        if e.__cause__:
            print(f"   Cause: {e.__cause__}")
        return None


# 📁📄📄 Load all games from all .pgn files in a folder
def load_all_games_from_dir(directory):
    all_games = []
    pgn_files = Path(directory).rglob("*.pgn")
    for pgn_path in sorted(pgn_files):
        games = load_multiple_games_from_file(pgn_path)
        all_games.extend(games)

    print(f"🔍 Loaded {len(all_games)} games from {directory}")
    return all_games

# 🧠 Compatibility with the old name


def parse_pgn_file(path):
    return load_multiple_games_from_file(path)


def pgn_to_position_sequence(pgn_text: str, critical_fens: List[str] = None) -> List[Dict]:
    """
    Converts a PGN into a sequence of positions with FENs and marks the critical ones.

    :param pgn_text: Full PGN content as string
    :param critical_fens: Optional list of FENs considered critical
    :return: List of dicts with 'fen', 'comment' and 'is_critical'
    """
    critical_fens = set(critical_fens or [])
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()
    position_sequence = []

    for move in game.mainline_moves():
        fen_before_move = board.fen()
        is_critical = fen_before_move in critical_fens
        position_sequence.append({
            "fen": fen_before_move,
            "comment": "",
            "is_critical": is_critical
        })
        board.push(move)

    # Add the final position if desired
    position_sequence.append({
        "fen": board.fen(),
        "comment": "",
        "is_critical": board.fen() in critical_fens
    })

    return position_sequence


# 📝 Extract positions (FENs) from all moves
def load_pgn_positions(path):
    positions = []
    with open(path, 'r') as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                positions.append(board.fen())
    return positions

# 🔄 Serialize to PGN string


def game_to_string(game):
    out = io.StringIO()
    print(game, file=out)
    return out.getvalue()

# 💾 Save PGN game to file


def save_game_to_file(game, path):
    with open(path, "w", encoding="utf-8") as f:
        print(game, file=f)


def count_mainline_moves(game):
    return len(list(game.mainline_moves()))


def count_all_moves_with_variants(game):
    def recursive_count(node):
        count = len(node.variations)
        for variation in node.variations:
            count += recursive_count(variation)
        return count

    return recursive_count(game)


def extract_all_moves_with_variants(game):
    moves = []

    def recurse(node, move_number=1, variant_depth=0, board=None):
        if board is None:
            board = node.board()

        for var in node.variations:
            new_board = board.copy()
            new_board.push(var.move)
            moves.append({
                "move_number": move_number,
                "variant_depth": variant_depth,
                "san": board.san(var.move),
                "uci": var.move.uci(),
                "fen": board.fen()
            })
            recurse(var, move_number + 1, variant_depth + 1, new_board)

    recurse(game)
    return moves


def get_game_headers(game):
    headers = {}
    for key, value in game.headers.items():
        headers[key] = value
    return headers
