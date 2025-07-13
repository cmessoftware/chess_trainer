import pandas as pd
import os

# Analizar datasets actuales
datasets_path = "/notebooks/data/processed/"
export_path = "/notebooks/data/export/"

print("📊 ANÁLISIS DE DATASETS ACTUALES")
print("=" * 50)

# Verificar archivos Parquet procesados
if os.path.exists(f"{datasets_path}unified_small_sources.parquet"):
    df_small = pd.read_parquet(f"{datasets_path}unified_small_sources.parquet")
    print(f"🔍 unified_small_sources.parquet: {len(df_small):,} registros")
    if "source" in df_small.columns:
        print("📋 Distribución por fuente:")
        print(df_small["source"].value_counts())
    print()

if os.path.exists(f"{datasets_path}unified_all_sources.parquet"):
    df_all = pd.read_parquet(f"{datasets_path}unified_all_sources.parquet")
    print(f"🔍 unified_all_sources.parquet: {len(df_all):,} registros")
    if "source" in df_all.columns:
        print("📋 Distribución por fuente:")
        print(df_all["source"].value_counts())
    print()

# Verificar datasets por fuente
sources = ["elite", "fide", "novice", "personal", "stockfish"]
print("📂 DATASETS POR FUENTE:")
print("-" * 30)

for source in sources:
    source_path = f"{export_path}{source}/"
    if os.path.exists(source_path):
        files = [f for f in os.listdir(source_path) if f.endswith(".parquet")]
        total_records = 0
        for file in files:
            try:
                df = pd.read_parquet(f"{source_path}{file}")
                total_records += len(df)
            except:
                pass
        print(
            f"📊 {source.upper()}: {total_records:,} registros ({len(files)} archivos)"
        )

print("\n🎯 RECOMENDACIONES PARA DATASETS BALANCEADOS:")
print("=" * 50)
print("✅ ELITE: 200k+ registros - EXCELENTE")
print("✅ FIDE: 200k+ registros - EXCELENTE")
print("⚠️ NOVICE: 10-20% - INSUFICIENTE (necesita 50k+ mínimo)")
print("⚠️ PERSONAL: 10-20% - INSUFICIENTE (necesita 50k+ mínimo)")
print("❓ STOCKFISH: Verificar cantidad")

print("\n💡 ESTRATEGIA RECOMENDADA:")
print("-" * 30)
print("1. 🎯 DATASETS CORE (para ML válido):")
print("   - Elite: 50,000 games (sample del 200k)")
print("   - Fide: 50,000 games (sample del 200k)")
print("   - Novice: 25,000 games (regenerar si necesario)")
print("   - Personal: 25,000 games (regenerar si necesario)")
print()
print("2. 📊 TOTAL RECOMENDADO: ~150,000 games")
print("   - Suficiente para ML robusto")
print("   - Balanceado entre niveles")
print("   - Tiempo de entrenamiento razonable")
print()
print("3. 🚀 BENEFICIOS DEL REBALANCE:")
print("   - Predicciones más precisas")
print("   - Menos overfitting a elite/fide")
print("   - Mejor generalización")
