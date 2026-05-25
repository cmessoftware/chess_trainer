#!/usr/bin/env python3
"""
Script FINAL para importar partidas FIDE - con campos correctos
"""

import sys
import zipfile
import tempfile
import os
from pathlib import Path
import re
from datetime import datetime

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def extract_game_data_correct(pgn_text):
    """Extraer datos de una partida PGN usando campos correctos del modelo"""
    lines = pgn_text.strip().split('\n')
    
    # Extraer headers
    headers = {}
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            match = re.match(r'\[(\w+)\s+"([^"]+)"\]', line)
            if match:
                headers[match.group(1)] = match.group(2)
    
    # Encontrar movimientos
    moves_lines = [line for line in lines if not line.startswith('[') and line.strip()]
    moves_text = ' '.join(moves_lines)
    
    # Limpiar game_id
    white = headers.get('White', 'Unknown').replace(',', '').replace(' ', '_')
    black = headers.get('Black', 'Unknown').replace(',', '').replace(' ', '_')
    date = headers.get('Date', '').replace('.', '_')
    game_id = f"fide_{white}_{black}_{date}"[:80]
    
    # Usar campos correctos del modelo Games
    return {
        'game_id': game_id,
        'white_player': headers.get('White', 'Unknown')[:50],
        'black_player': headers.get('Black', 'Unknown')[:50],
        'result': headers.get('Result', '*'),
        'white_elo': headers.get('WhiteElo', '') or '',  # String vacío si no existe
        'black_elo': headers.get('BlackElo', '') or '',  # String vacío si no existe
        'pgn': moves_text[:2000] if moves_text else '',  # pgn en lugar de moves
        'source': 'fide',
        'time_control': headers.get('TimeControl', '')[:50],
        'opening': headers.get('Opening', '')[:100],
        'eco': headers.get('ECO', '')[:10],
        'date_played': headers.get('Date', ''),  # date_played en lugar de date
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def import_zip_correct(zip_path, max_games=100):
    """Importar partidas usando campos correctos"""
    zip_name = Path(zip_path).name
    print(f"\n📁 Procesando: {zip_name}")
    
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        
        imported = 0
        skipped = 0
        errors = 0
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Encontrar archivos PGN
                pgn_files = [f for f in zip_ref.namelist() if f.lower().endswith('.pgn')]
                
                if not pgn_files:
                    print(f"  ❌ No hay archivos PGN")
                    return 0
                
                # Procesar primer archivo PGN
                first_pgn = pgn_files[0]
                zip_ref.extract(first_pgn, temp_dir)
                pgn_file_path = os.path.join(temp_dir, first_pgn)
                
                with open(pgn_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Dividir en partidas
                games_raw = re.split(r'(?=\[Event )', content)
                games_clean = [g.strip() for g in games_raw if g.strip() and '[Event' in g]
                
                print(f"  🎮 Partidas encontradas: {len(games_clean)}")
                
                # Procesar partidas
                for i, game_text in enumerate(games_clean[:max_games]):
                    try:
                        game_data = extract_game_data_correct(game_text)
                        
                        # Verificar si ya existe
                        if repo.game_exists(game_data['game_id']):
                            skipped += 1
                            continue
                        
                        # Guardar partida
                        repo.save_game(game_data)
                        imported += 1
                        
                        if imported % 20 == 0:
                            print(f"    ✅ {imported} importadas...")
                        
                    except Exception as e:
                        errors += 1
                        if errors <= 3:  # Solo mostrar primeros 3 errores
                            print(f"    ⚠️  Error partida {i+1}: {str(e)[:50]}")
                        continue
                
                print(f"  ✅ Completado: {imported} nuevas, {skipped} duplicadas, {errors} errores")
                return imported
                
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return 0

def main():
    """Función principal - importar grandes maestros"""
    fide_dir = Path("src/data/games/fide")
    
    # Top 15 grandes maestros
    master_zips = [
        "Carlsen.zip", "Kasparov.zip", "Fischer.zip", "Anand.zip", 
        "Kramnik.zip", "Nakamura.zip", "Caruana.zip", "Giri.zip",
        "Aronian.zip", "Grischuk.zip", "Svidler.zip", "Topalov.zip",
        "Karpov.zip", "Petrosian.zip", "Tal.zip"
    ]
    
    print("🏆 IMPORTACIÓN FIDE - TOP GRANDES MAESTROS")
    print("=" * 60)
    print("⚡ Usando campos correctos del modelo Games")
    
    total_imported = 0
    successful_zips = 0
    
    for zip_name in master_zips:
        zip_path = fide_dir / zip_name
        
        if zip_path.exists():
            imported = import_zip_correct(zip_path, max_games=100)
            total_imported += imported
            if imported > 0:
                successful_zips += 1
        else:
            print(f"\n📁 {zip_name}: No encontrado")
    
    print(f"\n{'='*60}")
    print(f"RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"ZIPs exitosos: {successful_zips}")
    print(f"Total partidas importadas: {total_imported}")
    
    # Verificar BD final
    print(f"\n🔍 Estado final de la BD...")
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        games = repo.get_all_games()
        
        sources = {}
        for game in games:
            source = getattr(game, 'source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"📈 Partidas por fuente:")
        for source, count in sources.items():
            print(f"  - {source}: {count}")
        
        print(f"\n🎯 Total partidas en BD: {len(games)}")
        
        # Mostrar partidas FIDE
        fide_games = [g for g in games if getattr(g, 'source', '') == 'fide']
        if fide_games:
            print(f"\n🏆 Partidas FIDE importadas: {len(fide_games)}")
            print(f"Últimas 5 partidas FIDE:")
            for i, game in enumerate(fide_games[-5:]):
                print(f"  {i+1}. {getattr(game, 'white_player', 'N/A')} vs {getattr(game, 'black_player', 'N/A')}")
                print(f"     Fecha: {getattr(game, 'date_played', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error verificando BD: {str(e)}")

if __name__ == "__main__":
    main()
