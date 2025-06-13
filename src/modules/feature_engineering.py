# src/modules/feature_engineering.py

import chess
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer


def is_center_controlled(board, color):
    central_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    control = 0
    for square in central_squares:
        if board.is_attacked_by(color, square):
            control += 1
    return control >= 2  # Se considera control si al menos 2 están bajo ataque


def is_pawn_endgame(board):
    return int(all(piece.piece_type in [chess.KING, chess.PAWN] for piece in board.piece_map().values()))


def binarize_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Expande la columna 'tags' (lista de strings) en columnas binarias."""
    if df['tags'].notna().any():
        mlb = MultiLabelBinarizer()
        tag_matrix = mlb.fit_transform(df['tags'].dropna())
        df_tags_bin = pd.DataFrame(tag_matrix, columns=mlb.classes_)
        df_tags_bin.index = df['tags'].dropna().index
        df = pd.concat([df, df_tags_bin], axis=1)
    return df


def add_error_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas binarias: is_blunder, is_mistake, is_inaccuracy basadas en tags."""
    df['is_blunder'] = df['tags'].apply(
        lambda x: 'blunder' in x if isinstance(x, list) else False)
    df['is_mistake'] = df['tags'].apply(
        lambda x: 'mistake' in x if isinstance(x, list) else False)
    df['is_inaccuracy'] = df['tags'].apply(
        lambda x: 'inaccuracy' in x if isinstance(x, list) else False)
    return df


def score_to_label(score: float) -> str:
    """Clasifica la diferencia de evaluación en etiquetas."""
    if score < -200:
        return 'blunder'
    elif score < -100:
        return 'mistake'
    elif score < -50:
        return 'inaccuracy'
    else:
        return 'ok'


def add_score_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna 'score_label' basada en score_diff."""
    df['score_label'] = df['score_diff'].apply(score_to_label)
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica columnas categóricas para ML: phase_encoded, color_encoded."""
    df['phase_encoded'] = df['phase'].map(
        {'opening': 0, 'middlegame': 1, 'endgame': 2})
    df['color_encoded'] = df['player_color'].map({'white': 0, 'black': 1})
    return df


def extract_castling_rights(fen: str, player: str) -> int:
    """Determina si el jugador (white o black) aún puede enrocar en base al FEN."""
    try:
        castling = fen.split()[2]
        if player == 'white':
            return int('K' in castling or 'Q' in castling)
        else:
            return int('k' in castling or 'q' in castling)
    except:
        return 0


def add_castling_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas separadas: white_can_castle, black_can_castle."""
    df['white_can_castle'] = df['fen'].apply(
        lambda f: extract_castling_rights(f, 'white'))
    df['black_can_castle'] = df['fen'].apply(
        lambda f: extract_castling_rights(f, 'black'))
    return df


def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las transformaciones de feature engineering al dataframe."""
    df = binarize_tags(df)
    df = add_error_flags(df)
    df = add_score_labels(df)
    df = encode_categoricals(df)
    df = add_castling_columns(df)
    return df
