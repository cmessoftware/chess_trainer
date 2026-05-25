import os
from sqlalchemy import create_engine, text

db_url = 'postgresql://chess:chess_pass@localhost:5432/chess_trainer_db'
engine = create_engine(db_url)

query = """
SELECT game_id, player_color, COUNT(*) as moves
FROM features
WHERE game_id LIKE 'b73806%'
GROUP BY game_id, player_color
ORDER BY game_id, player_color
"""

with engine.connect() as conn:
    result = conn.execute(text(query))
    for row in result:
        game_id, player_color, moves = row
        color = "WHITE" if player_color == 1 else "BLACK"
        print(f"{game_id} - {color}: {moves} moves")
