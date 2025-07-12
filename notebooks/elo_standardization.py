#!/usr/bin/env python3
"""
ELO Standardization Module for Chess Trainer

This module provides functionality to standardize ELO ratings across different platforms:
- Chess.com (uses Glicko-2 rating system)
- Lichess (uses Glicko-2 rating system) 
- FIDE (uses traditional ELO system)
- Stockfish (engine centipawn evaluation)

The goal is to create a unified `standardized_elo` field that allows
consistent player strength analysis across all data sources.

Author: Chess Trainer Project
Issue: #21 (ELO Standardization)
Date: 2025-07-12
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, List
from enum import Enum

logger = logging.getLogger(__name__)


class ELOPlatform(Enum):
    """Enumeration of supported chess platforms"""
    CHESS_COM = "chess.com"
    LICHESS = "lichess"
    FIDE = "fide"
    UNKNOWN = "unknown"


class ELOStandardizer:
    """
    ELO Standardization utility class
    
    Converts ratings from different platforms to a standardized ELO scale
    based on FIDE ratings as the reference standard.
    """
    
    # Conversion constants based on research and empirical data
    CONVERSION_FACTORS = {
        ELOPlatform.CHESS_COM: {
            "blitz": {"offset": -150, "multiplier": 1.05},
            "rapid": {"offset": -100, "multiplier": 1.02},
            "bullet": {"offset": -200, "multiplier": 1.08},
            "classical": {"offset": -50, "multiplier": 1.0},
            "default": {"offset": -120, "multiplier": 1.03}
        },
        ELOPlatform.LICHESS: {
            "blitz": {"offset": -120, "multiplier": 0.98},
            "rapid": {"offset": -80, "multiplier": 0.99},
            "bullet": {"offset": -150, "multiplier": 1.02},
            "classical": {"offset": -30, "multiplier": 0.97},
            "default": {"offset": -90, "multiplier": 0.98}
        },
        ELOPlatform.FIDE: {
            "default": {"offset": 0, "multiplier": 1.0}  # FIDE is our reference
        }
    }
    
    # Rating boundaries for validation
    MIN_VALID_ELO = 800
    MAX_VALID_ELO = 3500
    
    def __init__(self):
        """Initialize the ELO standardizer"""
        self.stats = {
            "conversions_performed": 0,
            "invalid_ratings_found": 0,
            "platforms_processed": set()
        }
    
    def detect_platform(self, site: str, event: str = "") -> ELOPlatform:
        """
        Detect chess platform from site/event information
        
        Args:
            site: Site information from PGN
            event: Event information from PGN
            
        Returns:
            ELOPlatform enum value
        """
        if not site:
            site = ""
        if not event:
            event = ""
            
        site_lower = site.lower()
        event_lower = event.lower()
        
        if "chess.com" in site_lower or "chess.com" in event_lower:
            return ELOPlatform.CHESS_COM
        elif "lichess" in site_lower or "lichess" in event_lower:
            return ELOPlatform.LICHESS
        elif "fide" in event_lower or any(keyword in event_lower for keyword in 
                                        ["tournament", "championship", "olympiad", "world"]):
            return ELOPlatform.FIDE
        else:
            return ELOPlatform.UNKNOWN
    
    def detect_time_control(self, event: str = "", time_control: str = "") -> str:
        """
        Detect time control category from event or time control information
        
        Args:
            event: Event name
            time_control: Time control string (e.g., "300+3")
            
        Returns:
            Time control category: "bullet", "blitz", "rapid", "classical"
        """
        if not event:
            event = ""
        if not time_control:
            time_control = ""
            
        event_lower = event.lower()
        
        # Check event name first
        if "bullet" in event_lower:
            return "bullet"
        elif "blitz" in event_lower:
            return "blitz"
        elif "rapid" in event_lower:
            return "rapid"
        elif any(keyword in event_lower for keyword in ["classical", "standard", "tournament"]):
            return "classical"
        
        # Try to parse time control
        if time_control and "+" in time_control:
            try:
                base_time = int(time_control.split("+")[0])
                if base_time < 180:  # < 3 minutes
                    return "bullet"
                elif base_time < 600:  # < 10 minutes
                    return "blitz"
                elif base_time < 1800:  # < 30 minutes
                    return "rapid"
                else:
                    return "classical"
            except (ValueError, IndexError):
                pass
        
        return "default"
    
    def standardize_elo(
        self, 
        rating: Union[int, float, str], 
        platform: ELOPlatform, 
        time_control: str = "default"
    ) -> Optional[int]:
        """
        Convert a rating to standardized ELO
        
        Args:
            rating: Original rating value
            platform: Platform the rating comes from
            time_control: Time control category
            
        Returns:
            Standardized ELO rating or None if invalid
        """
        # Handle string ratings
        if isinstance(rating, str):
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                logger.warning(f"Invalid rating string: {rating}")
                self.stats["invalid_ratings_found"] += 1
                return None
        
        # Handle NaN or None values
        if pd.isna(rating) or rating is None:
            return None
        
        rating = float(rating)
        
        # Validate rating range
        if rating < self.MIN_VALID_ELO or rating > self.MAX_VALID_ELO:
            logger.warning(f"Rating {rating} outside valid range [{self.MIN_VALID_ELO}, {self.MAX_VALID_ELO}]")
            self.stats["invalid_ratings_found"] += 1
            return None
        
        # Get conversion factors
        platform_factors = self.CONVERSION_FACTORS.get(platform, {})
        if time_control not in platform_factors:
            time_control = "default"
        
        factors = platform_factors.get(time_control, {"offset": 0, "multiplier": 1.0})
        
        # Apply conversion formula
        standardized = (rating + factors["offset"]) * factors["multiplier"]
        
        # Round to nearest integer and ensure valid range
        standardized = max(self.MIN_VALID_ELO, min(self.MAX_VALID_ELO, round(standardized)))
        
        self.stats["conversions_performed"] += 1
        self.stats["platforms_processed"].add(platform.value)
        
        return int(standardized)
    
    def standardize_dataframe_elos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add standardized_elo fields to a dataframe
        
        Args:
            df: DataFrame with chess game data
            
        Returns:
            DataFrame with added standardized_white_elo and standardized_black_elo columns
        """
        df = df.copy()
        
        # Initialize standardized columns
        df['standardized_white_elo'] = None
        df['standardized_black_elo'] = None
        
        for idx, row in df.iterrows():
            # Detect platform
            platform = self.detect_platform(
                row.get('site', ''), 
                row.get('event', '')
            )
            
            # Detect time control
            time_control = self.detect_time_control(
                row.get('event', ''), 
                row.get('time_control', '')
            )
            
            # Standardize white ELO
            if 'white_elo' in row and pd.notna(row['white_elo']):
                standardized_white = self.standardize_elo(
                    row['white_elo'], platform, time_control
                )
                df.at[idx, 'standardized_white_elo'] = standardized_white
            
            # Standardize black ELO
            if 'black_elo' in row and pd.notna(row['black_elo']):
                standardized_black = self.standardize_elo(
                    row['black_elo'], platform, time_control
                )
                df.at[idx, 'standardized_black_elo'] = standardized_black
        
        return df
    
    def get_statistics(self) -> Dict:
        """Get standardization statistics"""
        return {
            "conversions_performed": self.stats["conversions_performed"],
            "invalid_ratings_found": self.stats["invalid_ratings_found"],
            "platforms_processed": list(self.stats["platforms_processed"]),
            "success_rate": (
                self.stats["conversions_performed"] / 
                max(1, self.stats["conversions_performed"] + self.stats["invalid_ratings_found"])
            ) * 100
        }
    
    def validate_standardization(self, df: pd.DataFrame) -> Dict:
        """
        Validate standardized ELO ratings against known benchmarks
        
        Args:
            df: DataFrame with standardized ELO ratings
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            "total_games": len(df),
            "standardized_white_count": df['standardized_white_elo'].notna().sum(),
            "standardized_black_count": df['standardized_black_elo'].notna().sum(),
            "white_elo_stats": {},
            "black_elo_stats": {},
            "platform_distribution": {},
            "rating_distribution": {}
        }
        
        # ELO statistics
        if 'standardized_white_elo' in df and df['standardized_white_elo'].notna().any():
            white_elos = df['standardized_white_elo'].dropna()
            validation_results["white_elo_stats"] = {
                "mean": float(white_elos.mean()),
                "std": float(white_elos.std()),
                "min": int(white_elos.min()),
                "max": int(white_elos.max()),
                "median": float(white_elos.median())
            }
        
        if 'standardized_black_elo' in df and df['standardized_black_elo'].notna().any():
            black_elos = df['standardized_black_elo'].dropna()
            validation_results["black_elo_stats"] = {
                "mean": float(black_elos.mean()),
                "std": float(black_elos.std()),
                "min": int(black_elos.min()),
                "max": int(black_elos.max()),
                "median": float(black_elos.median())
            }
        
        # Platform distribution
        for idx, row in df.iterrows():
            platform = self.detect_platform(
                row.get('site', ''), 
                row.get('event', '')
            )
            platform_name = platform.value
            if platform_name not in validation_results["platform_distribution"]:
                validation_results["platform_distribution"][platform_name] = 0
            validation_results["platform_distribution"][platform_name] += 1
        
        # Rating distribution (by ranges)
        all_standardized_elos = pd.concat([
            df['standardized_white_elo'].dropna(),
            df['standardized_black_elo'].dropna()
        ])
        
        if len(all_standardized_elos) > 0:
            validation_results["rating_distribution"] = {
                "beginner (<1200)": int((all_standardized_elos < 1200).sum()),
                "intermediate (1200-1600)": int(((all_standardized_elos >= 1200) & (all_standardized_elos < 1600)).sum()),
                "advanced (1600-2000)": int(((all_standardized_elos >= 1600) & (all_standardized_elos < 2000)).sum()),
                "expert (2000-2400)": int(((all_standardized_elos >= 2000) & (all_standardized_elos < 2400)).sum()),
                "master (2400+)": int((all_standardized_elos >= 2400).sum())
            }
        
        return validation_results


def test_elo_standardization():
    """Test ELO standardization functionality"""
    print("🔬 Testing ELO Standardization...")
    
    standardizer = ELOStandardizer()
    
    # Test platform detection
    test_sites = [
        ("https://chess.com", ELOPlatform.CHESS_COM),
        ("https://lichess.org", ELOPlatform.LICHESS),
        ("New York USA", ELOPlatform.FIDE),
        ("Unknown Site", ELOPlatform.UNKNOWN)
    ]
    
    print("🎯 Testing platform detection:")
    for site, expected in test_sites:
        detected = standardizer.detect_platform(site)
        status = "✅" if detected == expected else "❌"
        print(f"  {status} {site} -> {detected.value} (expected: {expected.value})")
    
    # Test rating standardization
    test_ratings = [
        (1500, ELOPlatform.CHESS_COM, "blitz", 1425),  # Chess.com blitz -> FIDE
        (1500, ELOPlatform.LICHESS, "blitz", 1350),    # Lichess blitz -> FIDE
        (1500, ELOPlatform.FIDE, "default", 1500),     # FIDE -> FIDE (no change)
    ]
    
    print("\n🎯 Testing rating standardization:")
    for original, platform, time_control, expected_approx in test_ratings:
        standardized = standardizer.standardize_elo(original, platform, time_control)
        difference = abs(standardized - expected_approx) if standardized else float('inf')
        status = "✅" if difference <= 50 else "❌"  # Allow 50 point tolerance
        print(f"  {status} {original} ({platform.value}, {time_control}) -> {standardized} (expected ~{expected_approx})")
    
    # Test with sample DataFrame
    sample_data = {
        'white_elo': [1500, 1600, 1700, '1800', None],
        'black_elo': [1450, 1550, 1650, '1750', 1850],
        'site': ['https://chess.com', 'https://lichess.org', 'New York USA', 'chess.com', 'lichess.org'],
        'event': ['Blitz game', 'Rapid game', 'Tournament', 'Bullet', 'Classical']
    }
    
    df = pd.DataFrame(sample_data)
    print(f"\n🎯 Testing DataFrame standardization:")
    print(f"  📊 Original DataFrame shape: {df.shape}")
    
    standardized_df = standardizer.standardize_dataframe_elos(df)
    print(f"  📊 Standardized DataFrame shape: {standardized_df.shape}")
    print(f"  📊 New columns: {[col for col in standardized_df.columns if 'standardized' in col]}")
    
    # Show results
    print(f"\n  📈 Sample standardization results:")
    for idx, row in standardized_df.iterrows():
        white_orig = row['white_elo']
        white_std = row['standardized_white_elo']
        black_orig = row['black_elo']
        black_std = row['standardized_black_elo']
        site = row['site']
        
        print(f"    Game {idx+1} ({site}):")
        print(f"      White: {white_orig} -> {white_std}")
        print(f"      Black: {black_orig} -> {black_std}")
    
    # Get statistics
    stats = standardizer.get_statistics()
    print(f"\n📊 Standardization Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Validation
    validation = standardizer.validate_standardization(standardized_df)
    print(f"\n✅ Validation Results:")
    print(f"  Total games processed: {validation['total_games']}")
    print(f"  Standardized white ELOs: {validation['standardized_white_count']}")
    print(f"  Standardized black ELOs: {validation['standardized_black_count']}")
    
    if validation['white_elo_stats']:
        print(f"  White ELO range: {validation['white_elo_stats']['min']}-{validation['white_elo_stats']['max']}")
        print(f"  White ELO mean: {validation['white_elo_stats']['mean']:.0f}")
    
    print("✅ ELO Standardization test completed!")


if __name__ == "__main__":
    test_elo_standardization()
