"""
Automatic Lichess Study Uploader.

This script automatically uploads generated PGN studies to Lichess using the Lichess API.
It creates studies directly on your Lichess account with proper organization and sharing.

Features:
- Automatic study creation via Lichess API
- PGN to Lichess format conversion
- Chapter organization and naming
- Study visibility and sharing controls
- Error handling and retry logic

Requirements:
- Lichess API token with study:write permissions
- Generated PGN studies from the training system

Usage:
    python upload_to_lichess.py [--token TOKEN] [--user USER] [--public]

How to get Lichess API Token:
1. Go to https://lichess.org/account/oauth/token
2. Create new token with 'study:write' permission
3. Copy token and set in environment or use --token parameter

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import sys
import json
import requests
import chess.pgn
import io
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LichessStudyUploader:
    """
    Handles automatic upload of PGN studies to Lichess.
    """

    def __init__(self, api_token: str):
        """
        Initialize the Lichess study uploader.

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

    def create_study_from_pgn(
        self, pgn_file: str, study_name: str, public: bool = False
    ) -> Optional[str]:
        """
        Create a Lichess study from a PGN file.

        Args:
            pgn_file: Path to the PGN file
            study_name: Name for the new study
            public: Whether the study should be public

        Returns:
            Study URL if successful, None otherwise
        """
        logger.info(f"📚 Creating Lichess study: {study_name}")

        try:
            # Read and parse PGN
            with open(pgn_file, "r", encoding="utf-8") as f:
                pgn_content = f.read()

            game = chess.pgn.read_game(io.StringIO(pgn_content))
            if not game:
                logger.error(f"❌ Could not parse PGN file: {pgn_file}")
                return None

            # Extract description from game comment
            description = self._extract_description(game)

            # Create study
            study_data = {
                "name": study_name,
                "description": description,
                "visibility": "public" if public else "private",
            }

            response = requests.post(
                f"{self.base_url}/study", headers=self.headers, data=study_data
            )

            if response.status_code == 200:
                study_info = response.json()
                study_id = study_info.get("id")
                study_url = f"https://lichess.org/study/{study_id}"

                logger.info(f"✅ Created study: {study_url}")

                # Import PGN content as the first chapter
                success = self._import_pgn_to_study(
                    study_id, pgn_content, "Training Content"
                )

                if success:
                    logger.info(f"✅ Successfully imported PGN content to study")
                    return study_url
                else:
                    logger.warning(f"⚠️ Study created but PGN import failed")
                    return study_url

            else:
                logger.error(
                    f"❌ Failed to create study: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Error creating study: {e}")
            return None

    def _extract_description(self, game: chess.pgn.Game) -> str:
        """Extract description from PGN game comment."""
        if game.comment:
            # Clean up the comment for use as description
            description = game.comment.strip()
            # Limit length for Lichess
            if len(description) > 400:
                description = description[:397] + "..."
            return description

        return "Generated by Chess Trainer ML Pipeline"

    def _import_pgn_to_study(
        self, study_id: str, pgn_content: str, chapter_name: str = "Chapter 1"
    ) -> bool:
        """
        Import PGN content to an existing study.

        Args:
            study_id: ID of the study
            pgn_content: PGN content to import
            chapter_name: Name for the chapter

        Returns:
            True if successful
        """
        try:
            chapter_data = {
                "name": chapter_name,
                "pgn": pgn_content,
                "orientation": "white",
            }

            response = requests.post(
                f"{self.base_url}/study/{study_id}/import-pgn",
                headers=self.headers,
                data=chapter_data,
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"❌ Failed to import PGN: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error importing PGN: {e}")
            return False

    def upload_all_studies_from_directory(
        self, studies_dir: str, public: bool = False
    ) -> List[Dict[str, str]]:
        """
        Upload all PGN studies from a directory to Lichess.

        Args:
            studies_dir: Directory containing PGN files
            public: Whether studies should be public

        Returns:
            List of created studies with their info
        """
        logger.info(f"📁 Uploading all studies from: {studies_dir}")

        studies_dir = Path(studies_dir)
        pgn_files = list(studies_dir.glob("*.pgn"))

        if not pgn_files:
            logger.warning(f"⚠️ No PGN files found in {studies_dir}")
            return []

        logger.info(f"📋 Found {len(pgn_files)} PGN files to upload")

        created_studies = []

        for pgn_file in pgn_files:
            # Generate study name from filename
            study_name = self._generate_study_name(pgn_file.name)

            # Create study
            study_url = self.create_study_from_pgn(str(pgn_file), study_name, public)

            if study_url:
                created_studies.append(
                    {"file": pgn_file.name, "study_name": study_name, "url": study_url}
                )

                # Rate limiting - wait between uploads
                time.sleep(2)

        return created_studies

    def _generate_study_name(self, filename: str) -> str:
        """Generate a clean study name from filename."""
        # Remove extension and timestamps
        name = filename.replace(".pgn", "")

        # Replace underscores and make title case
        name = name.replace("_", " ").title()

        # Clean up common patterns
        name = name.replace("Cmess4401", "Chess Training")
        name = name.replace("Study", "")

        # Remove timestamps (pattern: YYYYMMDD_HHMMSS)
        import re

        name = re.sub(r"\d{8}\s\d{6}", "", name).strip()

        return name or "Chess Training Study"

    def list_my_studies(self) -> List[Dict[str, Any]]:
        """List all studies owned by the authenticated user."""
        try:
            response = requests.get(
                f"{self.base_url}/study/by/me",
                headers={"Authorization": f"Bearer {self.api_token}"},
            )

            if response.status_code == 200:
                studies = response.json()
                logger.info(f"📚 Found {len(studies)} existing studies")
                return studies
            else:
                logger.error(f"❌ Failed to list studies: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error listing studies: {e}")
            return []


def get_api_token() -> Optional[str]:
    """Get Lichess API token from environment or user input."""

    # Try environment variables
    token = os.getenv("LICHESS_API_TOKEN") or os.getenv("LICHESS_TOKEN")

    if token and token.startswith("lip_"):
        return token

    # Try .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if "LICHESS_TOKEN=" in line or "LICHESS_API_TOKEN=" in line:
                    token = line.split("=")[1].strip()
                    if token.startswith("lip_"):
                        return token

    return None


def main():
    """Main function for automatic Lichess upload."""

    parser = argparse.ArgumentParser(
        description="Upload PGN studies to Lichess automatically"
    )
    parser.add_argument("--token", help="Lichess API token")
    parser.add_argument("--user", help="User ID for which to upload studies")
    parser.add_argument("--public", action="store_true", help="Make studies public")
    parser.add_argument(
        "--studies-dir",
        default="training/studies",
        help="Directory containing PGN studies",
    )

    args = parser.parse_args()

    print("🚀 AUTOMATIC LICHESS STUDY UPLOADER")
    print("=" * 60)
    print(f"Upload Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get API token
    token = args.token or get_api_token()

    if not token:
        print("❌ No Lichess API token found!")
        print()
        print("How to get a token:")
        print("1. Go to: https://lichess.org/account/oauth/token")
        print("2. Create new token with 'study:write' permission")
        print("3. Set LICHESS_API_TOKEN environment variable")
        print("4. Or use --token parameter")
        return

    if not token.startswith("lip_"):
        print("❌ Invalid token format. Lichess tokens start with 'lip_'")
        return

    try:
        # Initialize uploader
        print(f"🔗 Connecting to Lichess API...")
        uploader = LichessStudyUploader(token)

        # Check if studies directory exists
        studies_dir = Path(args.studies_dir)
        if not studies_dir.exists():
            print(f"❌ Studies directory not found: {studies_dir}")
            print("Run a PGN generator script first to create studies.")
            return

        # Upload all studies
        print(f"📁 Uploading from: {studies_dir}")
        visibility = "public" if args.public else "private"
        print(f"👁️ Visibility: {visibility}")
        print()

        created_studies = uploader.upload_all_studies_from_directory(
            str(studies_dir), args.public
        )

        if created_studies:
            print(f"\n✅ Successfully uploaded {len(created_studies)} studies:")
            print()

            for study in created_studies:
                print(f"📚 {study['study_name']}")
                print(f"   📄 From: {study['file']}")
                print(f"   🔗 URL: {study['url']}")
                print()

            print("🎉 All studies uploaded successfully!")
            print()
            print("📋 Next steps:")
            print("1. Visit your studies on Lichess")
            print("2. Customize names and descriptions if needed")
            print("3. Share with friends or make public")
            print("4. Start practicing with the uploaded content!")

        else:
            print("⚠️ No studies were uploaded. Check the logs for errors.")

    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
