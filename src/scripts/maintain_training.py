"""
Training System Maintenance and Updates.

This script handles maintenance tasks for the training resource system:
- Clean up old training files
- Validate resource links
- Update exercise recommendations based on new data
- Generate maintenance reports
- Archive completed training plans

Usage:
    python maintain_training.py [action]

Actions:
    cleanup     - Remove old training files
    validate    - Check all resource links
    update      - Update recommendations based on new data
    report      - Generate maintenance report
    archive     - Archive completed plans
    all         - Run all maintenance tasks

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import sys
import json
import glob
import requests
from datetime import datetime, timedelta
from pathlib import Path
import shutil


def print_status(message, level="INFO"):
    """Print a status message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(
        level, "📋"
    )
    print(f"{icon} [{timestamp}] {message}")


def cleanup_old_files(max_age_days=7):
    """Clean up training files older than specified days."""
    print_status("Starting cleanup of old training files...")

    training_dirs = ["training/exercises", "training/plans", "training/resources"]
    cleaned_count = 0

    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    for directory in training_dirs:
        if not os.path.exists(directory):
            continue

        json_files = glob.glob(f"{directory}/*.json")

        for file_path in json_files:
            try:
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))

                if file_time < cutoff_date:
                    # Archive before deletion
                    archive_dir = f"{directory}/archived"
                    os.makedirs(archive_dir, exist_ok=True)

                    archive_path = os.path.join(
                        archive_dir, os.path.basename(file_path)
                    )
                    shutil.move(file_path, archive_path)

                    print_status(f"Archived old file: {os.path.basename(file_path)}")
                    cleaned_count += 1

            except Exception as e:
                print_status(f"Error processing {file_path}: {e}", "WARNING")

    print_status(f"Cleanup completed. {cleaned_count} files archived.", "SUCCESS")
    return cleaned_count


def validate_resource_links():
    """Validate all resource links in training plans."""
    print_status("Validating resource links...")

    from training_manager import TrainingResourceManager

    manager = TrainingResourceManager()

    resources = manager.export_training_resources()

    valid_links = 0
    invalid_links = 0
    checked_links = []

    # Check Lichess studies
    for study in resources.get("lichess_studies", []):
        url = study["url"]
        if url not in checked_links:
            checked_links.append(url)
            if validate_url(url):
                valid_links += 1
                print_status(f"✓ Valid: {url}")
            else:
                invalid_links += 1
                print_status(f"✗ Invalid: {url}", "WARNING")

    # Check Chess.com links
    for link in resources.get("chess_com_links", []):
        url = link["url"]
        if url not in checked_links:
            checked_links.append(url)
            if validate_url(url):
                valid_links += 1
                print_status(f"✓ Valid: {url}")
            else:
                invalid_links += 1
                print_status(f"✗ Invalid: {url}", "WARNING")

    print_status(
        f"Link validation completed. {valid_links} valid, {invalid_links} invalid.",
        "SUCCESS",
    )
    return {"valid": valid_links, "invalid": invalid_links}


def validate_url(url, timeout=5):
    """Validate a single URL."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False


def update_recommendations():
    """Update exercise recommendations based on new data."""
    print_status("Updating exercise recommendations...")

    try:
        # Import required modules
        sys.path.append("src/scripts")
        from generate_concrete_exercises import main as generate_exercises
        from generate_real_user_analysis import main as generate_analysis

        print_status("Generating new user analysis...")
        generate_analysis()

        print_status("Generating updated exercises...")
        generate_exercises()

        print_status("Recommendations updated successfully.", "SUCCESS")
        return True

    except Exception as e:
        print_status(f"Error updating recommendations: {e}", "ERROR")
        return False


def generate_maintenance_report():
    """Generate a comprehensive maintenance report."""
    print_status("Generating maintenance report...")

    report = {
        "generated_at": datetime.now().isoformat(),
        "system_status": {},
        "file_counts": {},
        "resource_validation": {},
        "disk_usage": {},
        "recommendations": [],
    }

    # Count files in each directory
    training_dirs = ["training/exercises", "training/plans", "training/resources"]

    for directory in training_dirs:
        if os.path.exists(directory):
            json_files = len(glob.glob(f"{directory}/*.json"))
            all_files = len(glob.glob(f"{directory}/*"))
            report["file_counts"][directory] = {
                "json_files": json_files,
                "total_files": all_files,
            }
        else:
            report["file_counts"][directory] = {"json_files": 0, "total_files": 0}

    # Check system status
    from training_manager import TrainingResourceManager

    manager = TrainingResourceManager()

    try:
        exercise_plan = manager.get_latest_exercise_plan()
        training_plan = manager.get_latest_training_plan()

        report["system_status"]["latest_exercise_plan"] = bool(exercise_plan)
        report["system_status"]["latest_training_plan"] = bool(training_plan)

        if exercise_plan:
            report["system_status"]["total_exercises"] = exercise_plan.get(
                "total_exercises", 0
            )
            report["system_status"]["estimated_total_time"] = exercise_plan.get(
                "estimated_total_time", 0
            )

    except Exception as e:
        report["system_status"]["error"] = str(e)

    # Validate resources
    try:
        validation_result = validate_resource_links()
        report["resource_validation"] = validation_result
    except Exception as e:
        report["resource_validation"]["error"] = str(e)

    # Calculate disk usage
    try:
        total_size = 0
        for directory in training_dirs:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        total_size += os.path.getsize(os.path.join(root, file))

        report["disk_usage"]["total_bytes"] = total_size
        report["disk_usage"]["total_mb"] = round(total_size / (1024 * 1024), 2)
    except Exception as e:
        report["disk_usage"]["error"] = str(e)

    # Generate recommendations
    if report["file_counts"]["training/exercises"]["json_files"] == 0:
        report["recommendations"].append(
            "No exercise files found. Run generate_concrete_exercises.py"
        )

    if report["file_counts"]["training/plans"]["json_files"] == 0:
        report["recommendations"].append(
            "No training plans found. Run generate_real_user_analysis.py"
        )

    if report.get("resource_validation", {}).get("invalid", 0) > 0:
        report["recommendations"].append(
            "Some resource links are invalid. Check and update URLs"
        )

    # Save report
    report_path = (
        f"training/maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print_status(f"Maintenance report saved: {report_path}", "SUCCESS")

    # Print summary
    print_status("MAINTENANCE REPORT SUMMARY", "INFO")
    print(
        f"   📊 Total exercises: {report['system_status'].get('total_exercises', 'Unknown')}"
    )
    print(
        f"   📁 Exercise files: {report['file_counts']['training/exercises']['json_files']}"
    )
    print(f"   📁 Plan files: {report['file_counts']['training/plans']['json_files']}")
    print(f"   💾 Disk usage: {report['disk_usage'].get('total_mb', 'Unknown')} MB")
    print(f"   🔗 Valid links: {report['resource_validation'].get('valid', 'Unknown')}")
    print(
        f"   ⚠️  Invalid links: {report['resource_validation'].get('invalid', 'Unknown')}"
    )

    if report["recommendations"]:
        print(f"   💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"      • {rec}")

    return report


def archive_completed_plans():
    """Archive completed training plans."""
    print_status("Archiving completed training plans...")

    # This would integrate with actual progress tracking
    # For now, we'll just organize files by age

    archive_dir = "training/archived"
    os.makedirs(archive_dir, exist_ok=True)

    archived_count = 0

    # Archive plans older than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)

    for plan_file in glob.glob("training/plans/*.json"):
        try:
            file_time = datetime.fromtimestamp(os.path.getctime(plan_file))

            if file_time < cutoff_date:
                archive_path = os.path.join(archive_dir, os.path.basename(plan_file))
                shutil.move(plan_file, archive_path)
                archived_count += 1
                print_status(f"Archived plan: {os.path.basename(plan_file)}")

        except Exception as e:
            print_status(f"Error archiving {plan_file}: {e}", "WARNING")

    print_status(f"Archival completed. {archived_count} plans archived.", "SUCCESS")
    return archived_count


def show_help():
    """Show help information."""
    print(
        """
🔧 TRAINING SYSTEM MAINTENANCE

Available actions:

cleanup     - Remove old training files (>7 days) by moving to archive
validate    - Check all resource links for accessibility
update      - Update recommendations based on new data
report      - Generate comprehensive maintenance report
archive     - Archive completed training plans (>30 days)
all         - Run all maintenance tasks

Usage:
    python maintain_training.py [action]

Examples:
    python maintain_training.py cleanup
    python maintain_training.py validate
    python maintain_training.py report
    python maintain_training.py all
    """
    )


def main():
    """Main entry point for training system maintenance."""

    if len(sys.argv) < 2:
        show_help()
        return

    action = sys.argv[1].lower()

    print_status("🔧 TRAINING SYSTEM MAINTENANCE STARTED")

    try:
        if action == "cleanup":
            cleanup_old_files()

        elif action == "validate":
            validate_resource_links()

        elif action == "update":
            update_recommendations()

        elif action == "report":
            generate_maintenance_report()

        elif action == "archive":
            archive_completed_plans()

        elif action == "all":
            print_status("Running all maintenance tasks...")
            cleanup_old_files()
            validate_resource_links()
            update_recommendations()
            generate_maintenance_report()
            archive_completed_plans()
            print_status("All maintenance tasks completed.", "SUCCESS")

        elif action in ["help", "-h", "--help"]:
            show_help()

        else:
            print_status(f"Unknown action: {action}", "ERROR")
            show_help()

    except Exception as e:
        print_status(f"Error during maintenance: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
