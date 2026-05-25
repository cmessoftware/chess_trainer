"""
Script para procesar todas las partidas que no tienen features generados
Procesa en lotes para evitar sobrecargar el sistema
"""
import sys
import os
from pathlib import Path
import subprocess
import psycopg2
from datetime import datetime

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent))

def get_games_without_features():
    """Obtener lista de game_ids que no tienen features, agrupados por fuente"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chess_trainer_db",
        user="chess",
        password="chess_pass"
    )
    
    cur = conn.cursor()
    
    # Obtener conteo por fuente de partidas sin features
    cur.execute("""
        SELECT g.source, COUNT(*) as count
        FROM games g
        LEFT JOIN features f ON g.game_id = f.game_id
        WHERE f.game_id IS NULL
        GROUP BY g.source
        ORDER BY COUNT(*) DESC;
    """)
    
    by_source = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    
    return by_source

def process_batch(source, offset, max_games, workers=1):
    """Procesar un lote de partidas con offset específico"""
    script_path = Path(__file__).parent / "generate_features_with_tactics.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--source", source,
        "--max-games", str(max_games),
        "--workers", str(workers),
        "--offset", str(offset)
    ]
    
    print(f"\n{'='*60}")
    print(f"🚀 Procesando {source}: {max_games} partidas")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}\n")
    
    start_time = datetime.now()
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if result.returncode == 0:
        print(f"✅ Completado en {duration:.1f}s")
        if result.stdout:
            print(result.stdout[-500:])  # Últimas líneas
        return True
    else:
        print(f"❌ Error (código {result.returncode})")
        if result.stderr:
            print(result.stderr[-500:])
        return False

def main():
    print("="*60)
    print("PROCESAMIENTO BATCH DE FEATURES FALTANTES")
    print("="*60)
    
    # Obtener conteo de partidas sin features por fuente
    by_source = get_games_without_features()
    total_missing = sum(by_source.values())
    
    if total_missing == 0:
        print("\n✅ ¡Todas las partidas ya tienen features!")
        return
    
    print(f"\n📊 Partidas sin features: {total_missing:,}")
    print("\nDistribución por fuente:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {source}: {count:,} partidas")
    
    print("\n" + "="*60)
    input("Presiona ENTER para comenzar el procesamiento...")
    print()
    
    # Configuración de procesamiento
    BATCH_SIZE = 1000
    WORKERS = 1  # Reducido a 1 para evitar race conditions
    
    # Obtener offset actual para cada fuente (cuántas ya tienen features)
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chess_trainer_db",
        user="chess",
        password="chess_pass"
    )
    cur = conn.cursor()
    
    # Procesar por fuente
    for source in sorted(by_source.keys(), key=lambda s: by_source[s], reverse=True):
        count = by_source[source]
        batches = (count + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Obtener offset (cuántas partidas de esta fuente YA tienen features)
        cur.execute("""
            SELECT COUNT(DISTINCT f.game_id)
            FROM games g
            INNER JOIN features f ON g.game_id = f.game_id
            WHERE g.source = %s;
        """, (source,))
        offset = cur.fetchone()[0]
        
        print(f"\n{'='*60}")
        print(f"📦 Procesando fuente: {source}")
        print(f"   Offset: {offset:,} (ya procesadas)")
        print(f"   Total: {count:,} partidas en {batches} lotes")
        print(f"{'='*60}")
        
        for batch_num in range(batches):
            batch_size = min(BATCH_SIZE, count - (batch_num * BATCH_SIZE))
            current_offset = offset + (batch_num * BATCH_SIZE)
            
            print(f"\n🔄 Lote {batch_num + 1}/{batches} ({batch_size} partidas, offset {current_offset})")
            
            success = process_batch(source, current_offset, batch_size, WORKERS)
            
            if not success:
                print(f"\n⚠️  Error procesando {source}, continuando con siguiente fuente...")
                break
    
    cur.close()
    conn.close()
    
    # Verificación final
    print("\n" + "="*60)
    print("VERIFICACIÓN FINAL")
    print("="*60)
    
    by_source_final = get_games_without_features()
    remaining = sum(by_source_final.values())
    processed = total_missing - remaining
    
    print(f"✅ Procesadas: {processed:,} partidas")
    print(f"⏳ Pendientes: {remaining:,} partidas")
    print(f"📊 Progreso: {(processed/total_missing)*100:.1f}%")
    
    if remaining == 0:
        print("\n🎉 ¡Procesamiento completado! Todas las partidas tienen features.")
    
    print("="*60)

if __name__ == "__main__":
    main()
