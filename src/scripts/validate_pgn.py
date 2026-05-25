"""
PGN Validator - Test the generated PGN files for validity.

This script validates that the generated PGN files can be parsed correctly
and are suitable for import into Lichess or other chess platforms.

Usage:
    python validate_pgn.py [file_path]

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import sys
import chess.pgn
import io
from pathlib import Path


def validate_pgn_file(file_path: str) -> tuple[bool, str]:
    """
    Validate a PGN file.

    Args:
        file_path: Path to the PGN file

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse the PGN
        game = chess.pgn.read_game(io.StringIO(content))

        if game is None:
            return False, "Could not parse PGN - no game found"

        # Check headers
        required_headers = ["Event", "Site", "Date", "White", "Black", "Result"]
        missing_headers = [h for h in required_headers if h not in game.headers]

        if missing_headers:
            return False, f"Missing required headers: {missing_headers}"

        # Check if the game has valid structure
        has_comment = bool(game.comment)

        # Try to export it back to verify format
        exporter = chess.pgn.StringExporter()
        exported = game.accept(exporter)

        return True, f"Valid PGN - {len(exported)} chars, comment: {has_comment}"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def main():
    """Main validation function."""

    if len(sys.argv) < 2:
        print("Usage: python validate_pgn.py <pgn_file>")
        print("\nValidating all recent PGN files in training/studies/...")

        # Find recent PGN files
        studies_dir = Path("training/studies")
        if studies_dir.exists():
            pgn_files = list(studies_dir.glob("*.pgn"))

            if not pgn_files:
                print("No PGN files found in training/studies/")
                return

            # Sort by modification time, newest first
            pgn_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            print(f"Found {len(pgn_files)} PGN files:")

            for i, file_path in enumerate(pgn_files[:5]):  # Check latest 5
                print(f"\n{i+1}. {file_path.name}")
                is_valid, message = validate_pgn_file(str(file_path))

                status = "✅ VALID" if is_valid else "❌ INVALID"
                print(f"   {status}: {message}")

                if is_valid:
                    file_size = file_path.stat().st_size
                    print(f"   📊 Size: {file_size} bytes ({file_size/1024:.1f} KB)")
        else:
            print("training/studies/ directory not found")

    else:
        file_path = sys.argv[1]
        print(f"🔍 VALIDATING PGN FILE: {file_path}")
        print("=" * 50)

        is_valid, message = validate_pgn_file(file_path)

        if is_valid:
            print(f"✅ VALID: {message}")
            print("\n🚀 This file is ready for Lichess import!")
        else:
            print(f"❌ INVALID: {message}")
            print("\n⚠️  This file needs correction before import.")


if __name__ == "__main__":
    main()
