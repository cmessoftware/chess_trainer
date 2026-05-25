"""
Complete Study Generator and Import Assistant.

This script generates PGN studies from training data and provides assistance
for importing them into Lichess studies.

IMPORTANT: Lichess API does NOT support creating new studies automatically.
Studies must be created manually on Lichess website first, then PGN content
can be imported using the API.

Features:
- Generate PGN studies from training data
- Validate PGN format
- Provide instructions for manual study creation
- Assist with importing PGN to existing studies

Usage:
    python auto_study_generator.py [--user USER] [--instructions]

Workflow:
1. Generate PGN studies (this script)
2. Create studies manually on Lichess website
3. Use lichess_study_manager.py to import PGN content

Author: Chess Trainer ML Pipeline
Version: 2.0.0
"""

import os
import sys
import json
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

# Import our modules
from simple_study_pgn import SimpleStudyPGNGenerator
from validate_pgn import validate_pgn_file

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
logger = logging.getLogger(__name__)


class AutoStudyGenerator:
    """
    Study generation and import assistance.

    Note: Lichess API does NOT support creating new studies automatically.
    This tool generates PGN files and provides guidance for manual import.
    """

    def __init__(self):
        """Initialize the study generator."""
        self.pgn_generator = SimpleStudyPGNGenerator()

    def generate_studies(
        self,
        user_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate PGN studies from training data.

        Args:
            user_id: User to generate studies for

        Returns:
            Dictionary with generation results
        """
        results = {
            "generated_files": [],
            "validation_results": [],
            "errors": [],
        }

        logger.info("🎯 Starting study generation...")

        # Step 1: Generate PGN studies
        logger.info("📚 Step 1: Generating PGN studies...")
        try:
            generated_files = self.pgn_generator.export_all_studies(user_id)
            results["generated_files"] = generated_files

            if not generated_files:
                results["errors"].append("No PGN studies were generated")
                return results

            logger.info(f"✅ Generated {len(generated_files)} PGN studies")

        except Exception as e:
            error_msg = f"Failed to generate PGN studies: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results

        # Step 2: Validate PGN files
        logger.info("🔍 Step 2: Validating PGN files...")
        for file_path in generated_files:
            is_valid, message = validate_pgn_file(file_path)
            results["validation_results"].append(
                {
                    "file": os.path.basename(file_path),
                    "valid": is_valid,
                    "message": message,
                }
            )

            if is_valid:
                logger.info(f"✅ Valid: {os.path.basename(file_path)}")
            else:
                logger.error(f"❌ Invalid: {os.path.basename(file_path)} - {message}")

        return results

    def create_summary_report(
        self, results: Dict[str, any], user_id: Optional[str]
    ) -> str:
        """Create a summary report of the generation process."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"training/studies/study_generation_report_{timestamp}.md"

        # Ensure directory exists
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        report_content = f"""# Study Generation and Import Guide

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**User:** {user_id or 'General'}
**Status:** {"✅ Success" if results['generated_files'] else "❌ Failed"}

## Summary

- **PGN Files Generated:** {len(results['generated_files'])}
- **Valid PGN Files:** {len([r for r in results['validation_results'] if r['valid']])}
- **Studies Uploaded:** 0 (Manual import required)
- **Errors:** {len(results['errors'])}

## Generated Files

"""

        for file_path in results["generated_files"]:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024
            report_content += f"- **{file_name}** ({file_size:.1f} KB)\n"

        report_content += "\n## Validation Results\n\n"

        for validation in results["validation_results"]:
            status = "✅" if validation["valid"] else "❌"
            report_content += (
                f"- {status} **{validation['file']}**: {validation['message']}\n"
            )

        if results["errors"]:
            report_content += "\n## Errors\n\n"
            for error in results["errors"]:
                report_content += f"- ❌ {error}\n"

        report_content += "\n## Next Steps - Manual Import to Lichess\n\n"
        report_content += """### IMPORTANT: Lichess API cannot create new studies automatically!

### Complete Import Workflow:

#### 1. Create Studies Manually on Lichess:
- Go to: https://lichess.org/study
- Click 'New Study' 
- Set name: 'Chess Training - Tactics' and 'Chess Training - Endgames'
- Choose privacy settings (private recommended for personal training)
- Copy the study IDs from URLs (e.g., https://lichess.org/study/ABC123)

#### 2. Import PGN Content to Your Studies:
```bash"""

        for validation in results["validation_results"]:
            if validation["valid"]:
                file_name = validation["file"]
                if "tactical" in file_name.lower():
                    report_content += f"\n# Import tactical training:\npython lichess_study_manager.py --study-id YOUR_TACTICS_STUDY_ID --pgn-file training/studies/{file_name}"
                elif "endgame" in file_name.lower():
                    report_content += f"\n# Import endgame training:\npython lichess_study_manager.py --study-id YOUR_ENDGAME_STUDY_ID --pgn-file training/studies/{file_name}"

        report_content += """
```

#### 3. For Training:
1. Practice with uploaded studies regularly
2. Focus on identified weaknesses
3. Use provided Lichess training links
4. Track improvement over time

### Training Resources:
- **Lichess Studies:** https://lichess.org/study/mine
- **Lichess Training:** https://lichess.org/training
- **Analysis Board:** https://lichess.org/analysis

---
*Report generated by Chess Trainer ML Pipeline*

"""

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report_content)

            logger.info(f"📋 Summary report saved: {report_file}")
            return report_file

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""


def print_import_instructions():
    """Print detailed instructions for importing studies to Lichess."""
    print("\n" + "=" * 70)
    print("🎯 COMPLETE LICHESS IMPORT WORKFLOW")
    print("=" * 70)
    print("\n📖 IMPORTANT: Lichess API cannot create new studies automatically!")
    print("   Studies must be created manually on Lichess website first.\n")

    print("🔄 STEP-BY-STEP WORKFLOW:")
    print()
    print("1️⃣ GENERATE PGN STUDIES:")
    print("   python auto_study_generator.py --user YOUR_USERNAME")
    print()
    print("2️⃣ CREATE STUDIES ON LICHESS WEBSITE:")
    print("   - Go to: https://lichess.org/study")
    print("   - Click 'New Study'")
    print("   - Create two studies:")
    print("     • 'Chess Training - Tactics' for tactical problems")
    print("     • 'Chess Training - Endgames' for endgame positions")
    print("   - Set privacy (Private recommended for personal training)")
    print("   - Copy study IDs from URLs (e.g., ABC123 from lichess.org/study/ABC123)")
    print()
    print("3️⃣ IMPORT PGN CONTENT TO YOUR STUDIES:")
    print("   # For tactical training:")
    print(
        "   python lichess_study_manager.py --study-id YOUR_TACTICS_ID --pgn-file tactical_training_*.pgn"
    )
    print()
    print("   # For endgame training:")
    print(
        "   python lichess_study_manager.py --study-id YOUR_ENDGAMES_ID --pgn-file endgame_training_*.pgn"
    )
    print()
    print("4️⃣ START TRAINING:")
    print("   - Visit: https://lichess.org/study/mine")
    print("   - Practice with your personalized studies")
    print("   - Track your improvement over time")
    print()
    print("💡 PRO TIPS:")
    print("- Generated PGN files are in training/studies/ directory")
    print("- Studies can be shared with friends or coaches")
    print("- Use Lichess analysis board for deeper study")
    print("- Regular practice with personalized content improves results")
    print("=" * 70 + "\n")


def main():
    """Main function for study generation."""

    parser = argparse.ArgumentParser(
        description="Generate PGN studies for manual import to Lichess"
    )
    parser.add_argument("--user", help="User ID to generate studies for")
    parser.add_argument(
        "--instructions", action="store_true", help="Show detailed import instructions"
    )

    args = parser.parse_args()

    if args.instructions:
        print_import_instructions()
        return

    print("🚀 COMPLETE STUDY GENERATOR")
    print("=" * 70)
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 IMPORTANT: Lichess API cannot create studies automatically!")
    print("   Generated PGN files must be imported manually to existing studies.")
    print("   Use --instructions flag for detailed import workflow.")
    print()

    try:
        # Initialize generator
        generator = AutoStudyGenerator()

        # Run generation workflow
        print(f"👤 User: {args.user or 'General'}")
        print()

        results = generator.generate_studies(user_id=args.user)

        # Show results
        print("📊 RESULTS SUMMARY:")
        print(f"   📄 PGN files generated: {len(results['generated_files'])}")
        print(
            f"   ✅ Valid PGN files: {len([r for r in results['validation_results'] if r['valid']])}"
        )
        print(f"   ❌ Errors: {len(results['errors'])}")
        print()

        if results["errors"]:
            print("⚠️ ERRORS:")
            for error in results["errors"]:
                print(f"   ❌ {error}")
            print()

        # Generate summary report
        report_file = generator.create_summary_report(results, args.user)
        if report_file:
            print(f"📋 Detailed report: {report_file}")

        if results["generated_files"]:
            print("📁 Generated files located in: training/studies/")
            print()
            print("🔄 NEXT STEPS:")
            print("1. Create studies manually on Lichess website")
            print("2. Use lichess_study_manager.py to import PGN content")
            print("3. Run with --instructions for detailed workflow")

        print("✨ Generation completed!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
