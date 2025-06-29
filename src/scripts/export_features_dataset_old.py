
from datetime import datetime

from export_features_for_source import export_features_to_dataset


def get_output_path():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"/app/src/data/export/features_dataset_{timestamp}"


OUTPUT_PATH = get_output_path()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Exportar features filtrados a Parquet")
    parser.add_argument("--min_elo", type=int, help="Elo mínimo")
    parser.add_argument("--max_elo", type=int, help="Elo máximo")
    parser.add_argument("--player", type=str,
                        help="Nombre del jugador (parcial o completo)")
    parser.add_argument("--opening", type=str, help="Apertura (eco o nombre)")
    parser.add_argument("--limit", type=int,
                        help="Máximo de partidas a exportar")
    parser.add_argument("--output_path", type=str, default=OUTPUT_PATH,
                        help="Ruta de salida del archivo Parquet (default: %(default)s)")
    parser.add_argument("--file_type", type=str, default="parquet",
                        choices=["parquet", "csv"],
                        help="Tipo de archivo a exportar (default: %(default)s)")

    args = parser.parse_args()

    args.file_type = "parquet"
    export_features_to_dataset(
        output_path=OUTPUT_PATH,
        min_elo=args.min_elo,
        max_elo=args.max_elo,
        player=args.player,
        opening=args.opening,
        limit=args.limit,
        file_type=args.file_type
    )
