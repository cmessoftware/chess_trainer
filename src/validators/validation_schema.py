
import pandera.pandas as pa
from pandera import Column, DataFrameSchema, Check
# Updated schema to match the provided dataset schema
training_dataset_schema = DataFrameSchema({
    "game_id": Column(pa.String),
    "move_number": Column(pa.Int),
    "fen": Column(pa.String),
    "move_san": Column(pa.String),
    "move_uci": Column(pa.String),
    "material_balance": Column(pa.Float),
    "material_total": Column(pa.Float),
    "num_pieces": Column(pa.Int),
    "branching_factor": Column(pa.Int),
    "self_mobility": Column(pa.Float),
    "opponent_mobility": Column(pa.Float),
    "phase": Column(pa.String),
    "player_color": Column(pa.Int),
    "has_castling_rights": Column(pa.Float),
    "move_number_global": Column(pa.Float),
    "is_repetition": Column(pa.Float),
    "is_low_mobility": Column(pa.Float),
    "is_center_controlled": Column(pa.Float),
    "is_pawn_endgame": Column(pa.Float),
    "tags": Column(pa.String, nullable=True),
    "score_diff": Column(pa.Float, nullable=True),
    "site": Column(pa.String, nullable=True),
    "event": Column(pa.String, nullable=True),
    "date": Column(pa.String, nullable=True),
    "white_player": Column(pa.String, nullable=True),
    "black_player": Column(pa.String, nullable=True),
    "result": Column(pa.String, nullable=True)
})

# Function to validate the training dataset against the schema
def validate_training_dataset(df):
    return training_dataset_schema.validate(df)
