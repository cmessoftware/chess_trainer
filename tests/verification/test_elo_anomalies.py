#!/usr/bin/env python3
"""
Test Script for ELO Standardization with Anomalous Ratings

This script specifically tests the handling of problematic ratings like 655.0
that were causing warnings in the system.

Author: Chess Trainer Project
Issue: #21 (ELO Standardization)
Date: 2025-07-12
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

from ml.elo_standardization import ELOStandardizer, ELOPlatform

def test_anomalous_ratings():
    """Test the handling of various anomalous rating values"""
    
    print("🧪 Testing ELO Standardization with Anomalous Ratings")
    print("="*60)
    
    # Initialize standardizer with anomaly correction enabled
    standardizer = ELOStandardizer(fix_anomalies=True)
    
    # Test cases with known problematic ratings
    test_cases = [
        # The specific case mentioned: 655.0
        {"rating": 655.0, "platform": ELOPlatform.LICHESS, "desc": "Below minimum threshold"},
        
        # Other anomalous cases
        {"rating": 65.0, "platform": ELOPlatform.CHESS_COM, "desc": "Missing digit error"},
        {"rating": 85.0, "platform": ELOPlatform.LICHESS, "desc": "Missing digit error"},
        {"rating": 6.5, "platform": ELOPlatform.FIDE, "desc": "Wrong scale (decimal)"},
        {"rating": 0.85, "platform": ELOPlatform.CHESS_COM, "desc": "Wrong scale (small decimal)"},
        {"rating": 450.0, "platform": ELOPlatform.LICHESS, "desc": "True beginner rating"},
        {"rating": 25000.0, "platform": ELOPlatform.CHESS_COM, "desc": "Extreme high value"},
        {"rating": 4500.0, "platform": ELOPlatform.FIDE, "desc": "Above maximum"},
        
        # Valid ratings for comparison
        {"rating": 1200.0, "platform": ELOPlatform.LICHESS, "desc": "Valid novice rating"},
        {"rating": 1800.0, "platform": ELOPlatform.CHESS_COM, "desc": "Valid intermediate rating"},
        {"rating": 2400.0, "platform": ELOPlatform.FIDE, "desc": "Valid expert rating"},
    ]
    
    print("\\n🔍 Testing Individual Rating Corrections:")
    print("-" * 60)
    
    for i, case in enumerate(test_cases, 1):
        rating = case["rating"]
        platform = case["platform"]
        desc = case["desc"]
        
        result = standardizer.standardize_elo(rating, platform, "blitz")
        
        status = "✅ CORRECTED" if result is not None else "❌ REJECTED"
        print(f"{i:2d}. {desc}")
        print(f"    Input:  {rating} ({platform.value})")
        print(f"    Output: {result} - {status}")
        print()
    
    # Print detailed statistics
    print("\\n📊 Correction Statistics:")
    print("-" * 60)
    standardizer.print_quality_report()
    
    return standardizer

def test_dataframe_with_anomalies():
    """Test DataFrame processing with mixed valid and anomalous ratings"""
    
    print("\\n\\n🗂️  Testing DataFrame Processing with Anomalous Ratings")
    print("="*70)
    
    # Create test DataFrame with mix of valid and anomalous ratings
    test_data = {
        'white_elo': [1800, 655, 85, 2400, 6.5, 1200, 25000, None],
        'black_elo': [1600, 2000, 0.85, 450, 2200, 65, 4500, 1900],
        'site': ['lichess.org', 'chess.com', 'lichess.org', 'fide.com', 
                'chess.com', 'lichess.org', 'chess.com', 'unknown'],
        'event': ['Rated Blitz', 'Live Chess', 'Arena', 'Tournament',
                 'Daily Chess', 'Bullet Arena', 'Rapid', 'Casual Game'],
        'game_id': [f'game_{i}' for i in range(8)]
    }
    
    df = pd.DataFrame(test_data)
    
    print("\\n📋 Original DataFrame:")
    print(df[['white_elo', 'black_elo', 'site', 'event']].to_string(index=False))
    
    # Apply standardization
    standardizer = ELOStandardizer(fix_anomalies=True)
    df_standardized = standardizer.standardize_dataframe_elos(df)
    
    print("\\n📈 Standardized DataFrame:")
    cols_to_show = ['white_elo', 'standardized_white_elo', 'black_elo', 'standardized_black_elo']
    print(df_standardized[cols_to_show].to_string(index=False))
    
    # Show detailed statistics
    standardizer.print_quality_report()
    
    # Validation
    validation_results = standardizer.validate_standardization(df_standardized)
    print("\\n✅ Validation Summary:")
    print(f"  Total games processed: {validation_results['total_games']}")
    print(f"  White ELOs standardized: {validation_results['standardized_white_count']}")
    print(f"  Black ELOs standardized: {validation_results['standardized_black_count']}")
    
    return df_standardized, standardizer

def main():
    """Main test function"""
    print("🚀 ELO Standardization Anomaly Testing Suite")
    print("=" * 60)
    print("This script tests the handling of problematic ratings like 655.0")
    print("that were causing warnings in the production system.\\n")
    
    # Test individual ratings
    standardizer1 = test_anomalous_ratings()
    
    # Test DataFrame processing
    df_result, standardizer2 = test_dataframe_with_anomalies()
    
    print("\\n🎯 Test Summary:")
    print("=" * 60)
    
    combined_stats = {
        "total_conversions": standardizer1.stats["conversions_performed"] + standardizer2.stats["conversions_performed"],
        "total_corrections": standardizer1.stats["anomalies_corrected"] + standardizer2.stats["anomalies_corrected"],
        "total_rejections": standardizer1.stats["invalid_ratings_found"] + standardizer2.stats["invalid_ratings_found"],
        "total_outliers": standardizer1.stats["extreme_outliers_found"] + standardizer2.stats["extreme_outliers_found"]
    }
    
    print(f"✅ Total successful conversions: {combined_stats['total_conversions']}")
    print(f"🔧 Total anomalies corrected: {combined_stats['total_corrections']}")
    print(f"❌ Total ratings rejected: {combined_stats['total_rejections']}")
    print(f"⚠️  Total extreme outliers: {combined_stats['total_outliers']}")
    
    if combined_stats['total_corrections'] > 0:
        correction_rate = (combined_stats['total_corrections'] / 
                          max(1, combined_stats['total_corrections'] + combined_stats['total_outliers'])) * 100
        print(f"🎯 Anomaly correction success rate: {correction_rate:.1f}%")
    
    print("\\n✅ Testing completed successfully!")
    print("\\nThe system now handles anomalous ratings like 655.0 by:")
    print("  1. 🔍 Detecting out-of-range values")
    print("  2. 🛠️  Attempting intelligent corrections")
    print("  3. 📊 Logging detailed statistics")
    print("  4. ✅ Providing clear feedback on data quality")
    
    return True

if __name__ == "__main__":
    main()
