from services.feature_export_services import export_features_to_parquet

OUTPUT_PATH = "/app/src/data/export/features_dataset.parquet"

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

    args = parser.parse_args()

    export_features_to_parquet(
        output_path=OUTPUT_PATH,
        min_elo=args.min_elo,
        max_elo=args.max_elo,
        player=args.player,
        opening=args.opening,
        limit=args.limit
    )
