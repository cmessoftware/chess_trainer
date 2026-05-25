"""
Ver schema de la tabla games
"""

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass",
)
cursor = conn.cursor()

# Ver todas las columnas de la tabla games
cursor.execute(
    """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'games'
    ORDER BY ordinal_position
"""
)

print("Columnas de la tabla 'games':")
print("=" * 60)
for col_name, data_type in cursor.fetchall():
    print(f"{col_name:<30} {data_type}")

cursor.close()
conn.close()
