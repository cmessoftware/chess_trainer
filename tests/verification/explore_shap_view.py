import psycopg2

conn = psycopg2.connect(
    dbname="chess_trainer_db",
    user="chess",
    password="chess_pass",
    host="localhost",
    port=5432,
)
cur = conn.cursor()

# Ver estructura completa de la vista
print("Estructura de shap_values_with_games (vista):")
cur.execute(
    """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'shap_values_with_games'
    ORDER BY ordinal_position
"""
)
columns = cur.fetchall()
for col in columns:
    print(f"  - {col[0]}: {col[1]}")

# Ver definición de la vista
print("\n\nDefinición de la vista:")
cur.execute(
    """
    SELECT pg_get_viewdef('shap_values_with_games', true)
"""
)
view_def = cur.fetchone()
print(view_def[0])

# Ejemplo de uso con una de tus partidas
print("\n\n" + "=" * 60)
print("EJEMPLO: Query usando la vista")
print("=" * 60)

game_id = "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313"
cur.execute(
    """
    SELECT 
        game_id,
        COUNT(*) as total_shap,
        COUNT(DISTINCT move_number) as jugadas,
        COUNT(DISTINCT feature_name) as features_distintas
    FROM shap_values_with_games
    WHERE game_id = %s
    GROUP BY game_id
""",
    (game_id,),
)

result = cur.fetchone()
if result:
    print(f"\nGame ID: {result[0][:16]}...")
    print(f"Total SHAP values: {result[1]}")
    print(f"Jugadas analizadas: {result[2]}")
    print(f"Features distintas usadas: {result[3]}")

# Top 5 features más importantes
print("\n\nTop 5 features por SHAP value absoluto:")
cur.execute(
    """
    SELECT 
        feature_name,
        ABS(shap_value) as abs_shap,
        move_number,
        error_label
    FROM shap_values_with_games
    WHERE game_id = %s
    ORDER BY ABS(shap_value) DESC
    LIMIT 5
""",
    (game_id,),
)

for row in cur.fetchall():
    print(f"  - {row[0]}: {row[1]:.4f} (move {row[2]}, {row[3]})")

conn.close()
