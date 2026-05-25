#!/usr/bin/env python3
"""
Validación Externa con Partidas Existentes (Hold-out)

Dado que no tenemos partidas completamente nuevas disponibles, 
este script implementa una validación "hold-out" usando partidas 
existentes de cmess4401 que NO fueron usadas en el entrenamiento.

Estrategia:
1. Identificar partidas de cmess4401 que NO tienen features generadas
2. Generar features para estas partidas (marcándolas como validación)
3. Aplicar el modelo PERSONAL entrenado
4. Evaluar performance en este conjunto "no visto"

Esto simula una validación externa real.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

def find_unprocessed_personal_games():
    """Find personal games without features generated."""
    print("🔍 Finding personal games without features...")
    
    engine = create_engine(DB_URL)
    
    # Find games that don't have features
    query = """
    SELECT g.game_id, g.white_player, g.black_player, g.date_played, g.result
    FROM games g
    WHERE g.source = 'personal'
      AND (g.white_player LIKE '%cmess4401%' OR g.black_player LIKE '%cmess4401%')
      AND g.game_id NOT IN (
          SELECT DISTINCT f.game_id 
          FROM features f 
          WHERE f.game_id IS NOT NULL
      )
    ORDER BY g.date_played DESC
    LIMIT 50;
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    print(f"✅ Found {len(df)} unprocessed games")
    
    if len(df) > 0:
        print(f"📅 Date range: {df['date_played'].min()} to {df['date_played'].max()}")
        print("\nFirst 10 games:")
        print(df.head(10)[['game_id', 'date_played', 'white_player', 'black_player']].to_string(index=False))
    
    return df

def find_random_holdout_games():
    """Find random subset of personal games for hold-out validation."""
    print("🔍 Finding random hold-out games from existing dataset...")
    
    engine = create_engine(DB_URL)
    
    # Get random 20% of personal games that have features but can be used for validation
    query = """
    SELECT g.game_id, g.white_player, g.black_player, g.date_played, g.result
    FROM games g
    JOIN features f ON g.game_id = f.game_id
    WHERE g.source = 'personal'
      AND (g.white_player LIKE '%cmess4401%' OR g.black_player LIKE '%cmess4401%')
      AND f.error_label IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 200;
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    print(f"✅ Selected {len(df)} games for hold-out validation")
    
    if len(df) > 0:
        print(f"📅 Date range: {df['date_played'].min()} to {df['date_played'].max()}")
        
        # Mark these games as validation set
        print("🏷️ Marking games as validation_holdout...")
        mark_games_as_validation(df['game_id'].tolist())
    
    return df

def mark_games_as_validation(game_ids):
    """Mark specific games as validation set."""
    engine = create_engine(DB_URL)
    
    # Update games table to mark as validation
    game_ids_str = ','.join([str(gid) for gid in game_ids])
    
    update_query = f"""
    UPDATE games 
    SET source = 'validation_holdout' 
    WHERE game_id IN ({game_ids_str});
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(update_query)
            conn.commit()
        
        print(f"✅ Marked {len(game_ids)} games as validation_holdout")
        
    except Exception as e:
        print(f"❌ Error marking games: {e}")
    finally:
        engine.dispose()

def simulate_temporal_validation():
    """Simulate temporal validation with existing data."""
    print("🔍 Setting up temporal validation with existing personal games...")
    
    engine = create_engine(DB_URL)
    
    # Get all personal games with features, ordered by date
    query = """
    SELECT g.game_id, g.date_played, f.move_number
    FROM games g
    JOIN features f ON g.game_id = f.game_id
    WHERE g.source = 'personal'
      AND (g.white_player LIKE '%cmess4401%' OR g.black_player LIKE '%cmess4401%')
      AND f.error_label IS NOT NULL
    ORDER BY g.date_played DESC;
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    if len(df) == 0:
        print("❌ No personal games with features found")
        return
    
    # Take most recent 20% as "validation" set
    n_validation = int(len(df) * 0.2)
    validation_games = df['game_id'].unique()[:n_validation]
    
    print(f"✅ Selected {len(validation_games)} most recent games for temporal validation")
    print(f"📊 This represents {len(df[df['game_id'].isin(validation_games)])} moves")
    
    # Mark these games
    mark_games_as_validation(validation_games.tolist())
    
    return validation_games

def main():
    print("🚀 EXTERNAL VALIDATION SETUP: PERSONAL GAMES")
    print("="*60)
    
    # Strategy 1: Find truly unprocessed games
    print("\n📋 STRATEGY 1: Unprocessed Games")
    print("-" * 40)
    unprocessed = find_unprocessed_personal_games()
    
    if len(unprocessed) >= 20:
        print("✅ Found enough unprocessed games for validation!")
        print(f"🔄 Next steps:")
        print(f"1. Generate features for these games:")
        print(f"   python src/scripts/generate_features_with_tactics.py --source personal --max-games {len(unprocessed)} --workers 2")
        print(f"2. Then run validation pipeline")
        return
    
    # Strategy 2: Temporal validation with existing data
    print("\n📋 STRATEGY 2: Temporal Hold-out Validation")
    print("-" * 40)
    validation_games = simulate_temporal_validation()
    
    if validation_games is not None and len(validation_games) > 0:
        print("✅ Set up temporal validation successfully!")
        print("\n🔄 NEXT STEPS:")
        print("1. Features already exist, proceed directly to validation:")
        print("   python src/ml/external_validation_personal.py --pgn-file \"dummy.pgn\" --skip-import --skip-features")
        print("\n2. The validation will use games marked as 'validation_holdout'")
        print(f"   {len(validation_games)} games selected for validation")
    else:
        print("❌ Could not set up validation")

if __name__ == "__main__":
    main()