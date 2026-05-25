"""
Test script for Survivorship Bias Module.

This script validates the functionality of the survivorship bias analyzer
using PostgreSQL integration.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from analysis.survivorship_bias import SurvivorshipBiasAnalyzer, CriticalityLevel
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_survivorship_analyzer():
    """Test the survivorship bias analyzer."""
    logger.info("=== Testing Survivorship Bias Analyzer ===")

    # Get database URL from environment
    db_url = os.environ.get(
        "CHESS_TRAINER_DB_URL",
        "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
    )
    logger.info(f"Using database: {db_url.split('@')[1] if '@' in db_url else db_url}")

    # Initialize analyzer with PostgreSQL
    analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)

    # Test different data sources
    sources_to_test = ["novice", "elite", "personal"]

    for source in sources_to_test:
        logger.info(f"\n--- Testing source: {source} ---")
        try:
            # Run analysis
            results = analyzer.analyze_dataset(source_filter=source)

            # Display results
            logger.info("=== Analysis Results ===")
            logger.info(f"Dataset Overview: {results['dataset_overview']}")
            logger.info(f"Early Defeats Found: {len(results['early_defeats'])}")
            logger.info(f"Mate Patterns Found: {len(results['mate_patterns'])}")
            logger.info(f"Alerts Generated: {len(results['alerts'])}")

            # Show critical alerts
            critical_alerts = [
                alert
                for alert in results["alerts"]
                if alert["criticality"] == "CRITICAL"
            ]

            if critical_alerts:
                logger.warning(
                    f"\n⚠️  CRITICAL ALERTS DETECTED ({len(critical_alerts)}):"
                )
                for alert in critical_alerts[:3]:  # Show first 3
                    logger.warning(
                        f"   - {alert['pattern_type']}: {alert['description']}"
                    )
                    logger.warning(f"     Action: {alert['recommended_action']}")
            else:
                logger.info("✅ No critical alerts detected")

            return results

        except Exception as e:
            logger.error(f"Error testing source {source}: {e}")
            continue

    return None


def test_emergency_detection():
    """Test emergency pattern detection."""
    logger.info("\n=== Testing Emergency Pattern Detection ===")

    db_url = os.environ.get(
        "CHESS_TRAINER_DB_URL",
        "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
    )
    analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)

    # Test emergency patterns
    emergency_patterns = analyzer.emergency_patterns
    logger.info(f"Configured emergency patterns: {list(emergency_patterns.keys())}")

    for pattern_name, config in emergency_patterns.items():
        logger.info(
            f"- {pattern_name}: {config['moves']} moves, priority: {config['priority'].value}"
        )

    return emergency_patterns


def test_performance():
    """Test analyzer performance with PostgreSQL."""
    import time

    logger.info("\n=== Performance Test ===")

    db_url = os.environ.get(
        "CHESS_TRAINER_DB_URL",
        "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
    )

    analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)

    start_time = time.time()
    try:
        results = analyzer.analyze_dataset(source_filter="novice")
        elapsed = time.time() - start_time

        logger.info(f"✅ Analysis completed in {elapsed:.2f} seconds")
        logger.info(f"   Processed {results['dataset_overview']['total_games']} games")
        logger.info(f"   Generated {len(results['alerts'])} alerts")

        return elapsed
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return None


if __name__ == "__main__":
    try:
        logger.info("🚀 STARTING SURVIVORSHIP BIAS MODULE TESTS")

        # Test basic functionality
        logger.info("\n1️⃣ Testing Basic Functionality")
        results = test_survivorship_analyzer()

        # Test emergency detection
        logger.info("\n2️⃣ Testing Emergency Pattern Detection")
        emergency_patterns = test_emergency_detection()

        # Test performance
        logger.info("\n3️⃣ Testing Performance")
        performance_time = test_performance()

        logger.info("\n=== All Tests Completed Successfully ===")

        # Show summary
        if results and not results.get("error"):
            total_alerts = len(results.get("alerts", []))
            critical_alerts = len(
                [
                    alert
                    for alert in results.get("alerts", [])
                    if alert.get("criticality") == "CRITICAL"
                ]
            )
            logger.info(f"📊 Analysis Summary:")
            logger.info(f"   Total alerts: {total_alerts}")
            logger.info(f"   Critical alerts: {critical_alerts}")
            logger.info(f"   Emergency patterns: {len(emergency_patterns)}")
            if performance_time:
                logger.info(f"   Performance: {performance_time:.2f}s")
        else:
            logger.error(f"❌ Analysis failed")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
