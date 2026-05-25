"""
Script para verificar el impacto de features en la base de datos
"""
import psycopg2
from datetime import datetime, timedelta

# Conexión a PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chess_trainer_db",
    user="chess",
    password="chess_pass"
)

cur = conn.cursor()

print("=" * 60)
print("VERIFICACIÓN DE FEATURES EN BASE DE DATOS")
print("=" * 60)

# 1. Total de features
cur.execute("SELECT COUNT(*) FROM features;")
total_features = cur.fetchone()[0]
print(f"\n✅ Total de features en BD: {total_features:,}")

# 2. Total de partidas importadas recientemente (última hora)
cur.execute("""
    SELECT COUNT(*) 
    FROM games 
    WHERE created_at::timestamp > NOW() - INTERVAL '1 hour';
""")
games_ultima_hora = cur.fetchone()[0]
print(f"✅ Partidas importadas última hora: {games_ultima_hora:,}")

# 3. Partidas importadas últimos 5 minutos
cur.execute("""
    SELECT COUNT(*) 
    FROM games 
    WHERE created_at::timestamp > NOW() - INTERVAL '5 minutes';
""")
games_ultimos_5min = cur.fetchone()[0]
print(f"✅ Partidas importadas últimos 5 min: {games_ultimos_5min:,}")

# 4. Total de partidas
cur.execute("SELECT COUNT(*) FROM games;")
total_games = cur.fetchone()[0]
print(f"\n✅ Total de partidas en BD: {total_games:,}")

# 5. Partidas con source='personal'
cur.execute("SELECT COUNT(*) FROM games WHERE source = 'personal';")
personal_games = cur.fetchone()[0]
print(f"✅ Partidas personales: {personal_games:,}")

# 6. Partidas personales con features
cur.execute("""
    SELECT COUNT(DISTINCT f.game_id) 
    FROM features f
    JOIN games g ON f.game_id = g.game_id
    WHERE g.source = 'personal';
""")
personal_con_features = cur.fetchone()[0]
print(f"✅ Partidas personales CON features: {personal_con_features:,}")

# 7. Promedio de moves por partida con features
cur.execute("""
    SELECT AVG(move_count) as promedio
    FROM (
        SELECT game_id, COUNT(*) as move_count
        FROM features
        GROUP BY game_id
    ) subq;
""")
avg_moves = cur.fetchone()[0]
print(f"✅ Promedio de moves con features: {float(avg_moves):.1f}")

# 8. Últimas 10 partidas importadas
print("\n" + "=" * 60)
print("ÚLTIMAS 10 PARTIDAS IMPORTADAS:")
print("=" * 60)
cur.execute("""
    SELECT game_id, source, white_elo, black_elo, created_at
    FROM games 
    ORDER BY created_at DESC 
    LIMIT 10;
""")
for row in cur.fetchall():
    has_features = "✅" 
    cur.execute("SELECT COUNT(*) FROM features WHERE game_id = %s;", (row[0],))
    feature_count = cur.fetchone()[0]
    status = f"✅ {feature_count} moves" if feature_count > 0 else "❌ Sin features"
    print(f"  {row[0][:20]}... [{row[1]}] ELO:{row[2]}/{row[3]} - {status}")

# 9. Verificar cobertura de features
print("\n" + "=" * 60)
print("COBERTURA DE FEATURES:")
print("=" * 60)
cur.execute("""
    SELECT 
        COUNT(DISTINCT g.game_id) as total_partidas,
        COUNT(DISTINCT f.game_id) as partidas_con_features,
        ROUND(100.0 * COUNT(DISTINCT f.game_id) / COUNT(DISTINCT g.game_id), 2) as porcentaje_cobertura
    FROM games g
    LEFT JOIN features f ON g.game_id = f.game_id;
""")
row = cur.fetchone()
print(f"  Total partidas: {row[0]:,}")
print(f"  Con features: {row[1]:,}")
print(f"  Cobertura: {row[2]}%")

# 10. Top 5 partidas con más features
print("\n" + "=" * 60)
print("TOP 5 PARTIDAS CON MÁS FEATURES:")
print("=" * 60)
cur.execute("""
    SELECT f.game_id, COUNT(*) as moves, g.source
    FROM features f
    JOIN games g ON f.game_id = g.game_id
    GROUP BY f.game_id, g.source
    ORDER BY moves DESC
    LIMIT 5;
""")
for row in cur.fetchall():
    print(f"  {row[0][:30]}... [{row[2]}]: {row[1]} moves")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETADA")
print("=" * 60)

cur.close()
conn.close()
