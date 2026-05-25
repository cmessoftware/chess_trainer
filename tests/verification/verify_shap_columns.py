"""
Script rápido para verificar que las columnas se agregaron correctamente
"""
import psycopg2

conn = psycopg2.connect(
    dbname='chess_trainer_db',
    user='chess',
    password='chess_pass',
    host='localhost'
)
cur = conn.cursor()

# Verificar columnas en move_shap_values
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    AND table_name = 'move_shap_values'
    AND column_name IN ('move_san', 'move_uci', 'fen', 'player_color')
    ORDER BY column_name
""")

print("\n" + "="*70)
print("✅ COLUMNAS AGREGADAS A move_shap_values:")
print("="*70)
for row in cur.fetchall():
    col_name, data_type, max_length = row
    type_str = f"{data_type}({max_length})" if max_length else data_type
    print(f"  ✓ {col_name}: {type_str}")

# Verificar vista
cur.execute("""
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    AND table_name = 'shap_values_with_games'
    AND column_name IN ('move_san', 'move_uci', 'fen', 'player_color')
    ORDER BY column_name
""")

print("\n" + "="*70)
print("✅ COLUMNAS EN VISTA shap_values_with_games:")
print("="*70)
view_cols = cur.fetchall()
if view_cols:
    for row in view_cols:
        print(f"  ✓ {row[0]}")
else:
    print("  ⚠️  No se encontraron las columnas (vista puede no existir)")

# Contar SHAP values existentes
cur.execute("SELECT COUNT(*) FROM move_shap_values")
count = cur.fetchone()[0]
print("\n" + "="*70)
print(f"📊 SHAP VALUES EXISTENTES: {count}")
print("="*70)

if count > 0:
    print("\n⚠️  NOTA: Los SHAP values existentes tienen NULL en las nuevas columnas.")
    print("   Para poblarlas, regenera el análisis SHAP de las partidas.")

conn.close()

print("\n✅ Verificación completada!")
