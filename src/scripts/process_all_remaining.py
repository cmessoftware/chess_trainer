"""
Script para procesar automáticamente todas las partidas restantes
Ejecuta generate_features_with_tactics.py con offsets incrementales
"""
import subprocess
import psycopg2
from datetime import datetime

def get_remaining_by_source():
    """Obtener partidas sin features por fuente"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chess_trainer_db",
        user="chess",
        password="chess_pass"
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT g.source, COUNT(*) as sin_features
        FROM games g
        LEFT JOIN features f ON g.game_id = f.game_id
        WHERE f.game_id IS NULL
        GROUP BY g.source
        ORDER BY COUNT(*) DESC;
    """)
    
    result = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return result

def get_processed_count(source):
    """Obtener cuántas partidas ya tienen features para calcular offset"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chess_trainer_db",
        user="chess",
        password="chess_pass"
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(DISTINCT f.game_id)
        FROM games g
        JOIN features f ON g.game_id = f.game_id
        WHERE g.source = %s;
    """, (source,))
    
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def process_source(source, max_games, offset):
    """Ejecutar generate_features_with_tactics.py"""
    print(f"\n{'='*60}")
    print(f"🔄 Procesando {source}: {max_games} partidas (offset {offset})")
    print(f"{'='*60}")
    
    cmd = [
        r"C:\Users\sergiosal\miniforge3\envs\chess_trainer\python.exe",
        "generate_features_with_tactics.py",
        "--source", source,
        "--max-games", str(max_games),
        "--workers", "1",
        "--offset", str(offset)
    ]
    
    start = datetime.now()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"\n✅ Completado en {duration:.1f}s")
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr[-500:]}")
        return False
    
    return True

def main():
    print("="*60)
    print("PROCESAMIENTO AUTOMATIZADO DE TODAS LAS FEATURES RESTANTES")
    print("="*60)
    
    remaining = get_remaining_by_source()
    
    print(f"\n📊 Partidas pendientes:")
    for source, count in remaining.items():
        print(f"   - {source}: {count:,}")
    
    total = sum(remaining.values())
    print(f"\n   TOTAL: {total:,} partidas")
    
    input("\nPresiona ENTER para comenzar...")
    
    BATCH_SIZE = 1000
    
    for source, pending in remaining.items():
        processed_offset = get_processed_count(source)
        batches_needed = (pending + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n\n{'#'*60}")
        print(f"📦 FUENTE: {source}")
        print(f"   Pendientes: {pending:,}")
        print(f"   Offset inicial: {processed_offset}")
        print(f"   Lotes: {batches_needed}")
        print(f"{'#'*60}")
        
        for batch_num in range(batches_needed):
            batch_size = min(BATCH_SIZE, pending - (batch_num * BATCH_SIZE))
            current_offset = processed_offset + (batch_num * BATCH_SIZE)
            
            print(f"\n🔄 Lote {batch_num + 1}/{batches_needed} ({batch_size} partidas)")
            
            success = process_source(source, batch_size, current_offset)
            
            if not success:
                print(f"\n⚠️ Error en {source}, continuando con siguiente fuente...")
                break
    
    # Verificación final
    remaining_final = get_remaining_by_source()
    total_final = sum(remaining_final.values())
    
    print("\n\n" + "="*60)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("="*60)
    print(f"Pendientes restantes: {total_final:,}")
    
    if total_final == 0:
        print("\n🎉 ¡100% COMPLETADO! Todas las partidas tienen features.")
    else:
        print("\nPartidas restantes por fuente:")
        for source, count in remaining_final.items():
            print(f"   - {source}: {count:,}")

if __name__ == "__main__":
    main()
