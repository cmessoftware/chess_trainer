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
    try:
        output_path = Path(EXPORT_DIR) / source / "features"
        print(f"🔄 Exporting features for source: {source} to {output_path}")

        # For large datasets like FIDE, add a reasonable limit to prevent memory issues
        limit = None
        if source == "fide":
            limit = 50000  # Limit FIDE to 50k features to prevent memory issues
            print(
                f"⚠️  Applying limit of {limit} features for {source} source to prevent memory issues")

        export_features_to_dataset(
            source=source,
            output_path=str(output_path),
            file_type="parquet",
            limit=limit
        )
        print(f"✅ Successfully exported features for source: {source}")

    except Exception as e:
        print(f"❌ Error exporting features for source {source}: {e}")
        import traceback
        traceback.print_exc()


def export_all_sources_parallel():
    print("🔄 Exporting features by source in parallel...")
    print(f"Export directory: {EXPORT_DIR}")
    print(f"Sources: {SOURCES}")
    with ProcessPoolExecutor() as executor:
        executor.map(export_features_for_source, SOURCES)
    print("✅ Parallel export by source completed.")


def export_unified_dataset(
    output_filename: str = "unified_features",
    file_type: str = "parquet",
    limit_per_source: int | None = None,
    include_sources: list[str] | None = None
):
    """
    Exports a unified dataset combining all sources into a single file.
    
    Args:
        output_filename: Name of the output file (without extension)
        file_type: Output format ('parquet' or 'csv')
        limit_per_source: Limit rows per source to prevent memory issues
        include_sources: List of sources to include (defaults to all)
    """
    import pandas as pd
    
    print("🔄 Creating unified dataset from all sources...")
    
    sources_to_process = include_sources if include_sources else SOURCES
    print(f"📋 Sources to combine: {sources_to_process}")
    
    all_dataframes = []
    total_rows = 0
    total_games = 0
    
    features_repo = FeaturesRepository()
    
    for source in sources_to_process:
        print(f"🔄 Processing source: {source}")
        
        # Apply per-source limit if specified
        limit = limit_per_source
        if source == "fide" and limit_per_source is None:
            limit = 50000  # Default limit for FIDE to prevent memory issues
            print(f"⚠️  Applying default limit of {limit} for {source} to prevent memory issues")
        elif limit_per_source:
            print(f"📊 Applying limit of {limit} for {source}")
        
        try:
            df = features_repo.get_features_with_filters(
                source=source,
                limit=limit
            )
            
            if df is not None and len(df) > 0:
                # Add source column to track origin
                df['source_origin'] = source
                all_dataframes.append(df)
                
                source_rows = len(df)
                source_games = df['game_id'].nunique() if 'game_id' in df.columns else 0
                total_rows += source_rows
                total_games += source_games
                
                print(f"✅ {source}: {source_rows:,} rows ({source_games:,} games)")
            else:
                print(f"⚠️  {source}: No data found")
                
        except Exception as e:
            print(f"❌ Error processing {source}: {e}")
            continue
    
    if not all_dataframes:
        print("❌ No data found in any source")
        return
    
    print(f"🔄 Combining {len(all_dataframes)} datasets...")
    
    # Combine all dataframes
    unified_df = pd.concat(all_dataframes, ignore_index=True)
    
    print(f"📊 Unified dataset summary:")
    print(f"   - Total rows: {total_rows:,}")
    print(f"   - Total games: {total_games:,}")
    print(f"   - Sources combined: {len(all_dataframes)}")
    
    # Create output path
    output_path = Path(EXPORT_DIR) / output_filename
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Export unified dataset
    if file_type == "parquet":
        final_path = str(output_path) + ".parquet"
        print(f"🔄 Exporting unified dataset to Parquet at {final_path}")
        unified_df.to_parquet(final_path, index=False)
    elif file_type == "csv":
        final_path = str(output_path) + ".csv"
        print(f"🔄 Exporting unified dataset to CSV at {final_path}")
        unified_df.to_csv(final_path, index=False)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    print(f"✅ Unified dataset exported successfully!")
    print(f"📁 File: {final_path}")
    print(f"📊 Size: {unified_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB in memory")
    
    # Show source distribution
    if 'source_origin' in unified_df.columns:
        print(f"📈 Source distribution:")
        source_counts = unified_df['source_origin'].value_counts()
        for source, count in source_counts.items():
            percentage = (count / len(unified_df)) * 100
            print(f"   - {source}: {count:,} rows ({percentage:.1f}%)")
    
    return final_path


def export_unified_with_options():
    """Export unified dataset with different configuration options."""
    
    print("🔄 Exporting multiple unified dataset configurations...")
    
    # Configuration 1: All sources with limits
    print("\n" + "="*50)
    print("📊 Configuration 1: All sources (with limits)")
    export_unified_dataset(
        output_filename="unified_all_sources_limited",
        limit_per_source=10000,  # 10k rows per source
        file_type="parquet"
    )
    
    # Configuration 2: Only small sources (no limits)
    print("\n" + "="*50)
    print("📊 Configuration 2: Small sources only (no limits)")
    export_unified_dataset(
        output_filename="unified_small_sources",
        include_sources=["personal", "novice", "stockfish"],
        file_type="parquet"
    )
    
    # Configuration 3: Elite + Personal (balanced)
    print("\n" + "="*50)
    print("📊 Configuration 3: Elite + Personal (balanced)")
    export_unified_dataset(
        output_filename="unified_elite_personal",
        include_sources=["elite", "personal"],
        limit_per_source=25000,
        file_type="parquet"
    )
    
    print("\n✅ All unified dataset configurations exported!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "unified":
        # Export unified datasets
        export_unified_with_options()
    elif len(sys.argv) > 1 and sys.argv[1] == "unified-all":
        # Export single unified dataset with all sources
        export_unified_dataset(
            output_filename="unified_all_sources",
            limit_per_source=20000,
            file_type="parquet"
        )
    elif len(sys.argv) > 1 and sys.argv[1] == "unified-small":
        # Export unified dataset with only small sources
        export_unified_dataset(
            output_filename="unified_small_sources",
            include_sources=["personal", "novice", "stockfish"],
            file_type="parquet"
        )
    else:
        # Default: export all sources separately
        export_all_sources_parallel()
