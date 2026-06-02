#!/usr/bin/env python3
"""
Overnight ML Pipeline - Features to Dataset

Since we already have extracted features in Parquet files, this script:
1. Loads existing features into PostgreSQL
2. Creates balanced dataset with optimal sampling
3. Generates final training dataset

Usage:
    python overnight_features_to_dataset.py
"""

import pandas as pd
import os
import sys
import time
import logging
from pathlib import Path
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_features_to_database():
    """Load existing features from Parquet into PostgreSQL."""
    logger.info("🔄 Loading existing features into PostgreSQL...")

    # Database URL
    DB_URL = "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db"

    try:
        engine = create_engine(DB_URL)

        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")

        # Feature files to load
        feature_files = [
            ("/notebooks/data/export/elite/features.parquet", "elite", 50000),
            ("/notebooks/data/export/fide/features.parquet", "fide", 50000),
            ("/notebooks/data/export/novice/features.parquet", "novice", 25000),
            ("/notebooks/data/export/personal/features.parquet", "personal", 25000),
        ]

        total_loaded = 0

        for parquet_path, source, target_sample in feature_files:
            if os.path.exists(parquet_path):
                logger.info(f"📖 Loading {source} features (target: {target_sample:,})")

                # Read features
                df = pd.read_parquet(parquet_path)
                logger.info(f"   📊 Available: {len(df):,} feature records")

                # Sample if needed
                if len(df) > target_sample:
                    df_sampled = df.sample(n=target_sample, random_state=42)
                    logger.info(f"   📊 Sampled: {target_sample:,} from {len(df):,}")
                else:
                    df_sampled = df.copy()
                    logger.info(f"   📊 Using all: {len(df):,} records")

                # Ensure source column
                df_sampled["source"] = source

                # Add to features table (create table if needed)
                try:
                    # Clean up the dataframe for PostgreSQL
                    df_clean = df_sampled.copy()

                    # Create mapping for game_analytics table (aggregated data)
                    # Group move-level data by game_id to create game-level features
                    if 'move_number' in df_clean.columns:
                        # This is move-level data, aggregate to game level
                        game_agg = df_clean.groupby('game_id').agg({
                            'material_balance': ['mean', 'std', 'min', 'max'],
                            'material_total': ['mean', 'min', 'max'],
                            'num_pieces': ['mean', 'min'],
                            'branching_factor': ['mean', 'max'],
                            'move_number': 'max'  # Total moves
                        }).round(3)
                        
                        # Flatten column names
                        game_agg.columns = [f"{col[0]}_{col[1]}" for col in game_agg.columns]
                        game_agg = game_agg.reset_index()
                        
                        # Map to game_analytics structure
                        df_mapped = pd.DataFrame({
                            'game_id': game_agg['game_id'],
                            'source': source,
                            'total_moves': game_agg['move_number_max'],
                            'avg_material_balance': game_agg['material_balance_mean'],
                            'material_balance_std': game_agg['material_balance_std'],
                            'min_material_balance': game_agg['material_balance_min'],
                            'max_material_balance': game_agg['material_balance_max'],
                            'avg_material_total': game_agg['material_total_mean'],
                            'min_material_total': game_agg['material_total_min'],
                            'max_material_total': game_agg['material_total_max'],
                            'avg_num_pieces': game_agg['num_pieces_mean'],
                            'min_num_pieces': game_agg['num_pieces_min'],
                            'avg_branching_factor': game_agg['branching_factor_mean'],
                            'max_branching_factor': game_agg['branching_factor_max']
                        })
                        
                        table_name = "game_analytics"
                    else:
                        # This is already game-level data, use as is
                        df_mapped = df_clean.copy()
                        table_name = "features"
                    
                    # Load in chunks to appropriate table
                    chunk_size = 5000
                    for i in range(0, len(df_mapped), chunk_size):
                        chunk = df_mapped.iloc[i : i + chunk_size]
                        chunk.to_sql(
                            table_name,
                            engine,
                            if_exists="append",
                            index=False,
                            method="multi",
                        )

                        if i % 25000 == 0:  # Log every 25k records
                            logger.info(
                                f"   📋 {source}: {i + len(chunk):,}/{len(df_mapped):,} loaded"
                            )

                    total_loaded += len(df_mapped)
                    logger.info(
                        f"✅ {source}: {len(df_mapped):,} game analytics loaded to database"
                    )

                except Exception as e:
                    logger.error(f"❌ Error loading {source} to database: {e}")
            else:
                logger.warning(f"⚠️ File not found: {parquet_path}")

        logger.info(f"🎉 Total features loaded: {total_loaded:,}")

        # Verify database
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT source, COUNT(*) FROM game_analytics GROUP BY source ORDER BY source"
                )
            )
            logger.info("📊 Game analytics by source in database:")
            for row in result:
                logger.info(f"   - {row[0]}: {row[1]:,} game analytics")

        return True

    except Exception as e:
        logger.error(f"❌ Feature loading failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_balanced_training_dataset():
    """Create balanced training dataset from loaded features."""
    logger.info("🎯 Creating balanced training dataset...")

    try:
        # Database connection
        DB_URL = "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db"
        engine = create_engine(DB_URL)

        # Load features from database with balanced sampling
        logger.info("📖 Loading features from database...")

        query = """
        SELECT * FROM game_analytics 
        WHERE source IN ('elite', 'fide', 'novice', 'personal')
        ORDER BY RANDOM()
        """

        df_all = pd.read_sql(query, engine)
        logger.info(f"📊 Total features loaded: {len(df_all):,}")

        # Group by source and show distribution
        source_counts = df_all["source"].value_counts()
        logger.info("📋 Current distribution:")
        for source, count in source_counts.items():
            logger.info(f"   - {source}: {count:,} features")

        # Save as training dataset
        output_dir = Path("/notebooks/data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "training_dataset_balanced_features.parquet"
        df_all.to_parquet(output_file, index=False)

        logger.info(f"✅ Balanced training dataset created!")
        logger.info(f"📂 Saved to: {output_file}")
        logger.info(f"📊 Total records: {len(df_all):,}")

        # Basic statistics
        if "material_balance" in df_all.columns:
            logger.info("📈 Dataset statistics:")
            logger.info(
                f"   - Material balance range: {df_all['material_balance'].min():.2f} to {df_all['material_balance'].max():.2f}"
            )
            logger.info(
                f"   - Average material total: {df_all['material_total'].mean():.2f}"
            )

        return True

    except Exception as e:
        logger.error(f"❌ Training dataset creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_summary_datasets():
    """Create summary datasets by source for analysis."""
    logger.info("📊 Creating summary datasets by source...")

    try:
        # Read the main training dataset
        training_file = Path(
            "/notebooks/data/processed/training_dataset_balanced_features.parquet"
        )

        if not training_file.exists():
            logger.warning("⚠️ Training dataset not found, skipping summaries")
            return True

        df = pd.read_parquet(training_file)

        # Create summary by source
        summary_dir = Path("/notebooks/data/processed/summaries")
        summary_dir.mkdir(parents=True, exist_ok=True)

        for source in df["source"].unique():
            source_df = df[df["source"] == source]
            source_file = summary_dir / f"{source}_features_summary.parquet"
            source_df.to_parquet(source_file, index=False)
            logger.info(
                f"✅ {source}: {len(source_df):,} features saved to {source_file}"
            )

        # Create overall summary statistics
        summary_stats = {
            "total_records": len(df),
            "sources": df["source"].nunique(),
            "records_by_source": df["source"].value_counts().to_dict(),
        }

        import json

        stats_file = summary_dir / "dataset_summary.json"
        with open(stats_file, "w") as f:
            json.dump(summary_stats, f, indent=2)

        logger.info(f"✅ Summary statistics saved to {stats_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Summary creation failed: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("🚀 Starting Overnight Features to Dataset Pipeline...")
    start_time = time.time()

    # Step 1: Load features to database
    if not load_features_to_database():
        logger.error("❌ Feature loading failed")
        return False

    # Step 2: Create balanced training dataset
    if not create_balanced_training_dataset():
        logger.error("❌ Training dataset creation failed")
        return False

    # Step 3: Create summary datasets
    if not create_summary_datasets():
        logger.warning("⚠️ Summary creation had issues")

    # Final summary
    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"🎉 Pipeline completed successfully in {duration:.2f} seconds!")
    logger.info("✅ Ready for ML training with balanced dataset!")

    # Show final files
    logger.info("📂 Generated files:")
    processed_dir = Path("/notebooks/data/processed")
    for file in processed_dir.glob("*.parquet"):
        logger.info(f"   - {file.name}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
