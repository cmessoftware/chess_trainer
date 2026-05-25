"""
Data-Driven User Analysis and Recommendation System.

This module analyzes real game data from the database to generate
specific, actionable training recommendations based on actual
performance patterns and weaknesses.

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import psycopg2
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from training.training_recommender import (
    TrainingRecommender,
    TrainingRecommendation,
    TrainingPriority,
    UserProfile,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserGameStats:
    """Real game statistics for a user."""

    user_id: str
    total_games: int
    win_rate: float
    wins_as_white: int
    wins_as_black: int
    draws: int
    losses: int
    total_features: int
    blunders: int
    mistakes: int
    inaccuracies: int

    @property
    def error_rate(self) -> float:
        """Calculate overall error rate."""
        if self.total_features == 0:
            return 0.0
        return (
            (self.blunders + self.mistakes + self.inaccuracies)
            / self.total_features
            * 100
        )

    @property
    def blunder_rate(self) -> float:
        """Calculate blunder rate per game."""
        if self.total_games == 0:
            return 0.0
        return self.blunders / self.total_games

    @property
    def color_preference_issue(self) -> bool:
        """Detect if there's a significant color preference issue."""
        if self.total_games < 50:  # Not enough data
            return False

        white_rate = (
            self.wins_as_white / (self.total_games * 0.5) if self.total_games > 0 else 0
        )
        black_rate = (
            self.wins_as_black / (self.total_games * 0.5) if self.total_games > 0 else 0
        )

        # If one color performance is significantly worse
        return abs(white_rate - black_rate) > 0.2


class DataDrivenRecommender:
    """
    Advanced recommendation system based on real user data analysis.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize with database connection."""
        self.db_url = db_url or os.environ.get(
            "CHESS_TRAINER_DB_URL",
            "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db",
        )
        self.base_recommender = TrainingRecommender(db_url)

    def get_user_stats(self, user_ids: List[str]) -> UserGameStats:
        """
        Get comprehensive statistics for user(s) from database.

        Args:
            user_ids: List of user IDs (treating as same player)

        Returns:
            UserGameStats object with real performance data
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Get basic game statistics
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_games,
                    COUNT(CASE WHEN g.result = '1-0' AND g.white_player = ANY(%s) THEN 1 END) as wins_as_white,
                    COUNT(CASE WHEN g.result = '0-1' AND g.black_player = ANY(%s) THEN 1 END) as wins_as_black,
                    COUNT(CASE WHEN g.result = '1/2-1/2' THEN 1 END) as draws,
                    COUNT(CASE WHEN (g.result = '0-1' AND g.white_player = ANY(%s)) 
                                 OR (g.result = '1-0' AND g.black_player = ANY(%s)) THEN 1 END) as losses
                FROM games g 
                WHERE g.white_player = ANY(%s) OR g.black_player = ANY(%s)
            """,
                (user_ids, user_ids, user_ids, user_ids, user_ids, user_ids),
            )

            game_stats = cursor.fetchone()
            total_games, wins_white, wins_black, draws, losses = game_stats

            # Calculate win rate
            wins = wins_white + wins_black
            win_rate = (wins / total_games * 100) if total_games > 0 else 0

            # Get tactical error statistics
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_features,
                    COUNT(CASE WHEN f.error_label = 'blunder' THEN 1 END) as blunders,
                    COUNT(CASE WHEN f.error_label = 'mistake' THEN 1 END) as mistakes,
                    COUNT(CASE WHEN f.error_label = 'inaccuracy' THEN 1 END) as inaccuracies
                FROM features f
                JOIN games g ON f.game_id = g.game_id
                WHERE g.white_player = ANY(%s) OR g.black_player = ANY(%s)
            """,
                (user_ids, user_ids),
            )

            error_stats = cursor.fetchone()
            total_features, blunders, mistakes, inaccuracies = error_stats

            cursor.close()
            conn.close()

            return UserGameStats(
                user_id="+".join(user_ids),
                total_games=total_games,
                win_rate=win_rate,
                wins_as_white=wins_white,
                wins_as_black=wins_black,
                draws=draws,
                losses=losses,
                total_features=total_features,
                blunders=blunders,
                mistakes=mistakes,
                inaccuracies=inaccuracies,
            )

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            # Return default stats if database fails
            return UserGameStats(
                user_id="+".join(user_ids),
                total_games=0,
                win_rate=0,
                wins_as_white=0,
                wins_as_black=0,
                draws=0,
                losses=0,
                total_features=0,
                blunders=0,
                mistakes=0,
                inaccuracies=0,
            )

    def generate_data_driven_recommendations(
        self, stats: UserGameStats
    ) -> List[TrainingRecommendation]:
        """
        Generate specific recommendations based on real performance data.

        Args:
            stats: Real user statistics from database

        Returns:
            List of data-driven training recommendations
        """
        recommendations = []

        logger.info(f"Generating data-driven recommendations for {stats.user_id}")
        logger.info(
            f"Stats: {stats.total_games} games, {stats.win_rate:.1f}% win rate, {stats.error_rate:.1f}% error rate"
        )

        # 1. CRITICAL: High Blunder Rate Analysis
        if stats.blunder_rate > 0.5:  # More than 0.5 blunders per game
            recommendations.append(
                TrainingRecommendation(
                    priority=TrainingPriority.EMERGENCY,
                    category="Critical Error Prevention",
                    title=f"URGENT: Blunder Reduction Training",
                    description=f"You're averaging {stats.blunder_rate:.1f} blunders per game ({stats.blunders} blunders in {stats.total_games} games). This is significantly impacting your {stats.win_rate:.1f}% win rate.",
                    exercises=[
                        f"Complete 100 tactical puzzles daily focusing on opponent threats",
                        f"Implement 10-second rule: pause before every move to check for hanging pieces",
                        f"Review your last 20 games and identify the exact move where each blunder occurred",
                        f"Practice visualization exercises: calculate 3 moves ahead without moving pieces",
                        f"Use longer time controls (15+10 minimum) to reduce time pressure blunders",
                    ],
                    estimated_time=120,
                    success_criteria=[
                        f"Reduce blunder rate from {stats.blunder_rate:.1f} to under 0.3 per game",
                        f"Complete tactical trainer with 95% accuracy on 2000+ rated puzzles",
                        f"Play 10 games with zero blunders",
                        f"Improve overall win rate by 10 percentage points",
                    ],
                    source=f"data_analysis_blunders_{stats.blunders}",
                )
            )

        # 2. HIGH: Overall Error Rate Analysis
        elif stats.error_rate > 20:  # More than 20% moves have errors
            recommendations.append(
                TrainingRecommendation(
                    priority=TrainingPriority.HIGH,
                    category="Tactical Accuracy Improvement",
                    title=f"Reduce Overall Error Rate",
                    description=f"Your error rate is {stats.error_rate:.1f}% ({stats.blunders + stats.mistakes + stats.inaccuracies} errors in {stats.total_features} positions). This needs improvement.",
                    exercises=[
                        f"Solve 50 tactical puzzles daily at your rating level",
                        f"Practice candidate move analysis: find 3 candidate moves before choosing",
                        f"Study your game analysis reports and understand why moves were marked as mistakes",
                        f"Play longer games (30+0 minimum) to allow proper calculation time",
                        f"Focus on pattern recognition training for common tactical motifs",
                    ],
                    estimated_time=90,
                    success_criteria=[
                        f"Reduce error rate from {stats.error_rate:.1f}% to under 15%",
                        f"Decrease mistakes from {stats.mistakes} to under 50% of current level",
                        f"Improve position evaluation accuracy by practicing engine analysis",
                    ],
                    source=f"data_analysis_errors_{int(stats.error_rate)}",
                )
            )

        # 3. Win Rate Analysis and Improvement
        if stats.win_rate < 45:  # Below 45% win rate
            if stats.total_games > 100:  # Enough data to be meaningful
                recommendations.append(
                    TrainingRecommendation(
                        priority=(
                            TrainingPriority.HIGH
                            if stats.win_rate < 35
                            else TrainingPriority.MEDIUM
                        ),
                        category="Overall Performance Enhancement",
                        title=f"Improve Win Rate from {stats.win_rate:.1f}%",
                        description=f"With {stats.total_games} games played, your {stats.win_rate:.1f}% win rate ({stats.wins_as_white + stats.wins_as_black} wins, {stats.losses} losses) indicates systematic issues to address.",
                        exercises=[
                            f"Focus on converting winning positions: study basic endgames (King+Queen, King+Rook)",
                            f"Analyze your {stats.losses} losses to identify the most common losing patterns",
                            f"Practice time management: aim for using 70% of your time by move 30",
                            f"Study opening principles: complete development before attacking",
                            f"Learn when to exchange pieces vs keep material on the board",
                        ],
                        estimated_time=100,
                        success_criteria=[
                            f"Achieve 50%+ win rate within next 100 games",
                            f"Reduce loss rate from {stats.losses/stats.total_games*100:.1f}% to under 45%",
                            f"Master 3 basic endgame positions with 95% accuracy",
                            f"Complete opening repertoire for both colors",
                        ],
                        source=f"data_analysis_winrate_{int(stats.win_rate)}",
                    )
                )

        # 4. Color-Specific Performance Issues
        if stats.color_preference_issue and stats.total_games > 100:
            white_rate = (
                (stats.wins_as_white / (stats.total_games * 0.5)) * 100
                if stats.total_games > 0
                else 0
            )
            black_rate = (
                (stats.wins_as_black / (stats.total_games * 0.5)) * 100
                if stats.total_games > 0
                else 0
            )

            weaker_color = "white" if white_rate < black_rate else "black"
            stronger_color = "black" if weaker_color == "white" else "white"
            weaker_rate = min(white_rate, black_rate)
            stronger_rate = max(white_rate, black_rate)

            recommendations.append(
                TrainingRecommendation(
                    priority=TrainingPriority.MEDIUM,
                    category=f"Color-Specific Training",
                    title=f"Improve Performance as {weaker_color.title()}",
                    description=f"Significant performance gap: {stronger_rate:.1f}% as {stronger_color} vs {weaker_rate:.1f}% as {weaker_color}. Focus on {weaker_color}-specific skills.",
                    exercises=[
                        f"Study {weaker_color} opening repertoire: learn 2-3 solid systems",
                        f"Practice {weaker_color}-specific strategies and typical plans",
                        f"Analyze master games where {weaker_color} wins from typical openings",
                        f"Focus on {weaker_color} piece development patterns and timing",
                        f"Learn defensive techniques when playing as {weaker_color}",
                    ],
                    estimated_time=80,
                    success_criteria=[
                        f"Improve {weaker_color} performance from {weaker_rate:.1f}% to within 5% of {stronger_color} rate",
                        f"Build consistent {weaker_color} opening repertoire",
                        f"Understand typical {weaker_color} strategies in chosen openings",
                    ],
                    source=f"data_analysis_color_{weaker_color}_{int(weaker_rate)}",
                )
            )

        # 5. Specific Improvement Based on Game Volume
        if stats.total_games > 2000:  # Experienced player
            recommendations.append(
                TrainingRecommendation(
                    priority=TrainingPriority.MEDIUM,
                    category="Advanced Performance Analysis",
                    title="Breakthrough Training for Experienced Player",
                    description=f"With {stats.total_games} games under your belt, focus on advanced concepts to break through your current {stats.win_rate:.1f}% plateau.",
                    exercises=[
                        f"Deep analysis: spend 2 hours analyzing every loss from your last 50 games",
                        f"Study grandmaster games in your favorite openings (at least 20 games per opening)",
                        f"Focus on complex endgames: Rook+Pawn vs Rook, opposite-colored bishops",
                        f"Practice advanced tactics: X-ray attacks, deflection, interference patterns",
                        f"Work on positional understanding: weak squares, pawn chains, piece coordination",
                    ],
                    estimated_time=150,
                    success_criteria=[
                        f"Identify and fix your top 3 recurring strategic mistakes",
                        f"Master 5 advanced endgame positions",
                        f"Achieve rating improvement of 100+ points in next 6 months",
                    ],
                    source=f"data_analysis_experienced_{stats.total_games}",
                )
            )

        # 6. If performance is actually good, focus on refinement
        if stats.win_rate >= 55 and stats.error_rate < 15:
            recommendations.append(
                TrainingRecommendation(
                    priority=TrainingPriority.LOW,
                    category="Performance Optimization",
                    title="Fine-Tuning for Strong Player",
                    description=f"Excellent performance: {stats.win_rate:.1f}% win rate with {stats.error_rate:.1f}% error rate. Focus on elite-level refinement.",
                    exercises=[
                        f"Study cutting-edge opening theory in your main lines",
                        f"Analyze top-level games (2600+ players) in your openings",
                        f"Practice complex calculation exercises (5+ move combinations)",
                        f"Work on time management optimization for tournament play",
                        f"Study advanced endgame theory and nuances",
                    ],
                    estimated_time=120,
                    success_criteria=[
                        f"Maintain {stats.win_rate:.1f}%+ win rate consistently",
                        f"Reduce error rate below 12%",
                        f"Master 10 advanced theoretical endgames",
                    ],
                    source=f"data_analysis_strong_{int(stats.win_rate)}",
                )
            )

        logger.info(f"Generated {len(recommendations)} data-driven recommendations")
        return recommendations

    def create_unified_user_profile(
        self, user_ids: List[str], stats: UserGameStats
    ) -> UserProfile:
        """
        Create a unified user profile based on real data analysis.

        Args:
            user_ids: List of user IDs (same player)
            stats: Real performance statistics

        Returns:
            Data-driven UserProfile
        """
        # Determine skill level based on performance
        if stats.win_rate >= 55 and stats.error_rate < 15:
            skill_level = "advanced"
        elif stats.win_rate >= 45 and stats.error_rate < 25:
            skill_level = "intermediate"
        else:
            skill_level = "beginner"

        # Determine focus areas based on weaknesses
        focus_areas = ["tactics"]  # Always include tactics

        if stats.blunder_rate > 0.3:
            focus_areas.append("error_prevention")
        if stats.error_rate > 20:
            focus_areas.append("calculation")
        if stats.win_rate < 45:
            focus_areas.extend(["endgame", "fundamentals"])
        if stats.color_preference_issue:
            focus_areas.append("opening")

        # Determine common mistakes from data
        common_mistakes = []
        if stats.blunder_rate > 0.5:
            common_mistakes.append("frequent blunders - hanging pieces")
        if stats.mistakes > stats.blunders * 1.5:
            common_mistakes.append("strategic mistakes - poor position evaluation")
        if stats.inaccuracies > stats.mistakes:
            common_mistakes.append("minor inaccuracies - suboptimal move choices")
        if stats.win_rate < 40:
            common_mistakes.append("difficulty converting advantages")

        # Set time based on skill level and needs
        if skill_level == "beginner" or stats.blunder_rate > 0.5:
            time_available = 90  # More time needed for fundamental work
        elif skill_level == "advanced":
            time_available = 120  # More time for deep analysis
        else:
            time_available = 75  # Standard intermediate time

        return UserProfile(
            user_id="+".join(user_ids),
            skill_level=skill_level,
            preferred_openings=[
                "Data-driven selection needed"
            ],  # Would need opening analysis
            common_mistakes=common_mistakes,
            time_available=time_available,
            focus_areas=focus_areas,
        )


def main():
    """Generate data-driven recommendations for cmess users."""

    print("🔬 DATA-DRIVEN CHESS TRAINING ANALYSIS")
    print("=" * 80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: cmess4401 & cmess1315 (unified analysis)")
    print()

    try:
        # Initialize data-driven system
        analyzer = DataDrivenRecommender()

        # Get real user statistics
        print("📊 Fetching Real Performance Data...")
        user_ids = ["cmess4401", "cmess1315"]
        stats = analyzer.get_user_stats(user_ids)

        # Display comprehensive stats
        print("\n" + "=" * 60)
        print("📈 REAL PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"🎮 Total Games Played: {stats.total_games:,}")
        print(f"🏆 Overall Win Rate: {stats.win_rate:.1f}%")
        print(f"   • Wins as White: {stats.wins_as_white}")
        print(f"   • Wins as Black: {stats.wins_as_black}")
        print(f"   • Draws: {stats.draws}")
        print(f"   • Losses: {stats.losses}")

        print(f"\n🎯 Tactical Analysis ({stats.total_features:,} positions analyzed):")
        print(f"   • Overall Error Rate: {stats.error_rate:.1f}%")
        print(f"   • Blunders: {stats.blunders} ({stats.blunder_rate:.2f} per game)")
        print(f"   • Mistakes: {stats.mistakes}")
        print(f"   • Inaccuracies: {stats.inaccuracies}")

        if stats.color_preference_issue:
            white_rate = (stats.wins_as_white / (stats.total_games * 0.5)) * 100
            black_rate = (stats.wins_as_black / (stats.total_games * 0.5)) * 100
            print(f"\n⚠️  Color Performance Gap Detected:")
            print(f"   • White Performance: {white_rate:.1f}%")
            print(f"   • Black Performance: {black_rate:.1f}%")

        # Generate data-driven recommendations
        print("\n🔬 Generating Data-Driven Recommendations...")
        recommendations = analyzer.generate_data_driven_recommendations(stats)

        # Create unified user profile
        unified_profile = analyzer.create_unified_user_profile(user_ids, stats)

        print(f"\n" + "=" * 80)
        print("🎯 DATA-DRIVEN RECOMMENDATIONS")
        print("=" * 80)
        print(f"\n👤 UNIFIED PLAYER PROFILE:")
        print(f"   Skill Level: {unified_profile.skill_level.title()}")
        print(f"   Focus Areas: {', '.join(unified_profile.focus_areas)}")
        print(f"   Key Challenges: {', '.join(unified_profile.common_mistakes)}")
        print(f"   Recommended Session Time: {unified_profile.time_available} minutes")

        # Display specific recommendations
        if recommendations:
            total_time = sum(rec.estimated_time for rec in recommendations)
            print(
                f"\n📋 SPECIFIC RECOMMENDATIONS ({len(recommendations)} items, {total_time} min total):"
            )

            priority_icons = {
                TrainingPriority.EMERGENCY: "🚨",
                TrainingPriority.HIGH: "🔥",
                TrainingPriority.MEDIUM: "📚",
                TrainingPriority.LOW: "💡",
            }

            for i, rec in enumerate(recommendations, 1):
                icon = priority_icons.get(rec.priority, "📋")
                print(f"\n{icon} {i}. {rec.title} ({rec.priority.value})")
                print(f"   📝 {rec.description}")
                print(f"   ⏱️  Time: {rec.estimated_time} minutes")
                print(f"   📚 Category: {rec.category}")
                print(f"   🎯 Key Exercises:")
                for j, exercise in enumerate(rec.exercises[:3], 1):
                    print(f"      {j}. {exercise}")
                if len(rec.exercises) > 3:
                    print(f"      ... {len(rec.exercises) - 3} more exercises")

                print(f"   ✅ Success Criteria:")
                for criterion in rec.success_criteria[:2]:
                    print(f"      • {criterion}")
        else:
            print("No specific recommendations generated - performance may be optimal.")

        # Export the data-driven plan
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_driven_training_plan_cmess_{timestamp}.json"

        if recommendations:
            # Use base recommender for export
            success = analyzer.base_recommender.export_training_plan(
                recommendations, filename
            )
            if success:
                print(f"\n💾 Data-driven training plan exported: {filename}")

        print("\n" + "=" * 80)
        print("🎉 DATA-DRIVEN ANALYSIS COMPLETE")
        print("=" * 80)
        print("✨ These recommendations are based on your actual game performance")
        print("📊 Focus on the highest priority items for maximum improvement")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
