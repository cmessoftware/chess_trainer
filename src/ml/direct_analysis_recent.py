#!/usr/bin/env python3
"""
Análisis Directo de Partidas Recientes

Este script analiza directamente las partidas descargadas sin necesidad
de importar a la base de datos, aplicando el modelo PERSONAL entrenado.

Análisis que realizará:
1. Parse de partidas PGN descargadas
2. Generación de features básicas en memoria
3. Aplicación del modelo PERSONAL
4. Reporte de análisis de errores por partida
"""

import os
import sys
import chess
import chess.pgn
import chess.engine
import pandas as pd
import numpy as np
import mlflow
from datetime import datetime
from pathlib import Path
from io import StringIO
from collections import defaultdict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_recent_games(pgn_file):
    """Load and parse recent games from PGN file."""
    print(f"📥 Loading games from {pgn_file}")
    
    games = []
    
    try:
        with open(pgn_file, 'r', encoding='utf-8') as f:
            game_count = 0
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                
                game_count += 1
                
                # Extract game info
                game_info = {
                    'game_id': game_count,
                    'white': game.headers.get('White', 'Unknown'),
                    'black': game.headers.get('Black', 'Unknown'), 
                    'result': game.headers.get('Result', '*'),
                    'date': game.headers.get('Date', 'Unknown'),
                    'white_elo': game.headers.get('WhiteElo', '1500'),
                    'black_elo': game.headers.get('BlackElo', '1500'),
                    'time_control': game.headers.get('TimeControl', 'Unknown'),
                    'pgn_game': game
                }
                
                games.append(game_info)
                
                if game_count % 100 == 0:
                    print(f"   📝 Loaded {game_count} games...")
    
    except Exception as e:
        print(f"❌ Error loading games: {e}")
        return []
    
    print(f"✅ Loaded {len(games)} games total")
    return games

def classify_game_type(time_control):
    """Classify game type based on chess.com standard time controls."""
    if not time_control or time_control == 'Unknown':
        return 'Unknown'
    
    # Convert time control to lowercase for easier parsing
    tc = time_control.lower()
    
    # Daily games (correspondence chess)
    if '86400' in tc or '259200' in tc or '/86400' in tc or '/259200' in tc:
        return 'Daily'
    
    # Extract base time in seconds
    try:
        # Handle formats like "600+5" or "120+1"
        if '+' in tc:
            base_time = int(tc.split('+')[0])
        else:
            base_time = int(tc)
        
        # Chess.com classification:
        # Bullet: < 3 minutes total time
        # Blitz: 3-10 minutes total time  
        # Rapid: 10+ minutes total time
        # Daily: correspondence (handled above)
        
        # Calculate total approximate time (base + 30 moves * increment)
        if '+' in tc:
            increment = int(tc.split('+')[1])
            total_time = base_time + (30 * increment)  # Estimate for 30 moves
        else:
            total_time = base_time
        
        if total_time < 180:  # Less than 3 minutes total
            return 'Bullet'
        elif total_time < 600:  # 3-10 minutes total
            return 'Blitz' 
        else:  # 10+ minutes total
            return 'Rapid'
            
    except (ValueError, AttributeError):
        return 'Unknown'

def analyze_user_games(games, target_user='cmess1315'):
    """Filter and analyze games for specific user."""
    print(f"🎯 Analyzing games for {target_user}")
    
    user_games = []
    
    for game_info in games:
        white = game_info['white'].lower()
        black = game_info['black'].lower()
        
        if target_user.lower() in white or target_user.lower() in black:
            # Determine user color
            user_color = 'white' if target_user.lower() in white else 'black'
            game_info['user_color'] = user_color
            game_info['user_rating'] = game_info['white_elo'] if user_color == 'white' else game_info['black_elo']
            # Classify game type
            game_info['game_type'] = classify_game_type(game_info['time_control'])
            user_games.append(game_info)
    
    print(f"✅ Found {len(user_games)} games for {target_user}")
    
    # Analyze game types
    if user_games:
        game_types = defaultdict(int)
        for game in user_games:
            game_types[game['game_type']] += 1
        
        print("🎮 Game types distribution:")
        for game_type, count in sorted(game_types.items()):
            print(f"   {game_type}: {count} games ({count/len(user_games)*100:.1f}%)")
    
    if user_games:
        # Analyze ratings
        ratings = [int(g['user_rating']) for g in user_games if g['user_rating'].isdigit()]
        if ratings:
            print(f"📊 Rating range: {min(ratings)} - {max(ratings)} (avg: {np.mean(ratings):.0f})")
        
        # Analyze dates
        dates = [g['date'] for g in user_games if g['date'] != 'Unknown']
        if dates:
            print(f"📅 Date range: {min(dates)} to {max(dates)}")
    
    return user_games

def extract_basic_features_from_game(game_info):
    """Extract basic features from a single game."""
    features = []
    game = game_info['pgn_game']
    user_color = game_info['user_color']
    
    board = chess.Board()
    move_number = 0
    
    try:
        for node in game.mainline():
            move = node.move
            move_number += 1
            
            # Only analyze moves by our user
            is_user_move = (user_color == 'white' and move_number % 2 == 1) or \
                          (user_color == 'black' and move_number % 2 == 0)
            
            if is_user_move:
                # Calculate basic features
                features_dict = {
                    'game_id': game_info['game_id'],
                    'move_number': move_number,
                    'move_san': board.san(move),
                    'move_uci': move.uci(),
                    'fen': board.fen(),
                    
                    # Basic position features
                    'material_total': sum([
                        len(board.pieces(chess.PAWN, chess.WHITE)) + len(board.pieces(chess.PAWN, chess.BLACK)),
                        len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)) * 3,
                        len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)) * 3,
                        len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)) * 5,
                        len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)) * 9
                    ]),
                    
                    'num_pieces': len(board.piece_map()),
                    'num_moves': move_number,
                    'branching_factor': len(list(board.legal_moves)),
                    'self_mobility': len(list(board.legal_moves)),
                    'opponent_mobility': 0,  # Would need to flip board
                    'has_castling_rights': int(board.has_castling_rights(chess.WHITE if user_color == 'white' else chess.BLACK)),
                    'move_number_global': move_number,
                    'is_repetition': int(board.is_repetition()),
                    'is_low_mobility': int(len(list(board.legal_moves)) < 10),
                    'is_center_controlled': 0,  # Simplified
                    'is_pawn_endgame': int(len(board.pieces(chess.QUEEN, chess.WHITE)) == 0 and 
                                          len(board.pieces(chess.QUEEN, chess.BLACK)) == 0),
                }
                
                features.append(features_dict)
            
            # Make the move
            board.push(move)
            
            # Limit analysis to avoid memory issues
            if move_number > 50:  # Analyze first 50 moves only
                break
                
    except Exception as e:
        print(f"⚠️ Error analyzing game {game_info['game_id']}: {e}")
    
    return features

def load_personal_model():
    """Load the trained PERSONAL model - preferring calibrated version."""
    print("🤖 Loading PERSONAL model...")
    
    try:
        # Set MLflow tracking URI to local
        mlflow.set_tracking_uri("file:./mlruns")
        
        # Try to load calibrated model first, fallback to original
        model_names = ["personal_calibrated", "personal_conservative_specialist"]
        
        for model_name in model_names:
            try:
                model = mlflow.sklearn.load_model(f"models:/{model_name}/latest")
                print(f"✅ Modelo cargado: {model_name}")
                if hasattr(model, 'classes_'):
                    print(f"   Clases disponibles: {list(model.classes_)}")
                return model
            except Exception as e:
                print(f"⚠️ No se pudo cargar {model_name}: {e}")
                continue
                
        raise Exception("No se pudo cargar ningún modelo")
        
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return None

def predict_errors_for_games(user_games, model, max_games=50):
    """Predict errors for user games."""
    if max_games is None:
        max_games = len(user_games)
    
    print(f"🎯 Analyzing up to {max_games} games...")
    
    all_predictions = []
    game_summaries = []
    
    # Progress tracking for large analyses
    total_games = min(len(user_games), max_games)
    
    for i, game_info in enumerate(user_games[:max_games]):
        # Progress report - more frequent for large analyses
        if i % 100 == 0 and i > 0 and total_games > 500:
            print(f"   📈 Progreso: {i}/{total_games} partidas ({i/total_games*100:.1f}%)")
        elif i % 50 == 0 and i > 0 and total_games > 200:
            print(f"   📝 Analizando partida {i}/{total_games} ({i/total_games*100:.1f}%)")
        elif (i + 1) % 10 == 0 and total_games <= 200:
            print(f"   📝 Analyzing game {i + 1}/{total_games}")
        
        # Extract features for this game
        game_features = extract_basic_features_from_game(game_info)
        
        if not game_features:
            continue
            
        # Convert to DataFrame
        df_features = pd.DataFrame(game_features)
        
        # Prepare features for prediction (same as training)
        feature_columns = [
            'material_total', 'num_pieces', 'branching_factor', 'self_mobility', 
            'opponent_mobility', 'has_castling_rights', 'move_number_global',
            'is_repetition', 'is_low_mobility', 'is_center_controlled', 
            'is_pawn_endgame', 'num_moves'
        ]
        
        # Select only available features
        available_features = [col for col in feature_columns if col in df_features.columns]
        X = df_features[available_features].fillna(0)
        
        if len(X) == 0:
            continue
            
        # Make predictions
        try:
            predictions = model.predict(X)
            probabilities = model.predict_proba(X)
            
            # Add predictions to features
            df_features['predicted_error'] = predictions
            
            # Add probabilities
            # Use actual model classes instead of hardcoded ones
            if hasattr(model, 'classes_'):
                classes = list(model.classes_)  # Convert to list if numpy array
            else:
                classes = ['blunder', 'good', 'inaccuracy', 'mistake']  # Fallback
            
            for j, class_name in enumerate(classes):
                if j < probabilities.shape[1]:  # Check if index exists
                    df_features[f'prob_{class_name}'] = probabilities[:, j]
            
            all_predictions.append(df_features)
            
            # Create game summary
            game_summary = {
                'game_id': game_info['game_id'],
                'date': game_info['date'],
                'user_color': game_info['user_color'],
                'user_rating': game_info['user_rating'],
                'result': game_info['result'],
                'game_type': game_info['game_type'],  # Add game type
                'time_control': game_info['time_control'],  # Add time control
                'total_moves_analyzed': len(predictions),
                'predicted_blunders': sum(predictions == 'blunder'),
                'predicted_mistakes': sum(predictions == 'mistake'),
                'predicted_inaccuracies': sum(predictions == 'inaccuracy'),
                'predicted_good': sum(predictions == 'good'),
                # Store probabilities with correct mapping
                'avg_prob_blunder': probabilities[:, classes.index('blunder')].mean() if 'blunder' in classes else 0,
                'avg_prob_mistake': probabilities[:, classes.index('mistake')].mean() if 'mistake' in classes else 0,
                'avg_prob_inaccuracy': probabilities[:, classes.index('inaccuracy')].mean() if 'inaccuracy' in classes else 0,
                'avg_prob_good': probabilities[:, classes.index('good')].mean() if 'good' in classes else 0,
            }
            
            game_summaries.append(game_summary)
            
        except Exception as e:
            print(f"⚠️ Error predicting for game {game_info['game_id']}: {e}")
    
    return all_predictions, game_summaries

def create_segmented_analysis_report(game_summaries, target_user):
    """Create comprehensive analysis report segmented by game type."""
    print(f"\n🏆 ANÁLISIS SEGMENTADO POR TIPO: {target_user.upper()}")
    print("="*70)
    
    if not game_summaries:
        print("❌ No games analyzed")
        return
    
    df_summary = pd.DataFrame(game_summaries)
    
    # Overall statistics first
    total_games = len(df_summary)
    total_moves = df_summary['total_moves_analyzed'].sum()
    total_errors = (df_summary['predicted_blunders'].sum() + 
                   df_summary['predicted_mistakes'].sum() + 
                   df_summary['predicted_inaccuracies'].sum())
    
    print(f"📊 RESUMEN GLOBAL:")
    print(f"  🎮 Partidas analizadas: {total_games}")
    print(f"  🎯 Jugadas analizadas: {total_moves}")
    print(f"  ⚠️ Errores predichos: {total_errors} ({total_errors/total_moves*100:.1f}%)")
    
    # Show breakdown of error types
    total_blunders = df_summary['predicted_blunders'].sum()
    total_mistakes = df_summary['predicted_mistakes'].sum()
    total_inaccuracies = df_summary['predicted_inaccuracies'].sum()
    total_good = df_summary['predicted_good'].sum()
    
    print(f"\n📈 DISTRIBUCIÓN DETALLADA DE PREDICCIONES:")
    print(f"  🔥 Blunders (errores graves): {total_blunders} ({total_blunders/total_moves*100:.1f}%)")
    print(f"  ⚠️ Mistakes (errores moderados): {total_mistakes} ({total_mistakes/total_moves*100:.1f}%)")
    print(f"  📉 Inaccuracies (imprecisiones): {total_inaccuracies} ({total_inaccuracies/total_moves*100:.1f}%)")
    print(f"  ✅ Good moves (jugadas buenas): {total_good} ({total_good/total_moves*100:.1f}%)")
    
    # Show average probabilities
    avg_prob_blunder = df_summary['avg_prob_blunder'].mean()
    avg_prob_mistake = df_summary['avg_prob_mistake'].mean() 
    avg_prob_inaccuracy = df_summary['avg_prob_inaccuracy'].mean()
    avg_prob_good = df_summary['avg_prob_good'].mean()
    
    print(f"\n🎯 PROBABILIDADES PROMEDIO DEL MODELO:")
    print(f"  🔥 Blunder: {avg_prob_blunder:.1%}")
    print(f"  ⚠️ Mistake: {avg_prob_mistake:.1%}") 
    print(f"  📉 Inaccuracy: {avg_prob_inaccuracy:.1%}")
    print(f"  ✅ Good: {avg_prob_good:.1%}")
    
    # Analyze by game type
    print(f"\n🎮 ANÁLISIS POR TIPO DE PARTIDA:")
    print("-" * 50)
    
    for game_type in sorted(df_summary['game_type'].unique()):
        type_games = df_summary[df_summary['game_type'] == game_type]
        
        if len(type_games) == 0:
            continue
            
        type_total_games = len(type_games)
        type_total_moves = type_games['total_moves_analyzed'].sum()
        type_total_errors = (type_games['predicted_blunders'].sum() + 
                            type_games['predicted_mistakes'].sum() + 
                            type_games['predicted_inaccuracies'].sum())
        
        type_blunders = type_games['predicted_blunders'].sum()
        type_mistakes = type_games['predicted_mistakes'].sum()
        type_inaccuracies = type_games['predicted_inaccuracies'].sum()
        type_good = type_games['predicted_good'].sum()
        
        # Get average rating for this type
        type_ratings = [int(r) for r in type_games['user_rating'] if str(r).isdigit()]
        avg_rating = np.mean(type_ratings) if type_ratings else 0
        
        # Error rate
        error_rate = type_total_errors/type_total_moves*100 if type_total_moves > 0 else 0
        
        print(f"\n🎯 {game_type.upper()}:")
        print(f"   📊 Partidas: {type_total_games} ({type_total_games/total_games*100:.1f}% del total)")
        print(f"   🎯 Jugadas: {type_total_moves}")
        print(f"   📈 Rating promedio: {avg_rating:.0f}")
        print(f"   ⚠️ Tasa de errores: {error_rate:.1f}%")
        print(f"   🔥 Blunders: {type_blunders} ({type_blunders/type_total_moves*100:.1f}%)")
        print(f"   ⚠️ Mistakes: {type_mistakes} ({type_mistakes/type_total_moves*100:.1f}%)")
        print(f"   📉 Inaccuracies: {type_inaccuracies} ({type_inaccuracies/type_total_moves*100:.1f}%)")
        print(f"   ✅ Good moves: {type_good} ({type_good/type_total_moves*100:.1f}%)")
    
    # Ranking by error rate
    print(f"\n📈 RANKING DE TIPOS POR TASA DE ERRORES (menor = mejor):")
    type_stats = []
    for game_type in df_summary['game_type'].unique():
        type_games = df_summary[df_summary['game_type'] == game_type]
        type_total_moves = type_games['total_moves_analyzed'].sum()
        type_total_errors = (type_games['predicted_blunders'].sum() + 
                            type_games['predicted_mistakes'].sum() + 
                            type_games['predicted_inaccuracies'].sum())
        error_rate = type_total_errors/type_total_moves*100 if type_total_moves > 0 else 0
        type_stats.append((game_type, error_rate, len(type_games)))
    
    type_stats.sort(key=lambda x: x[1])  # Sort by error rate
    for i, (game_type, error_rate, game_count) in enumerate(type_stats, 1):
        print(f"   {i}. {game_type}: {error_rate:.1f}% errores ({game_count} partidas)")
    
    # Save detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_file = f"analysis_report_segmented_{target_user}_{timestamp}.csv"
    df_summary.to_csv(report_file, index=False)
    print(f"\n💾 Reporte detallado guardado: {report_file}")

def create_analysis_report(game_summaries, target_user):
    """Create comprehensive analysis report."""
    print(f"\n🏆 ANÁLISIS COMPLETO: {target_user.upper()}")
    print("="*60)
    
    if not game_summaries:
        print("❌ No games analyzed")
        return
    
    df_summary = pd.DataFrame(game_summaries)
    
    # Overall statistics
    total_games = len(df_summary)
    total_moves = df_summary['total_moves_analyzed'].sum()
    total_errors = (df_summary['predicted_blunders'].sum() + 
                   df_summary['predicted_mistakes'].sum() + 
                   df_summary['predicted_inaccuracies'].sum())
    
    print(f"📊 RESUMEN GENERAL:")
    print(f"  🎮 Partidas analizadas: {total_games}")
    print(f"  🎯 Jugadas analizadas: {total_moves}")
    print(f"  ⚠️ Errores predichos: {total_errors} ({total_errors/total_moves*100:.1f}%)")
    
    # Error breakdown
    total_blunders = df_summary['predicted_blunders'].sum()
    total_mistakes = df_summary['predicted_mistakes'].sum()
    total_inaccuracies = df_summary['predicted_inaccuracies'].sum()
    total_good = df_summary['predicted_good'].sum()
    
    print(f"\n📈 DISTRIBUCIÓN DE ERRORES:")
    print(f"  🔥 Blunders: {total_blunders} ({total_blunders/total_moves*100:.1f}%)")
    print(f"  ⚠️ Mistakes: {total_mistakes} ({total_mistakes/total_moves*100:.1f}%)")
    print(f"  📉 Inaccuracies: {total_inaccuracies} ({total_inaccuracies/total_moves*100:.1f}%)")
    print(f"  ✅ Good moves: {total_good} ({total_good/total_moves*100:.1f}%)")
    
    # Rating analysis
    ratings = [int(r) for r in df_summary['user_rating'] if str(r).isdigit()]
    if ratings:
        print(f"\n🎯 ANÁLISIS DE RATING:")
        print(f"  📊 Rango: {min(ratings)} - {max(ratings)}")
        print(f"  📈 Promedio: {np.mean(ratings):.0f}")
        print(f"  📊 Mediana: {np.median(ratings):.0f}")
    
    # Recent performance (last 10 games)
    recent_games = df_summary.tail(10)
    recent_error_rate = (recent_games['predicted_blunders'].sum() + 
                        recent_games['predicted_mistakes'].sum() + 
                        recent_games['predicted_inaccuracies'].sum()) / recent_games['total_moves_analyzed'].sum()
    
    print(f"\n🕐 RENDIMIENTO RECIENTE (últimas 10 partidas):")
    print(f"  📉 Tasa de errores: {recent_error_rate*100:.1f}%")
    
    # Games with most errors
    df_summary['total_errors'] = (df_summary['predicted_blunders'] + 
                                 df_summary['predicted_mistakes'] + 
                                 df_summary['predicted_inaccuracies'])
    df_summary['error_rate'] = df_summary['total_errors'] / df_summary['total_moves_analyzed']
    
    print(f"\n🎮 PARTIDAS CON MÁS ERRORES (top 5):")
    top_error_games = df_summary.nlargest(5, 'error_rate')[['game_id', 'date', 'user_rating', 'result', 'total_errors', 'total_moves_analyzed', 'error_rate']]
    for _, game in top_error_games.iterrows():
        print(f"  🎯 Game {game['game_id']} ({game['date']}): {game['total_errors']}/{game['total_moves_analyzed']} errors ({game['error_rate']*100:.1f}%) - {game['result']}")
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_file = f"analysis_report_{target_user}_{timestamp}.csv"
    df_summary.to_csv(report_file, index=False)
    print(f"\n💾 Reporte guardado: {report_file}")
    
    return df_summary

def main():
    print("🚀 ANÁLISIS DIRECTO DE PARTIDAS RECIENTES")
    print("="*60)
    
    # Configuration
    pgn_file = "data/validation_recent/combined_recent_20260101_1613.pgn"
    target_user = "cmess1315"  # More active user
    
    # Check if PGN file exists
    if not Path(pgn_file).exists():
        print(f"❌ PGN file not found: {pgn_file}")
        return
    
    # Load games
    games = load_recent_games(pgn_file)
    if not games:
        return
    
    # Filter user games  
    user_games = analyze_user_games(games, target_user)
    if not user_games:
        print(f"❌ No games found for {target_user}")
        return
    
    # Load model
    model = load_personal_model()
    if not model:
        return
    
    # Analyze games
    print(f"🎯 Iniciando análisis completo de {len(user_games)} partidas...")
    all_predictions, game_summaries = predict_errors_for_games(user_games, model, max_games=len(user_games))
    
    # Create segmented report
    if game_summaries:
        create_segmented_analysis_report(game_summaries, target_user)
    else:
        print("❌ No predictions generated")

if __name__ == "__main__":
    main()