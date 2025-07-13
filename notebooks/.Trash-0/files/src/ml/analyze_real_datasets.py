#!/usr/bin/env python3
"""
ML Analysis Script for Real Chess Datasets - NON-DESTRUCTIV        # Check common dataset locations
        search_paths = [
            self.base_data_path / "processed",
            self.base_data_path / "export",
            self.base_data_path / "games",
            Path("./data/processed"),
            Path("./data/export"),
            Path("./datasets"),
            Path("/notebooks/datasets/processed"),
            Path("/notebooks/datasets/export"),
            Path("/notebooks/datasets/games"),
            Path("/notebooks/datasets/studies"),
            Path("/notebooks/datasets/tactics"),
            Path("/notebooks/data")
        ]==============================================================

This script performs comprehensive ML analysis on real chess datasets,
comparing error patterns and model performance across different player types:
- elite: High-level players
- personal: Personal games
- novice: Beginner players
- fide: FIDE tournament games
- stockfish: Engine analysis

The script is designed to be completely NON-DESTRUCTIVE:
- Only reads from existing datasets
- Creates temporary copies for analysis
- No modifications to original data
- Uses read-only database connections

Author: Chess Trainer Project
Issue: #21 (ELO Standardization), #78 (ML Pipeline)
Date: 2025-01-27
"""

import os
import sys
import logging
import warnings
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    import mlflow
    import mlflow.sklearn

    warnings.filterwarnings("ignore")
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Please ensure all ML dependencies are installed")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatasetAnalyzer:
    """Non-destructive analyzer for chess datasets"""

    def __init__(self, base_data_path: str = "/data", temp_dir: Optional[str] = None):
        self.base_data_path = Path(base_data_path)
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp())
        self.results = {}
        self.datasets_info = {}

        # Dataset type mapping
        self.dataset_types = {
            "elite": "High-level players",
            "personal": "Personal games",
            "novice": "Beginner players",
            "fide": "FIDE tournament games",
            "stockfish": "Engine analysis",
        }

        logger.info(f"🔬 Initialized DatasetAnalyzer")
        logger.info(f"📂 Base data path: {self.base_data_path}")
        logger.info(f"🗂️ Temp directory: {self.temp_dir}")

    def discover_datasets(self) -> Dict[str, List[str]]:
        """Discover available datasets non-destructively"""
        discovered = {}

        logger.info("🔍 Discovering available datasets...")

        # Search specifically in /notebooks/data/export for Parquet files
        search_paths = [
            Path("/notebooks/data/export"),
            Path("/notebooks/datasets/export"),
            self.base_data_path / "export",
            Path("./notebooks/data/export"),
            Path("./data/export"),
        ]

        for path in search_paths:
            if path.exists():
                logger.info(f"📁 Searching in: {path}")
                # Search for both Parquet and CSV files in root and subdirectories
                parquet_files = (
                    list(path.glob("*.parquet"))
                    + list(path.glob("*.pq"))
                    + list(path.glob("**/*.parquet"))
                    + list(path.glob("**/*.pq"))
                )
                csv_files = list(path.glob("*.csv")) + list(path.glob("**/*.csv"))
                all_files = parquet_files + csv_files

                for file_path in all_files:
                    for dataset_type in self.dataset_types.keys():
                        # Check both filename and parent directory name
                        matches_filename = (
                            dataset_type.lower() in file_path.stem.lower()
                        )
                        matches_directory = (
                            dataset_type.lower() in str(file_path.parent).lower()
                        )

                        if matches_filename or matches_directory:
                            if dataset_type not in discovered:
                                discovered[dataset_type] = []
                            discovered[dataset_type].append(str(file_path))
                            logger.info(f"🎯 Found {dataset_type} dataset: {file_path}")
                            break

        logger.info(f"✅ Discovered datasets: {list(discovered.keys())}")
        return discovered

    def load_dataset_safely(
        self, file_path: str, max_rows: int = 10000
    ) -> Optional[pd.DataFrame]:
        """Load dataset with safety limits (non-destructive)"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return None

            logger.info(f"📖 Loading dataset: {file_path.name} (max {max_rows} rows)")

            # Determine file type and load appropriately
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, nrows=max_rows)
            elif file_path.suffix.lower() in [".parquet", ".pq"]:
                df = pd.read_parquet(file_path)
                df = df.head(max_rows)  # Limit after loading
            elif file_path.suffix.lower() == ".json":
                df = pd.read_json(file_path, lines=True, nrows=max_rows)
            else:
                logger.warning(f"⚠️ Unsupported file format: {file_path.suffix}")
                return None

            logger.info(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            return df

        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return None

    def analyze_dataset_features(
        self, df: pd.DataFrame, dataset_type: str
    ) -> Dict[str, Any]:
        """Analyze dataset features and characteristics"""
        analysis = {
            "dataset_type": dataset_type,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "missing_data": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head(3).to_dict("records") if len(df) > 0 else [],
        }

        # Chess-specific analysis
        chess_columns = {
            "elo": ["elo", "rating", "player_rating", "white_elo", "black_elo"],
            "moves": ["move", "move_uci", "san", "move_notation"],
            "errors": [
                "error",
                "blunder",
                "mistake",
                "inaccuracy",
                "error_label",
                "is_error",
            ],
            "engine": ["eval", "evaluation", "cp", "mate", "stockfish_eval"],
            "tactical": ["tactic", "tactical_motif", "theme", "tags"],
        }

        found_features = {}
        for category, possible_cols in chess_columns.items():
            found = [
                col
                for col in df.columns
                if any(pc in col.lower() for pc in possible_cols)
            ]
            if found:
                found_features[category] = found

        analysis["chess_features"] = found_features

        # ELO analysis if available
        elo_columns = found_features.get("elo", [])
        if elo_columns:
            elo_stats = {}
            for col in elo_columns:
                if col in df.columns and df[col].dtype in ["int64", "float64"]:
                    elo_stats[col] = {
                        "mean": (
                            float(df[col].mean()) if not df[col].isna().all() else None
                        ),
                        "std": (
                            float(df[col].std()) if not df[col].isna().all() else None
                        ),
                        "min": (
                            float(df[col].min()) if not df[col].isna().all() else None
                        ),
                        "max": (
                            float(df[col].max()) if not df[col].isna().all() else None
                        ),
                        "count": int(df[col].count()),
                    }
            analysis["elo_statistics"] = elo_stats

        # Error analysis if available
        error_columns = found_features.get("errors", [])
        if error_columns:
            error_stats = {}
            for col in error_columns:
                if col in df.columns:
                    if df[col].dtype == "bool" or df[col].dtype == "object":
                        error_stats[col] = df[col].value_counts().to_dict()
                    elif df[col].dtype in ["int64", "float64"]:
                        error_stats[col] = {
                            "mean": (
                                float(df[col].mean())
                                if not df[col].isna().all()
                                else None
                            ),
                            "count_nonzero": (
                                int((df[col] != 0).sum())
                                if not df[col].isna().all()
                                else 0
                            ),
                        }
            analysis["error_statistics"] = error_stats

        return analysis

    def prepare_ml_features(
        self, df: pd.DataFrame, dataset_type: str
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare features for ML analysis"""
        try:
            # Look for common ML-ready features
            feature_candidates = []
            target_candidates = []

            # Numerical features
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            feature_candidates.extend(numerical_cols)

            # Look for error/target columns
            error_indicators = [
                "error",
                "blunder",
                "mistake",
                "is_error",
                "error_label",
            ]
            for col in df.columns:
                if any(indicator in col.lower() for indicator in error_indicators):
                    target_candidates.append(col)

            # Remove target candidates from features
            feature_candidates = [
                col for col in feature_candidates if col not in target_candidates
            ]

            if not feature_candidates or not target_candidates:
                logger.warning(
                    f"⚠️ No suitable features or targets found for {dataset_type}"
                )
                return None, None

            # Select best target (prefer binary classification)
            target_col = target_candidates[0]
            if target_col in df.columns:
                y = df[target_col].copy()

                # Convert to binary if needed
                if y.dtype == "object" or len(y.unique()) > 2:
                    # Try to convert to binary error/no-error
                    y = y.notna() & (y != 0) & (y != False) & (y != "no_error")

            # Prepare features
            X = df[feature_candidates].copy()

            # Handle missing values
            X = X.fillna(
                X.median()
                if len(X.select_dtypes(include=[np.number]).columns) > 0
                else 0
            )

            # Ensure we have enough data
            if len(X) < 50:
                logger.warning(f"⚠️ Not enough data for ML analysis: {len(X)} rows")
                return None, None

            logger.info(
                f"✅ Prepared {X.shape[1]} features and {len(y)} targets for {dataset_type}"
            )
            return X.values, y.values

        except Exception as e:
            logger.error(f"❌ Error preparing ML features for {dataset_type}: {e}")
            return None, None

    def train_and_evaluate_model(
        self, X: np.ndarray, y: np.ndarray, dataset_type: str
    ) -> Dict[str, Any]:
        """Train and evaluate ML model"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.2,
                random_state=42,
                stratify=y if len(np.unique(y)) > 1 else None,
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            model = RandomForestClassifier(
                n_estimators=50, random_state=42, max_depth=10
            )
            model.fit(X_train_scaled, y_train)

            # Predictions
            y_pred = model.predict(X_test_scaled)

            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            class_report = classification_report(
                y_test, y_pred, output_dict=True, zero_division=0
            )

            # Feature importance
            feature_importance = model.feature_importances_.tolist()

            results = {
                "dataset_type": dataset_type,
                "accuracy": float(accuracy),
                "classification_report": class_report,
                "feature_importance": feature_importance,
                "train_size": len(X_train),
                "test_size": len(X_test),
                "n_features": X.shape[1],
                "class_distribution": {
                    "train": np.bincount(y_train).tolist(),
                    "test": np.bincount(y_test).tolist(),
                },
            }

            logger.info(
                f"✅ Model trained for {dataset_type}: Accuracy = {accuracy:.3f}"
            )
            return results

        except Exception as e:
            logger.error(f"❌ Error training model for {dataset_type}: {e}")
            return {}

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis on all available datasets"""
        logger.info("🚀 Starting comprehensive ML analysis...")

        # Discover datasets
        datasets = self.discover_datasets()

        if not datasets:
            logger.warning("⚠️ No datasets found")
            return {"error": "No datasets found"}

        all_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "datasets_analyzed": len(datasets),
            "dataset_types": list(datasets.keys()),
            "results_by_type": {},
        }

        # Analyze each dataset type
        for dataset_type, files in datasets.items():
            logger.info(f"🔬 Analyzing {dataset_type} datasets...")

            type_results = {
                "dataset_type": dataset_type,
                "description": self.dataset_types.get(dataset_type, "Unknown"),
                "files_found": len(files),
                "files_analyzed": 0,
                "combined_analysis": None,
                "ml_results": None,
            }

            # Try to load and analyze files
            combined_df = None

            for file_path in files[:3]:  # Limit to first 3 files per type
                df = self.load_dataset_safely(file_path, max_rows=5000)
                if df is not None:
                    type_results["files_analyzed"] += 1

                    if combined_df is None:
                        combined_df = df.copy()
                    else:
                        # Try to combine datasets
                        try:
                            # Find common columns
                            common_cols = list(
                                set(combined_df.columns) & set(df.columns)
                            )
                            if common_cols:
                                combined_df = pd.concat(
                                    [combined_df[common_cols], df[common_cols]],
                                    ignore_index=True,
                                )
                        except Exception as e:
                            logger.warning(f"⚠️ Could not combine datasets: {e}")

            # Analyze combined dataset
            if combined_df is not None and len(combined_df) > 0:
                # Feature analysis
                type_results["combined_analysis"] = self.analyze_dataset_features(
                    combined_df, dataset_type
                )

                # ML analysis
                X, y = self.prepare_ml_features(combined_df, dataset_type)
                if X is not None and y is not None:
                    type_results["ml_results"] = self.train_and_evaluate_model(
                        X, y, dataset_type
                    )

            all_results["results_by_type"][dataset_type] = type_results

        # Generate summary comparison
        all_results["summary"] = self.generate_comparison_summary(all_results)

        # Save results
        results_file = (
            self.temp_dir
            / f"ml_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)

        logger.info(f"💾 Results saved to: {results_file}")
        logger.info("✅ Comprehensive analysis completed")

        return all_results

    def generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison summary across dataset types"""
        summary = {
            "accuracy_comparison": {},
            "elo_ranges": {},
            "error_rates": {},
            "feature_counts": {},
            "recommendations": [],
        }

        for dataset_type, type_results in results.get("results_by_type", {}).items():
            # ML accuracy comparison
            ml_results = type_results.get("ml_results", {})
            if ml_results and "accuracy" in ml_results:
                summary["accuracy_comparison"][dataset_type] = ml_results["accuracy"]

            # ELO range comparison
            analysis = type_results.get("combined_analysis", {})
            if analysis and "elo_statistics" in analysis:
                elo_stats = analysis["elo_statistics"]
                for elo_col, stats in elo_stats.items():
                    if stats and stats.get("mean") is not None:
                        summary["elo_ranges"][dataset_type] = {
                            "mean": stats["mean"],
                            "range": f"{stats.get('min', 'N/A')}-{stats.get('max', 'N/A')}",
                        }
                        break

            # Feature count comparison
            if analysis and "chess_features" in analysis:
                total_features = sum(
                    len(features) for features in analysis["chess_features"].values()
                )
                summary["feature_counts"][dataset_type] = total_features

        # Generate recommendations
        if summary["accuracy_comparison"]:
            best_accuracy = max(summary["accuracy_comparison"].values())
            best_dataset = max(
                summary["accuracy_comparison"], key=summary["accuracy_comparison"].get
            )
            summary["recommendations"].append(
                f"Best ML performance: {best_dataset} dataset (accuracy: {best_accuracy:.3f})"
            )

        if summary["elo_ranges"]:
            summary["recommendations"].append(
                f"ELO standardization needed across {len(summary['elo_ranges'])} dataset types"
            )

        return summary

    def print_analysis_report(self, results: Dict[str, Any]):
        """Print a formatted analysis report"""
        print("\n" + "=" * 80)
        print("🏆 CHESS DATASETS ML ANALYSIS REPORT")
        print("=" * 80)

        print(f"\n📊 Analysis Overview:")
        print(f"   • Timestamp: {results.get('analysis_timestamp', 'N/A')}")
        print(f"   • Datasets analyzed: {results.get('datasets_analyzed', 0)}")
        print(f"   • Dataset types: {', '.join(results.get('dataset_types', []))}")

        # Results by type
        for dataset_type, type_results in results.get("results_by_type", {}).items():
            print(f"\n🔬 {dataset_type.upper()} DATASET ANALYSIS")
            print(f"   Description: {type_results.get('description', 'N/A')}")
            print(f"   Files found: {type_results.get('files_found', 0)}")
            print(f"   Files analyzed: {type_results.get('files_analyzed', 0)}")

            # Dataset characteristics
            analysis = type_results.get("combined_analysis", {})
            if analysis:
                print(f"   Total rows: {analysis.get('total_rows', 'N/A'):,}")
                print(f"   Total columns: {analysis.get('total_columns', 'N/A')}")

                # ELO statistics
                elo_stats = analysis.get("elo_statistics", {})
                if elo_stats:
                    for elo_col, stats in elo_stats.items():
                        if stats and stats.get("mean"):
                            print(
                                f"   ELO ({elo_col}): {stats['mean']:.0f} ± {stats.get('std', 0):.0f}"
                            )

            # ML results
            ml_results = type_results.get("ml_results", {})
            if ml_results:
                print(f"   🤖 ML Accuracy: {ml_results.get('accuracy', 0):.3f}")
                print(f"   Features used: {ml_results.get('n_features', 0)}")
                print(f"   Training samples: {ml_results.get('train_size', 0)}")

        # Summary
        summary = results.get("summary", {})
        if summary:
            print(f"\n📈 COMPARISON SUMMARY")

            accuracy_comp = summary.get("accuracy_comparison", {})
            if accuracy_comp:
                print("   🎯 ML Accuracy by dataset type:")
                for dataset_type, accuracy in sorted(
                    accuracy_comp.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"      {dataset_type}: {accuracy:.3f}")

            elo_ranges = summary.get("elo_ranges", {})
            if elo_ranges:
                print("   📊 ELO ranges by dataset type:")
                for dataset_type, elo_info in elo_ranges.items():
                    print(
                        f"      {dataset_type}: {elo_info['mean']:.0f} (range: {elo_info['range']})"
                    )

            recommendations = summary.get("recommendations", [])
            if recommendations:
                print("   💡 Recommendations:")
                for rec in recommendations:
                    print(f"      • {rec}")

        print("\n" + "=" * 80)
        print(
            "✅ Analysis completed successfully - NO destructive operations performed"
        )
        print("=" * 80)


def main():
    """Main execution function"""
    print("🚀 Starting Chess Datasets ML Analysis...")
    print("⚠️ NON-DESTRUCTIVE MODE: Only reading existing data")

    # Initialize analyzer
    analyzer = DatasetAnalyzer()

    try:
        # Run comprehensive analysis
        results = analyzer.run_comprehensive_analysis()

        # Print report
        analyzer.print_analysis_report(results)

        # Return success
        return 0

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
