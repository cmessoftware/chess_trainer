# src/modules/feature_engineering.py

import chess
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from typing import Optional, List, Union


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


# ===== NUEVAS FUNCIONES PARA INTEGRACIÓN CON ML_PREPROCESSING =====

def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features basadas en información temporal de las partidas.
    
    Args:
        df: DataFrame con columna 'date'
        
    Returns:
        DataFrame con nuevas features temporales
    """
    if 'date' not in df.columns:
        return df
    
    df = df.copy()
    
    # Convertir fecha a datetime
    df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Features temporales
    df['year'] = df['date_parsed'].dt.year
    df['month'] = df['date_parsed'].dt.month
    df['day_of_week'] = df['date_parsed'].dt.dayofweek
    df['quarter'] = df['date_parsed'].dt.quarter
    
    # Características del período
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_holiday_season'] = ((df['month'] == 12) | (df['month'] == 1)).astype(int)
    
    return df


def create_sequence_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features basadas en secuencias de movimientos dentro de una partida.
    
    Args:
        df: DataFrame con datos por movimiento
        
    Returns:
        DataFrame con features de secuencia
    """
    df = df.copy()
    
    if 'game_id' not in df.columns or 'move_number' not in df.columns:
        return df
    
    # Ordenar por partida y número de movimiento
    df = df.sort_values(['game_id', 'move_number'])
    
    # Features de secuencia por partida
    for col in ['score_diff', 'material_balance', 'branching_factor']:
        if col in df.columns:
            # Movimiento anterior
            df[f'{col}_prev'] = df.groupby('game_id')[col].shift(1)
            
            # Cambio respecto al movimiento anterior
            df[f'{col}_change'] = df[col] - df[f'{col}_prev']
            
            # Tendencia (promedio móvil de últimos 3 movimientos)
            df[f'{col}_trend'] = df.groupby('game_id')[col].rolling(
                window=3, min_periods=1
            ).mean().reset_index(0, drop=True)
    
    # Features de momentum
    if 'score_diff' in df.columns:
        df['momentum_positive'] = (df['score_diff_change'] > 0).astype(int)
        df['momentum_streak'] = df.groupby('game_id')['momentum_positive'].cumsum()
    
    return df


def create_opponent_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features relacionadas con el oponente y la diferencia de nivel.
    
    Args:
        df: DataFrame con información de jugadores
        
    Returns:
        DataFrame con features del oponente
    """
    df = df.copy()
    
    # ELO features si están disponibles
    if 'white_elo' in df.columns and 'black_elo' in df.columns:
        # Diferencia de ELO absoluta
        df['elo_difference_abs'] = abs(df['white_elo'] - df['black_elo'])
        
        # Categoría de diferencia de ELO
        df['elo_gap_category'] = pd.cut(
            df['elo_difference_abs'],
            bins=[0, 50, 150, 300, 1000],
            labels=['equal', 'slight', 'moderate', 'large'],
            include_lowest=True
        )
        
        # Jugador es favorito/underdog
        if 'player_color' in df.columns:
            df['player_elo'] = np.where(
                df['player_color'] == 0,  # Asumiendo 0=white, 1=black
                df['white_elo'], 
                df['black_elo']
            )
            df['opponent_elo'] = np.where(
                df['player_color'] == 0,
                df['black_elo'],
                df['white_elo']
            )
            
            df['is_favorite'] = (df['player_elo'] > df['opponent_elo']).astype(int)
            df['elo_advantage'] = df['player_elo'] - df['opponent_elo']
    
    return df


def create_opening_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features relacionadas con la apertura de la partida.
    
    Args:
        df: DataFrame con información de la partida
        
    Returns:
        DataFrame con features de apertura
    """
    df = df.copy()
    
    # Determinar fase de apertura
    if 'move_number' in df.columns:
        df['is_opening_phase'] = (df['move_number'] <= 10).astype(int)
        df['is_early_middlegame'] = (
            (df['move_number'] > 10) & (df['move_number'] <= 20)
        ).astype(int)
    
    # Features específicas de apertura
    if 'phase' in df.columns:
        df['opening_length'] = df.groupby('game_id')['phase'].transform(
            lambda x: (x == 'opening').sum()
        )
    
    # Características del desarrollo en apertura
    if all(col in df.columns for col in ['move_number', 'has_castling_rights', 'is_opening_phase']):
        # ¿Enroque temprano?
        df['early_castling'] = (
            (df['move_number'] <= 8) & 
            (df['has_castling_rights'] == 0) &
            (df['has_castling_rights'].shift(1) == 1)
        ).astype(int)
    
    return df


def create_tactical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquece las features tácticas existentes con nuevas métricas.
    
    Args:
        df: DataFrame con tags tácticas
        
    Returns:
        DataFrame con features tácticas mejoradas
    """
    df = df.copy()
    
    # Contador de motivos tácticos por partida
    if 'tags' in df.columns and 'game_id' in df.columns:
        tactical_motifs = ['pin', 'fork', 'skewer', 'double_attack', 'sacrifice', 'deflection']
        
        for motif in tactical_motifs:
            df[f'has_{motif}'] = df['tags'].apply(
                lambda x: motif in str(x).lower() if x else False
            ).astype(int)
        
        # Total de motivos tácticos en la partida
        df['tactical_density'] = df.groupby('game_id')[
            [f'has_{motif}' for motif in tactical_motifs if f'has_{motif}' in df.columns]
        ].transform('sum').sum(axis=1)
    
    # Complejidad táctica
    if all(col in df.columns for col in ['branching_factor', 'self_mobility', 'opponent_mobility']):
        df['tactical_complexity'] = (
            df['branching_factor'] * 0.4 + 
            df['self_mobility'] * 0.3 + 
            df['opponent_mobility'] * 0.3
        )
    
    return df


def create_endgame_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features específicas para finales de partida.
    
    Args:
        df: DataFrame con información posicional
        
    Returns:
        DataFrame con features de finales
    """
    df = df.copy()
    
    # Actividad del rey en finales
    if all(col in df.columns for col in ['phase', 'is_center_controlled', 'num_pieces']):
        df['king_activity_endgame'] = np.where(
            (df['phase'] == 'endgame') & (df['num_pieces'] <= 8),
            df['is_center_controlled'],  # Rey activo = controla centro
            0
        )
    
    # Finales de peones
    if all(col in df.columns for col in ['is_pawn_endgame', 'material_balance']):
        df['pawn_endgame_advantage'] = np.where(
            df['is_pawn_endgame'] == 1,
            abs(df['material_balance']),  # Ventaja material en final de peones
            0
        )
    
    # Proximidad al final
    if 'num_pieces' in df.columns:
        df['endgame_proximity'] = np.maximum(0, (20 - df['num_pieces']) / 20)
    
    return df


def create_positional_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features posicionales avanzadas.
    
    Args:
        df: DataFrame con información posicional básica
        
    Returns:
        DataFrame con features posicionales mejoradas
    """
    df = df.copy()
    
    # Ratio de movilidad
    if 'self_mobility' in df.columns and 'opponent_mobility' in df.columns:
        df['mobility_dominance'] = np.where(
            df['opponent_mobility'] > 0,
            df['self_mobility'] / df['opponent_mobility'],
            df['self_mobility']  # Si oponente no tiene movilidad
        )
    
    # Índice de actividad de piezas
    if all(col in df.columns for col in ['self_mobility', 'num_pieces']):
        df['piece_activity_index'] = df['self_mobility'] / (df['num_pieces'] + 1)
    
    # Presión posicional
    if all(col in df.columns for col in ['is_center_controlled', 'self_mobility', 'material_balance']):
        df['positional_pressure'] = (
            df['is_center_controlled'] * 0.4 +
            (df['self_mobility'] / 50) * 0.3 +  # Normalizar movilidad
            np.tanh(df['material_balance'] / 100) * 0.3  # Normalizar material
        )
    
    return df


def apply_comprehensive_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones de feature engineering, tanto las originales
    como las nuevas funciones integradas con ML preprocessing.
    
    Args:
        df: DataFrame con datos de partidas de ajedrez
        
    Returns:
        DataFrame con features completas para ML
    """
    # Features originales
    df = apply_feature_engineering(df)
    
    # Nuevas features integradas
    df = create_temporal_features(df)
    df = create_sequence_features(df)
    df = create_opponent_features(df)
    df = create_opening_features(df)
    df = create_tactical_features(df)
    df = create_endgame_features(df)
    df = create_positional_features(df)
    
    return df
