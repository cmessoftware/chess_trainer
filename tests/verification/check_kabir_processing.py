#!/usr/bin/env python3
"""Verificar si se procesaron los datos del archivo kabir_pathak_bis5.pgn"""

import psycopg2
import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    # Conectar a la base de datos
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='chess_trainer_db',
            user='chess',
            password='chess_pass',
            port=5432
        )

        cur = conn.cursor()

        print('🔍 VERIFICACIÓN DE PROCESAMIENTO DE FEATURES')
        print('=' * 50)

        # Verificar totales generales
        cur.execute('SELECT COUNT(*) FROM games')
        total_games = cur.fetchone()[0]
        print(f'📊 Total games en DB: {total_games}')

        cur.execute('SELECT COUNT(*) FROM features') 
        total_features = cur.fetchone()[0]
        print(f'🎯 Total features en DB: {total_features}')

        # Buscar archivos con 'kabir' en el nombre
        cur.execute("SELECT filename, COUNT(*) FROM games WHERE filename ILIKE %s GROUP BY filename", 
                   ('%kabir%',))
        kabir_results = cur.fetchall()

        if kabir_results:
            print(f'\n📄 ARCHIVOS CON "kabir" ENCONTRADOS:')
            for fname, count in kabir_results:
                print(f'   ▶ {fname}: {count} partidas')
                
                # Verificar features para este archivo
                cur.execute("""
                SELECT COUNT(f.id) 
                FROM features f 
                JOIN games g ON f.game_id = g.id 
                WHERE g.filename = %s
                """, (fname,))
                
                features_count = cur.fetchone()[0]
                print(f'     ↳ Features generados: {features_count}')
        else:
            print(f'\n❌ No se encontraron archivos con "kabir" en el nombre')
            
            # Mostrar archivos recientes para referencia
            print(f'\n📁 ARCHIVOS RECIENTES (últimos 10 por cantidad):')
            cur.execute('SELECT filename, COUNT(*) FROM games GROUP BY filename ORDER BY COUNT(*) DESC LIMIT 10')
            recent_files = cur.fetchall()
            for fname, count in recent_files:
                print(f'   📄 {fname}: {count} partidas')

        # Verificar files más recientes por timestamp si existe esa columna
        try:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'games' AND column_name LIKE '%created%'")
            timestamp_cols = cur.fetchall()
            
            if timestamp_cols:
                col_name = timestamp_cols[0][0]
                print(f'\n⏰ ARCHIVOS ORDENADOS POR {col_name} (últimos 5):')
                cur.execute(f'SELECT filename, COUNT(*) FROM games GROUP BY filename ORDER BY MAX({col_name}) DESC LIMIT 5')
                recent_by_time = cur.fetchall()
                for fname, count in recent_by_time:
                    print(f'   🕒 {fname}: {count} partidas')
                    
        except Exception as e:
            print(f'\n⚠️ No se pudo verificar por timestamp: {e}')

        conn.close()
        print(f'\n✅ Verificación completada')

    except Exception as e:
        print(f'❌ Error conectando a la base de datos: {e}')

if __name__ == "__main__":
    main()