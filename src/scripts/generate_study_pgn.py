"""
Study PGN Generator and Exporter.

This module creates training studies in PGN format from the training resources
and user analysis data. The studies can then be imported into Lichess or Chess.com.

Key Features:
- Generate PGN studies from training plans and exercises
- Export position sequences with annotations
- Create study chapters organized by theme
- Generate Lichess-importable PGN format
- Export tactical puzzles as annotated games

Usage:
    python generate_study_pgn.py [user_id] [--export-path path]

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import sys
import json
import chess
import chess.pgn
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

# Add src to path for imports
sys.path.append("src")
from modules.pgn_utils import load_pgn_from_string
from modules.pgn_generator import generate_pgn_from_moves
from training_manager import TrainingResourceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StudyPGNGenerator:
    """
    Generates PGN studies from training resources and analysis data.
    """

    def __init__(self, export_dir: str = "training/studies"):
        """
        Initialize the study PGN generator.

        Args:
            export_dir: Directory to export PGN studies
        """
        self.export_dir = export_dir
        self.training_manager = TrainingResourceManager()

        # Ensure export directory exists
        os.makedirs(self.export_dir, exist_ok=True)

    def generate_tactical_study_pgn(self, user_id: Optional[str] = None) -> str:
        """
        Generate a tactical training study in PGN format.

        Args:
            user_id: Specific user to generate study for

        Returns:
            PGN string of the tactical study
        """
        logger.info("Generating tactical training study PGN...")

        # Get exercise plan
        exercise_plan = self.training_manager.get_latest_exercise_plan(user_id)
        if not exercise_plan:
            logger.warning("No exercise plan found")
            return ""

        # Create main study game
        study_game = chess.pgn.Game()
        study_game.headers["Event"] = "Chess Trainer: Tactical Study"
        study_game.headers["Site"] = "Chess Trainer ML Pipeline"
        study_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        study_game.headers["Round"] = "1"
        study_game.headers["White"] = f"Student ({user_id or 'User'})"
        study_game.headers["Black"] = "Training System"
        study_game.headers["Result"] = "*"

        # Add study description
        user_ids = exercise_plan.get("user_ids", [])
        total_exercises = exercise_plan.get("total_exercises", 0)
        study_game.comment = f"""
        TACTICAL TRAINING STUDY
        
        Generated for users: {', '.join(user_ids)}
        Total exercises: {total_exercises}
        Generated: {exercise_plan.get('generated_at', 'Unknown')}
        
        This study contains tactical exercises based on your actual game analysis.
        Each variation represents a specific tactical theme you need to practice.
        """.strip()

        # Get tactical exercises
        tactical_exercises = self.training_manager.get_exercises_by_type(
            "tactical", user_id
        )

        node = study_game
        chapter_number = 1

        for exercise in tactical_exercises:
            # Add chapter for each exercise
            chapter_comment = f"""
            CHAPTER {chapter_number}: {exercise.get('title', 'Tactical Exercise')}
            
            Description: {exercise.get('description', '')}
            Time estimate: {exercise.get('time_estimate', 0)} minutes
            
            Lichess link: {exercise.get('lichess_study_url', 'N/A')}
            Chess.com link: {exercise.get('chess_com_url', 'N/A')}
            """.strip()

            # Create variation for this exercise
            variation = node.add_variation(chess.Move.null())
            variation.comment = chapter_comment

            # Add specific moves if available
            specific_moves = exercise.get("specific_moves", [])
            if specific_moves:
                moves_text = "\n".join(f"• {move}" for move in specific_moves)
                variation.comment += f"\n\nSpecific training moves:\n{moves_text}"

            chapter_number += 1

        # Export to PGN string
        exporter = chess.pgn.StringExporter(
            headers=True, variations=True, comments=True
        )

        return study_game.accept(exporter)

    def generate_position_analysis_pgn(self, user_id: Optional[str] = None) -> str:
        """
        Generate position analysis study in PGN format.

        Args:
            user_id: Specific user to generate study for

        Returns:
            PGN string of the position analysis study
        """
        logger.info("Generating position analysis study PGN...")

        exercise_plan = self.training_manager.get_latest_exercise_plan(user_id)
        if not exercise_plan:
            return ""

        # Create analysis study game
        study_game = chess.pgn.Game()
        study_game.headers["Event"] = "Chess Trainer: Position Analysis"
        study_game.headers["Site"] = "Chess Trainer ML Pipeline"
        study_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        study_game.headers["Round"] = "1"
        study_game.headers["White"] = f"Analyst ({user_id or 'User'})"
        study_game.headers["Black"] = "Training Positions"
        study_game.headers["Result"] = "*"

        study_game.comment = """
        POSITION ANALYSIS STUDY
        
        This study contains critical positions from your games that require deeper analysis.
        Focus on understanding the strategic and tactical themes in each position.
        """.strip()

        # Get analysis exercises
        analysis_exercises = self.training_manager.get_exercises_by_type(
            "position_analysis", user_id
        )

        node = study_game
        for i, exercise in enumerate(analysis_exercises, 1):
            # Create variation for each position
            variation = node.add_variation(chess.Move.null())
            variation.comment = f"""
            POSITION {i}: {exercise.get('title', 'Analysis Position')}
            
            {exercise.get('description', '')}
            
            Key themes to analyze:
            • Strategic elements
            • Tactical motifs
            • Endgame principles
            """.strip()

            # Add position FEN if available
            position_fen = exercise.get("position_fen")
            if position_fen:
                variation.comment += f"\n\nPosition FEN: {position_fen}"

        exporter = chess.pgn.StringExporter(
            headers=True, variations=True, comments=True
        )

        return study_game.accept(exporter)

    def generate_endgame_study_pgn(self, user_id: Optional[str] = None) -> str:
        """
        Generate endgame training study in PGN format.

        Args:
            user_id: Specific user to generate study for

        Returns:
            PGN string of the endgame study
        """
        logger.info("Generating endgame study PGN...")

        exercise_plan = self.training_manager.get_latest_exercise_plan(user_id)
        if not exercise_plan:
            return ""

        # Create endgame study
        study_game = chess.pgn.Game()
        study_game.headers["Event"] = "Chess Trainer: Endgame Mastery"
        study_game.headers["Site"] = "Chess Trainer ML Pipeline"
        study_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        study_game.headers["Round"] = "1"
        study_game.headers["White"] = f"Student ({user_id or 'User'})"
        study_game.headers["Black"] = "Endgame Trainer"
        study_game.headers["Result"] = "*"

        study_game.comment = """
        ENDGAME TRAINING STUDY
        
        Master the fundamental endgame patterns and techniques.
        These positions are based on common endgame scenarios from your games.
        """.strip()

        # Get endgame exercises
        endgame_exercises = self.training_manager.get_exercises_by_type(
            "endgame", user_id
        )

        node = study_game
        for exercise in endgame_exercises:
            variation = node.add_variation(chess.Move.null())
            variation.comment = f"""
            ENDGAME THEME: {exercise.get('title', 'Endgame Position')}
            
            {exercise.get('description', '')}
            
            Practice focus:
            • Technique and accuracy
            • Key theoretical positions
            • Practical conversion skills
            """.strip()

        exporter = chess.pgn.StringExporter(
            headers=True, variations=True, comments=True
        )

        return study_game.accept(exporter)

    def create_complete_study_collection(
        self, user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a complete collection of study PGNs.

        Args:
            user_id: Specific user to generate studies for

        Returns:
            Dictionary mapping study names to PGN content
        """
        logger.info("Creating complete study collection...")

        collection = {}

        # Generate all study types
        collection["tactical_training"] = self.generate_tactical_study_pgn(user_id)
        collection["position_analysis"] = self.generate_position_analysis_pgn(user_id)
        collection["endgame_mastery"] = self.generate_endgame_study_pgn(user_id)

        # Filter out empty studies
        collection = {name: content for name, content in collection.items() if content}

        logger.info(f"Generated {len(collection)} study PGNs")
        return collection

    def export_studies_to_files(self, user_id: Optional[str] = None) -> List[str]:
        """
        Export all studies to PGN files.

        Args:
            user_id: Specific user to generate studies for

        Returns:
            List of exported file paths
        """
        logger.info("Exporting studies to PGN files...")

        collection = self.create_complete_study_collection(user_id)
        exported_files = []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_suffix = f"_{user_id}" if user_id else ""

        for study_name, pgn_content in collection.items():
            filename = f"{study_name}_study{user_suffix}_{timestamp}.pgn"
            file_path = os.path.join(self.export_dir, filename)

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(pgn_content)

                exported_files.append(file_path)
                logger.info(f"Exported study: {file_path}")

            except Exception as e:
                logger.error(f"Failed to export {filename}: {e}")

        return exported_files

    def generate_lichess_import_instructions(self, exported_files: List[str]) -> str:
        """
        Generate instructions for importing studies into Lichess.

        Args:
            exported_files: List of exported PGN file paths

        Returns:
            Instructions text
        """
        instructions = f"""
# 📚 LICHESS STUDY IMPORT INSTRUCTIONS

## Generated Studies ({len(exported_files)} files):
"""

        for file_path in exported_files:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB

            instructions += f"""
### {filename}
- **Size**: {file_size:.1f} KB
- **Path**: `{file_path}`
"""

        instructions += """

## How to Import into Lichess:

### Method 1: Create New Study
1. Go to https://lichess.org/study
2. Click "New Study"
3. Click "Import PGN" tab
4. Copy and paste the content from one of the generated PGN files
5. Click "Import"
6. Customize study name and settings

### Method 2: Add to Existing Study
1. Open your existing study on Lichess
2. Click "New Chapter"
3. Select "Import PGN"
4. Paste the PGN content
5. Set chapter name and save

## Study Structure:
- **Tactical Training**: Focus on tactical puzzles and combinations
- **Position Analysis**: Deep analysis of strategic positions
- **Endgame Mastery**: Endgame techniques and theoretical positions

## Tips for Best Results:
- Import one study type at a time
- Use descriptive chapter names
- Add your own annotations and variations
- Share studies with training partners
- Practice regularly using the Lichess study tools

## Alternative Links:
If you prefer ready-made content, use these verified Lichess links:
- Tactical Training: https://lichess.org/training/theme/hangingPiece
- Position Analysis: https://lichess.org/analysis
- Endgame Practice: https://lichess.org/training/theme/endgame

---
Generated by Chess Trainer ML Pipeline on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return instructions


def main():
    """Main function to generate study PGNs."""

    print("📚 STUDY PGN GENERATOR")
    print("=" * 50)
    print(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Parse command line arguments
    user_id = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        # Initialize generator
        generator = StudyPGNGenerator()

        # Export studies
        print(f"🎯 Generating studies{f' for user: {user_id}' if user_id else ''}...")
        exported_files = generator.export_studies_to_files(user_id)

        if not exported_files:
            print("⚠️  No studies were generated. Check that training resources exist.")
            return

        print(f"\n✅ Successfully exported {len(exported_files)} study files:")
        for file_path in exported_files:
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"   📄 {os.path.basename(file_path)} ({file_size:.1f} KB)")

        # Generate import instructions
        instructions = generator.generate_lichess_import_instructions(exported_files)
        instructions_file = os.path.join(
            generator.export_dir,
            f"IMPORT_INSTRUCTIONS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        )

        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write(instructions)

        print(f"\n📋 Import instructions saved: {instructions_file}")

        # Show summary
        print(f"\n🚀 READY TO IMPORT TO LICHESS:")
        print(f"   1. Go to https://lichess.org/study")
        print(f"   2. Click 'New Study'")
        print(f"   3. Import the generated PGN files")
        print(f"   4. Follow instructions in: {os.path.basename(instructions_file)}")

    except Exception as e:
        print(f"\n❌ Error generating studies: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
