import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass",
)

cursor = conn.cursor()

# Ver columnas de features
print("\n" + "=" * 80)
print("Columnas en tabla 'features':")
print("=" * 80)
cursor.execute(
    """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'features' 
    ORDER BY ordinal_position
    LIMIT 30
"""
)

for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

# Ver sample de datos con error_label
print("\n" + "=" * 80)
print("Sample de features con error_label:")
print("=" * 80)
cursor.execute(
    """
    SELECT game_id, move_number, error_label, material_balance, self_mobility
    FROM features
    WHERE game_id IN (
        SELECT DISTINCT game_id FROM shap_values_with_games LIMIT 1
    )
    ORDER BY move_number
    LIMIT 10
"""
)

for row in cursor.fetchall():
    print(f"Move {row[1]}: {row[2]} (material: {row[3]:.2f}, mobility: {row[4]:.2f})")

cursor.close()
conn.close()
