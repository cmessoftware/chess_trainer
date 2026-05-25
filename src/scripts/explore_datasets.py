#!/usr/bin/env python3
"""
Verificador y explorador de datasets Parquet generados
"""

import pandas as pd
from pathlib import Path

def explore_datasets():
    """Explorar los datasets generados"""
    print("🔍 EXPLORACIÓN DE DATASETS PARQUET")
    print("=" * 60)
    
    datasets_dir = Path("data/datasets")
    
    if not datasets_dir.exists():
        print("❌ Directorio de datasets no encontrado")
        return
    
    # Cargar estadísticas
    stats_file = datasets_dir / "chess_datasets_statistics.parquet"
    if stats_file.exists():
        print("📊 ESTADÍSTICAS DE DATASETS:")
        df_stats = pd.read_parquet(stats_file)
        print(df_stats.to_string(index=False))
        print()
    
    # Explorar dataset unificado
    unified_file = datasets_dir / "chess_games_unified.parquet"
    if unified_file.exists():
        print("🎯 DATASET UNIFICADO:")
        df = pd.read_parquet(unified_file)
        print(f"  📋 Registros: {len(df):,}")
        print(f"  📋 Columnas: {len(df.columns)}")
        print(f"  📋 Columnas disponibles:")
        for i, col in enumerate(df.columns, 1):
            print(f"    {i:2d}. {col}")
        
        print(f"\n  📊 Primeras 5 filas:")
        print(df.head().to_string(index=False))
        
        print(f"\n  🎯 Distribución por fuente:")
        print(df['source'].value_counts().to_string())
        
        print(f"\n  🏆 Distribución por nivel:")
        print(df['skill_level'].value_counts().to_string())
        
        print(f"\n  📈 Estadísticas ELO:")
        print(f"    - ELO promedio: {df['elo_avg'].mean():.1f}")
        print(f"    - ELO mínimo: {df['elo_avg'].min():.1f}")
        print(f"    - ELO máximo: {df['elo_avg'].max():.1f}")
        print(f"    - ELO mediana: {df['elo_avg'].median():.1f}")
    
    # Lista de archivos
    print(f"\n💾 ARCHIVOS GENERADOS:")
    for file_path in sorted(datasets_dir.glob("*.parquet")):
        size_mb = file_path.stat().st_size / 1024 / 1024
        print(f"  ✅ {file_path.name}: {size_mb:.2f} MB")
    
    print(f"\n🎉 Todos los datasets están listos para ML workflows!")

if __name__ == "__main__":
    explore_datasets()
