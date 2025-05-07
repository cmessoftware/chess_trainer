# utils.py - Funciones auxiliares

import chess.pgn
import os

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
