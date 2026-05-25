#!/usr/bin/env python3
"""
🚀 Lichess PGN Downloader - Descarga partidas de usuarios específicos

Descarga todas las partidas de un usuario de Lichess en formato PGN.

Usage:
    python lichess_user_downloader.py USERNAME [--output-dir PATH] [--after-date YYYY-MM-DD] [--max-games N]

Examples:
    python lichess_user_downloader.py Th3_hound
    python lichess_user_downloader.py Th3_hound --after-date 2024-01-01
    python lichess_user_downloader.py Th3_hound --max-games 500 --output-dir data/games/personal
"""

import argparse
import requests
import time
from datetime import datetime
from pathlib import Path
import sys


class LichessDownloader:
    """Cliente robusto para descargar partidas de Lichess."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Chess Trainer Project (github.com/chess_trainer)",
            "Accept": "application/x-chess-pgn"
        })
        self.base_url = "https://lichess.org/api"

    def check_user_exists(self, username: str) -> dict:
        """Verifica si el usuario existe y obtiene su perfil."""
        url = f"{self.base_url}/user/{username}"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"❌ Usuario '{username}' no encontrado en Lichess")
                return None
            else:
                print(f"⚠️  Error al verificar usuario: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return None

    def download_games(
        self,
        username: str,
        output_file: Path,
        after_date: datetime = None,
        max_games: int = None
    ) -> int:
        """
        Descarga las partidas del usuario en formato PGN.

        Args:
            username: Nombre de usuario de Lichess
            output_file: Archivo de salida para las partidas
            after_date: Solo partidas después de esta fecha
            max_games: Límite máximo de partidas (None = todas)

        Returns:
            Número de partidas descargadas
        """
        # Construir URL con parámetros
        url = f"{self.base_url}/games/user/{username}"
        params = {
            "rated": "true",  # Solo partidas rankeadas
            "clocks": "false",  # No incluir información de tiempo
            "evals": "false",  # No incluir evaluaciones
            "opening": "true",  # Incluir información de apertura
        }

        if max_games:
            params["max"] = max_games

        if after_date:
            # Lichess API acepta timestamps en milisegundos
            timestamp_ms = int(after_date.timestamp() * 1000)
            params["since"] = timestamp_ms

        print(f"🔄 Descargando partidas de {username}...")
        print(f"   URL: {url}")
        print(f"   Parámetros: {params}")

        try:
            response = self.session.get(url, params=params, timeout=300, stream=True)  # Timeout más largo

            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                return 0

            # Guardar las partidas en el archivo
            output_file.parent.mkdir(parents=True, exist_ok=True)

            game_count = 0
            bytes_downloaded = 0
            with open(output_file, 'wb') as f:  # Write in binary mode
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        # Contar juegos aproximadamente
                        try:
                            text_chunk = chunk.decode('utf-8', errors='ignore')
                            new_games = text_chunk.count('[Event ')
                            game_count += new_games
                            # Mostrar progreso cada 100 partidas
                            if new_games > 0 and game_count % 100 < new_games:
                                mb = bytes_downloaded / (1024 * 1024)
                                print(f"   📥 {game_count} partidas ({mb:.1f} MB)...")
                        except:
                            pass

            print(f"✅ {game_count} partidas guardadas en {output_file}")
            return game_count

        except requests.exceptions.Timeout:
            print("❌ Timeout al descargar partidas")
            return 0
        except Exception as e:
            print(f"❌ Error al descargar: {e}")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="Descargar partidas de un usuario de Lichess en formato PGN"
    )
    parser.add_argument("username", help="Nombre de usuario de Lichess")
    parser.add_argument(
        "--output-dir",
        default="data/games/personal",
        help="Directorio de salida (default: data/games/personal)"
    )
    parser.add_argument(
        "--after-date",
        help="Solo partidas después de esta fecha (formato: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--max-games",
        type=int,
        help="Número máximo de partidas a descargar"
    )

    args = parser.parse_args()

    # Parse after_date si se proporciona
    after_date = None
    if args.after_date:
        try:
            after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Formato de fecha inválido: {args.after_date}")
            print("   Use formato YYYY-MM-DD (ej: 2024-01-01)")
            sys.exit(1)

    # Configurar archivo de salida
    output_dir = Path(args.output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"lichess_{args.username}_{timestamp}.pgn"

    print("=" * 50)
    print("🚀 LICHESS PGN DOWNLOADER")
    print("=" * 50)
    print(f"👤 Usuario: {args.username}")
    if after_date:
        print(f"📅 Desde: {after_date.strftime('%Y-%m-%d')}")
    else:
        print(f"📅 Fecha: Todas las partidas")
    if args.max_games:
        print(f"📊 Límite: {args.max_games} partidas")
    print(f"📁 Output: {output_file}")
    print()

    # Crear downloader
    downloader = LichessDownloader()

    # Verificar usuario
    print("🔍 Verificando usuario...")
    profile = downloader.check_user_exists(args.username)

    if not profile:
        sys.exit(1)

    # Mostrar información del usuario
    print(f"✅ Usuario encontrado:")
    print(f"   Nombre: {profile.get('username')}")
    if 'profile' in profile and 'country' in profile['profile']:
        print(f"   País: {profile['profile']['country']}")

    # Mostrar rating si está disponible
    if 'perfs' in profile:
        print(f"   Ratings:")
        for game_type, data in profile['perfs'].items():
            if 'rating' in data:
                print(f"      {game_type}: {data['rating']}")

    print()

    # Descargar partidas
    game_count = downloader.download_games(
        args.username,
        output_file,
        after_date,
        args.max_games
    )

    if game_count > 0:
        print()
        print("=" * 50)
        print("✅ DESCARGA COMPLETADA")
        print("=" * 50)
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Total: {game_count} partidas")
        print()
        print("💡 Próximos pasos:")
        print(f"   1. Importar a la base de datos:")
        print(f"      python src/scripts/import_pgns_parallel.py {output_file}")
        print(f"   2. Generar features:")
        print(f"      python src/scripts/generate_features_with_tactics.py")
    else:
        print()
        print("⚠️  No se descargaron partidas")
        sys.exit(1)


if __name__ == "__main__":
    main()
