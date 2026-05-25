#!/usr/bin/env python3
"""
Verificar qué jugadores están disponibles en la base de datos PostgreSQL
"""
import pandas as pd
import os
import dotenv
from sqlalchemy import create_engine

# Load environment variables
dotenv.load_dotenv()

print("🔍 VERIFICANDO JUGADORES DISPONIBLES EN POSTGRESQL...")

DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")
engine = create_engine(DATABASE_URL)

try:
    # Verificar jugadores en la tabla games
    games_query = """
        SELECT 
            white_player, 
            COUNT(*) as games_as_white,
            AVG(CASE WHEN white_elo ~ '^[0-9]+$' THEN CAST(white_elo AS INTEGER) END) as avg_white_elo
        FROM games 
        WHERE white_player IS NOT NULL
        GROUP BY white_player
        ORDER BY games_as_white DESC
        LIMIT 20
    """
    
    white_players = pd.read_sql(games_query, engine)
    
    print("\n🟡 TOP 20 JUGADORES COMO BLANCAS:")
    for _, row in white_players.iterrows():
        name = row['white_player']
        games = row['games_as_white']
        elo = row['avg_white_elo'] if pd.notna(row['avg_white_elo']) else 'N/A'
        print(f"   {name:25}: {games:4} partidas | ELO promedio: {elo}")
    
    # Verificar jugadores como negras
    black_query = """
        SELECT 
            black_player, 
            COUNT(*) as games_as_black,
            AVG(CASE WHEN black_elo ~ '^[0-9]+$' THEN CAST(black_elo AS INTEGER) END) as avg_black_elo
        FROM games 
        WHERE black_player IS NOT NULL
        GROUP BY black_player
        ORDER BY games_as_black DESC
        LIMIT 20
    """
    
    black_players = pd.read_sql(black_query, engine)
    
    print("\n⚫ TOP 20 JUGADORES COMO NEGRAS:")
    for _, row in black_players.iterrows():
        name = row['black_player']
        games = row['games_as_black']
        elo = row['avg_black_elo'] if pd.notna(row['avg_black_elo']) else 'N/A'
        print(f"   {name:25}: {games:4} partidas | ELO promedio: {elo}")
    
    # Buscar específicamente cmess y th3
    specific_query = """
        SELECT 
            player_name,
            total_games,
            avg_elo,
            color_distribution
        FROM (
            SELECT 
                white_player as player_name,
                COUNT(*) as total_games,
                AVG(CASE WHEN white_elo ~ '^[0-9]+$' THEN CAST(white_elo AS INTEGER) END) as avg_elo,
                'blancas' as color_distribution
            FROM games 
            WHERE white_player ILIKE '%cmess%' OR white_player ILIKE '%th3%' OR white_player ILIKE '%hound%'
            GROUP BY white_player
            
            UNION ALL
            
            SELECT 
                black_player as player_name,
                COUNT(*) as total_games,
                AVG(CASE WHEN black_elo ~ '^[0-9]+$' THEN CAST(black_elo AS INTEGER) END) as avg_elo,
                'negras' as color_distribution
            FROM games 
            WHERE black_player ILIKE '%cmess%' OR black_player ILIKE '%th3%' OR black_player ILIKE '%hound%'
            GROUP BY black_player
        ) combined
        ORDER BY total_games DESC
    """
    
    specific_players = pd.read_sql(specific_query, engine)
    
    print("\n🎯 BÚSQUEDA ESPECÍFICA (cmess, th3, hound):")
    if len(specific_players) > 0:
        for _, row in specific_players.iterrows():
            name = row['player_name']
            games = row['total_games']
            elo = row['avg_elo'] if pd.notna(row['avg_elo']) else 'N/A'
            color = row['color_distribution']
            print(f"   {name:25}: {games:4} partidas como {color} | ELO: {elo}")
    else:
        print("   ❌ No se encontraron jugadores con esos nombres")
    
    # Verificar features disponibles para cmess
    features_query = """
        SELECT 
            COUNT(*) as total_features,
            COUNT(DISTINCT f.game_id) as unique_games,
            MIN(f.move_number) as min_move,
            MAX(f.move_number) as max_move
        FROM features f
        LEFT JOIN games g ON f.game_id = g.game_id
        WHERE g.white_player ILIKE '%cmess%' OR g.black_player ILIKE '%cmess%'
    """
    
    features_df = pd.read_sql(features_query, engine)
    
    print(f"\n📊 FEATURES DISPONIBLES PARA CMESS:")
    if len(features_df) > 0:
        row = features_df.iloc[0]
        print(f"   Total features: {row['total_features']:,}")
        print(f"   Partidas únicas: {row['unique_games']:,}")
        print(f"   Rango movimientos: {row['min_move']} - {row['max_move']}")
    
    engine.dispose()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    engine.dispose()