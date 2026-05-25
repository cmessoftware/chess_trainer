#!/usr/bin/env python3
"""Verificar si se procesaron correctamente los features del archivo kabir_pathak_bis5.pgn"""

import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

def main():
    load_dotenv()

    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'chess_trainer_db'),
        user=os.getenv('DB_USER', 'chess'), 
        password=os.getenv('DB_PASSWORD', 'chess_pass'),
        port=int(os.getenv('DB_PORT', 5432))
    )

    cur = conn.cursor()

    print('🔍 VERIFICANDO PROCESAMIENTO DE FEATURES...\n')

    # Buscar registros recientes en games (últimas 2 horas)
    recent_time = datetime.now() - timedelta(hours=2)
    
    cur.execute("""
    SELECT source, COUNT(*) as count, MIN(created_at) as first, MAX(created_at) as last
    FROM games 
    WHERE created_at >= %s
    GROUP BY source
    ORDER BY last DESC
    """, (recent_time,))

    games_data = cur.fetchall()
    print('📊 GAMES PROCESADOS RECIENTEMENTE:')
    if games_data:
        for source, count, first, last in games_data:
            print(f'   {source}: {count} partidas ({first} a {last})')
    else:
        print('   ❌ No se encontraron games recientes')

    # Buscar registros en features 
    cur.execute("""
    SELECT COUNT(*) as total_features, MIN(created_at) as first, MAX(created_at) as last
    FROM features
    WHERE created_at >= %s
    """, (recent_time,))

    features_data = cur.fetchone()
    print(f'\n🎯 FEATURES GENERADOS: {features_data[0]} registros')
    if features_data[0] > 0:
        print(f'   Desde: {features_data[1]}')
        print(f'   Hasta: {features_data[2]}')

    # Buscar el archivo específico por nombre
    cur.execute("""
    SELECT DISTINCT filename, COUNT(*) 
    FROM games 
    WHERE created_at >= %s AND (filename LIKE %s OR filename LIKE %s)
    GROUP BY filename
    """, (recent_time, '%kabir%', '%pathak%'))

    kabir_files = cur.fetchall()
    if kabir_files:
        print(f'\n📁 ARCHIVOS KABIR/PATHAK ENCONTRADOS:')
        for filename, count in kabir_files:
            print(f'   {filename}: {count} partidas')
    else:
        print(f'\n❌ NO se encontraron archivos con "kabir" o "pathak" en el nombre')

    # Verificar features por game_id recientes 
    cur.execute("""
    SELECT g.filename, COUNT(f.id) as features_count, g.source
    FROM games g
    LEFT JOIN features f ON g.id = f.game_id 
    WHERE g.created_at >= %s
    GROUP BY g.filename, g.source
    ORDER BY g.created_at DESC
    LIMIT 10
    """, (recent_time,))

    games_features = cur.fetchall()
    if games_features:
        print(f'\n📋 RELACIÓN GAMES-FEATURES RECIENTES:')
        for filename, feat_count, source in games_features:
            print(f'   {filename} ({source}): {feat_count} features')

    conn.close()

if __name__ == "__main__":
    main()