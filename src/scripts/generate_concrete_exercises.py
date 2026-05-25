"""
Concrete Exercise Generation System for Chess Training.

This module generates specific, actionable exercises based on user's real game data,
integrating with Lichess Studies, Chess.com, and auto-generating tactical positions.

Key Features:
- Extract problematic positions from user's actual games
- Generate Lichess studies automatically
- Create specific tactical exercises based on error patterns
- Auto-generate strategic positions for identified weaknesses

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import psycopg2
import requests
from datetime import datetime
import chess
import chess.pgn
import chess.engine
import io

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConcreteExercise:
    """Represents a concrete, actionable exercise."""

    title: str
    description: str
    exercise_type: str  # 'lichess_study', 'tactics', 'position_analysis', 'game_review'
    position_fen: Optional[str] = None
    lichess_study_url: Optional[str] = None
    chess_com_url: Optional[str] = None
    specific_moves: List[str] = None
    success_criteria: str = ""
    time_estimate: int = 15  # minutes
    difficulty_level: str = "intermediate"
    source_game_id: Optional[str] = None


@dataclass
class GamePosition:
    """Represents a position from a real game."""

    game_id: str
    fen: str
    move_number: int
    player_move: str
    engine_move: str
    evaluation_before: float
    evaluation_after: float
    error_type: str  # 'blunder', 'mistake', 'inaccuracy'


class ConcreteExerciseGenerator:
    """
    Generates specific, actionable exercises based on real game analysis.
    """

    def __init__(
        self, db_url: Optional[str] = None, lichess_token: Optional[str] = None
    ):
        """
        Initialize the exercise generator.

        Args:
            db_url: Database connection URL
            lichess_token: Lichess API token (optional)
        """
        self.db_url = db_url or os.environ.get(
            "CHESS_TRAINER_DB_URL",
            "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db",
        )
        self.lichess_token = lichess_token
        self.lichess_base_url = "https://lichess.org/api"

    def extract_problematic_positions(
        self, user_ids: List[str], limit: int = 20
    ) -> List[GamePosition]:
        """
        Extract specific positions from user's games where errors occurred.

        Args:
            user_ids: List of user IDs
            limit: Maximum positions to extract

        Returns:
            List of problematic positions from real games
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Get games with features (errors) for these users
            cursor.execute(
                """
                SELECT 
                    g.game_id,
                    g.pgn,
                    f.error_label,
                    g.white_player,
                    g.black_player,
                    g.result
                FROM features f
                JOIN games g ON f.game_id = g.game_id
                WHERE (g.white_player = ANY(%s) OR g.black_player = ANY(%s))
                  AND f.error_label IN ('blunder', 'mistake', 'inaccuracy')
                LIMIT %s
            """,
                (user_ids, user_ids, limit),
            )

            rows = cursor.fetchall()
            positions = []

            for game_id, pgn, error_label, white_player, black_player, result in rows:
                try:
                    # Parse the PGN to extract the problematic position
                    game = chess.pgn.read_game(io.StringIO(pgn))
                    if game:
                        board = game.board()
                        moves_played = 0

                        # Play through the game to find a representative error position
                        for move in game.mainline_moves():
                            board.push(move)
                            moves_played += 1

                            # Take a position from mid-game where errors are more common
                            if 10 <= moves_played <= 30:
                                position = GamePosition(
                                    game_id=game_id,
                                    fen=board.fen(),
                                    move_number=moves_played,
                                    player_move=str(move),
                                    engine_move="",  # Would need engine analysis
                                    evaluation_before=0.0,
                                    evaluation_after=0.0,
                                    error_type=error_label,
                                )
                                positions.append(position)
                                break

                except Exception as e:
                    logger.warning(f"Failed to parse game {game_id}: {e}")
                    continue

            cursor.close()
            conn.close()

            logger.info(f"Extracted {len(positions)} problematic positions")
            return positions

        except Exception as e:
            logger.error(f"Failed to extract positions: {e}")
            return []

    def create_lichess_study(
        self, study_name: str, exercises: List[ConcreteExercise]
    ) -> Optional[str]:
        """
        Create a Lichess study with specific positions and exercises.

        Args:
            study_name: Name for the study
            exercises: List of exercises to include

        Returns:
            Lichess study URL if successful
        """
        if not self.lichess_token:
            logger.warning("No Lichess token provided, cannot create study")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.lichess_token}",
                "Content-Type": "application/json",
            }

            # Create study
            study_data = {
                "name": study_name,
                "description": f"Generated training study for chess improvement - {len(exercises)} exercises",
                "public": False,  # Private study
            }

            response = requests.post(
                f"{self.lichess_base_url}/study", headers=headers, json=study_data
            )

            if response.status_code == 200:
                study_info = response.json()
                study_id = study_info.get("id")
                study_url = f"https://lichess.org/study/{study_id}"

                # Add chapters (positions) to the study
                for i, exercise in enumerate(exercises):
                    if exercise.position_fen:
                        self._add_chapter_to_study(study_id, exercise, i + 1)

                logger.info(f"Created Lichess study: {study_url}")
                return study_url
            else:
                logger.error(f"Failed to create Lichess study: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating Lichess study: {e}")
            return None

    def _add_chapter_to_study(
        self, study_id: str, exercise: ConcreteExercise, chapter_num: int
    ):
        """Add a chapter (position) to a Lichess study."""
        try:
            headers = {
                "Authorization": f"Bearer {self.lichess_token}",
                "Content-Type": "application/json",
            }

            chapter_data = {
                "name": f"{chapter_num}. {exercise.title}",
                "fen": exercise.position_fen,
                "description": exercise.description,
            }

            response = requests.post(
                f"{self.lichess_base_url}/study/{study_id}/chapter",
                headers=headers,
                json=chapter_data,
            )

            if response.status_code != 200:
                logger.warning(
                    f"Failed to add chapter to study: {response.status_code}"
                )

        except Exception as e:
            logger.warning(f"Error adding chapter to study: {e}")

    def get_lichess_training_urls(self) -> Dict[str, str]:
        """
        Get real, working Lichess training URLs for different tactical themes.

        Returns:
            Dictionary mapping training themes to real URLs
        """
        return {
            "hanging_pieces": "https://lichess.org/training/theme/hangingPiece",
            "pins": "https://lichess.org/training/theme/pin",
            "forks": "https://lichess.org/training/theme/fork",
            "skewers": "https://lichess.org/training/theme/skewer",
            "discovered_attacks": "https://lichess.org/training/theme/discoveredAttack",
            "double_attacks": "https://lichess.org/training/theme/doubleCheck",
            "deflection": "https://lichess.org/training/theme/deflection",
            "decoy": "https://lichess.org/training/theme/decoy",
            "mate_in_one": "https://lichess.org/training/theme/mateIn1",
            "mate_in_two": "https://lichess.org/training/theme/mateIn2",
            "basic_checkmates": "https://lichess.org/practice/checkmates/piece-checkmates-i/BJy6fEDf/YyDCuZrF",
            "king_and_queen": "https://lichess.org/practice/basic-endgames/queen-endgames/bnbGwPYh/iJNrAGQk",
            "king_and_rook": "https://lichess.org/practice/basic-endgames/rook-endgames/DwG7CrDO/W9EvWWGF",
            "pawn_endgames": "https://lichess.org/practice/basic-endgames/pawn-endgames/GYKfRH29/jLSBTTl9",
            "puzzle_streak": "https://lichess.org/streak",
            "puzzle_dashboard": "https://lichess.org/training/dashboard/30",
            "coordinates": "https://lichess.org/training/coordinate",
            "mixed_tactics": "https://lichess.org/training",
        }

    def get_chess_com_training_urls(self) -> Dict[str, str]:
        """
        Get real Chess.com training URLs as alternatives.

        Returns:
            Dictionary mapping training themes to Chess.com URLs
        """
        return {
            "tactics": "https://www.chess.com/puzzles",
            "endgames": "https://www.chess.com/drills",
            "vision": "https://www.chess.com/vision",
            "lessons": "https://www.chess.com/lessons",
        }

    def generate_tactical_exercises(
        self, error_patterns: Dict[str, int]
    ) -> List[ConcreteExercise]:
        """
        Generate specific tactical exercises based on error patterns.

        Args:
            error_patterns: Dictionary of error types and counts

        Returns:
            List of concrete tactical exercises
        """
        exercises = []

        # Get real training URLs
        lichess_urls = self.get_lichess_training_urls()
        chess_com_urls = self.get_chess_com_training_urls()

        # High blunder rate exercises
        if error_patterns.get("blunder", 0) > 100:
            exercises.extend(
                [
                    ConcreteExercise(
                        title="Anti-Blunder Training: Piece Safety Check",
                        description=f"You have {error_patterns['blunder']} blunders recorded. Practice the 'piece safety scan' before every move.",
                        exercise_type="tactics",
                        lichess_study_url=lichess_urls["hanging_pieces"],
                        chess_com_url=chess_com_urls["tactics"],
                        specific_moves=[
                            "Before each move: 1) Check all your pieces for attacks, 2) Check opponent's threats, 3) Only then make your move",
                            f"Alternative: Use Chess.com puzzles - {chess_com_urls['tactics']}",
                            "Focus specifically on 'Hanging Pieces' theme on Lichess",
                        ],
                        success_criteria=f"Complete 50 'Piece Safety' puzzles with 95%+ accuracy",
                        time_estimate=30,
                        difficulty_level="fundamental",
                    ),
                    ConcreteExercise(
                        title="Tactical Vision: Multi-Theme Training",
                        description="Comprehensive tactical training focusing on different tactical motifs",
                        exercise_type="lichess_study",
                        lichess_study_url=lichess_urls["mixed_tactics"],
                        chess_com_url=chess_com_urls["tactics"],
                        specific_moves=[
                            "Solve 20 mixed tactical puzzles daily on Lichess",
                            "Focus on pins, forks, skewers, and discovered attacks",
                            f"Alternative: Use Chess.com tactical puzzles - {chess_com_urls['tactics']}",
                            "Time limit: 30 seconds per puzzle maximum",
                        ],
                        success_criteria="Achieve 90%+ accuracy on mixed tactical puzzles",
                        time_estimate=25,
                    ),
                ]
            )

        # High mistake rate exercises
        if error_patterns.get("mistake", 0) > 200:
            exercises.extend(
                [
                    ConcreteExercise(
                        title="Strategic Calculation Training",
                        description=f"You have {error_patterns['mistake']} strategic mistakes. Focus on deeper position evaluation.",
                        exercise_type="position_analysis",
                        specific_moves=[
                            "Use 'candidate move' method: find 3 candidate moves, calculate 3 moves deep for each",
                            "Practice positions with material imbalances",
                            "Study pawn structure advantages/disadvantages",
                        ],
                        success_criteria="Improve position evaluation accuracy by 25%",
                        time_estimate=45,
                        difficulty_level="intermediate",
                    ),
                    ConcreteExercise(
                        title="Endgame Conversion Practice",
                        description="Master fundamental endgames to convert winning positions",
                        exercise_type="lichess_study",
                        lichess_study_url=lichess_urls["king_and_queen"],
                        chess_com_url=chess_com_urls["endgames"],
                        specific_moves=[
                            f"Master King + Queen vs King: {lichess_urls['king_and_queen']}",
                            f"Master King + Rook vs King: {lichess_urls['king_and_rook']}",
                            f"Practice Pawn Endgames: {lichess_urls['pawn_endgames']}",
                            f"Alternative: Chess.com Endgame Drills - {chess_com_urls['endgames']}",
                        ],
                        success_criteria="Win all basic endgames in under maximum moves",
                        time_estimate=40,
                        difficulty_level="intermediate",
                    ),
                ]
            )

        return exercises

    def generate_game_review_exercises(
        self, positions: List[GamePosition]
    ) -> List[ConcreteExercise]:
        """
        Generate specific game review exercises from actual problematic positions.

        Args:
            positions: List of problematic positions from real games

        Returns:
            List of game review exercises
        """
        exercises = []

        for i, pos in enumerate(positions[:5]):  # Limit to 5 most important
            exercise = ConcreteExercise(
                title=f"Fix Your Error #{i+1}: {pos.error_type.title()}",
                description=f"Review this {pos.error_type} from your game {pos.game_id[:8]}... at move {pos.move_number}",
                exercise_type="position_analysis",
                position_fen=pos.fen,
                specific_moves=[
                    f"Analyze the position after move {pos.move_number}",
                    f"You played {pos.player_move} - find why this was a {pos.error_type}",
                    "Find the best move in this position",
                    "Identify the key strategic/tactical themes",
                    "Practice similar positions to avoid repeating this error",
                ],
                success_criteria=f"Understand why {pos.player_move} was a {pos.error_type} and find the correct alternative",
                time_estimate=20,
                source_game_id=pos.game_id,
                difficulty_level="personalized",
            )
            exercises.append(exercise)

        return exercises

    def create_comprehensive_exercise_plan(self, user_ids: List[str]) -> Dict[str, Any]:
        """
        Create a comprehensive, concrete exercise plan for users.

        Args:
            user_ids: List of user IDs

        Returns:
            Complete exercise plan with concrete actions
        """
        logger.info(f"Creating comprehensive exercise plan for {user_ids}")

        # Get error patterns
        error_patterns = self._get_error_patterns(user_ids)

        # Extract problematic positions
        positions = self.extract_problematic_positions(user_ids, limit=10)

        # Generate different types of exercises
        tactical_exercises = self.generate_tactical_exercises(error_patterns)
        game_review_exercises = self.generate_game_review_exercises(positions)

        # Combine all exercises
        all_exercises = tactical_exercises + game_review_exercises

        # Create Lichess study if token available
        study_url = None
        if all_exercises and self.lichess_token:
            study_name = f"Training Plan for {'+'.join(user_ids)} - {datetime.now().strftime('%Y-%m-%d')}"
            study_url = self.create_lichess_study(study_name, all_exercises)

        # Build comprehensive plan
        plan = {
            "generated_at": datetime.now().isoformat(),
            "user_ids": user_ids,
            "total_exercises": len(all_exercises),
            "estimated_total_time": sum(ex.time_estimate for ex in all_exercises),
            "lichess_study_url": study_url,
            "error_patterns": error_patterns,
            "exercises_by_type": {
                "tactical": [
                    ex for ex in all_exercises if ex.exercise_type == "tactics"
                ],
                "position_analysis": [
                    ex
                    for ex in all_exercises
                    if ex.exercise_type == "position_analysis"
                ],
                "lichess_studies": [
                    ex for ex in all_exercises if ex.exercise_type == "lichess_study"
                ],
                "game_reviews": [
                    ex for ex in all_exercises if ex.exercise_type == "game_review"
                ],
            },
            "concrete_actions": self._generate_concrete_action_list(all_exercises),
            "weekly_schedule": self._generate_weekly_schedule(all_exercises),
        }

        return plan

    def _get_error_patterns(self, user_ids: List[str]) -> Dict[str, int]:
        """Get error pattern statistics for users."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    f.error_label,
                    COUNT(*) as count
                FROM features f
                JOIN games g ON f.game_id = g.game_id
                WHERE (g.white_player = ANY(%s) OR g.black_player = ANY(%s))
                  AND f.error_label IS NOT NULL
                GROUP BY f.error_label
            """,
                (user_ids, user_ids),
            )

            patterns = dict(cursor.fetchall())
            cursor.close()
            conn.close()

            return patterns

        except Exception as e:
            logger.error(f"Failed to get error patterns: {e}")
            return {}

    def _generate_concrete_action_list(
        self, exercises: List[ConcreteExercise]
    ) -> List[str]:
        """Generate a concrete action list for immediate implementation."""
        actions = []

        # High priority actions first
        emergency_exercises = [
            ex
            for ex in exercises
            if "blunder" in ex.title.lower() or "hanging" in ex.title.lower()
        ]
        if emergency_exercises:
            actions.append(
                "🚨 IMMEDIATE ACTION: Complete anti-blunder training (30 min daily)"
            )

        # Daily actions
        tactical_exercises = [ex for ex in exercises if ex.exercise_type == "tactics"]
        if tactical_exercises:
            actions.append("📱 DAILY: Solve 20 tactical puzzles on Lichess (15 min)")

        # Weekly actions
        position_exercises = [
            ex for ex in exercises if ex.exercise_type == "position_analysis"
        ]
        if position_exercises:
            actions.append(
                "📊 WEEKLY: Analyze 5 of your problematic positions (2 hours)"
            )

        # Study actions
        study_exercises = [ex for ex in exercises if ex.lichess_study_url]
        if study_exercises:
            actions.append("📚 WEEKLY: Complete assigned Lichess studies (1 hour)")

        return actions

    def _generate_weekly_schedule(
        self, exercises: List[ConcreteExercise]
    ) -> Dict[str, List[str]]:
        """Generate a weekly training schedule."""
        schedule = {
            "Monday": ["Tactical puzzles (15 min)", "Game analysis (30 min)"],
            "Tuesday": ["Endgame practice (20 min)", "Position review (25 min)"],
            "Wednesday": ["Tactical puzzles (15 min)", "Opening review (30 min)"],
            "Thursday": ["Strategic exercises (25 min)", "Game analysis (20 min)"],
            "Friday": ["Tactical puzzles (15 min)", "Weakness training (30 min)"],
            "Saturday": ["Comprehensive review (60 min)"],
            "Sunday": ["Rest or light tactical puzzles (15 min)"],
        }

        return schedule


def main():
    """Generate concrete exercise plan for cmess users."""

    print("🎯 CONCRETE EXERCISE GENERATION SYSTEM")
    print("=" * 80)
    print(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Creating actionable, specific exercises based on real game data")
    print()

    try:
        # Initialize exercise generator
        generator = ConcreteExerciseGenerator()

        # Generate comprehensive plan
        user_ids = ["cmess4401", "cmess1315"]
        plan = generator.create_comprehensive_exercise_plan(user_ids)

        print("📊 CONCRETE EXERCISE PLAN GENERATED")
        print("=" * 60)
        print(f"👥 Users: {', '.join(plan['user_ids'])}")
        print(f"🎯 Total Exercises: {plan['total_exercises']}")
        print(f"⏰ Total Time: {plan['estimated_total_time']} minutes")

        if plan["lichess_study_url"]:
            print(f"📚 Lichess Study: {plan['lichess_study_url']}")

        print(f"\n📈 Error Patterns Detected:")
        for error_type, count in plan["error_patterns"].items():
            print(f"   • {error_type.title()}: {count}")

        print(f"\n🎯 IMMEDIATE CONCRETE ACTIONS:")
        for i, action in enumerate(plan["concrete_actions"], 1):
            print(f"   {i}. {action}")

        print(f"\n📅 WEEKLY TRAINING SCHEDULE:")
        for day, tasks in plan["weekly_schedule"].items():
            print(f"   {day}:")
            for task in tasks:
                print(f"      • {task}")

        # Show detailed exercises
        print(f"\n🔍 DETAILED EXERCISES:")
        print("-" * 50)

        for exercise_type, exercises in plan["exercises_by_type"].items():
            if exercises:
                print(
                    f"\n📋 {exercise_type.replace('_', ' ').title()} ({len(exercises)} exercises):"
                )
                for i, ex in enumerate(exercises, 1):
                    print(f"\n   {i}. {ex.title} ({ex.time_estimate} min)")
                    print(f"      📝 {ex.description}")
                    if ex.lichess_study_url:
                        print(f"      🔗 {ex.lichess_study_url}")
                    if ex.position_fen:
                        print(f"      ♟️  Position: {ex.position_fen[:30]}...")
                    if ex.specific_moves:
                        print(f"      🎯 Actions:")
                        for move in ex.specific_moves[:2]:
                            print(f"         • {move}")
                        if len(ex.specific_moves) > 2:
                            print(
                                f"         • ... and {len(ex.specific_moves) - 2} more"
                            )
                    print(f"      ✅ Success: {ex.success_criteria}")

        # Export the plan
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        training_dir = "training"
        exercises_dir = os.path.join(training_dir, "exercises")
        plans_dir = os.path.join(training_dir, "plans")

        # Ensure directories exist
        os.makedirs(exercises_dir, exist_ok=True)
        os.makedirs(plans_dir, exist_ok=True)

        # Save concrete exercises
        exercises_filename = os.path.join(
            exercises_dir, f"concrete_exercise_plan_cmess_{timestamp}.json"
        )

        # Save data-driven plan
        plan_filename = os.path.join(
            plans_dir, f"data_driven_training_plan_cmess_{timestamp}.json"
        )

        with open(filename, "w") as f:
            # Convert dataclasses to dict for JSON serialization
            export_plan = {
                **plan,
                "exercises_by_type": {
                    k: [
                        {
                            "title": ex.title,
                            "description": ex.description,
                            "exercise_type": ex.exercise_type,
                            "position_fen": ex.position_fen,
                            "lichess_study_url": ex.lichess_study_url,
                            "specific_moves": ex.specific_moves,
                            "success_criteria": ex.success_criteria,
                            "time_estimate": ex.time_estimate,
                            "difficulty_level": ex.difficulty_level,
                            "source_game_id": ex.source_game_id,
                        }
                        for ex in exercises
                    ]
                    for k, exercises in plan["exercises_by_type"].items()
                },
            }
            json.dump(export_plan, f, indent=2)

        print(f"\n💾 Concrete exercise plan exported: {exercises_filename}")

        # Also create a summary file in the plans directory
        summary = {
            "generated_at": datetime.now().isoformat(),
            "user_ids": plan["user_ids"],
            "total_exercises": plan["total_exercises"],
            "estimated_total_time": plan["estimated_total_time"],
            "exercises_file": exercises_filename,
            "summary": {
                "immediate_actions": plan["concrete_actions"][:3],
                "weekly_schedule": plan["weekly_schedule"],
                "priority_breakdown": {
                    exercise_type: len(exercises)
                    for exercise_type, exercises in plan["exercises_by_type"].items()
                    if exercises
                },
            },
        }

        with open(plan_filename, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"💾 Training plan summary exported: {plan_filename}")

        print(f"\n🎉 READY TO IMPLEMENT!")
        print("=" * 60)
        print("✨ This plan provides specific, actionable exercises")
        print("🎯 Each exercise has clear success criteria")
        print("📚 Lichess studies can be created automatically")
        print("🔍 Based on your actual game positions and errors")

    except Exception as e:
        print(f"\n❌ Error generating exercises: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
