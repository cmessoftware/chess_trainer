"""
Test Lichess Upload - Debug Script

This script tests the Lichess upload functionality with detailed error reporting.
"""

import os
from pathlib import Path
import logging
from upload_to_lichess import LichessStudyUploader


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

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    print("🔍 LICHESS UPLOAD DEBUG TEST")
    print("=" * 50)

    # Get token from environment
    token = os.getenv("LICHESS_API_TOKEN")
    if not token:
        print("❌ No LICHESS_API_TOKEN found in environment")
        return False

    print(f"🔐 Using token: {token[:10]}...")

    try:
        # Create uploader
        uploader = LichessStudyUploader(token)
        print("✅ Uploader created successfully")

        # Find a recent PGN file to test
        studies_dir = Path("training/studies")
        if studies_dir.exists():
            pgn_files = list(studies_dir.glob("*.pgn"))
            if pgn_files:
                test_file = pgn_files[0]
                print(f"📄 Testing with file: {test_file}")

                # Try to upload
                study_name = f"Test Study - {test_file.stem}"
                study_url = uploader.create_study_from_pgn(
                    str(test_file), study_name, public=False
                )

                if study_url:
                    print(f"✅ SUCCESS! Study created: {study_url}")
                    return True
                else:
                    print("❌ Upload failed - check logs above")
                    return False
            else:
                print("❌ No PGN files found in training/studies")
                return False
        else:
            print("❌ training/studies directory not found")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
