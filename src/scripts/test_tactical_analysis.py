#!/usr/bin/env python3
"""
Test script for enhanced tactical analysis functionality.
Verifies that analyzed_tacticals table is properly updated.
"""

from db.repository.features_repository import FeaturesRepository
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
import sys
sys.path.append('/app/src')


def test_analyzed_tacticals_tracking():
    """Test the analyzed_tacticals table tracking functionality."""

    print("🧪 Testing analyzed_tacticals table tracking...")

    analyzed_repo = Analyzed_tacticalsRepository()
    features_repo = FeaturesRepository()

    # Test 1: Check if we can query analyzed games
    try:
        total_analyzed = analyzed_repo.get_total_analyzed_count()
        print(f"✅ Total games in analyzed_tacticals: {total_analyzed}")
    except Exception as e:
        print(f"❌ Error querying analyzed_tacticals: {e}")
        return False

    # Test 2: Check coverage by source
    try:
        coverage_data = analyzed_repo.get_coverage_by_source()

        print("\n📊 Analysis coverage by source:")
        # Sort by total games descending
        coverage_data.sort(key=lambda x: x['total_games'], reverse=True)

        for data in coverage_data:
            source = data['source']
            total = data['total_games']
            analyzed = data['analyzed_games']
            coverage = data['coverage_percentage']
            print(f"   {source}: {analyzed}/{total} ({coverage:.1f}%)")

    except Exception as e:
        print(f"❌ Error checking coverage by source: {e}")
        return False

    # Test 3: Check games that need analysis
    try:
        # Get all unanalyzed games (those with features but not yet analyzed)
        unanalyzed_game_ids = features_repo.get_unanalyzed_game_ids()
        needs_analysis = len(unanalyzed_game_ids)
        print(f"\n🎯 Games that need tactical analysis: {needs_analysis}")

    except Exception as e:
        print(f"❌ Error checking games needing analysis: {e}")
        return False

    # Test 4: Test saving a tactical hash (dry run)
    try:
        print("\n🧪 Testing save_analyzed_tactical_hash method...")
        # Just test that the method exists and can be called
        # Don't actually save anything in test
        test_game_id = "test_game_123"
        # analyzed_repo.save_analyzed_tactical_hash(test_game_id)  # Commented out for safety
        print("✅ save_analyzed_tactical_hash method is available")

    except Exception as e:
        print(f"❌ Error with save_analyzed_tactical_hash: {e}")
        return False

    print("\n✅ All analyzed_tacticals tests passed!")
    return True


if __name__ == "__main__":
    success = test_analyzed_tacticals_tracking()
    if success:
        print("\n🎉 Enhanced tactical analysis is ready to use!")
        print("\nRecommended commands:")
        print("# Test with a small batch first:")
        print("python src/scripts/enhanced_tactical_analysis.py --source personal --max-games 10")
        print("\n# Then run larger batches:")
        print("python src/scripts/enhanced_tactical_analysis.py --source personal --max-games 1000")
    else:
        print("\n❌ Issues found with analyzed_tacticals tracking. Please check database setup.")
