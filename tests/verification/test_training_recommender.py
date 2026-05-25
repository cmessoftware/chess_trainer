"""
Comprehensive Test for Training Recommender with Survivorship Bias Integration.

This script tests the complete training recommendation system including
survivorship bias analysis integration and emergency protocol generation.

Usage:
    python test_training_recommender.py
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from training.training_recommender import (
    TrainingRecommender,
    UserProfile,
    TrainingPriority,
)


def create_test_user_profile() -> UserProfile:
    """Create a test user profile for demonstration."""
    return UserProfile(
        user_id="test_user_001",
        skill_level="intermediate",
        preferred_openings=["Sicilian Defense", "French Defense", "Queen's Gambit"],
        common_mistakes=["hanging pieces", "weak pawn structures"],
        time_available=60,  # 60 minutes per session
        focus_areas=["opening", "tactics", "endgame"],
    )


def test_survivorship_analysis():
    """Test the survivorship bias analysis integration."""
    print("=" * 60)
    print("TESTING SURVIVORSHIP BIAS ANALYSIS")
    print("=" * 60)

    try:
        recommender = TrainingRecommender()

        # Analyze survivorship patterns
        print("Running survivorship bias analysis...")
        results = recommender.analyze_survivorship_patterns()

        print(f"\nAnalysis Results:")
        print(f"- Total games analyzed: {results.get('total_games', 0)}")
        print(f"- Alerts generated: {len(results.get('alerts', []))}")

        critical_alerts = [
            alert
            for alert in results.get("alerts", [])
            if alert.get("criticality") == "CRITICAL"
        ]
        print(f"- Critical alerts: {len(critical_alerts)}")

        # Show critical alerts
        for i, alert in enumerate(critical_alerts, 1):
            print(f"\n  Critical Alert {i}:")
            print(f"    Type: {alert.get('pattern_type', 'N/A')}")
            print(f"    Description: {alert.get('description', 'N/A')}")
            print(f"    Affected Games: {alert.get('affected_games', 'N/A')}")

        return results

    except Exception as e:
        print(f"Error in survivorship analysis: {e}")
        return None


def test_emergency_recommendations(recommender):
    """Test emergency recommendation generation."""
    print("\n" + "=" * 60)
    print("TESTING EMERGENCY RECOMMENDATIONS")
    print("=" * 60)

    try:
        emergency_recs = recommender.generate_emergency_recommendations()

        print(f"Generated {len(emergency_recs)} emergency recommendations:")

        for i, rec in enumerate(emergency_recs, 1):
            print(f"\n  Emergency Recommendation {i}:")
            print(f"    Title: {rec.title}")
            print(f"    Priority: {rec.priority.value}")
            print(f"    Category: {rec.category}")
            print(f"    Description: {rec.description}")
            print(f"    Estimated Time: {rec.estimated_time} minutes")
            print(f"    Exercises: {len(rec.exercises)} planned")

        return emergency_recs

    except Exception as e:
        print(f"Error generating emergency recommendations: {e}")
        return []


def test_user_recommendations(recommender):
    """Test personalized user recommendations."""
    print("\n" + "=" * 60)
    print("TESTING PERSONALIZED USER RECOMMENDATIONS")
    print("=" * 60)

    try:
        # Create test user
        user_profile = create_test_user_profile()
        print(f"Test User Profile:")
        print(f"  ID: {user_profile.user_id}")
        print(f"  Skill Level: {user_profile.skill_level}")
        print(f"  Preferred Openings: {', '.join(user_profile.preferred_openings)}")
        print(f"  Available Time: {user_profile.time_available} minutes")

        # Generate recommendations
        recommendations = recommender.generate_user_recommendations(user_profile)

        print(f"\nGenerated {len(recommendations)} personalized recommendations:")

        # Group by priority
        priority_groups = {}
        for rec in recommendations:
            priority = rec.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(rec)

        # Display by priority
        for priority in ["EMERGENCY", "HIGH", "MEDIUM", "LOW"]:
            if priority in priority_groups:
                print(
                    f"\n  {priority} Priority ({len(priority_groups[priority])} recommendations):"
                )
                for rec in priority_groups[priority]:
                    print(f"    - {rec.title} ({rec.estimated_time} min)")
                    print(f"      Category: {rec.category}")
                    print(f"      Source: {rec.source}")

        return recommendations

    except Exception as e:
        print(f"Error generating user recommendations: {e}")
        return []


def test_emergency_status(recommender):
    """Test emergency status monitoring."""
    print("\n" + "=" * 60)
    print("TESTING EMERGENCY STATUS MONITORING")
    print("=" * 60)

    try:
        status = recommender.get_emergency_status()

        print("Emergency Status Report:")
        print(f"  Has Emergency: {status['has_emergency']}")
        print(f"  Critical Patterns: {status['critical_patterns']}")
        print(f"  Requires Immediate Action: {status['requires_immediate_action']}")
        print(f"  Emergency Plan Available: {status['emergency_plan_available']}")
        print(f"  Status Level: {status['status']}")

        return status

    except Exception as e:
        print(f"Error checking emergency status: {e}")
        return {}


def test_training_plan_export(recommendations):
    """Test training plan export functionality."""
    print("\n" + "=" * 60)
    print("TESTING TRAINING PLAN EXPORT")
    print("=" * 60)

    try:
        recommender = TrainingRecommender()
        export_path = f"training_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        success = recommender.export_training_plan(recommendations, export_path)

        if success:
            print(f"Training plan exported successfully to: {export_path}")

            # Verify file contents
            with open(export_path, "r") as f:
                plan_data = json.load(f)

            print(f"Export verification:")
            print(f"  Total Recommendations: {plan_data['total_recommendations']}")
            print(f"  Emergency Count: {plan_data['emergency_count']}")
            print(
                f"  Total Estimated Time: {plan_data['estimated_total_time']} minutes"
            )

            return export_path
        else:
            print("Export failed!")
            return None

    except Exception as e:
        print(f"Error in training plan export: {e}")
        return None


def generate_test_report(results: Dict[str, Any]):
    """Generate comprehensive test report."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST REPORT - TRAINING RECOMMENDER SYSTEM")
    print("=" * 80)

    print(f"\nTest Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Survivorship Analysis Results
    if results.get("survivorship_results"):
        survivorship = results["survivorship_results"]
        print(f"\n📊 SURVIVORSHIP BIAS ANALYSIS:")
        print(f"   Games Analyzed: {survivorship.get('total_games', 0):,}")
        print(f"   Total Alerts: {len(survivorship.get('alerts', []))}")
        critical_alerts = [
            a
            for a in survivorship.get("alerts", [])
            if a.get("criticality") == "CRITICAL"
        ]
        print(f"   Critical Alerts: {len(critical_alerts)}")
        print(
            f"   Status: {'🚨 EMERGENCY' if len(critical_alerts) > 0 else '✅ NORMAL'}"
        )

    # Emergency Recommendations
    if results.get("emergency_recommendations"):
        emergency_recs = results["emergency_recommendations"]
        print(f"\n🚨 EMERGENCY RECOMMENDATIONS:")
        print(f"   Count: {len(emergency_recs)}")
        total_emergency_time = sum(rec.estimated_time for rec in emergency_recs)
        print(f"   Total Training Time: {total_emergency_time} minutes")

        # Show categories
        categories = {}
        for rec in emergency_recs:
            cat = rec.category
            categories[cat] = categories.get(cat, 0) + 1

        print("   Categories:")
        for cat, count in categories.items():
            print(f"     - {cat}: {count}")

    # User Recommendations
    if results.get("user_recommendations"):
        user_recs = results["user_recommendations"]
        print(f"\n👤 PERSONALIZED RECOMMENDATIONS:")
        print(f"   Total Count: {len(user_recs)}")

        # Priority breakdown
        priorities = {}
        for rec in user_recs:
            priority = rec.priority.value
            priorities[priority] = priorities.get(priority, 0) + 1

        print("   Priority Distribution:")
        for priority in ["EMERGENCY", "HIGH", "MEDIUM", "LOW"]:
            count = priorities.get(priority, 0)
            if count > 0:
                print(f"     - {priority}: {count}")

    # Emergency Status
    if results.get("emergency_status"):
        status = results["emergency_status"]
        print(f"\n⚠️  EMERGENCY STATUS:")
        print(f"   Current Status: {status.get('status', 'UNKNOWN')}")
        print(
            f"   Immediate Action Required: {status.get('requires_immediate_action', False)}"
        )
        print(
            f"   Emergency Plan Available: {status.get('emergency_plan_available', False)}"
        )

    # Export Results
    if results.get("export_path"):
        print(f"\n💾 EXPORT RESULTS:")
        print(f"   Training Plan Exported: ✅")
        print(f"   Export Path: {results['export_path']}")

    print(f"\n🎯 INTEGRATION STATUS:")
    integration_score = 0

    if results.get("survivorship_results"):
        integration_score += 25
        print("   ✅ Survivorship Bias Analysis: INTEGRATED")

    if results.get("emergency_recommendations"):
        integration_score += 25
        print("   ✅ Emergency Recommendations: INTEGRATED")

    if results.get("user_recommendations"):
        integration_score += 25
        print("   ✅ Personalized Recommendations: INTEGRATED")

    if results.get("export_path"):
        integration_score += 25
        print("   ✅ Training Plan Export: INTEGRATED")

    print(f"\n🏆 OVERALL INTEGRATION SCORE: {integration_score}%")

    if integration_score >= 100:
        print("   Status: 🎉 FULLY INTEGRATED - Ready for Production!")
    elif integration_score >= 75:
        print("   Status: 🔨 Nearly Complete - Minor issues remaining")
    elif integration_score >= 50:
        print("   Status: ⚠️  Partially Integrated - Major work needed")
    else:
        print("   Status: ❌ Integration Failed - Significant issues")


def main():
    """Main test execution function."""
    print("🏗️  Starting Comprehensive Training Recommender Test Suite")
    print("This test validates the complete integration of Survivorship Bias Analysis")
    print("with the Training Recommendation System\n")

    results = {}

    # Initialize recommender
    recommender = TrainingRecommender()

    # Test 1: Survivorship Analysis
    survivorship_results = test_survivorship_analysis()
    results["survivorship_results"] = survivorship_results

    # Test 2: Emergency Recommendations
    if survivorship_results:
        emergency_recs = test_emergency_recommendations(recommender)
        results["emergency_recommendations"] = emergency_recs

    # Test 3: User Recommendations
    user_recs = test_user_recommendations(recommender)
    results["user_recommendations"] = user_recs

    # Test 4: Emergency Status
    emergency_status = test_emergency_status(recommender)
    results["emergency_status"] = emergency_status

    # Test 5: Training Plan Export
    if user_recs:
        export_path = test_training_plan_export(user_recs)
        results["export_path"] = export_path

    # Generate comprehensive report
    generate_test_report(results)


if __name__ == "__main__":
    main()
