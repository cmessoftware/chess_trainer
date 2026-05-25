"""
Training module for the Chess Trainer ML Pipeline.

This module provides comprehensive training recommendations and planning
capabilities, including integration with survivorship bias analysis
for emergency training protocols.

Key Components:
- TrainingRecommender: Core recommendation system
- SurvivorshipBias Integration: Critical pattern detection
- Personalized Training Plans: User-specific recommendations
- Emergency Protocols: Critical issue response

Usage:
    from training.training_recommender import TrainingRecommender

    recommender = TrainingRecommender()
    recommendations = recommender.generate_user_recommendations(user_profile)

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

from .training_recommender import (
    TrainingRecommender,
    TrainingRecommendation,
    TrainingPriority,
    UserProfile,
)

__all__ = [
    "TrainingRecommender",
    "TrainingRecommendation",
    "TrainingPriority",
    "UserProfile",
]
