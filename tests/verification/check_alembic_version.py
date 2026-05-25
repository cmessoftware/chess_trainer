"""Verificar estado de Alembic version"""
import psycopg2

conn = psycopg2.connect(
    dbname='chess_trainer_db',
    user='chess',
    password='chess_pass',
    host='localhost'
)
cur = conn.cursor()

# Ver versión actual de Alembic
cur.execute("SELECT * FROM alembic_version")
result = cur.fetchall()

print("\n" + "="*70)
print("ALEMBIC VERSION ACTUAL:")
print("="*70)
for row in result:
    print(f"  Version: {row[0]}")

conn.close()
