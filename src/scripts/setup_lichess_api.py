"""
Setup Lichess API Token - Interactive Helper

This script helps you configure your Lichess API token for automatic study upload.

Instructions:
1. Go to: https://lichess.org/account/oauth/token
2. Create a new Personal API Token with these permissions:
   - study:write (required for creating studies)
   - study:read (optional, for reading existing studies)
3. Copy the generated token
4. Run this script and paste the token when prompted

The token will be saved to your environment configuration.
"""

import os
from pathlib import Path
import sys


def main():
    print("🔑 LICHESS API TOKEN SETUP")
    print("=" * 50)
    print()
    print("📝 INSTRUCTIONS:")
    print("1. Open: https://lichess.org/account/oauth/token")
    print("2. Click 'Create a new personal access token'")
    print("3. Give it a name like: 'Chess Trainer Auto Upload'")
    print("4. Check the permission: study:write")
    print("5. Click 'Create token'")
    print("6. Copy the generated token (it looks like: lip_xxxxxxxxxxxx)")
    print()

    # Get token from user
    token = input("🔐 Paste your Lichess API token here: ").strip()

    if not token:
        print("❌ No token provided. Exiting.")
        return False

    if not token.startswith("lip_"):
        print("⚠️  Warning: Lichess API tokens usually start with 'lip_'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Setup cancelled.")
            return False

    # Save to .env file
    env_file = Path(".env")
    env_content = ""

    # Read existing .env content
    if env_file.exists():
        env_content = env_file.read_text(encoding="utf-8")

    # Remove any existing LICHESS_API_TOKEN line
    lines = env_content.split("\n")
    lines = [line for line in lines if not line.startswith("LICHESS_API_TOKEN=")]

    # Add new token
    lines.append(f"LICHESS_API_TOKEN={token}")

    # Write back to file
    env_file.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ Token saved to {env_file.absolute()}")
    print()
    print("🧪 TESTING CONNECTION...")

    # Test the token
    import requests

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://lichess.org/api/account", headers=headers, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connection successful!")
            print(f"👤 Logged in as: {data.get('username', 'Unknown')}")
            print(
                f"📊 Rating: {data.get('perfs', {}).get('blitz', {}).get('rating', 'N/A')}"
            )
            print()
            print("🚀 READY TO USE!")
            print("Now you can run:")
            print("python auto_study_generator.py --user YOUR_USERNAME")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print("Double-check your token and try again.")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("Check your internet connection and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
