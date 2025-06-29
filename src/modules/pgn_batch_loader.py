import traceback

from anyio import Path
from db.models.games import Games
import io
import chess.pgn
import bz2
import gzip
import os
import shutil
import tarfile
import tempfile
from typing import IO, Generator, Iterable, Tuple
import zipfile

from modules.pgn_utils import get_game_id
from modules.utils import safe_int


def extract_pgn_files(input_path):
    def is_pgn_file(name):
        return name.endswith(".pgn")

    def extract_from_nested_compressed(name, byte_stream):
        # Detect inner compressed formats
        if name.endswith(".bz2"):
            with bz2.open(byte_stream, "rt", encoding="utf-8") as f:
                with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pgn", encoding="utf-8") as tmp:
                    shutil.copyfileobj(f, tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield name.replace(".bz2", ""), open(tmp.name, encoding="utf-8")
        elif name.endswith(".gz"):
            with gzip.open(byte_stream, "rt", encoding="utf-8") as f:
                with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pgn", encoding="utf-8") as tmp:
                    shutil.copyfileobj(f, tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield name.replace(".gz", ""), open(tmp.name, encoding="utf-8")
        elif name.endswith(".pgn"):
            with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
                tmp.write(byte_stream.read())
                tmp.flush()
                yield name, open(tmp.name, encoding="utf-8")

    if os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            yield from extract_pgn_files(os.path.join(input_path, filename))

    elif zipfile.is_zipfile(input_path):
        with zipfile.ZipFile(input_path) as zf:
            for name in zf.namelist():
                with zf.open(name) as f:
                    yield from extract_from_nested_compressed(name, f)

    elif tarfile.is_tarfile(input_path):
        with tarfile.open(input_path) as tf:
            for member in tf.getmembers():
                if member.isfile():
                    f = tf.extractfile(member)
                    if f:
                        yield from extract_from_nested_compressed(member.name, f)

    elif input_path.endswith(".gz") or input_path.endswith(".bz2"):
        # Single compressed file on disk
        yield from extract_from_nested_compressed(input_path, open(input_path, "rb"))

    elif is_pgn_file(input_path):
        yield input_path, open(input_path, encoding="utf-8")

    else:
        print(f"❌ Unsupported file or format: {input_path}")


def chunked_iterable(iterable: Iterable, chunk_size: int) -> Generator[list, None, None]:
    """
    Divide an iterable into chunks of a specified size.

    Args:
        iterable (Iterable): The input iterable to be divided into chunks.
        chunk_size (int): The size of each chunk.

    Yields:
        list: Lists containing up to `chunk_size` elements from the iterable.

    Example:
        >>> list(chunked_iterable([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]

    Notes:
        - The last chunk may contain fewer than `chunk_size` elements if the total number of items is not divisible by `chunk_size`.
        - This function does not consume more than `chunk_size` elements into memory at a time.

    """
    # Initialize an empty chunk list
    # Iterate through each item in the iterable
    #   Append item to the current chunk
    #   If chunk reaches the specified size, yield it and reset chunk
    # After iteration, yield any remaining items as the last chunk
    """Divide un iterable en bloques de tamaño `chunk_size`."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def load_pgn_batches(input_path: str, batch_size: int) -> Generator[list[Tuple[str, IO]], None, None]:
    """
    Carga archivos PGN desde el path dado, usando extract_pgn_files,
    y los agrupa en batches para procesamiento eficiente.
    """
    return chunked_iterable(extract_pgn_files(input_path), batch_size)


def extract_features_from_game(game_text: str) -> dict:
    try:
        print(f"🔍 Parsing game text resume: {game_text[:50]}")
        pgn_io = io.StringIO(game_text)
        game = chess.pgn.read_game(pgn_io)

        if game is None or not game.headers:
            print("❌ No se pudo leer el juego o no tiene encabezados.")
            return None

        # Verificar si tiene encabezado FEN
        if "FEN" not in game.headers:
            print("⚠️ No se encontró FEN en los encabezados, usando posición inicial.")
            board = chess.Board()  # posición inicial
        else:
            board = chess.Board(game.headers["FEN"])

        headers = game.headers
        game_id = get_game_id(game)

        # Intentar validar al menos la primera jugada
        moves = list(game.mainline_moves())
        board_copy = board.copy()
        for move in moves:
            board_copy.push(move)

        print(f"HEADERS: {headers}")

        return {
            "game_id": game_id,
            "white_player": headers.get("White", "Unknown"),
            "black_player": headers.get("Black", "Unknown"),
            "white_elo": safe_int(int(headers.get("WhiteElo", 0))) if safe_int(headers.get("WhiteElo")) else None,
            "black_elo": safe_int(int(headers.get("BlackElo", 0))) if safe_int(headers.get("BlackElo")) else None,
            "result": headers.get("Result", ""),
            "event": headers.get("Event", ""),
            "site": headers.get("Site", ""),
            "date": headers.get("Date", ""),
            "eco": headers.get("ECO", ""),
            "opening": headers.get("Opening", ""),
            "pgn": game_text,
            "source": headers.get("Source", "unknown"),
        }
    except Exception as e:
        print(f"❌ Error al procesar el juego: {e} - {traceback.format_exc()}")
        if e.__cause__:
            print(f"🔍 Causa del error: {e.__cause__}")
        return None
