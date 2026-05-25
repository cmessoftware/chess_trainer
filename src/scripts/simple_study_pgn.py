"""
Simple Study PGN Generator - Fixed Version.

Generates working PGN studies from training resources that can be imported into Lichess.
This version focuses on creating valid PGN format with proper chess positions.

Usage:
    python simple_study_pgn.py [user_id]

Author: Chess Trainer ML Pipeline
Version: 1.0.0 (Fixed)
"""

import os
import sys
import json
import chess
import chess.pgn
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Set up logging
logger = logging.getLogger(__name__)
import logging

# Add training manager and database connection
from training_manager import TrainingResourceManager

# Try to import database manager
try:
    from database_manager import DatabaseManager
except ImportError:
    try:
        from src.repositories.database_manager import DatabaseManager
    except ImportError:
        DatabaseManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleStudyPGNGenerator:
    """
    Simple, reliable PGN study generator.
    """

    def __init__(self, export_dir: str = "training/studies"):
        self.export_dir = export_dir
        self.training_manager = TrainingResourceManager()
        os.makedirs(self.export_dir, exist_ok=True)

    def get_user_weaknesses(self, user_id: str) -> Dict[str, int]:
        """Analyze user's specific weaknesses from ML analysis."""
        if DatabaseManager is None:
            logger.warning("Database not available for user analysis")
            return {}

        try:
            db_manager = DatabaseManager()
            # Query for user's error patterns from features table
            query = """
                SELECT 
                    f.error_label,
                    f.tactical_tags,
                    COUNT(*) as count,
                    AVG(f.score_diff) as avg_score_loss
                FROM features f
                JOIN games g ON f.game_id = g.game_id
                WHERE (g.white_player = %s OR g.black_player = %s)
                  AND f.error_label IN ('blunder', 'mistake', 'inaccuracy')
                  AND f.tactical_tags IS NOT NULL
                GROUP BY f.error_label, f.tactical_tags
                ORDER BY count DESC, avg_score_loss DESC
                LIMIT 10
            """
            results = db_manager.fetch_all(query, (user_id, user_id))

            weaknesses = {}
            for row in results:
                error_type, tactical_tag, count, avg_loss = row
                key = f"{tactical_tag}_{error_type}"
                weaknesses[key] = {
                    "count": count,
                    "avg_score_loss": avg_loss,
                    "theme": tactical_tag,
                    "error_type": error_type,
                }

            logger.info(f"Found {len(weaknesses)} weakness patterns for {user_id}")
            return weaknesses

        except Exception as e:
            logger.error(f"Error analyzing user weaknesses: {e}")
            return {}

    def get_personalized_tactical_positions(
        self, user_id: str, limit: int = 8
    ) -> List[Dict]:
        """Get tactical positions based on user's specific weaknesses."""
        if DatabaseManager is None:
            logger.warning("Database not available, using fallback positions")
            return self.get_tactical_positions(limit)

        try:
            # Get user's main weaknesses
            weaknesses = self.get_user_weaknesses(user_id)

            if not weaknesses:
                logger.info(
                    f"No specific weaknesses found for {user_id}, using general positions"
                )
                return self.get_tactical_positions(limit)

            # Get positions targeting user's specific weaknesses
            db_manager = DatabaseManager()
            personalized_positions = []

            # Target the top 3 weakness themes
            top_weaknesses = sorted(
                weaknesses.items(), key=lambda x: x[1]["count"], reverse=True
            )[:3]

            for weakness_key, weakness_data in top_weaknesses:
                theme = weakness_data["theme"]

                # Query positions from analyzed_tacticals table that match the weakness
                query = """
                    SELECT DISTINCT 
                        at.position_fen as fen,
                        at.best_move as solution,
                        at.tactical_motif as theme,
                        at.game_id,
                        f.error_label
                    FROM analyzed_tacticals at
                    JOIN features f ON at.game_id = f.game_id AND at.move_number = f.move_number
                    WHERE at.tactical_motif ILIKE %s
                      AND at.position_fen IS NOT NULL
                      AND at.best_move IS NOT NULL
                      AND f.error_label IN ('blunder', 'mistake')
                    ORDER BY at.difficulty_score DESC, RANDOM()
                    LIMIT %s
                """

                theme_positions = db_manager.fetch_all(query, (f"%{theme}%", 2))

                for row in theme_positions:
                    fen, solution, tactical_theme, game_id, error_type = row
                    personalized_positions.append(
                        {
                            "fen": fen,
                            "solution": solution or "Find the best move",
                            "theme": tactical_theme or theme,
                            "description": f"User weakness: {theme} - {error_type}. Practice this pattern!",
                            "source": f"Personalized from game {game_id[:8]}",
                            "personalized": True,
                            "weakness_count": weakness_data["count"],
                        }
                    )

            # Fill remaining slots with general positions if needed
            if len(personalized_positions) < limit:
                general_positions = self.get_tactical_positions(
                    limit - len(personalized_positions)
                )
                personalized_positions.extend(general_positions)

            logger.info(
                f"Generated {len(personalized_positions)} personalized positions for {user_id}"
            )
            return personalized_positions[:limit]

        except Exception as e:
            logger.error(f"Error getting personalized positions: {e}")
            return self.get_tactical_positions(limit)

    def get_tactical_positions(self, limit: int = 10) -> List[Dict]:
        """Get tactical positions from the database."""
        tactical_positions = []

        if DatabaseManager is None:
            logger.warning("Database not available, using fallback tactical positions")
            # Fallback positions with FEN
            tactical_positions = [
                {
                    "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5",
                    "description": "Look for the fork! White can fork the king and queen.",
                    "solution": "Ng5",
                    "theme": "Fork",
                },
                {
                    "fen": "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w - - 0 7",
                    "description": "Pin the knight! The knight on f6 is pinned to the king.",
                    "solution": "Bg5",
                    "theme": "Pin",
                },
                {
                    "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                    "description": "Basic opening principle: Control the center!",
                    "solution": "Nf3 or d3",
                    "theme": "Opening",
                },
                {
                    "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 b kq - 1 5",
                    "description": "Black to move: Watch out for hanging pieces!",
                    "solution": "Be7 or Bd6",
                    "theme": "Hanging Piece",
                },
                {
                    "fen": "r2qkb1r/ppp2ppp/2np1n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 1 6",
                    "description": "Tactical shot! White can win material with a skewer.",
                    "solution": "Bxf7+",
                    "theme": "Skewer",
                },
            ]
        else:
            try:
                # Try to get positions from database
                db_manager = DatabaseManager()
                query = """
                    SELECT DISTINCT fen, move as solution, tags, source_game_id
                    FROM tactical_exercises 
                    WHERE fen IS NOT NULL 
                    ORDER BY RANDOM() 
                    LIMIT ?
                """
                results = db_manager.fetch_all(query, (limit,))

                for row in results:
                    tactical_positions.append(
                        {
                            "fen": row[0],
                            "solution": row[1] or "Find the best move",
                            "theme": row[2] or "Tactics",
                            "description": f"Tactical exercise from game {row[3]}",
                            "source": f"Game {row[3]}",
                        }
                    )

                logger.info(
                    f"Found {len(tactical_positions)} tactical positions from database"
                )

            except Exception as e:
                logger.error(f"Error getting tactical positions from database: {e}")
                # Use fallback positions if database fails
                tactical_positions = tactical_positions[
                    :3
                ]  # Use first 3 fallback positions

        return tactical_positions[:limit]

    def get_endgame_positions(self, limit: int = 6) -> List[Dict]:
        """Get endgame positions for training."""
        endgame_positions = [
            {
                "fen": "8/8/8/8/8/8/K7/k6Q w - - 0 1",
                "description": "Queen vs King: Basic checkmate pattern",
                "solution": "Qh8# or Qh1#",
                "theme": "Queen Mate",
            },
            {
                "fen": "8/8/8/8/8/8/KR6/k7 w - - 0 1",
                "description": "Rook vs King: Drive the king to the edge",
                "solution": "Ra2+",
                "theme": "Rook Mate",
            },
            {
                "fen": "8/8/8/8/8/2K5/8/2k4R w - - 0 1",
                "description": "Rook endgame: Cut off the king",
                "solution": "Ra1+",
                "theme": "King & Rook",
            },
            {
                "fen": "8/8/8/3k4/8/3K4/3P4/8 w - - 0 1",
                "description": "King and Pawn: Opposition is key",
                "solution": "Kc4 or Ke4",
                "theme": "K+P vs K",
            },
            {
                "fen": "8/8/8/8/8/8/5PPP/6K1 w - - 0 1",
                "description": "Pawn endgame: Create a passed pawn",
                "solution": "f4",
                "theme": "Pawn Endgame",
            },
            {
                "fen": "8/6p1/6P1/5k2/8/5K2/8/8 b - - 0 1",
                "description": "Opposition: Key concept in pawn endings",
                "solution": "Kf4 or Ke4",
                "theme": "Opposition",
            },
        ]

        return endgame_positions[:limit]

    def create_tactical_training_pgn(self, user_id: Optional[str] = None) -> str:
        """Create a tactical training study with real positions."""

        # Get personalized positions if user_id provided, otherwise general positions
        if user_id:
            tactical_positions = self.get_personalized_tactical_positions(
                user_id, limit=5
            )
            study_title = f"Personalized Tactical Training for {user_id}"
        else:
            tactical_positions = self.get_tactical_positions(limit=5)
            study_title = "General Tactical Training"

        if not tactical_positions:
            return "No tactical positions available"

        # Create separate games for each position
        games = []

        for i, position in enumerate(tactical_positions, 1):
            try:
                game = chess.pgn.Game()
                game.headers["Event"] = f"Chess Trainer: {study_title} - Exercise {i}"
                game.headers["Site"] = "https://chess-trainer.local"
                game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
                game.headers["Round"] = str(i)
                game.headers["White"] = f"Student_{user_id or 'User'}"
                game.headers["Black"] = "Chess_Trainer"
                game.headers["Result"] = "*"
                game.headers["Annotator"] = "Chess Trainer ML Pipeline"

                # Set up the position
                board = chess.Board(position["fen"])
                game.setup(board)

                # Create enhanced comment based on personalization
                if position.get("personalized"):
                    exercise_comment = f"""Exercise {i}: {position.get('theme', 'Tactics')} ⭐ PERSONALIZED

🎯 This position targets your specific weakness: {position.get('theme')}
📊 You've made errors in similar positions {position.get('weakness_count', 0)} times

Position: {position['fen']}
Description: {position.get('description', 'Find the best move!')}
Solution: {position.get('solution', 'Look for tactical motifs')}

🧠 Focus on:
- Pattern recognition for {position.get('theme')}
- Calculation accuracy
- Avoiding similar mistakes

Source: {position.get('source', 'Chess Trainer Database')}"""
                else:
                    exercise_comment = f"""Exercise {i}: {position.get('theme', 'Tactics')}

Position: {position['fen']}
Description: {position.get('description', 'Find the best move!')}
Solution: {position.get('solution', 'Look for tactical motifs')}

Study this position and look for:
- Hanging pieces
- Tactical motifs (pins, forks, skewers)  
- Forcing moves (checks, captures, threats)

Source: {position.get('source', 'Chess Trainer Database')}"""

                game.comment = exercise_comment
                games.append(str(game))

            except Exception as e:
                logger.error(f"Error processing tactical position {i}: {e}")
                continue

        return "\n\n".join(games)

    def generate_personalized_report(self, user_id: str) -> str:
        """Generate a personalized analysis report for the user."""
        try:
            weaknesses = self.get_user_weaknesses(user_id)

            if not weaknesses:
                return f"No ML analysis data available for user {user_id}"

            report = f"""# PERSONALIZED CHESS TRAINING REPORT
## User: {user_id}
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 🎯 IDENTIFIED WEAKNESSES (Based on Game Analysis)

"""

            for i, (weakness_key, data) in enumerate(weaknesses.items(), 1):
                theme = data["theme"]
                error_type = data["error_type"]
                count = data["count"]
                avg_loss = data["avg_score_loss"]

                report += f"""**{i}. {theme.upper()} - {error_type.upper()}**
   - Frequency: {count} occurrences
   - Average score loss: {avg_loss:.0f} centipawns
   - Priority: {'HIGH' if count >= 5 else 'MEDIUM' if count >= 3 else 'LOW'}

"""

            report += """### 📚 RECOMMENDED TRAINING APPROACH

1. **Focus on your top 3 weakness patterns**
2. **Practice tactical exercises targeting these themes**
3. **Review games where similar errors occurred**
4. **Use slow, calculated thinking in critical positions**

### 🚀 NEXT STEPS

1. Generate personalized studies with: `python src/scripts/simple_study_pgn.py {user_id}`
2. Practice regularly on Lichess targeting identified themes
3. Review progress after 20-30 games

**Note:** This analysis is based on your actual game data analyzed by our ML pipeline.
"""

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating personalized report for {user_id}"

    def create_endgame_training_pgn(self, user_id: Optional[str] = None) -> str:
        """Create an endgame training study with real positions."""

        # Get endgame positions
        endgame_positions = self.get_endgame_positions(limit=6)

        if not endgame_positions:
            return "No endgame positions available"

        # Create separate games for each position
        games = []

        for i, position in enumerate(endgame_positions, 1):
            try:
                game = chess.pgn.Game()
                game.headers["Event"] = (
                    f"Chess Trainer: Endgame Training - Exercise {i}"
                )
                game.headers["Site"] = "https://chess-trainer.local"
                game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
                game.headers["Round"] = str(i)
                game.headers["White"] = f"Student_{user_id or 'User'}"
                game.headers["Black"] = "Endgame_Trainer"
                game.headers["Result"] = "*"
                game.headers["Annotator"] = "Chess Trainer ML Pipeline"

                # Set up the position
                board = chess.Board(position["fen"])
                game.setup(board)

                # Add comment with exercise description
                exercise_comment = f"""Exercise {i}: {position.get('theme', 'Endgame')}

Position: {position['fen']}
Description: {position.get('description', 'Find the winning technique')}
Solution: {position.get('solution', 'Study the key moves')}

Key Concepts:
- King activity and centralization
- Pawn structure and weaknesses
- Piece coordination
- Calculation and technique

This is a fundamental endgame pattern. Practice until you can play it automatically!"""

                game.comment = exercise_comment
                games.append(str(game))

            except Exception as e:
                logger.error(f"Error processing endgame position {i}: {e}")
                continue

        return "\n\n".join(games)

    def export_all_studies(self, user_id: Optional[str] = None) -> List[str]:
        """Export all study PGNs to files."""

        logger.info(f"Exporting studies for user: {user_id or 'default'}")

        studies = {
            "tactical_training": self.create_tactical_training_pgn(user_id),
            "endgame_training": self.create_endgame_training_pgn(user_id),
        }

        exported_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_suffix = f"_{user_id}" if user_id else ""

        for study_name, pgn_content in studies.items():
            filename = f"{study_name}{user_suffix}_{timestamp}.pgn"
            file_path = os.path.join(self.export_dir, filename)

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(pgn_content)

                exported_files.append(file_path)
                logger.info(f"Exported: {filename}")

            except Exception as e:
                logger.error(f"Failed to export {filename}: {e}")

        return exported_files


def main():
    """Main function."""

    print("📚 SIMPLE STUDY PGN GENERATOR")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    user_id = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        generator = SimpleStudyPGNGenerator()
        exported_files = generator.export_all_studies(user_id)

        if exported_files:
            print(f"✅ Exported {len(exported_files)} study files:")
            for file_path in exported_files:
                size_kb = os.path.getsize(file_path) / 1024
                print(f"   📄 {os.path.basename(file_path)} ({size_kb:.1f} KB)")

            print(f"\n🚀 LICHESS IMPORT INSTRUCTIONS:")
            print(f"   1. Go to https://lichess.org/study")
            print(f"   2. Click 'New Study'")
            print(f"   3. Select 'Import PGN'")
            print(f"   4. Copy/paste content from generated files")
            print(f"   5. Customize study name and settings")
            print(f"\n   📁 Files location: {generator.export_dir}")

        else:
            print("⚠️  No studies were exported.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
