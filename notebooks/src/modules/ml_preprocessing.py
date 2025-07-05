#!/usr/bin/env python3
"""
ML Preprocessing Module for Chess Trainer

This module provides comprehensive preprocessing capabilities for chess game data,
handling multiple source types (personal, novice, elite, fide, stockfish) with
specialized transformations for each category.

Features:
- ELO standardization between Chess.com and Lichess ratings
- Source-aware feature scaling and normalization
- Intelligent null value handling by feature type
- Categorical encoding optimized for chess data
- Feature engineering for ML-ready datasets
- Data validation and quality checks
- Tactical features from Stockfish analysis (depth_score_diff, threatens_mate, is_forced_move)

Author: Chess Trainer ML Pipeline
Date: 2025-07-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Literal
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, 
    LabelEncoder, OneHotEncoder
)
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer, KNNImputer
import warnings
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions
SourceType = Literal["personal", "novice", "elite", "fide", "stockfish"]
ScalerType = Literal["standard", "minmax", "robust", "none"]

class ChessMLPreprocessor:
    """
    Comprehensive preprocessor for chess game data with source-aware transformations.
    
    This class handles the complete preprocessing pipeline for chess training data,
    including ELO standardization, feature scaling, encoding, and validation.
    """
    
    def __init__(
        self,
        elo_standardization: bool = True,
        scaler_type: ScalerType = "standard",
        handle_outliers: bool = True,
        random_state: int = 42
    ):
        """
        Initialize the Chess ML Preprocessor.
        
        Args:
            elo_standardization: Whether to apply ELO standardization between platforms
            scaler_type: Type of scaler to use for numerical features
            handle_outliers: Whether to detect and handle outliers
            random_state: Random state for reproducible results
        """
        self.elo_standardization = elo_standardization
        self.scaler_type = scaler_type
        self.handle_outliers = handle_outliers
        self.random_state = random_state
        
        # Initialize scalers and encoders
        self.scalers = {}
        self.encoders = {}
        self.feature_stats = {}
        self.is_fitted = False
        
        # Define feature categories
        self._define_feature_categories()
        
        # ELO standardization parameters (Chess.com to FIDE-like scale)
        self.elo_conversion_params = {
            "lichess_to_fide": {
                "intercept": -100,  # Lichess ratings are typically 100-150 points higher
                "slope": 0.92,      # Slight adjustment for rating compression
                "min_elo": 800,
                "max_elo": 2800
            },
            "chesscom_to_fide": {
                "intercept": 50,    # Chess.com ratings are closer to FIDE
                "slope": 1.02,      # Slight inflation correction
                "min_elo": 600,
                "max_elo": 2700
            }
        }
    
    def _define_feature_categories(self):
        """Define feature categories for different preprocessing strategies."""
        self.feature_categories = {
            "numerical_continuous": [
                "material_balance", "material_total", "branching_factor",
                "self_mobility", "opponent_mobility", "score_diff",
                "move_number", "num_pieces", "depth_score_diff"
            ],
            "numerical_binary": [
                "has_castling_rights", "is_repetition", "is_low_mobility",
                "is_center_controlled", "is_pawn_endgame", "is_stockfish_test",
                "threatens_mate", "is_forced_move"
            ],
            "categorical_ordinal": [
                "phase",  # opening -> middlegame -> endgame has order
                "error_label"  # ok -> inaccuracy -> mistake -> blunder has severity order
            ],
            "categorical_nominal": [
                "player_color", "site", "event", "result"
            ],
            "elo_features": [
                "white_elo", "black_elo", "standardized_elo"
            ],
            "text_features": [
                "tags", "white_player", "black_player"
            ],
            "temporal_features": [
                "date"
            ],
            "tactical_features": [
                "depth_score_diff", "threatens_mate", "is_forced_move"
            ]
        }
    
    def standardize_elo(
        self, 
        df: pd.DataFrame, 
        source_platform: str = "auto"
    ) -> pd.DataFrame:
        """
        Standardize ELO ratings to FIDE-like scale.
        
        This addresses the issue where Lichess ratings are typically 100-150 points
        higher than Chess.com, and Chess.com ratings are closer to FIDE ratings.
        
        Args:
            df: DataFrame with ELO columns
            source_platform: Platform source ("lichess", "chess.com", "auto")
            
        Returns:
            DataFrame with standardized ELO ratings
        """
        if not self.elo_standardization:
            return df
            
        df = df.copy()
        
        # Auto-detect platform if not specified
        if source_platform == "auto":
            source_platform = self._detect_platform(df)
        
        # Apply ELO standardization
        for elo_col in ["white_elo", "black_elo"]:
            if elo_col in df.columns:
                df[f"{elo_col}_original"] = df[elo_col].copy()
                df[elo_col] = self._convert_elo_to_fide(
                    df[elo_col], source_platform
                )
        
        # Create standardized ELO feature (average of white and black)
        if "white_elo" in df.columns and "black_elo" in df.columns:
            df["standardized_elo"] = (df["white_elo"] + df["black_elo"]) / 2
            
            # Add ELO difference feature
            df["elo_difference"] = abs(df["white_elo"] - df["black_elo"])
            
            # Add ELO category features
            df["elo_category"] = pd.cut(
                df["standardized_elo"],
                bins=[0, 1200, 1600, 2000, 2400, 3000],
                labels=["beginner", "intermediate", "advanced", "expert", "master"],
                include_lowest=True
            )
        
        logger.info(f"ELO standardization completed for platform: {source_platform}")
        return df
    
    def _detect_platform(self, df: pd.DataFrame) -> str:
        """Auto-detect platform based on site information."""
        if "site" in df.columns:
            site_values = df["site"].str.lower().fillna("")
            if site_values.str.contains("lichess").any():
                return "lichess"
            elif site_values.str.contains("chess.com").any():
                return "chess.com"
        
        # Fallback: analyze ELO distribution
        if "white_elo" in df.columns and "black_elo" in df.columns:
            avg_elo = df[["white_elo", "black_elo"]].mean().mean()
            if avg_elo > 1600:  # Lichess tends to have higher averages
                return "lichess"
        
        return "chess.com"  # Default to chess.com (closer to FIDE)
    
    def _convert_elo_to_fide(self, elo_series: pd.Series, platform: str) -> pd.Series:
        """Convert platform-specific ELO to FIDE-like scale."""
        if platform == "lichess":
            params = self.elo_conversion_params["lichess_to_fide"]
        else:
            params = self.elo_conversion_params["chesscom_to_fide"]
        
        # Apply linear transformation
        converted = (elo_series * params["slope"]) + params["intercept"]
        
        # Clip to reasonable ranges
        converted = np.clip(converted, params["min_elo"], params["max_elo"])
        
        return converted
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame, 
        strategy: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Intelligent missing value handling based on feature types.
        
        Args:
            df: Input DataFrame
            strategy: Custom strategy dict for specific columns
            
        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()
        
        # Default strategies by feature type
        default_strategies = {
            "numerical_continuous": "median",
            "numerical_binary": "most_frequent",
            "categorical_ordinal": "most_frequent",
            "categorical_nominal": "constant",
            "elo_features": "median",
            "text_features": "constant",
            "temporal_features": "constant",
            "tactical_features": "constant"  # Tactical features often missing for non-analyzed games
        }
        
        # Override with custom strategies if provided
        if strategy:
            default_strategies.update(strategy)
        
        for category, columns in self.feature_categories.items():
            strategy_type = default_strategies.get(category, "constant")
            
            for col in columns:
                if col in df.columns and df[col].isnull().any():
                    # Special handling for tactical features
                    if category == "tactical_features":
                        if col == "depth_score_diff":
                            df[col] = df[col].fillna(0)  # Neutral score diff
                        elif col in ["threatens_mate", "is_forced_move"]:
                            df[col] = df[col].fillna(False)  # No threat/force by default
                    elif strategy_type == "knn":
                        # Use KNN imputation for numerical features
                        imputer = KNNImputer(n_neighbors=5)
                        df[[col]] = imputer.fit_transform(df[[col]])
                    else:
                        # Use simple imputation
                        fill_value = "unknown" if strategy_type == "constant" else None
                        imputer = SimpleImputer(strategy=strategy_type, fill_value=fill_value)
                        df[[col]] = imputer.fit_transform(df[[col]])
        
        logger.info("Missing value handling completed")
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode categorical features with appropriate methods.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with encoded categorical features
        """
        df = df.copy()
        
        # Handle ordinal features (maintain order)
        ordinal_mappings = {
            "phase": {"opening": 0, "middlegame": 1, "endgame": 2},
            "error_label": {"ok": 0, "inaccuracy": 1, "mistake": 2, "blunder": 3}
        }
        
        for col, mapping in ordinal_mappings.items():
            if col in df.columns:
                df[f"{col}_encoded"] = df[col].map(mapping).fillna(-1)
        
        # Handle nominal features (one-hot encoding for low cardinality)
        for col in self.feature_categories["categorical_nominal"]:
            if col in df.columns:
                unique_values = df[col].nunique()
                
                if unique_values <= 10:  # One-hot encode low cardinality
                    dummies = pd.get_dummies(df[col], prefix=col, dummy_na=True)
                    df = pd.concat([df, dummies], axis=1)
                else:  # Label encode high cardinality
                    if col not in self.encoders:
                        self.encoders[col] = LabelEncoder()
                        df[f"{col}_encoded"] = self.encoders[col].fit_transform(
                            df[col].fillna("unknown")
                        )
                    else:
                        # Handle unseen categories
                        known_categories = set(self.encoders[col].classes_)
                        df[col] = df[col].apply(
                            lambda x: x if x in known_categories else "unknown"
                        )
                        df[f"{col}_encoded"] = self.encoders[col].transform(
                            df[col].fillna("unknown")
                        )
        
        logger.info("Categorical encoding completed")
        return df
    
    def scale_numerical_features(
        self, 
        df: pd.DataFrame, 
        source_type: SourceType = None
    ) -> pd.DataFrame:
        """
        Scale numerical features with source-aware strategies.
        
        Different sources may have different scaling needs:
        - stockfish: May have different score_diff ranges
        - elite: May have higher mobility/branching factors
        - novice: May have more conservative play patterns
        
        Args:
            df: Input DataFrame
            source_type: Type of source data
            
        Returns:
            DataFrame with scaled features
        """
        if self.scaler_type == "none":
            return df
            
        df = df.copy()
        
        # Select appropriate scaler
        scaler_map = {
            "standard": StandardScaler(),
            "minmax": MinMaxScaler(),
            "robust": RobustScaler()
        }
        
        scaler = scaler_map[self.scaler_type]
        
        # Features to scale
        features_to_scale = (
            self.feature_categories["numerical_continuous"] + 
            self.feature_categories["elo_features"]
        )
        
        # Include tactical features that are numerical (not binary)
        tactical_numerical = ["depth_score_diff"]
        features_to_scale.extend([f for f in tactical_numerical if f in df.columns])
        
        # Filter existing columns
        existing_features = [f for f in features_to_scale if f in df.columns]
        
        if existing_features:
            # Source-specific adjustments
            if source_type == "stockfish":
                # Stockfish may have extreme score_diff values
                if "score_diff" in existing_features:
                    df["score_diff"] = np.clip(df["score_diff"], -2000, 2000)
            
            # Fit and transform
            scaler_key = f"{source_type or 'default'}_{self.scaler_type}"
            
            if scaler_key not in self.scalers:
                self.scalers[scaler_key] = scaler
                df[existing_features] = self.scalers[scaler_key].fit_transform(
                    df[existing_features]
                )
            else:
                df[existing_features] = self.scalers[scaler_key].transform(
                    df[existing_features]
                )
            
            # Store feature statistics
            self.feature_stats[scaler_key] = {
                "mean": df[existing_features].mean().to_dict(),
                "std": df[existing_features].std().to_dict(),
                "min": df[existing_features].min().to_dict(),
                "max": df[existing_features].max().to_dict()
            }
        
        logger.info(f"Numerical scaling completed for source: {source_type}")
        return df
    
    def create_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived features for enhanced ML performance.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with additional derived features
        """
        df = df.copy()
        
        # Mobility ratio features
        if "self_mobility" in df.columns and "opponent_mobility" in df.columns:
            df["mobility_ratio"] = df["self_mobility"] / (df["opponent_mobility"] + 1)
            df["mobility_advantage"] = df["self_mobility"] - df["opponent_mobility"]
            df["total_mobility"] = df["self_mobility"] + df["opponent_mobility"]
        
        # Material features
        if "material_total" in df.columns and "num_pieces" in df.columns:
            df["material_per_piece"] = df["material_total"] / (df["num_pieces"] + 1)
        
        # Position complexity
        if "branching_factor" in df.columns and "num_pieces" in df.columns:
            df["complexity_score"] = df["branching_factor"] * df["num_pieces"]
        
        # Score-based features
        if "score_diff" in df.columns:
            df["score_diff_abs"] = abs(df["score_diff"])
            df["score_diff_sign"] = np.sign(df["score_diff"])
            df["is_losing_position"] = (df["score_diff"] < -100).astype(int)
            df["is_winning_position"] = (df["score_diff"] > 100).astype(int)
        
        # Phase-based features
        if "phase" in df.columns and "move_number" in df.columns:
            df["phase_move_interaction"] = df["phase_encoded"] * df["move_number"]
        
        # ELO-based features
        if "standardized_elo" in df.columns:
            df["elo_squared"] = df["standardized_elo"] ** 2
            df["elo_log"] = np.log(df["standardized_elo"] + 1)
        
        # Tactical features derived
        if "depth_score_diff" in df.columns:
            df["depth_score_diff_abs"] = abs(df["depth_score_diff"])
            df["depth_score_diff_sign"] = np.sign(df["depth_score_diff"])
            df["is_tactical_blunder"] = (df["depth_score_diff"] < -200).astype(int)
            df["is_tactical_excellence"] = (df["depth_score_diff"] > 100).astype(int)
        
        # Combined tactical indicators
        if all(col in df.columns for col in ["threatens_mate", "is_forced_move", "depth_score_diff"]):
            df["tactical_opportunity"] = (
                df["threatens_mate"].astype(int) + 
                df["is_forced_move"].astype(int) + 
                (df["depth_score_diff"] > 50).astype(int)
            )
        
        # Game phase interactions with tactical features
        if "phase_encoded" in df.columns and "threatens_mate" in df.columns:
            df["endgame_mate_threat"] = (
                (df["phase_encoded"] == 2) & df["threatens_mate"]
            ).astype(int)
        
        logger.info("Derived features created")
        return df
    
    def detect_and_handle_outliers(
        self, 
        df: pd.DataFrame,
        method: str = "iqr",
        factor: float = 1.5
    ) -> pd.DataFrame:
        """
        Detect and handle outliers in numerical features.
        
        Args:
            df: Input DataFrame
            method: Outlier detection method ("iqr", "zscore")
            factor: Outlier threshold factor
            
        Returns:
            DataFrame with outliers handled
        """
        if not self.handle_outliers:
            return df
            
        df = df.copy()
        numerical_cols = (
            self.feature_categories["numerical_continuous"] + 
            self.feature_categories["elo_features"]
        )
        
        existing_cols = [col for col in numerical_cols if col in df.columns]
        
        for col in existing_cols:
            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - factor * IQR
                upper_bound = Q3 + factor * IQR
                
                # Cap outliers instead of removing them
                df[col] = np.clip(df[col], lower_bound, upper_bound)
                
            elif method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df.loc[z_scores > factor, col] = df[col].median()
        
        logger.info(f"Outlier handling completed using {method} method")
        return df
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate data quality and return quality metrics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with quality metrics
        """
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_percentage": df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100,
            "duplicate_rows": df.duplicated().sum(),
            "columns_with_missing": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
            "data_types": df.dtypes.to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2
        }
        
        # Source-specific validations
        if "site" in df.columns:
            quality_report["source_distribution"] = df["site"].value_counts().to_dict()
        
        if "standardized_elo" in df.columns:
            quality_report["elo_stats"] = {
                "mean": df["standardized_elo"].mean(),
                "median": df["standardized_elo"].median(),
                "std": df["standardized_elo"].std(),
                "min": df["standardized_elo"].min(),
                "max": df["standardized_elo"].max()
            }
        
        return quality_report
    
    def fit_transform(
        self, 
        df: pd.DataFrame, 
        source_type: SourceType = None,
        platform: str = "auto"
    ) -> pd.DataFrame:
        """
        Complete preprocessing pipeline: fit and transform.
        
        Args:
            df: Input DataFrame
            source_type: Type of source data
            platform: Platform source for ELO standardization
            
        Returns:
            Fully preprocessed DataFrame
        """
        logger.info(f"Starting fit_transform for source: {source_type}")
        
        # Pipeline steps
        df = self.standardize_elo(df, platform)
        df = self.handle_missing_values(df)
        df = self.encode_categorical_features(df)
        df = self.create_derived_features(df)
        df = self.detect_and_handle_outliers(df)
        df = self.scale_numerical_features(df, source_type)
        
        self.is_fitted = True
        logger.info("Preprocessing pipeline completed")
        
        return df
    
    def transform(
        self, 
        df: pd.DataFrame, 
        source_type: SourceType = None
    ) -> pd.DataFrame:
        """
        Transform new data using fitted preprocessing pipeline.
        
        Args:
            df: Input DataFrame
            source_type: Type of source data
            
        Returns:
            Transformed DataFrame
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transform")
        
        logger.info(f"Transforming new data for source: {source_type}")
        
        # Apply same pipeline but using fitted transformers
        df = self.standardize_elo(df)
        df = self.handle_missing_values(df)
        df = self.encode_categorical_features(df)
        df = self.create_derived_features(df)
        df = self.detect_and_handle_outliers(df)
        df = self.scale_numerical_features(df, source_type)
        
        return df
    
    def get_feature_importance_ready_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of columns ready for ML feature importance analysis.
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            List of ML-ready column names
        """
        # Exclude original categorical columns and metadata
        exclude_patterns = [
            "_original", "game_id", "fen", "move_san", "move_uci",
            "white_player", "black_player", "date", "site", "event"
        ]
        
        ml_columns = []
        for col in df.columns:
            if not any(pattern in col for pattern in exclude_patterns):
                if df[col].dtype in ["int64", "float64", "bool"]:
                    ml_columns.append(col)
        
        return ml_columns
    
    def prepare_train_test_split(
        self,
        df: pd.DataFrame,
        target_column: str,
        test_size: float = 0.2,
        validation_size: float = 0.1,
        stratify_by: str = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Prepare train/validation/test splits for ML training.
        
        Args:
            df: Preprocessed DataFrame
            target_column: Name of target variable
            test_size: Proportion for test set
            validation_size: Proportion for validation set
            stratify_by: Column to stratify split (optional)
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        # Get ML-ready features
        feature_columns = self.get_feature_importance_ready_columns(df)
        feature_columns = [col for col in feature_columns if col != target_column]
        
        X = df[feature_columns]
        y = df[target_column]
        
        # Stratification
        stratify = df[stratify_by] if stratify_by and stratify_by in df.columns else None
        
        # First split: train+val vs test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, 
            test_size=test_size,
            stratify=stratify,
            random_state=self.random_state
        )
        
        # Second split: train vs validation
        val_size_adjusted = validation_size / (1 - test_size)
        stratify_temp = None
        if stratify is not None:
            stratify_temp = stratify.loc[X_temp.index]
            
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size_adjusted,
            stratify=stratify_temp,
            random_state=self.random_state
        )
        
        logger.info(f"Data split completed:")
        logger.info(f"  Train: {len(X_train)} samples")
        logger.info(f"  Validation: {len(X_val)} samples") 
        logger.info(f"  Test: {len(X_test)} samples")
        logger.info(f"  Features: {len(feature_columns)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test


def create_source_specific_preprocessor(source_type: SourceType) -> ChessMLPreprocessor:
    """
    Factory function to create source-specific preprocessors.
    
    Args:
        source_type: Type of chess data source
        
    Returns:
        Configured ChessMLPreprocessor instance
    """
    config_map = {
        "personal": {
            "elo_standardization": True,
            "scaler_type": "standard",
            "handle_outliers": True
        },
        "novice": {
            "elo_standardization": True, 
            "scaler_type": "robust",  # More robust to outliers in novice play
            "handle_outliers": True
        },
        "elite": {
            "elo_standardization": True,
            "scaler_type": "standard",
            "handle_outliers": False  # Elite play is generally more consistent
        },
        "fide": {
            "elo_standardization": False,  # FIDE ratings are already standard
            "scaler_type": "standard",
            "handle_outliers": False
        },
        "stockfish": {
            "elo_standardization": False,  # Test data
            "scaler_type": "minmax",  # Bounded engine evaluations
            "handle_outliers": True
        }
    }
    
    config = config_map.get(source_type, config_map["personal"])
    return ChessMLPreprocessor(**config)


# Utility functions for quick preprocessing
def quick_preprocess_for_training(
    df: pd.DataFrame,
    source_type: SourceType,
    target_column: str = "error_label"
) -> Tuple[pd.DataFrame, Dict]:
    """
    Quick preprocessing pipeline for immediate ML training.
    
    Args:
        df: Raw chess data DataFrame
        source_type: Type of source data
        target_column: Target variable for ML
        
    Returns:
        Tuple of (preprocessed_df, quality_report)
    """
    preprocessor = create_source_specific_preprocessor(source_type)
    
    # Preprocess
    df_processed = preprocessor.fit_transform(df, source_type)
    
    # Quality report
    quality_report = preprocessor.validate_data_quality(df_processed)
    
    return df_processed, quality_report


def preprocess_multiple_sources(
    source_dataframes: Dict[SourceType, pd.DataFrame],
    target_column: str = "error_label"
) -> Tuple[pd.DataFrame, Dict]:
    """
    Preprocess multiple source types and combine them.
    
    Args:
        source_dataframes: Dict mapping source types to DataFrames
        target_column: Target variable for ML
        
    Returns:
        Tuple of (combined_df, processing_report)
    """
    processed_dfs = []
    processing_report = {}
    
    for source_type, df in source_dataframes.items():
        logger.info(f"Processing source: {source_type}")
        
        # Preprocess each source
        df_processed, quality_report = quick_preprocess_for_training(
            df, source_type, target_column
        )
        
        # Add source identifier
        df_processed["source_type"] = source_type
        
        processed_dfs.append(df_processed)
        processing_report[source_type] = quality_report
    
    # Combine all sources
    combined_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Overall quality report
    processing_report["combined"] = {
        "total_samples": len(combined_df),
        "source_distribution": combined_df["source_type"].value_counts().to_dict(),
        "combined_quality": ChessMLPreprocessor().validate_data_quality(combined_df)
    }
    
    logger.info("Multi-source preprocessing completed")
    return combined_df, processing_report


if __name__ == "__main__":
    # Example usage
    print("🚀 Chess ML Preprocessing Module")
    print("Ready for comprehensive chess data preprocessing!")
    
    # Example configuration for different sources
    sources = ["personal", "novice", "elite", "fide", "stockfish"]
    for source in sources:
        preprocessor = create_source_specific_preprocessor(source)
        print(f"✅ {source.capitalize()} preprocessor configured")
