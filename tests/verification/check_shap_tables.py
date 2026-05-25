import psycopg2

conn = psycopg2.connect(
    dbname="chess_trainer_db",
    user="chess",
    password="chess_pass",
    host="localhost",
    port=5432,
)
cur = conn.cursor()

# Listar todas las tablas
cur.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
)
tables = cur.fetchall()

print("Tablas en la base de datos:")
for t in tables:
    print(f"  - {t[0]}")

# Buscar tablas relacionadas con SHAP o análisis
print('\nBuscando tablas con "shap" o "analysis":')
cur.execute(
    """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%shap%' OR table_name LIKE '%analysis%')
    ORDER BY table_name
"""
)
shap_tables = cur.fetchall()
for t in shap_tables:
    print(f"  - {t[0]}")

# Verificar vistas también
print("\nVistas en la base de datos:")
cur.execute(
    "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name"
)
views = cur.fetchall()
for v in views:
    print(f"  - {v[0]}")

conn.close()
