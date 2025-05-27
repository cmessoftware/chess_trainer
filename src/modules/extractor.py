# extractor.py - Extrae features básicas desde una lista de posiciones

import numpy as np

def extract_features_from_fen(fen: str) -> np.ndarray:
    # Ejemplo simplificado: cuenta material
    from chess import Board

    board = Board(fen)
    material = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9,
        'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9
    }
    total = sum(material.get(piece.symbol(), 0) for piece in board.piece_map().values())
    return np.array([total])
