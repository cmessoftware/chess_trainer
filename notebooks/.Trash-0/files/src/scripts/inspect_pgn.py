import chess.pgn
from modules.pgn_utils import (
    game_to_string,
    save_game_to_file,
    count_mainline_moves,
    count_all_moves_with_variants,
)
import argparse
import os
import glob

def process_pgn_file(input_file, output_file_base):
    with open(input_file, "r", encoding="utf-8") as pgn:
        all_mainline_moves = 0
        all_moves_with_variants = 0
        game_idx = 1
        #En cada ciclo leemos un juego del archivo PGN.
        # Si no hay más juegos, el método read_game devuelve None y salimos del ciclo.
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            print(f"File: {input_file} | Game {game_idx}:")
            all_mainline_moves += count_mainline_moves(game)
            print(f"Mainline moves: {all_mainline_moves}")
            all_moves_with_variants += count_all_moves_with_variants(game)
            print(f"All moves with variants: {all_moves_with_variants}")
            game_str = game_to_string(game)
            #save_game_to_file(game_str, f"{output_file_base}_{os.path.basename(input_file)}_game{game_idx}.pgn")
            game_idx += 1
    return all_mainline_moves, all_moves_with_variants, game_idx - 1

def main(input_dir, output_dir):
    mainline_moves = 0
    moves_with_variants = 0
    all_mainline_moves = 0
    all_moves_with_variants = 0
    all_games_count = 0
    os.makedirs(output_dir, exist_ok=True)
    pgn_files = glob.glob(os.path.join(input_dir, "*.pgn"))
    for pgn_file in pgn_files:
        output_file_base = os.path.join(output_dir, os.path.splitext(os.path.basename(pgn_file))[0])
        mainline_moves , moves_with_variants, games_count = process_pgn_file(pgn_file, output_file_base)
        all_mainline_moves += mainline_moves
        all_moves_with_variants += moves_with_variants
        all_games_count += games_count
        print(f"Total games processed: {all_games_count}")
        print(f"Processed {pgn_file}: Mainline moves = {mainline_moves}, Moves with variants = {moves_with_variants}")
    
    print(f"Total games found: {all_games_count}")
    print(f"Total mainline moves: {all_mainline_moves}")
    print(f"Total moves with variants: {all_moves_with_variants}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect all games from PGN files in a directory.")
    parser.add_argument("--input",default="/app/src/data/games" ,help="Path to the directory containing PGN files")
    parser.add_argument("--output", help="Directory to save the processed games")
    args = parser.parse_args()
    main(args.input, args.output)
