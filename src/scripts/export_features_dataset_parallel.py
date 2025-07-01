import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from db.repository.features_repository import FeaturesRepository

# Constants
EXPORT_DIR = os.environ.get("EXPORT_DIR", "/app/src/data/export")
SOURCES = ["personal", "novice", "elite", "stockfish", "fide"]


def export_features_to_dataset(
    source: str,
    output_path: str,
    player: str | None = None,
    opening: str | None = None,
    min_elo: int | None = None,
    max_elo: int | None = None,
    limit: int | None = None,
    file_type: str = "parquet"
):
    """
    Exports a subset of the `features` table to a Parquet file,
    applying optional filters by player, opening, ELO, and game limit.
    """
    print("🔄 Exporting features dataset...")
    print(f"Applied filters:  ")
    print(f"  - Source: {source}")
    print(f"  - Opening: {opening if opening else 'All'}")
    print(f"  - Player: {player if player else 'All'}")
    print(f"  - Min elo: {min_elo}")
    print(f"  - Max elo: {max_elo} ")
    print(f"  - Limit games: {limit}")
    print(f"  - File type: {file_type}")

    features_repo = FeaturesRepository()

    df = features_repo.get_features_with_filters(
        source,
        player_name=player,
        opening=opening,
        min_elo=min_elo,
        max_elo=max_elo,
        limit=limit
    )

    if df is None:
        print("⚠️ No data found with those filters.")
        return

    print(f"🔄 Total features found: {len(df)}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if file_type == "parquet":
        output_path = output_path + ".parquet"
        print(f"🔄 Exporting to Parquet at {output_path}")
        df.to_parquet(output_path, index=False)
    elif file_type == "csv":
        output_path = output_path + ".csv"
        df.to_csv(output_path, index=False)

    # Handle empty DataFrames safely
    if len(df) == 0:
        print(f"✅ Exported 0 rows (0 games) to {output_path}")
    else:
        game_count = df['game_id'].nunique() if 'game_id' in df.columns else 0
        print(
            f"✅ Exported {len(df)} rows ({game_count} games) to {output_path}")


def export_features_for_source(source: str):
    output_path = Path(EXPORT_DIR) / source / "features"
    print(f"🔄 Exporting features for source: {source} to {output_path}")
    export_features_to_dataset(source=source, output_path=str(
        output_path), file_type="parquet")


def export_all_sources_parallel():
    print("🔄 Exporting features by source in parallel...")
    print(f"Export directory: {EXPORT_DIR}")
    print(f"Sources: {SOURCES}")
    with ProcessPoolExecutor() as executor:
        executor.map(export_features_for_source, SOURCES)
    print("✅ Parallel export by source completed.")


if __name__ == "__main__":
    export_all_sources_parallel()
