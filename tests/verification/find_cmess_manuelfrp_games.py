"""
Buscar partidas entre cmess1315 y manuelfrp79 con SHAP values
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

# Buscar partidas donde juegue cmess1315 o manuelfrp79
cursor.execute(
    """
    SELECT DISTINCT 
        g.game_id, 
        g.white_player, 
        g.black_player, 
        COUNT(*) as shap_count
    FROM shap_values_with_games s
    JOIN games g ON s.game_id = g.game_id
    WHERE (g.white_player IN ('cmess1315', 'manuelfrp79') 
           OR g.black_player IN ('cmess1315', 'manuelfrp79'))
    GROUP BY g.game_id, g.white_player, g.black_player
    ORDER BY COUNT(*) DESC
    LIMIT 10
"""
)

results = cursor.fetchall()

print(f"Total partidas encontradas: {len(results)}")
print("\nPartidas de cmess1315 o manuelfrp79:")
print("=" * 100)

for game_id, white, black, shap_count in results:
    print(f"\nGame ID: {game_id}")
    print(f"  {white} (blancas) vs {black} (negras)")
    print(f"  SHAP values: {shap_count}")

# Imprimir solo los game_ids para el environment
print("\n" + "=" * 100)
print("Game IDs para environment (formato lista):")
print("=" * 100)
for i, (game_id, white, black, shap_count) in enumerate(results, 1):
    print(f"game_id_{i}: {game_id}")

cursor.close()
conn.close()
