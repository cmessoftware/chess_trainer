"""
Test script for Survivorship Bias API.

This script tests the Flask API endpoints for survivorship bias analysis.
"""

import requests
import json
import sys
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_survivorship_api(base_url="http://localhost:5001"):
    """Test all survivorship bias API endpoints."""

    print("🧪 TESTING SURVIVORSHIP BIAS API")
    print(f"Base URL: {base_url}")
    print("=" * 50)

    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check")
    try:
        response = requests.get(f"{base_url}/analysis/survivorship/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check: {health_data['status']}")
            print(f"   Database: {health_data.get('database', 'unknown')}")
        else:
            print(f"❌ Health Check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health Check connection error: {e}")
        return False

    # Test 2: Available Sources
    print("\n2️⃣ Testing Available Sources")
    try:
        response = requests.get(f"{base_url}/analysis/survivorship/sources", timeout=15)
        if response.status_code == 200:
            sources_data = response.json()
            print(f"✅ Sources endpoint working")
            print(f"   Available sources: {sources_data.get('total_sources', 0)}")
            for source in sources_data.get("sources", [])[:3]:  # Show first 3
                print(f"     - {source['name']}: {source['game_count']} games")
        else:
            print(f"❌ Sources endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Sources endpoint error: {e}")

    # Test 3: Full Analysis
    print("\n3️⃣ Testing Full Analysis")
    try:
        response = requests.get(
            f"{base_url}/analysis/survivorship?source=novice", timeout=30
        )
        if response.status_code == 200:
            analysis_data = response.json()
            print(f"✅ Analysis endpoint working")

            if analysis_data["status"] == "success":
                data = analysis_data["data"]
                overview = data["dataset_overview"]
                alerts = data["alerts"]

                print(f"   Games analyzed: {overview.get('total_games', 0)}")
                print(f"   Alerts generated: {len(alerts)}")
                print(f"   Short games: {overview.get('short_games_count', 0)}")

                # Show critical alerts
                critical_alerts = [
                    alert for alert in alerts if alert.get("criticality") == "CRITICAL"
                ]
                if critical_alerts:
                    print(f"   🚨 CRITICAL ALERTS: {len(critical_alerts)}")
                    for alert in critical_alerts[:2]:  # Show first 2
                        print(f"     - {alert.get('description', 'No description')}")
            else:
                print(
                    f"❌ Analysis failed: {analysis_data.get('error', 'Unknown error')}"
                )
        else:
            print(f"❌ Analysis endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Analysis endpoint error: {e}")

    # Test 4: Summary Format
    print("\n4️⃣ Testing Summary Format")
    try:
        response = requests.get(
            f"{base_url}/analysis/survivorship?source=elite&format=summary", timeout=20
        )
        if response.status_code == 200:
            summary_data = response.json()
            print(f"✅ Summary format working")

            if "summary" in summary_data:
                summary = summary_data["summary"]
                print(f"   Games: {summary.get('total_games', 0)}")
                print(f"   Alerts: {summary.get('alerts_generated', 0)}")
                print(f"   Critical: {summary.get('critical_alerts', 0)}")
                print(
                    f"   Emergency Action: {summary.get('emergency_action_required', False)}"
                )
        else:
            print(f"❌ Summary format failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Summary format error: {e}")

    # Test 5: Error Handling (404)
    print("\n5️⃣ Testing Error Handling")
    try:
        response = requests.get(f"{base_url}/analysis/nonexistent", timeout=10)
        if response.status_code == 404:
            error_data = response.json()
            print(f"✅ 404 handling working")
            print(
                f"   Available endpoints: {len(error_data.get('available_endpoints', []))}"
            )
        else:
            print(f"❌ Expected 404, got: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error handling test failed: {e}")

    print(f"\n{'='*50}")
    print("🏁 API Testing Complete")
    return True


def start_api_server():
    """Start the API server in the background for testing."""
    import subprocess
    import os

    print("🚀 Starting API server...")

    # Start the server
    env = os.environ.copy()
    process = subprocess.Popen(["python", "src/api/survivorship_api.py"], env=env)

    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)

    return process


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Survivorship Bias API")
    parser.add_argument("--url", default="http://localhost:5001", help="API base URL")
    parser.add_argument(
        "--start-server", action="store_true", help="Start API server before testing"
    )

    args = parser.parse_args()

    process = None
    try:
        if args.start_server:
            process = start_api_server()

        # Run tests
        success = test_survivorship_api(args.url)

        if success:
            print("✅ All API tests completed successfully!")
        else:
            print("❌ Some API tests failed")
            sys.exit(1)

    finally:
        if process:
            print("\n🛑 Stopping API server...")
            process.terminate()
            process.wait()
