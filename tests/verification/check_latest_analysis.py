"""Verificar error_labels en análisis más reciente"""

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass",
)

cursor = conn.cursor()

# Obtener el análisis más reciente
cursor.execute("SELECT MAX(id) FROM analysis_results")
latest_id = cursor.fetchone()[0]

print(f"\n{'='*80}")
print(f"ANÁLISIS MÁS RECIENTE (ID={latest_id})")
print(f"{'='*80}")

# Verificar error_labels
cursor.execute(
    f"""
    SELECT COUNT(*), error_label 
    FROM move_shap_values 
    WHERE analysis_id = {latest_id}
    GROUP BY error_label
    ORDER BY COUNT(*) DESC
"""
)

results = cursor.fetchall()

if not results:
    print("\n⚠️  No hay SHAP values")
else:
    total = sum(r[0] for r in results)
    print(f"\nTotal SHAP values: {total:,}")
    print(f"\n{'Error Label':<15} {'Count':<10} {'Percentage'}")
    print("-" * 40)
    for count, label in results:
        label_str = label if label else "NULL"
        percentage = (count / total) * 100
        print(f"{label_str:<15} {count:<10,} {percentage:>6.2f}%")

# Ver 5 ejemplos con diferentes moves
print(f"\n{'='*80}")
print("Ejemplos (primeros 10 SHAP values):")
print(f"{'='*80}")

cursor.execute(
    f"""
    SELECT move_number, feature_name, shap_value, error_label
    FROM move_shap_values
    WHERE analysis_id = {latest_id}
    ORDER BY id
    LIMIT 10
"""
)

for row in cursor.fetchall():
    move, feature, shap, label = row
    label_str = label if label else "NULL"
    print(f"Move {move:>2}: {feature:<25} shap={shap:>8.4f}  error_label={label_str}")

cursor.close()
conn.close()
