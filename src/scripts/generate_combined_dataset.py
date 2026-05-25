#!/usr/bin/env python3
"""
Optimized Combined Dataset Generator for Chess ML Training

This script creates a balanced dataset using the optimal configuration:
- Elite: 50,000 games (sample from 1.6M available)
- Fide: 50,000 games (sample from 2M available)
- Novice: 25,000 games (from 122k available)
- Personal: 25,000 games (from 337k available)
- Total: 150,000 games - optimal for ML training

Usage:
    python generate_combined_dataset.py
"""

import pandas as pd
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Configuration ---
BASE_DIR = Path("/notebooks/data/processed")
OUTPUT_FILE = "training_dataset_balanced.parquet"

# Optimal sampling configuration
OPTIMAL_SAMPLES = {
    "elite": 50000,  # Sample from 1.6M available
    "fide": 50000,  # Sample from 2M available
    "novice": 25000,  # From 122k available
    "personal": 25000,  # From 337k available
    "stockfish": 0,  # Skip for balanced training
}

TOTAL_TARGET = sum(OPTIMAL_SAMPLES.values())  # 150k total


def load_and_sample_dataset(source_name, target_samples, random_state=42):
    """Load dataset and sample the specified number of games."""
    source_file = BASE_DIR / f"{source_name}_games.parquet"

    if not source_file.exists():
        logger.warning(f"⚠️ Dataset not found: {source_file}")
        return None

    try:
        # Load full dataset
        df = pd.read_parquet(source_file)
        logger.info(f"📖 Loaded {source_name}: {len(df):,} games available")

        if target_samples == 0:
            logger.info(f"⏭️ Skipping {source_name} (target_samples = 0)")
            return None

        # Sample if needed
        if len(df) > target_samples:
            df_sampled = df.sample(n=target_samples, random_state=random_state)
            logger.info(
                f"📊 Sampled {source_name}: {target_samples:,} games (from {len(df):,})"
            )
        else:
            df_sampled = df.copy()
            logger.info(
                f"📊 Using all {source_name}: {len(df):,} games (target was {target_samples:,})"
            )

        # Ensure source column
        df_sampled["source"] = source_name

        return df_sampled

    except Exception as e:
        logger.error(f"❌ Error loading {source_name}: {e}")
        return None


def create_balanced_dataset():
    """Create the optimally balanced dataset."""
    logger.info("🚀 Creating optimally balanced dataset...")
    logger.info(f"🎯 Target configuration:")
    for source, count in OPTIMAL_SAMPLES.items():
        if count > 0:
            logger.info(f"   - {source.capitalize()}: {count:,} games")
    logger.info(f"📊 Total target: {TOTAL_TARGET:,} games")

    datasets = []
    actual_total = 0

    # Load and sample each source
    for source_name, target_samples in OPTIMAL_SAMPLES.items():
        df_source = load_and_sample_dataset(source_name, target_samples)

        if df_source is not None:
            datasets.append(df_source)
            actual_total += len(df_source)
            logger.info(
                f"✅ {source_name.capitalize()}: {len(df_source):,} games added"
            )

    if not datasets:
        logger.error("❌ No datasets loaded successfully")
        return False

    # Combine all datasets
    logger.info("🔄 Combining datasets...")
    df_combined = pd.concat(datasets, ignore_index=True)

    # Shuffle the combined dataset
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

    # Save combined dataset
    output_path = BASE_DIR / OUTPUT_FILE
    df_combined.to_parquet(output_path, index=False)

    # Summary
    logger.info(f"🎉 Balanced dataset created successfully!")
    logger.info(f"📊 Final summary:")
    logger.info(f"   - Total games: {len(df_combined):,}")
    logger.info(f"   - Target was: {TOTAL_TARGET:,}")
    logger.info(f"   - Saved to: {output_path}")

    # Distribution by source
    logger.info("📋 Distribution by source:")
    source_counts = df_combined["source"].value_counts().sort_index()
    for source, count in source_counts.items():
        percentage = (count / len(df_combined)) * 100
        logger.info(f"   - {source.capitalize()}: {count:,} games ({percentage:.1f}%)")

    # Basic statistics
    if "white_elo" in df_combined.columns:
        logger.info("📈 ELO statistics:")
        logger.info(
            f"   - White ELO range: {df_combined['white_elo'].min():.0f} - {df_combined['white_elo'].max():.0f}"
        )
        logger.info(
            f"   - Black ELO range: {df_combined['black_elo'].min():.0f} - {df_combined['black_elo'].max():.0f}"
        )
        logger.info(f"   - Average White ELO: {df_combined['white_elo'].mean():.0f}")
        logger.info(f"   - Average Black ELO: {df_combined['black_elo'].mean():.0f}")

    return True


def main():
    """Main execution function."""
    try:
        # Create output directory if needed
        BASE_DIR.mkdir(parents=True, exist_ok=True)

        # Create balanced dataset
        success = create_balanced_dataset()

        if success:
            logger.info("✅ Process completed successfully")
            return 0
        else:
            logger.error("❌ Process failed")
            return 1

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
