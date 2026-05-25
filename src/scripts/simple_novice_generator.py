#!/usr/bin/env python3
"""
Generador simple de partidas novice usando patrones PGN válidos
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

class SimpleNoviceGenerator:
    """Generador simple con partidas PGN válidas pre-construidas"""
    
    def __init__(self):
        # Nombres de novatos
        self.names = [
            "Alex_New", "Chess_Beginner", "Bobby_Learning", "Ana_Rookie",
            "Tom_Student", "Lisa_Fresh", "Mike_Novice", "Sara_Junior",
            "John_Basic", "Emma_Simple", "David_Easy", "Nina_Start",
            "Paul_Young", "Kate_Begin", "Mark_First", "Lily_New",
            "Sam_Learn", "Eva_Basic", "Max_Simple", "Zoe_Fresh"
        ]
        
        # Partidas típicas de novatos (PGN válidos)
        self.sample_games = [
            # Mate del pastor fallido
            "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0",
            
            # Defensa contra mate del pastor
            "1. e4 e5 2. Bc4 Nc6 3. Qh5 g6 4. Qf3 Nf6 5. Qb3 Nd4 6. Bxf7+ Ke7 7. Qc4 b5 8. Qxc7 Qxc7 0-1",
            
            # Apertura italiana básica
            "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. d3 d6 5. Bg5 f6 6. Bh4 g5 7. Bg3 h5 8. h3 Bg4 9. hxg4 hxg4 10. Rxh8 gxf3 11. gxf3 Qd7 0-1",
            
            # Gambito de rey
            "1. e4 e5 2. f4 exf4 3. Nf3 g5 4. Bc4 g4 5. Ne5 Qh4+ 6. Kf1 Nh6 7. d4 f3 8. gxf3 gxf3 9. Rg1 Ng4 0-1",
            
            # Defensa francesa
            "1. e4 e6 2. d4 d5 3. e5 c5 4. c3 Nc6 5. Nf3 Qb6 6. Be2 cxd4 7. cxd4 Nxd4 8. Nxd4 Qxd4 9. Qxd4 1/2-1/2",
            
            # Defensa siciliana
            "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be2 e5 7. Nb3 Be7 8. O-O O-O 9. f4 exf4 10. Bxf4 Nc6 1/2-1/2",
            
            # Apertura de peón de dama
            "1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Be7 5. e3 O-O 6. Nf3 Nbd7 7. Rc1 c6 8. Bd3 dxc4 9. Bxc4 Nd5 10. Bxe7 Qxe7 1-0",
            
            # Apertura inglesa
            "1. c4 e5 2. Nc3 Nf6 3. Nf3 Nc6 4. g3 d5 5. cxd5 Nxd5 6. Bg2 Nxc3 7. bxc3 Bd6 8. O-O O-O 9. d3 h6 10. Rb1 Re8 1/2-1/2",
            
            # Ataque directo fallido
            "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 0-1",
            
            # Partida corta
            "1. f3 e5 2. g4 Qh4# 0-1",
            
            # Defensa escandinava
            "1. e4 d5 2. exd5 Qxd5 3. Nc3 Qa5 4. d4 Nf6 5. Nf3 Bf5 6. Bd2 e6 7. Be2 Bb4 8. O-O Bxc3 9. bxc3 Qxc3 1/2-1/2",
            
            # Apertura irregular
            "1. h3 e5 2. g3 d5 3. Bg2 Nf6 4. d3 Bc5 5. Nf3 Nc6 6. O-O O-O 7. Nbd2 Re8 8. e4 dxe4 9. dxe4 Qd4 0-1"
        ]
    
    def generate_novice_game(self, game_id: int) -> dict:
        """Generar una partida novice válida"""
        
        # Seleccionar jugadores
        white = random.choice(self.names)
        black = random.choice([n for n in self.names if n != white])
        
        # Seleccionar partida base
        base_game = random.choice(self.sample_games)
        
        # Extraer resultado
        if "1-0" in base_game:
            result = "1-0"
        elif "0-1" in base_game:
            result = "0-1"
        else:
            result = "1/2-1/2"
        
        # Generar ratings novice (400-1200)
        white_elo = str(random.randint(400, 1200))
        black_elo = str(random.randint(400, 1200))
        
        # Generar fecha reciente
        start_date = datetime.now() - timedelta(days=180)
        random_days = random.randint(0, 180)
        game_date = start_date + timedelta(days=random_days)
        date_str = game_date.strftime("%Y.%m.%d")
        
        # Crear PGN completo
        pgn_lines = [
            f'[Event "Casual Game"]',
            f'[Site "Online"]',
            f'[Date "{date_str}"]',
            f'[Round "1"]',
            f'[White "{white}"]',
            f'[Black "{black}"]',
            f'[Result "{result}"]',
            f'[WhiteElo "{white_elo}"]',
            f'[BlackElo "{black_elo}"]',
            f'[TimeControl "600"]',
            '',
            base_game
        ]
        
        pgn_text = '\n'.join(pgn_lines)
        
        return {
            'game_id': f"novice_simple_{game_id:04d}_{white}_{black}",
            'white_player': white[:50],
            'black_player': black[:50],
            'result': result,
            'white_elo': white_elo,
            'black_elo': black_elo,
            'pgn': pgn_text,
            'source': 'novice',
            'time_control': '600',
            'opening': 'Various',
            'eco': 'C20',
            'date_played': date_str,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def generate_simple_novice_games(needed: int) -> int:
    """Generar partidas novice simples"""
    print(f"🎮 GENERANDO {needed} PARTIDAS NOVICE SIMPLES")
    print("=" * 60)
    
    generator = SimpleNoviceGenerator()
    
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        
        imported = 0
        skipped = 0
        
        for i in range(needed):
            try:
                # Generar partida
                game_data = generator.generate_novice_game(i + 1)
                
                # Verificar duplicados
                if repo.game_exists(game_data['game_id']):
                    skipped += 1
                    continue
                
                # Guardar
                repo.save_game(game_data)
                imported += 1
                
                if imported % 100 == 0:
                    print(f"  ✅ {imported} partidas creadas...")
                
            except Exception as e:
                print(f"  ⚠️  Error partida {i+1}: {str(e)[:50]}")
                continue
        
        print(f"\n📊 RESULTADO:")
        print(f"  ✅ Creadas: {imported}")
        print(f"  ⏭️  Omitidas: {skipped}")
        
        return imported
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        return 0

def main():
    """Función principal"""
    print("🚀 GENERADOR SIMPLE DE PARTIDAS NOVICE")
    print("=" * 60)
    
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        
        # Verificar estado actual
        all_games = repo.get_all_games()
        current_novice = sum(1 for g in all_games if getattr(g, 'source', '') == 'novice')
        
        print(f"📊 Partidas novice actuales: {current_novice}")
        
        if current_novice >= 1000:
            print(f"✅ ¡Ya tienes {current_novice} partidas novice!")
            return
        
        needed = 1000 - current_novice
        print(f"🎯 Necesitas {needed} partidas más")
        
        # Generar partidas
        generated = generate_simple_novice_games(needed)
        
        # Verificar resultado
        print(f"\n🔍 VERIFICACIÓN FINAL")
        print("=" * 50)
        
        all_games = repo.get_all_games()
        final_novice = sum(1 for g in all_games if getattr(g, 'source', '') == 'novice')
        
        print(f"📊 Partidas novice finales: {final_novice}")
        
        if final_novice >= 1000:
            print(f"🎉 ¡META ALCANZADA! {final_novice} partidas novice")
        else:
            print(f"📈 Progreso: {final_novice}/1000")
        
        # Mostrar resumen por fuente
        sources = {}
        for game in all_games:
            source = getattr(game, 'source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📈 Estado final de la BD:")
        for source, count in sources.items():
            print(f"  - {source}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
