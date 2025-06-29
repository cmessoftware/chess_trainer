from db.repository.features_repository import FeaturesRepository
import pandas as pd
import sys
import os
sys.path.insert(0, '/app/src')


repo = FeaturesRepository()  # Asumiendo que FuturesRepository es tu repositorio

tags_df = pd.DataFrame([
    {
        "move_number": 12,
        "player_color": 1,
        "tag": "discovered_attack",
        "score_diff": 150,
        "error_label": "good"
    },
    {
        "move_number": 15,
        "player_color": 0,
        "tag": "pin",
        "score_diff": -80,
        "error_label": "inaccuracy"
    }
])

repo.update_features_tags_and_score_diff(
    game_id='abcd1234testgame',
    tags_df=tags_df
)
