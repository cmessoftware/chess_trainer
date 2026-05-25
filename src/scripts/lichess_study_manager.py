"""
Lichess Study Management Assistant.

Since Lichess API does not support creating new studies programmatically,
this script helps manage the workflow of creating studies manually and then
using the API to import PGN content into existing studies.

Workflow:
1. Generate PGN studies using the training system
2. Create studies manually on Lichess website
3. Use this script to import PGN content into existing studies

Features:
- Validate PGN files before import
- Import PGN into existing Lichess studies
- Manage multiple study imports
- Track import success/failures

Usage:
    python lichess_study_manager.py --study-id STUDY_ID --pgn-file FILE.pgn

Author: Chess Trainer ML Pipeline
Version: 2.0.0
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging
import argparse


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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class LichessStudyManager:
    """
    Manages importing PGN content into existing Lichess studies.

    Note: Lichess API does NOT support creating new studies. Studies must be
    created manually on the Lichess website first.
    """

    def __init__(self, api_token: str):
        """
        Initialize the Lichess study manager.

        Args:
            api_token: Lichess API token with study:write permissions
        """
        self.api_token = api_token
        self.base_url = "https://lichess.org/api"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Verify token works
        if not self._verify_token():
            raise ValueError("Invalid Lichess API token or insufficient permissions")

    def _verify_token(self) -> bool:
        """Verify that the API token is valid and has correct permissions."""
        try:
            response = requests.get(
                f"{self.base_url}/account",
                headers={"Authorization": f"Bearer {self.api_token}"},
            )

            if response.status_code == 200:
                user_info = response.json()
                username = user_info.get("username", "Unknown")
                logger.info(f"✅ Connected to Lichess as: {username}")
                return True
            else:
                logger.error(f"❌ Token verification failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Token verification error: {e}")
            return False

    def import_pgn_to_study(
        self, study_id: str, pgn_file: str, chapter_name: Optional[str] = None
    ) -> bool:
        """
        Import PGN content to an existing Lichess study.

        Args:
            study_id: ID of the existing study (from study URL)
            pgn_file: Path to the PGN file to import
            chapter_name: Optional name for the chapter

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📚 Importing PGN to study: https://lichess.org/study/{study_id}")

        try:
            # Read PGN content
            with open(pgn_file, "r", encoding="utf-8") as f:
                pgn_content = f.read()

            if not chapter_name:
                chapter_name = Path(pgn_file).stem

            # Prepare data for import
            import_data = {
                "name": chapter_name,
                "pgn": pgn_content,
                "orientation": "white",
            }

            # Import PGN to existing study
            response = requests.post(
                f"{self.base_url}/study/{study_id}/import-pgn",
                headers=self.headers,
                data=import_data,
                timeout=30,
            )

            if response.status_code == 200:
                logger.info(f"✅ Successfully imported PGN as chapter: {chapter_name}")
                return True
            else:
                logger.error(
                    f"❌ Failed to import PGN: {response.status_code} - {response.text[:200]}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error importing PGN: {e}")
            return False

    def get_study_info(self, study_id: str) -> Optional[Dict]:
        """
        Get information about a study (to verify it exists).

        Args:
            study_id: ID of the study

        Returns:
            Study information if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/study/{study_id}.pgn",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"✅ Study {study_id} exists and is accessible")
                return {"id": study_id, "accessible": True}
            else:
                logger.error(f"❌ Study {study_id} not found or not accessible")
                return None

        except Exception as e:
            logger.error(f"❌ Error checking study: {e}")
            return None

    def batch_import_to_studies(self, import_config: List[Dict]) -> Dict[str, bool]:
        """
        Import multiple PGN files to different studies.

        Args:
            import_config: List of dicts with 'study_id', 'pgn_file', 'chapter_name'

        Returns:
            Dictionary with results for each import
        """
        results = {}

        for config in import_config:
            study_id = config.get("study_id")
            pgn_file = config.get("pgn_file")
            chapter_name = config.get("chapter_name")

            if not study_id or not pgn_file:
                logger.error(f"❌ Invalid config: {config}")
                results[f"{study_id}_{pgn_file}"] = False
                continue

            success = self.import_pgn_to_study(study_id, pgn_file, chapter_name)
            results[f"{study_id}_{Path(pgn_file).name}"] = success

            # Rate limiting
            time.sleep(2)

        return results


def print_usage_instructions():
    """Print detailed instructions for using this system."""
    print("\n" + "=" * 70)
    print("🎯 LICHESS STUDY IMPORT WORKFLOW")
    print("=" * 70)
    print("\n📖 IMPORTANT: Lichess API cannot create new studies!")
    print("   You must create studies manually on Lichess website first.\n")

    print("🔄 COMPLETE WORKFLOW:")
    print("1. Generate PGN studies:")
    print("   python auto_study_generator.py --user USERNAME --no-upload")
    print()
    print("2. Create studies manually on Lichess:")
    print("   - Go to: https://lichess.org/study")
    print("   - Click 'New Study'")
    print("   - Set name and privacy settings")
    print("   - Copy the study ID from URL (e.g., https://lichess.org/study/ABC123)")
    print()
    print("3. Import PGN content to your studies:")
    print(
        "   python lichess_study_manager.py --study-id ABC123 --pgn-file tactical_training.pgn"
    )
    print()
    print("💡 PRO TIPS:")
    print("- Create one study for tactical training, another for endgames")
    print("- Use meaningful study names like 'Chess Training - Tactics 2026'")
    print("- Set studies to private if you want personal training")
    print("- You can import multiple PGN files as separate chapters")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Import PGN files to existing Lichess studies"
    )
    parser.add_argument("--study-id", help="Lichess study ID (from study URL)")
    parser.add_argument("--pgn-file", help="Path to PGN file to import")
    parser.add_argument("--chapter-name", help="Name for the imported chapter")
    parser.add_argument("--token", help="Lichess API token (optional, uses env var)")
    parser.add_argument(
        "--instructions", action="store_true", help="Show usage instructions"
    )

    args = parser.parse_args()

    if args.instructions or (not args.study_id and not args.pgn_file):
        print_usage_instructions()
        return

    # Get API token
    token = args.token or os.getenv("LICHESS_API_TOKEN")
    if not token:
        print(
            "❌ No Lichess API token found. Set LICHESS_API_TOKEN env var or use --token"
        )
        print("💡 Get token at: https://lichess.org/account/oauth/token")
        return

    try:
        manager = LichessStudyManager(token)

        # Verify study exists
        study_info = manager.get_study_info(args.study_id)
        if not study_info:
            print(f"❌ Study {args.study_id} not found or not accessible")
            print("💡 Make sure the study exists and you have access to it")
            return

        # Import PGN
        success = manager.import_pgn_to_study(
            args.study_id, args.pgn_file, args.chapter_name
        )

        if success:
            print(
                f"✅ SUCCESS! PGN imported to: https://lichess.org/study/{args.study_id}"
            )
        else:
            print("❌ Import failed. Check logs above for details.")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
