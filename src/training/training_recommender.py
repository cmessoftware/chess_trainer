"""
Training Recommender with Survivorship Bias Integration.

This module provides personalized training recommendations based on user patterns
and critical survivorship bias alerts detected in the dataset.

Key Features:
- Integration with Survivorship Bias Analyzer
- Emergency plan generation for critical patterns
- Personalized recommendations based on user performance
- Opening-specific training suggestions

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from analysis.survivorship_bias import SurvivorshipBiasAnalyzer, CriticalityLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingPriority(Enum):
    """Enum for training priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


@dataclass
class TrainingRecommendation:
    """Data class for training recommendations."""

    priority: TrainingPriority
    category: str
    title: str
    description: str
    exercises: List[str]
    estimated_time: int  # minutes
    success_criteria: List[str]
    source: (
        str  # Where recommendation comes from (survivorship_bias, user_analysis, etc.)
    )


@dataclass
class UserProfile:
    """Data class for user profile information."""

    user_id: str
    skill_level: str  # beginner, intermediate, advanced
    preferred_openings: List[str]
    common_mistakes: List[str]
    time_available: int  # minutes per session
    focus_areas: List[str]  # opening, middlegame, endgame, tactics


class TrainingRecommender:
    """
    Core training recommendation system with survivorship bias integration.

    This system analyzes survivorship bias patterns and user data to generate
    personalized training recommendations with emergency protocols for critical issues.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the Training Recommender.

        Args:
            db_url: Database URL for survivorship bias analysis
        """
        self.survivorship_analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)
        self.emergency_patterns = {}
        self.global_recommendations = []

    def analyze_survivorship_patterns(
        self, source_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze survivorship bias patterns to identify critical training needs.

        Args:
            source_filter: Optional data source filter

        Returns:
            Analysis results with emergency patterns and recommendations
        """
        logger.info(
            "Analyzing survivorship bias patterns for training recommendations..."
        )

        results = self.survivorship_analyzer.analyze_dataset(
            source_filter=source_filter
        )

        # Extract critical patterns for emergency training
        critical_alerts = [
            alert
            for alert in results.get("alerts", [])
            if alert.get("criticality") == "CRITICAL"
        ]

        self.emergency_patterns = {
            "critical_alerts": critical_alerts,
            "emergency_plan": results.get("emergency_plan", {}),
            "survival_rates": results.get("opening_survival", {}),
        }

        logger.info(
            f"Detected {len(critical_alerts)} critical patterns requiring emergency training"
        )
        return results

    def generate_emergency_recommendations(self) -> List[TrainingRecommendation]:
        """
        Generate emergency training recommendations based on critical survivorship patterns.

        Returns:
            List of emergency training recommendations
        """
        recommendations = []

        for alert in self.emergency_patterns.get("critical_alerts", []):
            pattern_type = alert.get("pattern_type", "")
            description = alert.get("description", "")

            if pattern_type == "early_defeat":
                opening = alert.get("additional_data", {}).get("opening", "Unknown")
                rec = TrainingRecommendation(
                    priority=TrainingPriority.EMERGENCY,
                    category="Opening Survival",
                    title=f"Emergency Training: {opening}",
                    description=f"Critical survival issue detected: {description}",
                    exercises=[
                        f"Study defensive structures in {opening}",
                        f"Practice 20 games with {opening} focusing on move 5-15",
                        f"Analyze grandmaster games in {opening}",
                        "Complete tactical puzzles related to this opening",
                    ],
                    estimated_time=90,
                    success_criteria=[
                        f"Improve survival rate in {opening} above 50%",
                        "Complete 10 games lasting more than 20 moves",
                        "Identify key defensive moves in opening phase",
                    ],
                    source="survivorship_bias_emergency",
                )
                recommendations.append(rec)

            elif pattern_type == "catastrophic_blunders":
                rec = TrainingRecommendation(
                    priority=TrainingPriority.EMERGENCY,
                    category="Error Prevention",
                    title="Emergency Blunder Prevention Training",
                    description=f"Critical blunder pattern detected: {description}",
                    exercises=[
                        "Complete 50 tactical puzzles daily",
                        "Practice slow time control games (30+ minutes)",
                        "Review recent games for blunder patterns",
                        "Study candidate move analysis techniques",
                    ],
                    estimated_time=120,
                    success_criteria=[
                        "Reduce average blunders per game by 50%",
                        "Complete tactical trainer with 85% accuracy",
                        "Play 5 games with zero blunders",
                    ],
                    source="survivorship_bias_blunder",
                )
                recommendations.append(rec)

            elif pattern_type == "low_survival":
                opening = alert.get("additional_data", {}).get(
                    "opening", "Multiple Openings"
                )
                survival_rate = alert.get("additional_data", {}).get("survival_rate", 0)
                rec = TrainingRecommendation(
                    priority=TrainingPriority.HIGH,
                    category="Opening Defense",
                    title=f"Survival Training: {opening}",
                    description=f"Low survival rate ({survival_rate:.1%}) requires immediate attention",
                    exercises=[
                        f"Study key defensive ideas in {opening}",
                        "Practice endgames arising from this opening",
                        "Learn typical pawn structures and plans",
                        "Review common tactical motifs",
                    ],
                    estimated_time=75,
                    success_criteria=[
                        f"Achieve survival rate above 70% in {opening}",
                        "Understand key defensive setups",
                        "Complete opening-specific puzzle sets",
                    ],
                    source="survivorship_bias_survival",
                )
                recommendations.append(rec)

        logger.info(f"Generated {len(recommendations)} emergency recommendations")
        return recommendations

    def generate_user_recommendations(
        self, user_profile: UserProfile, include_emergency: bool = True
    ) -> List[TrainingRecommendation]:
        """
        Generate personalized training recommendations for a specific user.

        Args:
            user_profile: User's profile and preferences
            include_emergency: Whether to include emergency recommendations

        Returns:
            Personalized list of training recommendations
        """
        logger.info(f"Generating recommendations for user {user_profile.user_id}")

        recommendations = []

        # Add emergency recommendations first if enabled
        if include_emergency:
            emergency_recs = self.generate_emergency_recommendations()

            # Filter emergency recommendations by user skill level and time
            for rec in emergency_recs:
                if (
                    rec.estimated_time <= user_profile.time_available * 1.5
                ):  # Allow 50% overtime for emergencies
                    recommendations.append(rec)

        # Generate user-specific recommendations
        user_recs = self._generate_personalized_recommendations(user_profile)
        recommendations.extend(user_recs)

        # Sort by priority
        priority_order = {
            TrainingPriority.EMERGENCY: 0,
            TrainingPriority.HIGH: 1,
            TrainingPriority.MEDIUM: 2,
            TrainingPriority.LOW: 3,
        }

        recommendations.sort(key=lambda x: priority_order[x.priority])

        logger.info(f"Generated {len(recommendations)} total recommendations for user")
        return recommendations

    def _generate_personalized_recommendations(
        self, user_profile: UserProfile
    ) -> List[TrainingRecommendation]:
        """Generate recommendations based on user profile."""
        recommendations = []

        # Opening recommendations based on user preferences
        for opening in user_profile.preferred_openings:
            survival_rate = self.emergency_patterns.get("survival_rates", {}).get(
                opening, 1.0
            )

            if survival_rate < 0.7:  # Below 70% survival rate
                rec = TrainingRecommendation(
                    priority=TrainingPriority.HIGH,
                    category="Opening Improvement",
                    title=f"Improve {opening} Performance",
                    description=f"Your preferred opening {opening} has survival challenges",
                    exercises=[
                        f"Study {opening} masterclass videos",
                        f"Practice {opening} with computer analysis",
                        "Learn key defensive plans",
                        "Study typical middlegame structures",
                    ],
                    estimated_time=min(60, user_profile.time_available),
                    success_criteria=[
                        f"Improve win rate in {opening} by 15%",
                        "Learn 3 new defensive setups",
                        "Complete opening quiz with 90% accuracy",
                    ],
                    source="user_profile_opening",
                )
                recommendations.append(rec)

        # Skill level appropriate recommendations
        if user_profile.skill_level == "beginner":
            recommendations.extend(
                self._generate_beginner_recommendations(user_profile)
            )
        elif user_profile.skill_level == "intermediate":
            recommendations.extend(
                self._generate_intermediate_recommendations(user_profile)
            )
        elif user_profile.skill_level == "advanced":
            recommendations.extend(
                self._generate_advanced_recommendations(user_profile)
            )

        return recommendations

    def _generate_beginner_recommendations(
        self, user_profile: UserProfile
    ) -> List[TrainingRecommendation]:
        """Generate beginner-specific recommendations."""
        return [
            TrainingRecommendation(
                priority=TrainingPriority.MEDIUM,
                category="Fundamentals",
                title="Chess Fundamentals Mastery",
                description="Build solid foundation in chess basics",
                exercises=[
                    "Complete basic tactics puzzles (50 per day)",
                    "Learn piece values and exchange principles",
                    "Practice basic endgames (K+Q vs K, K+R vs K)",
                    "Study opening principles (development, control center, king safety)",
                ],
                estimated_time=min(45, user_profile.time_available),
                success_criteria=[
                    "Solve basic tactics with 90% accuracy",
                    "Demonstrate understanding of piece values",
                    "Win basic endgame positions consistently",
                ],
                source="beginner_fundamentals",
            )
        ]

    def _generate_intermediate_recommendations(
        self, user_profile: UserProfile
    ) -> List[TrainingRecommendation]:
        """Generate intermediate-specific recommendations."""
        return [
            TrainingRecommendation(
                priority=TrainingPriority.MEDIUM,
                category="Strategic Improvement",
                title="Positional Understanding Development",
                description="Advance your positional chess skills",
                exercises=[
                    "Study pawn structures and their characteristics",
                    "Practice piece coordination exercises",
                    "Analyze annotated grandmaster games",
                    "Complete intermediate tactical combinations",
                ],
                estimated_time=min(60, user_profile.time_available),
                success_criteria=[
                    "Identify key pawn structures in your games",
                    "Improve piece coordination scores by 20%",
                    "Complete positional assessment tests",
                ],
                source="intermediate_strategy",
            )
        ]

    def _generate_advanced_recommendations(
        self, user_profile: UserProfile
    ) -> List[TrainingRecommendation]:
        """Generate advanced-specific recommendations."""
        return [
            TrainingRecommendation(
                priority=TrainingPriority.MEDIUM,
                category="Advanced Concepts",
                title="Deep Strategic Mastery",
                description="Refine your advanced chess understanding",
                exercises=[
                    "Study complex endgame positions",
                    "Analyze dynamic imbalances in positions",
                    "Practice deep calculation exercises",
                    "Study opening novelties in your repertoire",
                ],
                estimated_time=min(75, user_profile.time_available),
                success_criteria=[
                    "Solve complex endgames accurately",
                    "Demonstrate advanced positional judgment",
                    "Calculate 5+ moves deep consistently",
                ],
                source="advanced_mastery",
            )
        ]

    def export_training_plan(
        self, recommendations: List[TrainingRecommendation], file_path: str
    ) -> bool:
        """
        Export training plan to JSON file.

        Args:
            recommendations: List of recommendations to export
            file_path: Output file path

        Returns:
            Success status
        """
        try:
            import json
            from datetime import datetime

            plan = {
                "generated_at": datetime.now().isoformat(),
                "total_recommendations": len(recommendations),
                "emergency_count": len(
                    [
                        r
                        for r in recommendations
                        if r.priority == TrainingPriority.EMERGENCY
                    ]
                ),
                "estimated_total_time": sum(r.estimated_time for r in recommendations),
                "recommendations": [
                    {
                        "priority": rec.priority.value,
                        "category": rec.category,
                        "title": rec.title,
                        "description": rec.description,
                        "exercises": rec.exercises,
                        "estimated_time": rec.estimated_time,
                        "success_criteria": rec.success_criteria,
                        "source": rec.source,
                    }
                    for rec in recommendations
                ],
            }

            with open(file_path, "w") as f:
                json.dump(plan, f, indent=2)

            logger.info(f"Training plan exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export training plan: {e}")
            return False

    def get_emergency_status(self) -> Dict[str, Any]:
        """
        Get current emergency status for immediate attention items.

        Returns:
            Emergency status information
        """
        critical_count = len(self.emergency_patterns.get("critical_alerts", []))

        return {
            "has_emergency": critical_count > 0,
            "critical_patterns": critical_count,
            "requires_immediate_action": critical_count > 0,
            "emergency_plan_available": bool(
                self.emergency_patterns.get("emergency_plan")
            ),
            "status": (
                "EMERGENCY"
                if critical_count > 2
                else "HIGH" if critical_count > 0 else "NORMAL"
            ),
        }
