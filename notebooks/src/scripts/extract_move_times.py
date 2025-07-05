
import chess.pgn
import re
import pandas as pd

def parse_clock(comment):
    match = re.search(r"\[%clk (\d+):(\d+):(\d+)\]", comment)
    if match:
        h, m, s = map(int, match.groups())
        return h * 3600 + m * 60 + s
    return None

def classify_impulse(time_control_base):
    if time_control_base <= 300:
        return 1  # Blitz → umbral 1s
    elif time_control_base <= 900:
        return 3  # Rapid → umbral 3s
    else:
        return 5  # Classical or longer

def extract_move_times(pgn_path, output_csv, limit_games=None):
    data = []
    with open(pgn_path, "r", encoding="utf-8") as f:
        game_count = 0
        while True:
            game = chess.pgn.read_game(f)
            if game is None or (limit_games and game_count >= limit_games):
                break

            tc_header = game.headers.get("TimeControl", "600+0")
            try:
                base_sec = int(tc_header.split("+")[0])
            except:
                base_sec = 600  # fallback

            impulse_threshold = classify_impulse(base_sec)

            board = game.board()
            prev_white_clk = None
            prev_black_clk = None
            ply = 0

            for node in game.mainline():
                move = node.move
                comment = node.comment
                clk = parse_clock(comment)
                ply += 1
                move_color = "white" if board.turn else "black"

                move_time = None
                is_impulsive = None

                if clk is not None:
                    if move_color == "white" and prev_white_clk is not None:
                        move_time = prev_white_clk - clk
                        is_impulsive = move_time <= impulse_threshold
                    elif move_color == "black" and prev_black_clk is not None:
                        move_time = prev_black_clk - clk
                        is_impulsive = move_time <= impulse_threshold

                    if move_color == "white":
                        prev_white_clk = clk
                    else:
                        prev_black_clk = clk

                row = {
                    "fen": board.fen(),
                    "move_san": board.san(move),
                    "move_uci": move.uci(),
                    "move_number": board.fullmove_number,
                    "player_color": move_color,
                    "move_time_sec": move_time,
                    "is_impulsive": int(is_impulsive) if is_impulsive is not None else None
                }
                data.append(row)
                board.push(move)

            game_count += 1
            if game_count % 50 == 0:
                print(f"{game_count} partidas procesadas...")

    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    print(f"Tiempos de jugadas extraídos a: {output_csv}")
