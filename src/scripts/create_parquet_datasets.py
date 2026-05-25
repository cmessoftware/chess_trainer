#!/usr/bin/env python3
"""
Generador de datasets Parquet por fuente y unificado
Exporta todas las partidas de la BD a archivos Parquet optimizados para ML
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def extract_game_features(game) -> dict:
    """Extraer features útiles de una partida para ML"""
    try:
        # Datos básicos
        features = {
            'game_id': getattr(game, 'game_id', ''),
            'white_player': getattr(game, 'white_player', ''),
            'black_player': getattr(game, 'black_player', ''),
            'result': getattr(game, 'result', ''),
            'source': getattr(game, 'source', ''),
            'date_played': getattr(game, 'date_played', ''),
            'time_control': getattr(game, 'time_control', ''),
            'opening': getattr(game, 'opening', ''),
            'eco': getattr(game, 'eco', ''),
            'created_at': getattr(game, 'created_at', ''),
        }
        
        # Procesar ELOs
        white_elo_str = getattr(game, 'white_elo', '') or '0'
        black_elo_str = getattr(game, 'black_elo', '') or '0'
        
        try:
            features['white_elo'] = int(white_elo_str) if white_elo_str.isdigit() else 0
        except:
            features['white_elo'] = 0
            
        try:
            features['black_elo'] = int(black_elo_str) if black_elo_str.isdigit() else 0
        except:
            features['black_elo'] = 0
        
        # Features derivados
        features['elo_avg'] = (features['white_elo'] + features['black_elo']) / 2 if features['white_elo'] > 0 and features['black_elo'] > 0 else 0
        features['elo_diff'] = abs(features['white_elo'] - features['black_elo']) if features['white_elo'] > 0 and features['black_elo'] > 0 else 0
        
        # Categorizar por nivel
        avg_elo = features['elo_avg']
        if avg_elo == 0:
            features['skill_level'] = 'unknown'
        elif avg_elo < 800:
            features['skill_level'] = 'beginner'
        elif avg_elo < 1200:
            features['skill_level'] = 'novice'
        elif avg_elo < 1600:
            features['skill_level'] = 'intermediate'
        elif avg_elo < 2000:
            features['skill_level'] = 'advanced'
        elif avg_elo < 2400:
            features['skill_level'] = 'expert'
        else:
            features['skill_level'] = 'master'
        
        # Resultado numérico
        result = features['result']
        if result == '1-0':
            features['result_numeric'] = 1.0  # White wins
        elif result == '0-1':
            features['result_numeric'] = 0.0  # Black wins
        elif result == '1/2-1/2':
            features['result_numeric'] = 0.5  # Draw
        else:
            features['result_numeric'] = np.nan
        
        # Features de PGN
        pgn_text = getattr(game, 'pgn', '') or ''
        features['pgn_length'] = len(pgn_text)
        features['move_count_estimate'] = pgn_text.count('.') if pgn_text else 0
        
        # Features temporales
        date_str = features['date_played']
        try:
            if date_str and '.' in date_str:
                year, month, day = date_str.split('.')
                features['year'] = int(year) if year.isdigit() else 0
                features['month'] = int(month) if month.isdigit() else 0
                features['day'] = int(day) if day.isdigit() else 0
            else:
                features['year'] = 0
                features['month'] = 0
                features['day'] = 0
        except:
            features['year'] = 0
            features['month'] = 0
            features['day'] = 0
        
        # Features de control de tiempo
        time_control = features['time_control']
        if 'blitz' in time_control.lower():
            features['time_category'] = 'blitz'
        elif 'rapid' in time_control.lower():
            features['time_category'] = 'rapid'
        elif any(x in time_control for x in ['600', '900', '1800']):
            features['time_category'] = 'rapid'
        elif any(x in time_control for x in ['60', '180', '300']):
            features['time_category'] = 'blitz'
        else:
            features['time_category'] = 'classical'
        
        return features
        
    except Exception as e:
        print(f"  ⚠️  Error procesando partida {getattr(game, 'game_id', 'unknown')}: {str(e)}")
        return None

def create_datasets():
    """Crear datasets Parquet por fuente y unificado"""
    print("🗃️ GENERANDO DATASETS PARQUET")
    print("=" * 60)
    
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        
        print("📊 Cargando todas las partidas...")
        all_games = repo.get_all_games()
        print(f"✅ {len(all_games)} partidas cargadas")
        
        # Crear directorio de datasets
        datasets_dir = Path("data/datasets")
        datasets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🔄 Procesando partidas y extrayendo features...")
        
        # Procesar todas las partidas
        processed_games = []
        errors = 0
        
        for i, game in enumerate(all_games):
            features = extract_game_features(game)
            if features:
                processed_games.append(features)
            else:
                errors += 1
            
            if (i + 1) % 1000 == 0:
                print(f"  ✅ {i + 1} partidas procesadas...")
        
        print(f"📊 Procesamiento completado:")
        print(f"  ✅ Exitosas: {len(processed_games)}")
        print(f"  ❌ Errores: {errors}")
        
        # Crear DataFrame principal
        df_all = pd.DataFrame(processed_games)
        
        # Estadísticas generales
        print(f"\n📈 ESTADÍSTICAS DEL DATASET:")
        print(f"  📋 Total registros: {len(df_all)}")
        print(f"  📋 Columnas: {len(df_all.columns)}")
        
        print(f"\n📊 Distribución por fuente:")
        source_counts = df_all['source'].value_counts()
        for source, count in source_counts.items():
            print(f"  - {source}: {count:,}")
        
        print(f"\n🎯 Distribución por nivel:")
        skill_counts = df_all['skill_level'].value_counts()
        for skill, count in skill_counts.items():
            print(f"  - {skill}: {count:,}")
        
        # Guardar dataset unificado
        print(f"\n💾 Guardando dataset unificado...")
        unified_path = datasets_dir / "chess_games_unified.parquet"
        df_all.to_parquet(unified_path, index=False, compression='snappy')
        print(f"  ✅ Guardado: {unified_path}")
        print(f"  📏 Tamaño: {unified_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Crear datasets por fuente
        print(f"\n📂 Creando datasets por fuente...")
        source_stats = {}
        
        for source in df_all['source'].unique():
            source_df = df_all[df_all['source'] == source].copy()
            
            # Limpiar nombre para archivo
            safe_source = source.replace(' ', '_').replace('-', '_')
            source_path = datasets_dir / f"chess_games_{safe_source}.parquet"
            
            # Guardar
            source_df.to_parquet(source_path, index=False, compression='snappy')
            
            file_size_mb = source_path.stat().st_size / 1024 / 1024
            source_stats[source] = {
                'records': len(source_df),
                'file_size_mb': file_size_mb,
                'path': source_path
            }
            
            print(f"  ✅ {source}: {len(source_df):,} registros → {file_size_mb:.2f} MB")
        
        # Crear dataset de estadísticas
        print(f"\n📊 Creando dataset de estadísticas...")
        
        stats_data = []
        for source, stats in source_stats.items():
            source_df = df_all[df_all['source'] == source]
            
            stats_row = {
                'source': source,
                'total_games': stats['records'],
                'file_size_mb': stats['file_size_mb'],
                'avg_white_elo': source_df['white_elo'].mean(),
                'avg_black_elo': source_df['black_elo'].mean(),
                'avg_elo_combined': source_df['elo_avg'].mean(),
                'white_win_rate': (source_df['result_numeric'] == 1.0).mean(),
                'black_win_rate': (source_df['result_numeric'] == 0.0).mean(),
                'draw_rate': (source_df['result_numeric'] == 0.5).mean(),
                'avg_game_length': source_df['pgn_length'].mean(),
                'date_range_start': source_df['year'].min(),
                'date_range_end': source_df['year'].max()
            }
            stats_data.append(stats_row)
        
        # Agregar estadísticas globales
        stats_row = {
            'source': 'ALL_COMBINED',
            'total_games': len(df_all),
            'file_size_mb': unified_path.stat().st_size / 1024 / 1024,
            'avg_white_elo': df_all['white_elo'].mean(),
            'avg_black_elo': df_all['black_elo'].mean(),
            'avg_elo_combined': df_all['elo_avg'].mean(),
            'white_win_rate': (df_all['result_numeric'] == 1.0).mean(),
            'black_win_rate': (df_all['result_numeric'] == 0.0).mean(),
            'draw_rate': (df_all['result_numeric'] == 0.5).mean(),
            'avg_game_length': df_all['pgn_length'].mean(),
            'date_range_start': df_all['year'].min(),
            'date_range_end': df_all['year'].max()
        }
        stats_data.append(stats_row)
        
        df_stats = pd.DataFrame(stats_data)
        stats_path = datasets_dir / "chess_datasets_statistics.parquet"
        df_stats.to_parquet(stats_path, index=False)
        
        print(f"  ✅ Estadísticas guardadas: {stats_path}")
        
        # Crear sample datasets para testing
        print(f"\n🧪 Creando datasets de muestra...")
        
        # Sample pequeño (1000 registros de cada fuente)
        sample_data = []
        for source in df_all['source'].unique():
            source_df = df_all[df_all['source'] == source]
            sample_size = min(1000, len(source_df))
            source_sample = source_df.sample(n=sample_size, random_state=42)
            sample_data.append(source_sample)
        
        df_sample = pd.concat(sample_data, ignore_index=True)
        sample_path = datasets_dir / "chess_games_sample.parquet"
        df_sample.to_parquet(sample_path, index=False, compression='snappy')
        
        print(f"  ✅ Sample dataset: {len(df_sample):,} registros → {sample_path}")
        
        # Resumen final
        print(f"\n{'='*60}")
        print(f"✅ DATASETS CREADOS EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"📁 Directorio: {datasets_dir}")
        print(f"📊 Archivos creados:")
        
        for file_path in sorted(datasets_dir.glob("*.parquet")):
            size_mb = file_path.stat().st_size / 1024 / 1024
            print(f"  - {file_path.name}: {size_mb:.2f} MB")
        
        total_size = sum(f.stat().st_size for f in datasets_dir.glob("*.parquet")) / 1024 / 1024
        print(f"\n💾 Tamaño total: {total_size:.2f} MB")
        
        # Mostrar estadísticas clave
        print(f"\n📈 ESTADÍSTICAS CLAVE:")
        print(f"  🎮 Total partidas: {len(df_all):,}")
        print(f"  🏆 Ratio victorias blancas: {(df_all['result_numeric'] == 1.0).mean():.1%}")
        print(f"  🏴 Ratio victorias negras: {(df_all['result_numeric'] == 0.0).mean():.1%}")
        print(f"  🤝 Ratio empates: {(df_all['result_numeric'] == 0.5).mean():.1%}")
        print(f"  📊 ELO promedio: {df_all['elo_avg'].mean():.0f}")
        print(f"  📅 Rango años: {df_all['year'].min()}-{df_all['year'].max()}")
        
        return datasets_dir
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal"""
    print("🚀 GENERADOR DE DATASETS PARQUET")
    print("=" * 60)
    print("📝 Creando datasets por fuente y unificado")
    print(f"🕒 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    datasets_dir = create_datasets()
    
    if datasets_dir:
        print(f"\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print(f"📁 Todos los datasets están en: {datasets_dir}")
        print(f"🔗 Listos para usar en ML pipelines")
    else:
        print(f"\n❌ Error en el proceso")
    
    print(f"🕒 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
