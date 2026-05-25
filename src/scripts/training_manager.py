"""
Training Resources Manager.

This module manages loading, organizing, and accessing training plans and exercises
from the training directory structure.

Key Features:
- Load training plans from organized directory structure
- Access concrete exercises by type and priority
- Generate training schedules and progress tracking
- Export training resources for different platforms

Directory Structure:
- training/plans/ - Training plan summaries and metadata
- training/exercises/ - Detailed exercise definitions and instructions
- training/resources/ - Additional training materials and links

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingResource:
    """Represents a training resource with metadata."""

    title: str
    resource_type: str  # 'exercise', 'plan', 'study', 'reference'
    url: str
    description: str
    difficulty: str
    estimated_time: int
    tags: List[str]
    created_at: str


class TrainingResourceManager:
    """
    Manages training resources from the organized directory structure.
    """

    def __init__(self, base_dir: str = "training"):
        """
        Initialize the training resource manager.

        Args:
            base_dir: Base directory for training resources
        """
        self.base_dir = base_dir
        self.plans_dir = os.path.join(base_dir, "plans")
        self.exercises_dir = os.path.join(base_dir, "exercises")
        self.resources_dir = os.path.join(base_dir, "resources")

        # Ensure directories exist
        os.makedirs(self.plans_dir, exist_ok=True)
        os.makedirs(self.exercises_dir, exist_ok=True)
        os.makedirs(self.resources_dir, exist_ok=True)

    def get_latest_exercise_plan(
        self, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent exercise plan.

        Args:
            user_id: Specific user ID to filter by (optional)

        Returns:
            Latest exercise plan data or None if not found
        """
        try:
            # Find all exercise files
            pattern = "concrete_exercise_plan*.json"
            if user_id:
                pattern = f"concrete_exercise_plan*{user_id}*.json"

            exercise_files = glob.glob(os.path.join(self.exercises_dir, pattern))

            if not exercise_files:
                logger.warning(f"No exercise files found matching pattern: {pattern}")
                return None

            # Get the most recent file
            latest_file = max(exercise_files, key=os.path.getctime)

            with open(latest_file, "r") as f:
                data = json.load(f)

            logger.info(f"Loaded latest exercise plan: {os.path.basename(latest_file)}")
            return data

        except Exception as e:
            logger.error(f"Failed to load latest exercise plan: {e}")
            return None

    def get_latest_training_plan(
        self, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent training plan summary.

        Args:
            user_id: Specific user ID to filter by (optional)

        Returns:
            Latest training plan summary or None if not found
        """
        try:
            # Find all plan files
            pattern = "*training_plan*.json"
            if user_id:
                pattern = f"*training_plan*{user_id}*.json"

            plan_files = glob.glob(os.path.join(self.plans_dir, pattern))

            if not plan_files:
                logger.warning(f"No plan files found matching pattern: {pattern}")
                return None

            # Get the most recent file
            latest_file = max(plan_files, key=os.path.getctime)

            with open(latest_file, "r") as f:
                data = json.load(f)

            logger.info(f"Loaded latest training plan: {os.path.basename(latest_file)}")
            return data

        except Exception as e:
            logger.error(f"Failed to load latest training plan: {e}")
            return None

    def get_exercises_by_type(
        self, exercise_type: str, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get exercises filtered by type.

        Args:
            exercise_type: Type of exercises ('tactical', 'position_analysis', etc.)
            user_id: Specific user ID to filter by (optional)

        Returns:
            List of exercises matching the type
        """
        exercise_plan = self.get_latest_exercise_plan(user_id)

        if not exercise_plan:
            return []

        exercises_by_type = exercise_plan.get("exercises_by_type", {})
        return exercises_by_type.get(exercise_type, [])

    def get_exercises_by_priority(
        self, min_time: int = 0, max_time: int = 180
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get exercises organized by time requirement.

        Args:
            min_time: Minimum time in minutes
            max_time: Maximum time in minutes

        Returns:
            Dictionary with exercises grouped by time ranges
        """
        exercise_plan = self.get_latest_exercise_plan()

        if not exercise_plan:
            return {}

        time_groups = {
            "quick": [],  # 0-20 minutes
            "medium": [],  # 21-45 minutes
            "extended": [],  # 46-90 minutes
            "intensive": [],  # 90+ minutes
        }

        for exercise_type, exercises in exercise_plan.get(
            "exercises_by_type", {}
        ).items():
            for exercise in exercises:
                time_est = exercise.get("time_estimate", 0)

                if time_est <= 20:
                    time_groups["quick"].append(exercise)
                elif time_est <= 45:
                    time_groups["medium"].append(exercise)
                elif time_est <= 90:
                    time_groups["extended"].append(exercise)
                else:
                    time_groups["intensive"].append(exercise)

        return time_groups

    def get_daily_training_schedule(self, available_time: int = 60) -> Dict[str, Any]:
        """
        Generate a daily training schedule based on available time.

        Args:
            available_time: Available time in minutes

        Returns:
            Daily training schedule with exercises
        """
        time_groups = self.get_exercises_by_priority()

        schedule = {
            "total_time": 0,
            "exercises": [],
            "breakdown": {"tactics": 0, "analysis": 0, "study": 0},
        }

        remaining_time = available_time

        # Prioritize based on available time
        if remaining_time >= 15:
            # Always include quick tactical training
            quick_exercises = time_groups.get("quick", [])
            if quick_exercises:
                tactical_exercise = next(
                    (
                        ex
                        for ex in quick_exercises
                        if "tactical" in ex.get("exercise_type", "")
                    ),
                    None,
                )
                if tactical_exercise:
                    schedule["exercises"].append(tactical_exercise)
                    schedule["total_time"] += tactical_exercise.get("time_estimate", 15)
                    schedule["breakdown"]["tactics"] += tactical_exercise.get(
                        "time_estimate", 15
                    )
                    remaining_time -= tactical_exercise.get("time_estimate", 15)

        if remaining_time >= 20:
            # Add medium exercises if time permits
            medium_exercises = time_groups.get("medium", [])
            if medium_exercises:
                analysis_exercise = next(
                    (
                        ex
                        for ex in medium_exercises
                        if "analysis" in ex.get("exercise_type", "")
                    ),
                    None,
                )
                if (
                    analysis_exercise
                    and analysis_exercise.get("time_estimate", 30) <= remaining_time
                ):
                    schedule["exercises"].append(analysis_exercise)
                    schedule["total_time"] += analysis_exercise.get("time_estimate", 30)
                    schedule["breakdown"]["analysis"] += analysis_exercise.get(
                        "time_estimate", 30
                    )
                    remaining_time -= analysis_exercise.get("time_estimate", 30)

        if remaining_time >= 15:
            # Add study exercises if still time available
            quick_studies = [
                ex
                for ex in time_groups.get("quick", [])
                if "study" in ex.get("exercise_type", "")
            ]
            if quick_studies:
                study_exercise = quick_studies[0]
                schedule["exercises"].append(study_exercise)
                schedule["total_time"] += study_exercise.get("time_estimate", 15)
                schedule["breakdown"]["study"] += study_exercise.get(
                    "time_estimate", 15
                )

        return schedule

    def export_training_resources(
        self, format_type: str = "lichess"
    ) -> Dict[str, List[str]]:
        """
        Export training resources in different formats.

        Args:
            format_type: Export format ('lichess', 'chess_com', 'pdf', 'markdown')

        Returns:
            Organized training resources for export
        """
        exercise_plan = self.get_latest_exercise_plan()

        if not exercise_plan:
            return {}

        resources = {
            "lichess_studies": [],
            "chess_com_links": [],
            "practice_positions": [],
            "reference_materials": [],
        }

        for exercise_type, exercises in exercise_plan.get(
            "exercises_by_type", {}
        ).items():
            for exercise in exercises:
                # Collect Lichess URLs
                lichess_url = exercise.get("lichess_study_url")
                if lichess_url:
                    resources["lichess_studies"].append(
                        {
                            "title": exercise.get("title", ""),
                            "url": lichess_url,
                            "description": exercise.get("description", ""),
                            "time_estimate": exercise.get("time_estimate", 0),
                        }
                    )

                # Collect Chess.com URLs
                chess_com_url = exercise.get("chess_com_url")
                if chess_com_url:
                    resources["chess_com_links"].append(
                        {
                            "title": exercise.get("title", ""),
                            "url": chess_com_url,
                            "description": exercise.get("description", ""),
                            "time_estimate": exercise.get("time_estimate", 0),
                        }
                    )

                # Collect practice positions
                position_fen = exercise.get("position_fen")
                if position_fen:
                    resources["practice_positions"].append(
                        {
                            "title": exercise.get("title", ""),
                            "fen": position_fen,
                            "description": exercise.get("description", ""),
                            "source_game": exercise.get("source_game_id", ""),
                        }
                    )

        return resources

    def get_training_progress_template(self) -> Dict[str, Any]:
        """
        Generate a training progress tracking template.

        Returns:
            Template for tracking training progress
        """
        exercise_plan = self.get_latest_exercise_plan()

        if not exercise_plan:
            return {}

        template = {
            "user_ids": exercise_plan.get("user_ids", []),
            "plan_generated": exercise_plan.get("generated_at", ""),
            "total_exercises": exercise_plan.get("total_exercises", 0),
            "estimated_total_time": exercise_plan.get("estimated_total_time", 0),
            "progress_tracking": {
                "completed_exercises": 0,
                "total_time_spent": 0,
                "current_week": 1,
                "exercises_by_status": {
                    "not_started": exercise_plan.get("total_exercises", 0),
                    "in_progress": 0,
                    "completed": 0,
                },
            },
            "weekly_goals": {},
            "performance_metrics": {
                "tactical_accuracy": 0.0,
                "problem_solving_speed": 0.0,
                "consistency_score": 0.0,
            },
        }

        return template


def main():
    """Demonstrate training resource management functionality."""

    print("📚 TRAINING RESOURCES MANAGER")
    print("=" * 60)
    print(f"Loading Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Initialize manager
        manager = TrainingResourceManager()

        # Load latest plans
        print("📋 LOADING LATEST TRAINING RESOURCES...")
        exercise_plan = manager.get_latest_exercise_plan()
        training_plan = manager.get_latest_training_plan()

        if exercise_plan:
            print(
                f"✅ Loaded exercise plan with {exercise_plan.get('total_exercises', 0)} exercises"
            )
            print(
                f"   Total estimated time: {exercise_plan.get('estimated_total_time', 0)} minutes"
            )

        if training_plan:
            print(
                f"✅ Loaded training plan for users: {', '.join(training_plan.get('user_ids', []))}"
            )

        # Show exercises by time requirements
        print(f"\n⏰ EXERCISES BY TIME REQUIREMENT:")
        time_groups = manager.get_exercises_by_priority()

        for time_group, exercises in time_groups.items():
            if exercises:
                total_time = sum(ex.get("time_estimate", 0) for ex in exercises)
                print(
                    f"   📊 {time_group.title()}: {len(exercises)} exercises ({total_time} min total)"
                )

        # Generate daily schedule
        print(f"\n📅 DAILY TRAINING SCHEDULE (60 min available):")
        daily_schedule = manager.get_daily_training_schedule(60)

        print(f"   Total planned time: {daily_schedule['total_time']} minutes")
        print(f"   Breakdown:")
        for category, time in daily_schedule["breakdown"].items():
            if time > 0:
                print(f"      • {category.title()}: {time} minutes")

        print(f"   Scheduled exercises:")
        for i, exercise in enumerate(daily_schedule["exercises"], 1):
            print(
                f"      {i}. {exercise.get('title', '')} ({exercise.get('time_estimate', 0)} min)"
            )

        # Export resources
        print(f"\n🔗 TRAINING RESOURCE LINKS:")
        resources = manager.export_training_resources()

        lichess_studies = resources.get("lichess_studies", [])
        if lichess_studies:
            print(f"   📚 Lichess Studies ({len(lichess_studies)}):")
            for study in lichess_studies[:3]:  # Show first 3
                print(f"      • {study['title']}: {study['url']}")
            if len(lichess_studies) > 3:
                print(f"      • ... and {len(lichess_studies) - 3} more")

        chess_com_links = resources.get("chess_com_links", [])
        if chess_com_links:
            print(f"   ♟️  Chess.com Links ({len(chess_com_links)}):")
            for link in chess_com_links[:2]:  # Show first 2
                print(f"      • {link['title']}: {link['url']}")

        # Save progress template
        progress_template = manager.get_training_progress_template()
        if progress_template:
            progress_file = os.path.join(manager.base_dir, "progress_template.json")
            with open(progress_file, "w") as f:
                json.dump(progress_template, f, indent=2)
            print(f"\n📊 Progress tracking template saved: {progress_file}")

        print(f"\n✨ Training resources are organized and ready!")
        print(f"📁 Directory structure:")
        print(f"   • {manager.plans_dir} - Training plan summaries")
        print(f"   • {manager.exercises_dir} - Detailed exercise definitions")
        print(f"   • {manager.resources_dir} - Additional materials")

    except Exception as e:
        print(f"\n❌ Error managing training resources: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
