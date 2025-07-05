#!/usr/bin/env python3
"""
Prepare ML-Ready Datasets Script

This script integrates the comprehensive ML preprocessing pipeline with the existing
chess_trainer infrastructure to generate ML-ready datasets for different source types.

Features:
- Loads data from PostgreSQL using existing repositories
- Applies source-specific preprocessing strategies
- Generates train/validation/test splits
- Exports datasets in multiple formats (Parquet, CSV)
- Creates comprehensive preprocessing reports
- Supports both individual source processing and multi-source combinations

Usage Examples:
    # Process all sources
    python prepare_ml_datasets.py --all-sources

    # Process specific source
    python prepare_ml_datasets.py --source elite --max-samples 10000

    # Generate combined dataset
    python prepare_ml_datasets.py --combined --output-dir datasets/ml_ready

    # Quick personal model training set
    python prepare_ml_datasets.py --source personal --target error_label --quick-mode

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL
    ML_DATASETS_OUTPUT_PATH: Output directory for ML datasets (default: datasets/ml_ready)

Author: Chess Trainer ML Pipeline
Date: 2025-07-05
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import json
import warnings

# Add src to path for imports
sys.path.append('/app/src')

# Project imports
from modules.ml_preprocessing import (
    ChessMLPreprocessor, 
    create_source_specific_preprocessor,
    preprocess_multiple_sources,
    SourceType
)
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from modules.eda_utils import clean_and_prepare_dataset
import dotenv

# Load environment
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
OUTPUT_BASE_PATH = Path(os.environ.get("ML_DATASETS_OUTPUT_PATH", "datasets/ml_ready"))
MAX_SAMPLES_DEFAULT = 50000

# Logging setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MLDatasetPreparer:
    """
    Comprehensive ML dataset preparation pipeline.
    """
    
    def __init__(self, output_path: Path = OUTPUT_BASE_PATH):
        """Initialize the dataset preparer."""
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize repositories
        self.features_repo = FeaturesRepository()
        self.games_repo = GamesRepository()
        
        # Processing statistics
        self.processing_stats = {}
        self.start_time = datetime.now()
    
    def load_source_data(
        self, 
        source_type: SourceType, 
        max_samples: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load data for a specific source type from the database.
        
        Args:
            source_type: Type of source to load
            max_samples: Maximum number of samples to load
            
        Returns:
            DataFrame with source data
        """
        logger.info(f"Loading data for source: {source_type}")
        
        try:
            # Load features data filtered by source
            if max_samples:
                games = self.games_repo.get_games_by_pagination_not_analyzed(
                    offset=0, 
                    limit=max_samples,
                    source_filter=source_type
                )
            else:
                # Load all available data for source
                games = self.games_repo.get_all_games_by_source(source_type)
            
            if not games:
                logger.warning(f"No games found for source: {source_type}")
                return pd.DataFrame()
            
            # Extract features from games
            features_data = []
            for game_data in games[:max_samples] if max_samples else games:
                # Convert to format expected by features_repository
                features = self.features_repo.get_features_from_pgn_string(game_data)
                if features is not None and not features.empty:
                    features_data.append(features)
            
            if not features_data:
                logger.warning(f"No features extracted for source: {source_type}")
                return pd.DataFrame()
            
            # Combine all features
            df = pd.concat(features_data, ignore_index=True)
            
            # Add source identifier
            df['source_type'] = source_type
            
            logger.info(f"Loaded {len(df)} samples for source: {source_type}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {source_type}: {e}")
            return pd.DataFrame()
    
    def load_all_sources_data(
        self, 
        max_samples_per_source: Optional[int] = None
    ) -> Dict[SourceType, pd.DataFrame]:
        """
        Load data for all source types.
        
        Args:
            max_samples_per_source: Max samples per source type
            
        Returns:
            Dictionary mapping source types to DataFrames
        """
        sources = ["personal", "novice", "elite", "fide", "stockfish"]
        source_data = {}
        
        for source in sources:
            df = self.load_source_data(source, max_samples_per_source)
            if not df.empty:
                source_data[source] = df
        
        logger.info(f"Loaded data for {len(source_data)} sources")
        return source_data
    
    def prepare_single_source_dataset(
        self,
        source_type: SourceType,
        target_column: str = "error_label",
        max_samples: Optional[int] = None,
        export_formats: List[str] = ["parquet", "csv"]
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepare ML dataset for a single source.
        
        Args:
            source_type: Source type to process
            target_column: Target variable
            max_samples: Maximum samples to include
            export_formats: Export formats ("parquet", "csv")
            
        Returns:
            Tuple of (processed_df, processing_report)
        """
        logger.info(f"🚀 Preparing dataset for source: {source_type}")
        
        # Load data
        df_raw = self.load_source_data(source_type, max_samples)
        
        if df_raw.empty:
            logger.error(f"No data available for source: {source_type}")
            return pd.DataFrame(), {}
        
        # Clean and prepare using existing EDA utils
        df_cleaned = clean_and_prepare_dataset(df_raw)
        
        # Apply ML preprocessing
        preprocessor = create_source_specific_preprocessor(source_type)
        
        # Detect platform for ELO standardization
        platform = self._detect_platform_from_data(df_cleaned)
        
        # Preprocess
        df_processed = preprocessor.fit_transform(
            df_cleaned, 
            source_type=source_type,
            platform=platform
        )
        
        # Quality validation
        quality_report = preprocessor.validate_data_quality(df_processed)
        
        # Prepare train/test splits if target column exists
        if target_column in df_processed.columns:
            try:
                X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_train_test_split(
                    df_processed,
                    target_column=target_column,
                    stratify_by="source_type"
                )
                
                # Save splits
                self._export_dataset_splits(
                    source_type, X_train, X_val, X_test, 
                    y_train, y_val, y_test, export_formats
                )
                
                quality_report["splits_created"] = True
                quality_report["train_samples"] = len(X_train)
                quality_report["val_samples"] = len(X_val)
                quality_report["test_samples"] = len(X_test)
                
            except Exception as e:
                logger.warning(f"Could not create splits for {source_type}: {e}")
                quality_report["splits_created"] = False
        
        # Export full dataset
        self._export_full_dataset(source_type, df_processed, export_formats)
        
        # Processing statistics
        processing_report = {
            "source_type": source_type,
            "raw_samples": len(df_raw),
            "processed_samples": len(df_processed),
            "processing_timestamp": datetime.now().isoformat(),
            "platform_detected": platform,
            "quality_metrics": quality_report,
            "preprocessor_config": {
                "elo_standardization": preprocessor.elo_standardization,
                "scaler_type": preprocessor.scaler_type,
                "handle_outliers": preprocessor.handle_outliers
            }
        }
        
        logger.info(f"✅ Dataset preparation completed for {source_type}")
        return df_processed, processing_report
    
    def prepare_combined_dataset(
        self,
        target_column: str = "error_label",
        max_samples_per_source: Optional[int] = None,
        export_formats: List[str] = ["parquet", "csv"]
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepare combined ML dataset from all sources.
        
        Args:
            target_column: Target variable
            max_samples_per_source: Max samples per source
            export_formats: Export formats
            
        Returns:
            Tuple of (combined_df, processing_report)
        """
        logger.info("🚀 Preparing combined multi-source dataset")
        
        # Load all sources
        source_data = self.load_all_sources_data(max_samples_per_source)
        
        if not source_data:
            logger.error("No source data available")
            return pd.DataFrame(), {}
        
        # Clean each source individually
        cleaned_sources = {}
        for source_type, df in source_data.items():
            cleaned_sources[source_type] = clean_and_prepare_dataset(df)
        
        # Multi-source preprocessing
        df_combined, processing_report = preprocess_multiple_sources(
            cleaned_sources, target_column
        )
        
        # Create global train/test splits
        if target_column in df_combined.columns:
            try:
                preprocessor = ChessMLPreprocessor()
                X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_train_test_split(
                    df_combined,
                    target_column=target_column,
                    stratify_by="source_type"
                )
                
                # Export combined splits
                self._export_dataset_splits(
                    "combined", X_train, X_val, X_test,
                    y_train, y_val, y_test, export_formats
                )
                
                processing_report["combined"]["splits_created"] = True
                
            except Exception as e:
                logger.warning(f"Could not create combined splits: {e}")
                processing_report["combined"]["splits_created"] = False
        
        # Export combined dataset
        self._export_full_dataset("combined", df_combined, export_formats)
        
        logger.info("✅ Combined dataset preparation completed")
        return df_combined, processing_report
    
    def _detect_platform_from_data(self, df: pd.DataFrame) -> str:
        """Detect platform from data characteristics."""
        if "site" in df.columns:
            site_values = df["site"].str.lower().fillna("")
            if site_values.str.contains("lichess").any():
                return "lichess"
            elif site_values.str.contains("chess.com").any():
                return "chess.com"
        return "auto"
    
    def _export_full_dataset(
        self, 
        source_name: str, 
        df: pd.DataFrame, 
        formats: List[str]
    ):
        """Export full dataset in specified formats."""
        base_filename = f"{source_name}_ml_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for fmt in formats:
            if fmt == "parquet":
                output_file = self.output_path / f"{base_filename}.parquet"
                df.to_parquet(output_file, index=False)
                logger.info(f"📄 Exported {fmt}: {output_file}")
            
            elif fmt == "csv":
                output_file = self.output_path / f"{base_filename}.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"📄 Exported {fmt}: {output_file}")
    
    def _export_dataset_splits(
        self,
        source_name: str,
        X_train: pd.DataFrame, X_val: pd.DataFrame, X_test: pd.DataFrame,
        y_train: pd.Series, y_val: pd.Series, y_test: pd.Series,
        formats: List[str]
    ):
        """Export train/validation/test splits."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Combine features and targets
        splits = {
            "train": pd.concat([X_train, y_train], axis=1),
            "val": pd.concat([X_val, y_val], axis=1),
            "test": pd.concat([X_test, y_test], axis=1)
        }
        
        for split_name, split_df in splits.items():
            for fmt in formats:
                if fmt == "parquet":
                    output_file = self.output_path / f"{source_name}_{split_name}_{timestamp}.parquet"
                    split_df.to_parquet(output_file, index=False)
                
                elif fmt == "csv":
                    output_file = self.output_path / f"{source_name}_{split_name}_{timestamp}.csv"
                    split_df.to_csv(output_file, index=False)
        
        logger.info(f"📊 Exported splits for {source_name}")
    
    def export_processing_report(self, processing_reports: Dict) -> Path:
        """Export comprehensive processing report."""
        report_file = self.output_path / f"ml_preprocessing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Add execution metadata
        execution_metadata = {
            "execution_timestamp": datetime.now().isoformat(),
            "execution_duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "python_version": sys.version,
            "output_directory": str(self.output_path),
            "database_url": DB_URL.split('@')[1] if DB_URL else "Not configured"  # Hide credentials
        }
        
        comprehensive_report = {
            "execution_metadata": execution_metadata,
            "processing_reports": processing_reports,
            "summary": self._generate_summary_statistics(processing_reports)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        logger.info(f"📋 Processing report exported: {report_file}")
        return report_file


def _generate_summary_statistics(processing_reports: Dict) -> Dict:
    """Generate summary statistics from processing reports."""
    summary = {
        "total_sources_processed": len(processing_reports),
        "total_samples_processed": sum(
            report.get("processed_samples", 0) 
            for report in processing_reports.values()
        ),
        "sources_with_splits": sum(
            1 for report in processing_reports.values()
            if report.get("quality_metrics", {}).get("splits_created", False)
        ),
        "preprocessing_configurations": {
            source: {
                "scaler": report.get("preprocessor_config", {}).get("scaler_type", "unknown"),
                "elo_standardization": report.get("preprocessor_config", {}).get("elo_standardization", False)
            }
            for source, report in processing_reports.items()
        }
    }
    return summary


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Prepare ML-ready datasets for chess_trainer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all-sources                          # Process all sources
  %(prog)s --source elite --max-samples 10000    # Process elite games only
  %(prog)s --combined --output-dir custom_path   # Generate combined dataset
  %(prog)s --source personal --quick-mode        # Quick personal model prep
        """
    )
    
    # Source selection
    parser.add_argument(
        "--source", 
        choices=["personal", "novice", "elite", "fide", "stockfish"],
        help="Process specific source type"
    )
    parser.add_argument(
        "--all-sources", 
        action="store_true",
        help="Process all source types individually"
    )
    parser.add_argument(
        "--combined", 
        action="store_true",
        help="Create combined multi-source dataset"
    )
    
    # Processing options
    parser.add_argument(
        "--max-samples", 
        type=int, 
        default=MAX_SAMPLES_DEFAULT,
        help=f"Maximum samples per source (default: {MAX_SAMPLES_DEFAULT})"
    )
    parser.add_argument(
        "--target", 
        default="error_label",
        help="Target column for ML (default: error_label)"
    )
    parser.add_argument(
        "--quick-mode", 
        action="store_true",
        help="Quick processing with reduced samples"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=OUTPUT_BASE_PATH,
        help="Output directory for datasets"
    )
    parser.add_argument(
        "--formats", 
        nargs="+",
        choices=["parquet", "csv"],
        default=["parquet", "csv"],
        help="Export formats"
    )
    
    # Execution options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Quick mode adjustments
    if args.quick_mode:
        args.max_samples = min(args.max_samples, 5000)
        logger.info("🚀 Quick mode enabled - limiting to 5000 samples max")
    
    # Initialize preparer
    preparer = MLDatasetPreparer(args.output_dir)
    processing_reports = {}
    
    try:
        # Process based on arguments
        if args.source:
            # Single source processing
            df, report = preparer.prepare_single_source_dataset(
                source_type=args.source,
                target_column=args.target,
                max_samples=args.max_samples,
                export_formats=args.formats
            )
            processing_reports[args.source] = report
            
        elif args.all_sources:
            # All sources individually
            sources = ["personal", "novice", "elite", "fide", "stockfish"]
            for source in sources:
                logger.info(f"Processing source: {source}")
                df, report = preparer.prepare_single_source_dataset(
                    source_type=source,
                    target_column=args.target,
                    max_samples=args.max_samples,
                    export_formats=args.formats
                )
                processing_reports[source] = report
        
        elif args.combined:
            # Combined dataset
            df, report = preparer.prepare_combined_dataset(
                target_column=args.target,
                max_samples_per_source=args.max_samples,
                export_formats=args.formats
            )
            processing_reports["combined"] = report
        
        else:
            # Default: process personal source
            logger.info("No specific source selected, processing 'personal' by default")
            df, report = preparer.prepare_single_source_dataset(
                source_type="personal",
                target_column=args.target,
                max_samples=args.max_samples,
                export_formats=args.formats
            )
            processing_reports["personal"] = report
        
        # Export comprehensive report
        report_file = preparer.export_processing_report(processing_reports)
        
        # Success summary
        logger.info("🎉 ML Dataset preparation completed successfully!")
        logger.info(f"📂 Output directory: {args.output_dir}")
        logger.info(f"📋 Processing report: {report_file}")
        
        # Quick stats
        total_samples = sum(
            report.get("processed_samples", 0) 
            for report in processing_reports.values()
        )
        logger.info(f"📊 Total samples processed: {total_samples:,}")
        
    except Exception as e:
        logger.error(f"❌ Error during dataset preparation: {e}")
        raise


if __name__ == "__main__":
    main()
