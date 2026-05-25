"""
Lichess API Explorer - Test available endpoints

This script tests various Lichess API endpoints to find the correct one for study creation.
"""

import os
import requests
import json
from pathlib import Path


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Load .env file
load_env_file()


def main():
    token = os.getenv("LICHESS_API_TOKEN")
    if not token:
        print("❌ No token found")
        return

    headers = {"Authorization": f"Bearer {token}"}
    base_url = "https://lichess.org/api"

    print("🔍 LICHESS API ENDPOINT EXPLORER")
    print("=" * 50)

    # Test different endpoints
    endpoints = [
        "/account",
        "/study",
        "/studies",
        "/study/create",
    ]

    for endpoint in endpoints:
        print(f"\n🧪 Testing: {endpoint}")
        try:
            response = requests.get(
                f"{base_url}{endpoint}", headers=headers, timeout=10
            )
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ Success!")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"Response text: {response.text[:200]}...")
            elif response.status_code == 404:
                print("❌ Not found")
            elif response.status_code == 405:
                print("⚠️  Method not allowed (might need POST)")
            else:
                print(f"⚠️  Other status: {response.text[:100]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Test POST methods
    print(f"\n🧪 Testing POST methods:")
    post_endpoints = [
        "/study",
    ]

    for endpoint in post_endpoints:
        print(f"\n📮 POST Testing: {endpoint}")
        try:
            test_data = {
                "name": "Test Study API",
                "description": "Testing API creation",
                "visibility": "private",
            }
            response = requests.post(
                f"{base_url}{endpoint}", headers=headers, data=test_data, timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}...")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
