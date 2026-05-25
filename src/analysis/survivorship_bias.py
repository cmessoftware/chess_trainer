"""
Survivorship Bias Module for Chess Training Analysis.

This module implements critical analysis for detecting survivorship bias patterns
in chess datasets, focusing on identifying games with early defeats, catastrophic
errors, and patterns that may be underrepresented due to data filtering.

Key Features:
- Early defeat detection (< 20 moves)
- Mate pattern analysis
- Opening survival rate calculation
- Catastrophic error identification
- Emergency plan generation for critical patterns

Author: Chess Trainer ML Pipeline
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import logging
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CriticalityLevel(Enum):
    """Enum for criticality levels of detected patterns."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SurvivorshipAlert:
    """Data class for survivorship bias alerts."""

    pattern_type: str
    criticality: CriticalityLevel
    affected_games: int
    description: str
    recommended_action: str
    additional_data: Dict[str, Any]


@dataclass
class EarlyDefeatPattern:
    """Data class for early defeat patterns."""

    opening_name: str
    moves_to_defeat: int
    frequency: int
    survival_rate: float
    typical_errors: List[str]


@dataclass
class MatePattern:
    """Data class for mate patterns."""

    mate_type: str
    moves_to_mate: int
    frequency: int
    opening_context: str
    prevention_tips: List[str]


class SurvivorshipBiasAnalyzer:
    """
    Core analyzer for detecting survivorship bias in chess training datasets.

    This analyzer implements critical detection algorithms to identify patterns
    that may be underrepresented due to data filtering or collection bias.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the Survivorship Bias Analyzer.

        Args:
            db_url: Optional database URL. If None, uses CHESS_TRAINER_DB_URL environment variable.
        """
        self.db_url = db_url or os.environ.get(
            "CHESS_TRAINER_DB_URL",
            "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
        )
        self.engine = None
        self.alerts: List[SurvivorshipAlert] = []
        self.early_defeat_threshold = 20  # moves
        self.mate_detection_threshold = 30  # moves
        self.critical_survival_rate = 0.3  # 30% or lower is critical

        # Emergency patterns that require immediate attention
        self.emergency_patterns = {
            "scholar_mate": {"moves": 4, "priority": CriticalityLevel.CRITICAL},
            "back_rank_mate": {"moves": 15, "priority": CriticalityLevel.HIGH},
            "smothered_mate": {"moves": 10, "priority": CriticalityLevel.HIGH},
            "fork_disasters": {"moves": 8, "priority": CriticalityLevel.MEDIUM},
        }

    def analyze_dataset(self, source_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive survivorship bias analysis on the dataset.

        Args:
            source_filter: Optional filter for specific data sources

        Returns:
            Dict containing comprehensive analysis results
        """
        logger.info(
            f"Starting survivorship bias analysis for source: {source_filter or 'ALL'}"
        )

        try:
            # Initialize database connection
            self._init_db_connection()

            # Load data from PostgreSQL
            data = self._load_data_postgresql(source_filter)

            if data.empty:
                logger.warning("No data found for analysis")
                return self._generate_empty_report()

            # Perform analysis components
            results = {
                "dataset_overview": self._analyze_dataset_overview(data),
                "early_defeats": self._detect_early_defeats(data),
                "mate_patterns": self._analyze_mate_patterns(data),
                "opening_survival": self._calculate_opening_survival_rates(data),
                "catastrophic_errors": self._detect_catastrophic_errors(data),
                "alerts": self._generate_alerts(),
                "emergency_plan": self._generate_emergency_plan(),
                "recommendations": self._generate_recommendations(),
            }

            logger.info(f"Analysis completed. Generated {len(self.alerts)} alerts.")
            return results

        except Exception as e:
            logger.error(f"Error during survivorship bias analysis: {e}")
            return self._generate_error_report(str(e))

    def _init_db_connection(self):
        """Initialize database connection."""
        try:
            self.engine = create_engine(self.db_url)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def _load_data_postgresql(self, source_filter: Optional[str]) -> pd.DataFrame:
        """Load data from PostgreSQL database."""
        # Simplified query that doesn't use GROUP BY to avoid aggregation issues
        query = """
        SELECT DISTINCT
            g.game_id,
            g.source,
            g.white_elo,
            g.black_elo,
            g.result,
            g.opening,
            f.num_moves as moves_count,
            'Normal' as termination
        FROM games g
        INNER JOIN features f ON g.game_id = f.game_id
        WHERE f.num_moves > 0
        """

        if source_filter:
            query += f" AND g.source = '{source_filter}'"

        query += """
        ORDER BY g.game_id 
        LIMIT 10000
        """

        try:
            with self.engine.connect() as conn:
                data = pd.read_sql_query(query, conn)

                # Add calculated fields after loading
                if not data.empty:
                    # Load error data separately for analysis
                    error_query = f"""
                    SELECT 
                        game_id,
                        COUNT(CASE WHEN error_label IN ('blunder', 'mistake') THEN 1 END) as blunder_count,
                        COUNT(CASE WHEN error_label = 'mistake' THEN 1 END) as mistake_count,
                        COUNT(*) as total_moves
                    FROM features 
                    WHERE game_id IN ({','.join([f"'{gid}'" for gid in data['game_id'][:100]])})
                    GROUP BY game_id
                    """

                    with self.engine.connect() as conn2:
                        error_data = pd.read_sql_query(error_query, conn2)

                    # Merge error data back into main data
                    data = data.merge(error_data, on="game_id", how="left")
                    data["blunder_count"] = data["blunder_count"].fillna(0)
                    data["mistake_count"] = data["mistake_count"].fillna(0)

                return data

        except Exception as e:
            logger.error(f"Error loading data from PostgreSQL: {e}")
            return pd.DataFrame()

    def _analyze_dataset_overview(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze basic dataset characteristics."""
        return {
            "total_games": len(data),
            "sources": (
                data["source"].value_counts().to_dict()
                if "source" in data.columns
                else {}
            ),
            "avg_game_length": (
                data["moves_count"].mean() if "moves_count" in data.columns else 0
            ),
            "short_games_count": (
                len(data[data["moves_count"] < self.early_defeat_threshold])
                if "moves_count" in data.columns
                else 0
            ),
            "termination_types": (
                data["termination"].value_counts().to_dict()
                if "termination" in data.columns
                else {"Normal": len(data)}
            ),
            "avg_blunder_count": (
                data["blunder_count"].mean() if "blunder_count" in data.columns else 0
            ),
            "avg_mistake_count": (
                data["mistake_count"].mean() if "mistake_count" in data.columns else 0
            ),
        }

    def _detect_early_defeats(self, data: pd.DataFrame) -> List[EarlyDefeatPattern]:
        """Detect patterns of early defeats (games ending < 20 moves)."""
        if "moves_count" not in data.columns or "opening" not in data.columns:
            return []

        early_games = data[data["moves_count"] < self.early_defeat_threshold]

        patterns = []
        for opening in early_games["opening"].value_counts().head(10).index:
            opening_data = early_games[early_games["opening"] == opening]
            total_games_opening = len(data[data["opening"] == opening])

            pattern = EarlyDefeatPattern(
                opening_name=opening,
                moves_to_defeat=int(opening_data["moves_count"].mean()),
                frequency=len(opening_data),
                survival_rate=1 - (len(opening_data) / max(total_games_opening, 1)),
                typical_errors=self._extract_typical_errors(opening_data),
            )
            patterns.append(pattern)

            # Generate alert if survival rate is critical
            if pattern.survival_rate < self.critical_survival_rate:
                self._add_alert(
                    pattern_type="early_defeat",
                    criticality=CriticalityLevel.CRITICAL,
                    affected_games=pattern.frequency,
                    description=f"Opening {opening} shows critical survival rate: {pattern.survival_rate:.2%}",
                    recommended_action="Add emergency training modules for this opening",
                    additional_data={"opening": opening, "pattern": pattern},
                )

        return patterns

    def _analyze_mate_patterns(self, data: pd.DataFrame) -> List[MatePattern]:
        """Analyze mate patterns in the dataset."""
        if "termination" not in data.columns:
            return []

        mate_games = data[
            data["termination"].str.contains("mate", case=False, na=False)
        ]
        patterns = []

        # Group by opening and analyze mate patterns
        for opening in mate_games["opening"].value_counts().head(5).index:
            opening_mates = mate_games[mate_games["opening"] == opening]

            pattern = MatePattern(
                mate_type="checkmate",
                moves_to_mate=(
                    int(opening_mates["moves_count"].mean())
                    if "moves_count" in opening_mates.columns
                    else 0
                ),
                frequency=len(opening_mates),
                opening_context=opening,
                prevention_tips=self._generate_mate_prevention_tips(opening),
            )
            patterns.append(pattern)

        return patterns

    def _calculate_opening_survival_rates(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate survival rates by opening."""
        if "opening" not in data.columns or "moves_count" not in data.columns:
            return {}

        survival_rates = {}

        for opening in data["opening"].value_counts().head(20).index:
            opening_games = data[data["opening"] == opening]
            survived_games = opening_games[
                opening_games["moves_count"] >= self.early_defeat_threshold
            ]

            survival_rate = len(survived_games) / len(opening_games)
            survival_rates[opening] = survival_rate

            # Generate alert for low survival rates
            if survival_rate < self.critical_survival_rate:
                self._add_alert(
                    pattern_type="low_survival",
                    criticality=CriticalityLevel.HIGH,
                    affected_games=len(opening_games),
                    description=f"Opening {opening} has low survival rate: {survival_rate:.2%}",
                    recommended_action="Focus training on this opening's early game",
                    additional_data={
                        "opening": opening,
                        "survival_rate": survival_rate,
                    },
                )

        return survival_rates

    def _detect_catastrophic_errors(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect catastrophic errors in the dataset."""
        catastrophic_errors = {}

        if "blunder_count" in data.columns:
            high_blunder_games = data[data["blunder_count"] >= 3]
            catastrophic_errors["high_blunder_games"] = len(high_blunder_games)

            if len(high_blunder_games) > 0:
                self._add_alert(
                    pattern_type="catastrophic_blunders",
                    criticality=CriticalityLevel.HIGH,
                    affected_games=len(high_blunder_games),
                    description=f"Found {len(high_blunder_games)} games with 3+ blunders",
                    recommended_action="Review blunder patterns and create targeted training",
                    additional_data={"blunder_threshold": 3},
                )

        return catastrophic_errors

    def _extract_typical_errors(self, game_data: pd.DataFrame) -> List[str]:
        """Extract typical errors from game data."""
        errors = []
        if "error_label" in game_data.columns:
            error_counts = game_data["error_label"].value_counts()
            errors = error_counts.head(3).index.tolist()
        return errors

    def _generate_mate_prevention_tips(self, opening: str) -> List[str]:
        """Generate prevention tips for mate patterns."""
        tips = [
            f"Study {opening} defensive structures",
            "Practice endgame positions for this opening",
            "Learn key tactical motifs",
        ]
        return tips

    def _add_alert(
        self,
        pattern_type: str,
        criticality: CriticalityLevel,
        affected_games: int,
        description: str,
        recommended_action: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Add an alert to the alerts list."""
        alert = SurvivorshipAlert(
            pattern_type=pattern_type,
            criticality=criticality,
            affected_games=affected_games,
            description=description,
            recommended_action=recommended_action,
            additional_data=additional_data or {},
        )
        self.alerts.append(alert)

    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate formatted alerts list."""
        return [
            {
                "pattern_type": alert.pattern_type,
                "criticality": alert.criticality.value,
                "affected_games": alert.affected_games,
                "description": alert.description,
                "recommended_action": alert.recommended_action,
                "additional_data": alert.additional_data,
            }
            for alert in self.alerts
        ]

    def _generate_emergency_plan(self) -> Dict[str, Any]:
        """Generate emergency plan based on detected patterns."""
        critical_alerts = [
            alert
            for alert in self.alerts
            if alert.criticality == CriticalityLevel.CRITICAL
        ]

        return {
            "critical_priorities": [
                {
                    "priority": i + 1,
                    "description": alert.description,
                    "action": alert.recommended_action,
                    "pattern_type": alert.pattern_type,
                }
                for i, alert in enumerate(critical_alerts[:5])  # Top 5 priorities
            ],
            "emergency_patterns": self.emergency_patterns,
            "requires_immediate_attention": len(critical_alerts) > 0,
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if len(self.alerts) == 0:
            recommendations.append("No critical survivorship bias patterns detected.")
        else:
            recommendations.append(
                f"Detected {len(self.alerts)} patterns requiring attention."
            )

            critical_count = len(
                [
                    alert
                    for alert in self.alerts
                    if alert.criticality == CriticalityLevel.CRITICAL
                ]
            )
            if critical_count > 0:
                recommendations.append(
                    f"URGENT: {critical_count} critical patterns need immediate action."
                )

        return recommendations

    def _generate_empty_report(self) -> Dict[str, Any]:
        """Generate report for empty dataset."""
        return {
            "dataset_overview": {
                "total_games": 0,
                "message": "No data available for analysis",
            },
            "early_defeats": [],
            "mate_patterns": [],
            "opening_survival": {},
            "catastrophic_errors": {},
            "alerts": [],
            "emergency_plan": {
                "critical_priorities": [],
                "requires_immediate_attention": False,
            },
            "recommendations": ["No data available for survivorship bias analysis"],
        }

    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """Generate error report."""
        return {
            "error": True,
            "message": error_message,
            "dataset_overview": {"total_games": 0},
            "early_defeats": [],
            "mate_patterns": [],
            "opening_survival": {},
            "catastrophic_errors": {},
            "alerts": [],
            "emergency_plan": {
                "critical_priorities": [],
                "requires_immediate_attention": False,
            },
            "recommendations": [f"Analysis failed: {error_message}"],
        }

    def export_report(self, file_path: str) -> bool:
        """Export the latest analysis report to JSON file."""
        try:
            import json

            results = self.analyze_dataset()
            with open(file_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False
