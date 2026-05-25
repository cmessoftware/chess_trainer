import psycopg2

conn = psycopg2.connect(
    dbname="chess_trainer_db",
    user="chess",
    password="chess_pass",
    host="localhost",
    port=5432,
)
cur = conn.cursor()

# Ver estructura de analysis_results
print("Estructura de analysis_results:")
cur.execute(
    """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'analysis_results'
    ORDER BY ordinal_position
"""
)
columns = cur.fetchall()
for col in columns:
    print(f"  - {col[0]}: {col[1]}")

# Contar SHAP values por game_id usando JOIN
game_ids = [
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",  # my_game_id_1
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",  # my_game_id_2
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",  # my_game_id_3
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",  # my_game_id_4
]

print("\n\nConteo de SHAP values por partida:")
for gid in game_ids:
    cur.execute(
        """
        SELECT 
            COUNT(msv.id) as total_shap,
            COUNT(DISTINCT msv.move_number) as total_moves,
            ar.id as analysis_id
        FROM analysis_results ar
        LEFT JOIN move_shap_values msv ON msv.analysis_id = ar.id
        WHERE ar.game_id = %s
        GROUP BY ar.id
    """,
        (gid,),
    )
    result = cur.fetchone()
    if result and result[0] > 0:
        total_shap, total_moves, analysis_id = result
        print(f"\nGame ID: {gid[:16]}...")
        print(f"  Analysis ID: {analysis_id}")
        print(f"  Total SHAP values: {total_shap}")
        print(f"  Jugadas analizadas: {total_moves}")
        print(f"  Promedio features/jugada: {total_shap/total_moves:.1f}")
    else:
        print(f"\nGame ID: {gid[:16]}... - NO TIENE SHAP VALUES")

conn.close()
