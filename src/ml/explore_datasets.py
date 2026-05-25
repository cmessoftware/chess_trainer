"""
🚀 Script de Análisis de Datasets Disponibles
Analiza todos los datasets existentes para predicciones ML
"""

import pandas as pd
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_datasets():
    """Analizar todos los datasets disponibles"""
    
    print("🔍 ANÁLISIS DE DATASETS DISPONIBLES")
    print("=" * 50)
    
    # Rutas de datasets
    DATA_DIR = Path("data/export")
    
    datasets = {
        "unified_all": DATA_DIR / "unified_all_sources.parquet",
        "unified_small": DATA_DIR / "unified_small_sources.parquet",
        "elite": DATA_DIR / "elite",
        "fide": DATA_DIR / "fide", 
        "novice": DATA_DIR / "novice",
        "personal": DATA_DIR / "personal",
        "stockfish": DATA_DIR / "stockfish"
    }
    
    summary = {}
    
    for name, path in datasets.items():
        print(f"\n📊 Dataset: {name}")
        print("-" * 30)
        
        try:
            if path.is_dir():
                # Directorio con múltiples archivos
                parquet_files = list(path.glob("*.parquet"))
                if parquet_files:
                    print(f"   📁 Directorio con {len(parquet_files)} archivos .parquet")
                    
                    # Analizar primer archivo como muestra
                    sample_file = parquet_files[0]
                    df_sample = pd.read_parquet(sample_file)
                    
                    print(f"   📄 Archivo muestra: {sample_file.name}")
                    print(f"   📏 Shape muestra: {df_sample.shape}")
                    
                    if 'error_label' in df_sample.columns:
                        print(f"   🎯 Target distribution:")
                        target_dist = df_sample['error_label'].value_counts()
                        for label, count in target_dist.items():
                            print(f"      {label}: {count}")
                    
                    summary[name] = {
                        'type': 'directory',
                        'files': len(parquet_files),
                        'sample_shape': df_sample.shape,
                        'columns': list(df_sample.columns)
                    }
                else:
                    print(f"   ❌ No se encontraron archivos .parquet")
                    
            elif path.exists() and path.suffix == '.parquet':
                # Archivo único
                df = pd.read_parquet(path)
                print(f"   📊 Shape: {df.shape}")
                print(f"   📈 Columnas: {len(df.columns)}")
                
                # Análisis de target
                if 'error_label' in df.columns:
                    print(f"   🎯 Target distribution:")
                    target_dist = df['error_label'].value_counts()
                    for label, count in target_dist.items():
                        print(f"      {label}: {count} ({count/len(df)*100:.1f}%)")
                
                # Análisis de missing values
                missing = df.isnull().sum().sum()
                print(f"   ❓ Missing values: {missing} ({missing/(df.shape[0]*df.shape[1])*100:.1f}%)")
                
                # Features más importantes
                feature_cols = [col for col in df.columns 
                              if col not in ['error_label', 'pgn', 'game_id', 'move_san']]
                print(f"   🔧 Features disponibles: {len(feature_cols)}")
                
                # Features tácticas
                tactical_features = [col for col in df.columns 
                                   if any(term in col.lower() for term in 
                                         ['depth_score', 'threatens_mate', 'forced_move', 'tactical'])]
                if tactical_features:
                    print(f"   ⚔️ Features tácticas: {len(tactical_features)}")
                    print(f"      {tactical_features[:5]}{'...' if len(tactical_features) > 5 else ''}")
                
                # ELO standardization
                elo_cols = [col for col in df.columns if 'elo' in col.lower()]
                if elo_cols:
                    print(f"   🎯 Columnas ELO: {elo_cols}")
                
                summary[name] = {
                    'type': 'file',
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'missing_values': missing,
                    'features': len(feature_cols),
                    'tactical_features': len(tactical_features),
                    'elo_columns': elo_cols
                }
                
            else:
                print(f"   ❌ No existe: {path}")
                
        except Exception as e:
            print(f"   ❌ Error al analizar: {e}")
    
    # Reporte final
    print(f"\n📋 RESUMEN FINAL")
    print("=" * 50)
    
    ready_datasets = []
    for name, info in summary.items():
        if info:
            if info['type'] == 'file':
                ready_datasets.append(name)
                print(f"✅ {name}: {info['shape'][0]:,} samples, {info['features']} features")
            elif info['type'] == 'directory':
                ready_datasets.append(name)
                print(f"✅ {name}: {info['files']} archivos, {info['sample_shape'][0]:,} samples (muestra)")
    
    print(f"\n🎯 Datasets listos para ML: {len(ready_datasets)}")
    print(f"📊 Recomendación: Usar 'unified_all' para máximo rendimiento")
    
    return summary

def recommend_dataset_strategy(summary):
    """Recomendar estrategia basada en análisis"""
    
    print(f"\n🎯 ESTRATEGIA RECOMENDADA")
    print("=" * 50)
    
    # Identificar mejor dataset
    if 'unified_all' in summary and summary['unified_all']:
        best_dataset = 'unified_all'
        info = summary['unified_all']
        print(f"🏆 Dataset principal: {best_dataset}")
        print(f"   📊 {info['shape'][0]:,} samples para entrenamiento")
        print(f"   🔧 {info['features']} features disponibles")
        
        if info['tactical_features'] > 0:
            print(f"   ⚔️ {info['tactical_features']} features tácticas - ¡Excelente!")
        
        print(f"\n📋 Plan de Experimentación:")
        print(f"   1. 🎯 Entrenamiento básico con {best_dataset}")
        print(f"   2. 📈 Comparación por fuentes (elite, novice, personal)")
        print(f"   3. ⚙️ Optimización de hiperparámetros")
        
        if info['tactical_features'] > 0:
            print(f"   4. ⚔️ Experimento específico con features tácticas")
        
        print(f"   5. 🔮 Predicciones en tiempo real")
        
    else:
        print("⚠️ Dataset unificado no disponible")
        available = [name for name, info in summary.items() if info and info['type'] == 'file']
        if available:
            print(f"📊 Usar datasets individuales: {available}")
        else:
            print("❌ No hay datasets listos para ML")

if __name__ == "__main__":
    summary = analyze_datasets()
    recommend_dataset_strategy(summary)
    
    print(f"\n🚀 Siguiente paso: python src/ml/train_basic_model.py")
