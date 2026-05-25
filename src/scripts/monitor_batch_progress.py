"""
Monitor del progreso de procesamiento batch de features
Actualiza cada 10 segundos
"""
import psycopg2
import time
from datetime import datetime
import os

def clear_screen():
    """Limpiar pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_stats():
    """Obtener estadísticas de la base de datos"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="chess_trainer_db",
        user="chess",
        password="chess_pass"
    )
    
    cur = conn.cursor()
    
    # Total features
    cur.execute("SELECT COUNT(*) FROM features;")
    total_features = cur.fetchone()[0]
    
    # Total games
    cur.execute("SELECT COUNT(*) FROM games;")
    total_games = cur.fetchone()[0]
    
    # Games sin features
    cur.execute("""
        SELECT COUNT(*)
        FROM games g
        LEFT JOIN features f ON g.game_id = f.game_id
        WHERE f.game_id IS NULL;
    """)
    games_sin_features = cur.fetchone()[0]
    
    # Features creadas en el último minuto
    cur.execute("""
        SELECT COUNT(*)
        FROM features
        WHERE created_at > NOW() - INTERVAL '1 minute';
    """)
    features_ultimo_minuto = cur.fetchone()[0]
    
    # Por fuente
    cur.execute("""
        SELECT g.source, COUNT(DISTINCT f.game_id) as con_features, COUNT(DISTINCT g.game_id) as total
        FROM games g
        LEFT JOIN features f ON g.game_id = f.game_id
        GROUP BY g.source
        ORDER BY g.source;
    """)
    by_source = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return {
        'total_features': total_features,
        'total_games': total_games,
        'games_sin_features': games_sin_features,
        'features_ultimo_minuto': features_ultimo_minuto,
        'by_source': by_source
    }

def format_number(num):
    """Formatear número con comas"""
    return f"{num:,}"

def main():
    print("Iniciando monitor de progreso...")
    print("Presiona Ctrl+C para salir\n")
    time.sleep(2)
    
    last_total = 0
    start_time = datetime.now()
    
    try:
        while True:
            clear_screen()
            
            stats = get_stats()
            current_time = datetime.now()
            elapsed = (current_time - start_time).total_seconds()
            
            # Calcular velocidad
            if last_total > 0:
                new_features = stats['total_features'] - last_total
                features_per_second = new_features / 10  # cada 10 segundos
            else:
                new_features = 0
                features_per_second = 0
            
            last_total = stats['total_features']
            
            games_con_features = stats['total_games'] - stats['games_sin_features']
            cobertura = (games_con_features / stats['total_games'] * 100) if stats['total_games'] > 0 else 0
            
            # Header
            print("=" * 80)
            print(f"🔄 MONITOR DE PROCESAMIENTO BATCH - {current_time.strftime('%H:%M:%S')}")
            print(f"⏱️  Tiempo transcurrido: {int(elapsed // 60)}m {int(elapsed % 60)}s")
            print("=" * 80)
            
            # Estado general
            print(f"\n📊 ESTADO GENERAL:")
            print(f"   Total Features: {format_number(stats['total_features'])}")
            print(f"   Total Partidas: {format_number(stats['total_games'])}")
            print(f"   Con Features: {format_number(games_con_features)} ({cobertura:.1f}%)")
            print(f"   Sin Features: {format_number(stats['games_sin_features'])}")
            
            # Velocidad
            print(f"\n⚡ VELOCIDAD:")
            print(f"   Últimos 10s: +{format_number(new_features)} features ({features_per_second:.1f}/s)")
            print(f"   Último minuto: {format_number(stats['features_ultimo_minuto'])} features")
            
            if features_per_second > 0 and stats['games_sin_features'] > 0:
                # Estimar tiempo restante (asumiendo ~66 moves por partida)
                features_restantes = stats['games_sin_features'] * 66
                segundos_restantes = features_restantes / features_per_second
                minutos_restantes = int(segundos_restantes // 60)
                print(f"   Tiempo estimado restante: ~{minutos_restantes}m")
            
            # Por fuente
            print(f"\n📁 COBERTURA POR FUENTE:")
            for source, con_features, total in stats['by_source']:
                pct = (con_features / total * 100) if total > 0 else 0
                sin_features = total - con_features
                bar_length = 30
                filled = int(bar_length * pct / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                print(f"   {source:20s} [{bar}] {pct:5.1f}% ({con_features}/{total}) - Falta: {sin_features}")
            
            print("\n" + "=" * 80)
            print("Actualizando en 10 segundos... (Ctrl+C para salir)")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitor detenido.")
        print(f"Tiempo total de monitoreo: {int(elapsed // 60)}m {int(elapsed % 60)}s")

if __name__ == "__main__":
    main()
