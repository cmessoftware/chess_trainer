
import pandera as pa
from pandera import Column, DataFrameSchema, Check

training_dataset_schema = DataFrameSchema({
    "fen": Column(pa.String),
    "move_san": Column(pa.String),
    "move_uci": Column(pa.String),
    "material_balance": Column(pa.Float),
    "material_total": Column(pa.Float, checks=Check.ge(0)),
    "num_pieces": Column(pa.Int, checks=Check.ge(0)),
    "branching_factor": Column(pa.Int, checks=Check.ge(0)),
    "self_mobility": Column(pa.Int, checks=Check.ge(0)),
    "opponent_mobility": Column(pa.Int, checks=Check.ge(0)),
    "phase": Column(pa.String, checks=Check.isin(["opening", "middlegame", "endgame"])),
    "player_color": Column(pa.String, checks=Check.isin(["white", "black"])),
    "has_castling_rights": Column(pa.Int, checks=Check.isin([0, 1])),
    "move_number": Column(pa.Int, checks=Check.ge(1)),
    "is_repetition": Column(pa.Int, checks=Check.isin([0, 1])),
    "is_low_mobility": Column(pa.Int, checks=Check.isin([0, 1])),
    "is_center_controlled": Column(pa.Int, checks=Check.isin([0, 1])),
    "is_pawn_endgame": Column(pa.Int, checks=Check.isin([0, 1]))
})

def validate_training_dataset(df):
    return training_dataset_schema.validate(df)
