"""
Quick Training Access Tool.

Provides quick command-line access to training resources and daily schedules.
This tool allows users to quickly access their personalized training plans
without running the full management system.

Usage:
    python quick_training.py [command] [options]

Commands:
    today [minutes]     - Get today's training schedule (default: 60 minutes)
    exercises [type]    - List exercises by type (tactical, analysis, study)
    links              - Show all training resource links
    progress           - Show training progress template
    user [user_id]     - Get resources for specific user

Examples:
    python quick_training.py today 30      # 30-minute training session
    python quick_training.py exercises tactical
    python quick_training.py links
    python quick_training.py user cmess4401

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import sys
import json
from datetime import datetime
from training_manager import TrainingResourceManager


def print_header(title):
    """Print a formatted header."""
    print(f"\n♟️  {title}")
    print("=" * (len(title) + 4))


def print_exercise(exercise, index=None):
    """Print a formatted exercise."""
    prefix = f"{index}. " if index else "• "
    title = exercise.get("title", "Unnamed Exercise")
    time_est = exercise.get("time_estimate", 0)
    description = exercise.get("description", "")

    print(f"{prefix}{title} ({time_est} min)")
    if description:
        print(f"   {description[:80]}{'...' if len(description) > 80 else ''}")

    # Show links if available
    lichess_url = exercise.get("lichess_study_url")
    chess_com_url = exercise.get("chess_com_url")

    if lichess_url:
        print(f"   🔗 Lichess: {lichess_url}")
    if chess_com_url:
        print(f"   🔗 Chess.com: {chess_com_url}")


def cmd_today(args):
    """Show today's training schedule."""
    available_time = int(args[0]) if args else 60

    print_header(f"TODAY'S TRAINING SCHEDULE ({available_time} minutes available)")

    manager = TrainingResourceManager()
    schedule = manager.get_daily_training_schedule(available_time)

    if not schedule["exercises"]:
        print("⚠️  No exercises scheduled. Try with more available time.")
        return

    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"⏱️  Total planned time: {schedule['total_time']} minutes")
    print(f"📋 Number of exercises: {len(schedule['exercises'])}")

    if schedule["breakdown"]:
        print("\n📊 Time breakdown:")
        for category, time in schedule["breakdown"].items():
            if time > 0:
                print(f"   {category.title()}: {time} minutes")

    print("\n🏋️‍♂️ Scheduled exercises:")
    for i, exercise in enumerate(schedule["exercises"], 1):
        print_exercise(exercise, i)

    remaining = available_time - schedule["total_time"]
    if remaining > 0:
        print(f"\n⏳ Remaining time: {remaining} minutes (available for free practice)")


def cmd_exercises(args):
    """List exercises by type."""
    exercise_type = args[0] if args else None

    manager = TrainingResourceManager()

    if exercise_type:
        print_header(f"EXERCISES: {exercise_type.upper()}")
        exercises = manager.get_exercises_by_type(exercise_type)

        if not exercises:
            print(f"❌ No exercises found for type: {exercise_type}")
            print("Available types: tactical, position_analysis, calculation, endgame")
            return

        for i, exercise in enumerate(exercises, 1):
            print_exercise(exercise, i)
            print()
    else:
        print_header("EXERCISES BY TIME REQUIREMENT")
        time_groups = manager.get_exercises_by_priority()

        for time_group, exercises in time_groups.items():
            if exercises:
                total_time = sum(ex.get("time_estimate", 0) for ex in exercises)
                print(
                    f"\n📊 {time_group.title()} ({len(exercises)} exercises, {total_time} min total):"
                )

                for exercise in exercises:
                    print_exercise(exercise)


def cmd_links(args):
    """Show all training resource links."""
    print_header("TRAINING RESOURCE LINKS")

    manager = TrainingResourceManager()
    resources = manager.export_training_resources()

    lichess_studies = resources.get("lichess_studies", [])
    if lichess_studies:
        print(f"\n📚 LICHESS STUDIES ({len(lichess_studies)}):")
        for i, study in enumerate(lichess_studies, 1):
            print(f"{i}. {study['title']} ({study['time_estimate']} min)")
            print(f"   🔗 {study['url']}")
            print(f"   📖 {study['description'][:60]}...")
            print()

    chess_com_links = resources.get("chess_com_links", [])
    if chess_com_links:
        print(f"\n♟️  CHESS.COM RESOURCES ({len(chess_com_links)}):")
        for i, link in enumerate(chess_com_links, 1):
            print(f"{i}. {link['title']} ({link['time_estimate']} min)")
            print(f"   🔗 {link['url']}")
            print(f"   📖 {link['description'][:60]}...")
            print()

    practice_positions = resources.get("practice_positions", [])
    if practice_positions:
        print(f"\n🎯 PRACTICE POSITIONS ({len(practice_positions)}):")
        for i, position in enumerate(practice_positions[:5], 1):  # Show first 5
            print(f"{i}. {position['title']}")
            print(f"   📍 FEN: {position['fen'][:40]}...")
            if position.get("source_game"):
                print(f"   🎮 Source: Game {position['source_game']}")
            print()


def cmd_progress(args):
    """Show training progress template."""
    print_header("TRAINING PROGRESS TRACKING")

    manager = TrainingResourceManager()
    progress = manager.get_training_progress_template()

    if not progress:
        print("❌ No training progress template available")
        return

    print(f"👥 Users: {', '.join(progress.get('user_ids', []))}")
    print(f"📅 Plan generated: {progress.get('plan_generated', 'Unknown')}")
    print(f"📋 Total exercises: {progress.get('total_exercises', 0)}")
    print(f"⏱️  Estimated total time: {progress.get('estimated_total_time', 0)} minutes")

    tracking = progress.get("progress_tracking", {})
    if tracking:
        print(f"\n📊 Current progress:")
        print(f"   Completed: {tracking.get('completed_exercises', 0)}")
        print(f"   Time spent: {tracking.get('total_time_spent', 0)} minutes")
        print(f"   Current week: {tracking.get('current_week', 1)}")

        by_status = tracking.get("exercises_by_status", {})
        print(f"\n📈 Exercise status breakdown:")
        for status, count in by_status.items():
            print(f"   {status.replace('_', ' ').title()}: {count}")


def cmd_user(args):
    """Get resources for specific user."""
    if not args:
        print("❌ Please specify a user ID")
        return

    user_id = args[0]
    print_header(f"TRAINING RESOURCES FOR USER: {user_id}")

    manager = TrainingResourceManager()

    # Try to load user-specific resources
    exercise_plan = manager.get_latest_exercise_plan(user_id)
    training_plan = manager.get_latest_training_plan(user_id)

    if exercise_plan:
        print(f"✅ Found exercise plan for {user_id}")
        print(f"   Total exercises: {exercise_plan.get('total_exercises', 0)}")
        print(
            f"   Estimated time: {exercise_plan.get('estimated_total_time', 0)} minutes"
        )
        print(f"   Generated: {exercise_plan.get('generated_at', 'Unknown')}")
    else:
        print(f"⚠️  No specific exercise plan found for {user_id}")

    if training_plan:
        print(f"✅ Found training plan for {user_id}")
        users = training_plan.get("user_ids", [])
        if user_id in users:
            print(f"   User is included in plan with: {', '.join(users)}")
        else:
            print(f"   User may be referenced in plan")
    else:
        print(f"⚠️  No specific training plan found for {user_id}")

    # Show a sample daily schedule
    print(f"\n📅 Sample daily schedule (45 minutes):")
    schedule = manager.get_daily_training_schedule(45)
    for i, exercise in enumerate(schedule["exercises"][:2], 1):
        print_exercise(exercise, i)


def show_help():
    """Show help information."""
    print_header("QUICK TRAINING ACCESS TOOL")
    print(
        """
Available commands:

📅 today [minutes]     - Get today's training schedule
                        Default: 60 minutes
                        Example: today 30

🏋️‍♂️ exercises [type]   - List exercises by type
                        Types: tactical, position_analysis, calculation, endgame
                        Example: exercises tactical

🔗 links              - Show all training resource links
                        Includes Lichess studies, Chess.com resources

📊 progress           - Show training progress template
                        Current status and tracking information

👤 user [user_id]     - Get resources for specific user
                        Example: user cmess4401

❓ help               - Show this help information

Examples:
    python quick_training.py today 30
    python quick_training.py exercises tactical
    python quick_training.py links
    python quick_training.py user cmess4401
    """
    )


def main():
    """Main entry point for quick training access."""

    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]  # Additional arguments

    try:
        if command in ["today", "schedule"]:
            cmd_today(args)
        elif command in ["exercises", "ex"]:
            cmd_exercises(args)
        elif command in ["links", "resources"]:
            cmd_links(args)
        elif command in ["progress", "status"]:
            cmd_progress(args)
        elif command in ["user", "u"]:
            cmd_user(args)
        elif command in ["help", "h", "--help", "-h"]:
            show_help()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python quick_training.py help' for available commands")

    except Exception as e:
        print(f"❌ Error executing command '{command}': {e}")
        print("Use 'python quick_training.py help' for available commands")


if __name__ == "__main__":
    main()
