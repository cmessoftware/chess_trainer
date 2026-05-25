import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass",
)

cursor = conn.cursor()

# Verificar análisis 19
print("\n" + "=" * 80)
print("ANÁLISIS 19 - Verificación de error_labels")
print("=" * 80)

cursor.execute(
    """
    SELECT COUNT(*), error_label 
    FROM move_shap_values 
    WHERE analysis_id = 19 
    GROUP BY error_label
"""
)

results = cursor.fetchall()

if not results:
    print("\n⚠️  No hay SHAP values para el análisis 19")
else:
    total = sum(r[0] for r in results)
    print(f"\nTotal SHAP values: {total:,}")
    print(f"\n{'Error Label':<15} {'Count':<10} {'Percentage'}")
    print("-" * 40)
    for count, label in results:
        label_str = label if label else "NULL"
        percentage = (count / total) * 100
        print(f"{label_str:<15} {count:<10,} {percentage:>6.2f}%")

# Verificar 5 ejemplos
print(f"\n{'='*80}")
print("Ejemplos de SHAP values (5 primeros):")
print("=" * 80)

cursor.execute(
    """
    SELECT move_number, feature_name, shap_value, error_label
    FROM move_shap_values
    WHERE analysis_id = 19
    ORDER BY move_number, ABS(shap_value) DESC
    LIMIT 5
"""
)

for row in cursor.fetchall():
    move, feature, shap, label = row
    label_str = label if label else "NULL"
    print(f"Move {move}: {feature:<25} shap={shap:>7.4f} error={label_str}")

cursor.close()
conn.close()
