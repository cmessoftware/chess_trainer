#!/usr/bin/env python3
"""
Script simple para verificar contenido de un ZIP FIDE
"""

import zipfile
import tempfile
import os
from pathlib import Path
import chess.pgn

def check_carlsen_zip():
    """Verificar contenido específico del ZIP de Carlsen"""
    zip_path = Path(r"c:\Users\sergiosal\source\repos\chess_trainer\src\data\games\fide\Carlsen.zip")
    
    if not zip_path.exists():
        print("❌ Carlsen.zip no encontrado")
        return
    
    print(f"📁 Verificando: {zip_path}")
    print(f"📏 Tamaño: {zip_path.stat().st_size / 1024:.1f} KB")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            print(f"\n📋 Contenido del ZIP:")
            for file_info in zip_ref.filelist:
                print(f"  - {file_info.filename} ({file_info.file_size} bytes)")
            
            # Extraer y leer primer PGN
            with tempfile.TemporaryDirectory() as temp_dir:
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.pgn'):
                        zip_ref.extract(file_info, temp_dir)
                        pgn_file = os.path.join(temp_dir, file_info.filename)
                        
                        print(f"\n📖 Leyendo: {file_info.filename}")
                        
                        with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            print(f"📄 Tamaño del archivo: {len(content)} caracteres")
                            print(f"📝 Primeras 200 caracteres:")
                            print(content[:200])
                            print("...")
                            
                            # Intentar leer primera partida
                            f.seek(0)
                            game = chess.pgn.read_game(f)
                            if game:
                                print(f"\n🎮 Primera partida encontrada:")
                                print(f"  White: {game.headers.get('White', 'N/A')}")
                                print(f"  Black: {game.headers.get('Black', 'N/A')}")
                                print(f"  Event: {game.headers.get('Event', 'N/A')}")
                                print(f"  Date: {game.headers.get('Date', 'N/A')}")
                                
                                # Contar total de partidas
                                f.seek(0)
                                count = 0
                                while chess.pgn.read_game(f) is not None:
                                    count += 1
                                    if count >= 10:  # Solo contar primeras 10 para test
                                        break
                                
                                print(f"🔢 Partidas encontradas (primeras 10): {count}")
                            else:
                                print("❌ No se pudo leer ninguna partida")
                        
                        break
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_carlsen_zip()
