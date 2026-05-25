#!/usr/bin/env python3
"""
AI Coach Pipeline - Phase 2 Integration
Connects Feature Summarizer → RAG → LLM for coaching reports

Usage:
    python test_coach_pipeline.py --game-id <id>
    python test_coach_pipeline.py --player-analysis <username>
"""

import sys
import os
from pathlib import Path

# Add parent directory (src/) to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import pandas as pd

from ai_coach.feature_summarizer import FeatureSummarizer
from ai_coach.rag import ChessRAG
from api.models.database_models import Features, Games
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CoachingReport:
    """Structured coaching report output"""

    game_id: str
    opening_analysis: str
    performance_summary: str
    critical_moments: List[Dict]
    tactical_insights: str
    strategic_insights: str
    training_recommendations: List[str]
    rag_knowledge: List[str]


class AICoachPipeline:
    """
    Complete AI Chess Coach Pipeline - Phase 2 Implementation

    Pipeline Flow:
    1. Fetch game features from database
    2. Summarize features with FeatureSummarizer
    3. Retrieve relevant chess knowledge from RAG
    4. Generate coaching report with LLM
    """

    def __init__(self, db_url: str = None, rag_persist_dir: str = None, player_color: str = None):
        """
        Initialize the AI Coach Pipeline

        Args:
            db_url: Database connection string
            rag_persist_dir: ChromaDB persistence directory
            player_color: Filter analysis for 'white' or 'black' player (None = both)
        """
        self.player_color = player_color
        # Database connection
        self.db_url = db_url or os.getenv(
            "CHESS_TRAINER_DB_URL",
            "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db",
        )
        self.engine = create_engine(self.db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Initialize components
        logger.info("Initializing AI Coach Pipeline...")
        self.feature_summarizer = FeatureSummarizer()

        # RAG System
        rag_dir = rag_persist_dir or str(
            project_root / "data" / "chess_books" / "chroma_db"
        )
        self.rag = ChessRAG(
            collection_name="chess_knowledge",
            persist_directory=rag_dir,
            embedding_model="all-MiniLM-L6-v2",
        )

        logger.info("✅ AI Coach Pipeline initialized successfully")
        logger.info(f"   Database: {self.db_url}")
        logger.info(f"   RAG documents: {self.rag.get_stats()['total_documents']}")

    def analyze_game(self, game_id: str) -> CoachingReport:
        """
        Analyze a single game and generate coaching report

        Args:
            game_id: Game identifier

        Returns:
            CoachingReport with insights and recommendations
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🎯 ANALYZING GAME: {game_id}")
        logger.info(f"{'=' * 70}\n")

        # Step 1: Fetch features from database
        logger.info("📊 Step 1: Fetching game features from database...")
        features_df = self._fetch_game_features(game_id)

        if features_df.empty:
            logger.error(f"No features found for game {game_id}")
            return None

        logger.info(f"   ✅ Loaded {len(features_df)} moves")

        # Step 2: Convert to FeatureSummarizer format
        logger.info("🔄 Step 2: Converting features to summary format...")
        game_features = self._prepare_features_for_summarizer(features_df, game_id)

        # Step 3: Summarize with FeatureSummarizer
        logger.info("📝 Step 3: Generating feature summaries...")
        summary = self.feature_summarizer.summarize_game(game_features)

        logger.info("   Opening: " + summary["opening"])
        logger.info("   Performance: " + summary["performance_summary"])
        logger.info(f"   Critical moments: {len(summary['critical_moments'])}")
        logger.info(f"   Patterns detected: {len(summary['patterns_detected'])}")

        # Step 4: Retrieve chess knowledge from RAG
        logger.info("\n📚 Step 4: Retrieving chess knowledge from RAG...")
        rag_insights = self._retrieve_rag_knowledge(summary, game_features)

        logger.info(f"   ✅ Retrieved {len(rag_insights)} relevant knowledge chunks")
        for i, insight in enumerate(rag_insights[:3], 1):
            # Extract source from metadata if available
            source = "Unknown source"
            if "metadata" in insight:
                metadata = insight["metadata"]
                source = metadata.get(
                    "source",
                    metadata.get("book", metadata.get("filename", "Unknown source")),
                )
            logger.info(f"   {i}. {source}: {insight['text'][:100]}...")

        # Step 5: Generate final coaching report
        logger.info("\n🤖 Step 5: Generating coaching report...")
        report = self._generate_coaching_report(summary, rag_insights, game_id)

        logger.info("\n" + "=" * 70)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("=" * 70)

        return report

    def _fetch_game_features(self, game_id: str) -> pd.DataFrame:
        """Fetch all features for a game from database"""
        query = self.session.query(Features).filter(Features.game_id == game_id)
        
        # Filter by player color if specified
        # Database mapping: player_color = 1 (WHITE), player_color = 0 (BLACK)
        if self.player_color:
            color_value = 1 if self.player_color == 'white' else 0
            query = query.filter(Features.player_color == color_value)
            logger.info(f"   Filtering for {self.player_color.upper()} player only")
        
        features = pd.read_sql(query.statement, self.session.bind)
        return features

    def _prepare_features_for_summarizer(
        self, features_df: pd.DataFrame, game_id: str
    ) -> Dict[str, Any]:
        """
        Convert database features to FeatureSummarizer format

        Maps:
        - Raw DB features → Aggregated game statistics
        - Score diffs → Performance metrics
        - Error labels → Error counts
        """
        # Get game metadata (skip if Games table schema doesn't match)
        opening_name = "Unknown Opening"
        
        # Convert numeric columns to proper dtypes (in case they were read as strings)
        numeric_cols = ['score_diff', 'material_balance', 'material_total', 
                       'num_pieces', 'branching_factor', 'self_mobility', 'opponent_mobility']
        for col in numeric_cols:
            if col in features_df.columns:
                features_df[col] = pd.to_numeric(features_df[col], errors='coerce')
        
        # DEBUG: Check data quality
        logger.info(f"   DEBUG - Features shape: {features_df.shape}")
        logger.info(f"   DEBUG - score_diff null count: {features_df['score_diff'].isna().sum()}/{len(features_df)}")
        logger.info(f"   DEBUG - score_diff sample: {features_df['score_diff'].dropna().head().tolist()}")
        logger.info(f"   DEBUG - error_label counts: {features_df['error_label'].value_counts().to_dict()}")
        logger.info(f"   DEBUG - player_color values: {features_df['player_color'].unique()}")
        
        try:
            # Query only specific columns instead of full Games object to avoid schema mismatch
            game_data = (
                self.session.query(Games.opening)
                .filter(Games.game_id == game_id)
                .first()
            )
            if game_data and game_data[0]:
                opening_name = game_data[0]
        except Exception as e:
            logger.warning(f"Could not fetch game metadata: {e}")
            # Try to extract opening from features tags
            first_move = features_df.iloc[0] if not features_df.empty else None
            if first_move is not None and "tags" in features_df.columns:
                tags = first_move.get("tags")
                if isinstance(tags, dict) and "opening" in tags:
                    opening_name = tags["opening"]

        # Calculate error counts
        error_counts = features_df["error_label"].value_counts().to_dict()
        blunders = error_counts.get("blunder", 0)
        mistakes = error_counts.get("mistake", 0)
        inaccuracies = error_counts.get("inaccuracy", 0)

        # Calculate average centipawn loss
        score_diffs = features_df["score_diff"].dropna().abs()
        avg_cpl = score_diffs.mean() if not score_diffs.empty else 0.0

        # Calculate accuracy (percentage of good/best moves)
        total_moves = len(features_df)
        good_moves = len(features_df[features_df["error_label"].isin(["good", "best"])])
        accuracy = (good_moves / total_moves * 100) if total_moves > 0 else 0.0

        # Identify critical moments (large score swings)
        critical_moments = []
        for _, row in features_df.nlargest(5, "score_diff", keep="first").iterrows():
            if abs(row["score_diff"]) > 50:  # Significant swing
                critical_moments.append(
                    {
                        "move_number": int(row["move_number"]),
                        "evaluation_swing": float(row["score_diff"]),
                        "move_played": row["move_san"],
                        "fen": row["fen"],
                    }
                )

        # Detect game phase errors
        phase_errors = (
            features_df[features_df["error_label"].isin(["blunder", "mistake"])]
            .groupby("phase")
            .size()
            .to_dict()
        )

        return {
            "opening_name": opening_name,
            "opening_evaluation": 0.0,  # TODO: Calculate from first moves
            "avg_centipawn_loss": avg_cpl,
            "accuracy": accuracy,
            "blunders": blunders,
            "mistakes": mistakes,
            "inaccuracies": inaccuracies,
            "blunders_opening": phase_errors.get("opening", 0),
            "blunders_middlegame": phase_errors.get("middlegame", 0),
            "blunders_endgame": phase_errors.get("endgame", 0),
            "time_trouble": False,  # TODO: Add time pressure detection
            "material_imbalance": features_df["material_balance"].mean(),
            "tactical_motifs": self._extract_tactical_motifs(features_df),
            "positional_themes": [],  # TODO: Extract from features
            "critical_moments": critical_moments,
        }

    def _extract_tactical_motifs(self, features_df: pd.DataFrame) -> List[str]:
        """Extract tactical motifs from tags"""
        motifs = []
        for tags in features_df["tags"].dropna():
            if isinstance(tags, dict):
                for tag in ["fork", "pin", "skewer", "discovered_attack"]:
                    if tag in tags:
                        motifs.append(tag)
        return list(set(motifs))

    def _retrieve_rag_knowledge(self, summary: Dict, features: Dict) -> List[Dict]:
        """
        Retrieve relevant chess knowledge from RAG system

        Queries:
        1. Opening specific knowledge
        2. Tactical patterns
        3. Error types (blunders, mistakes)
        4. Endgame principles (if applicable)
        """
        insights = []

        # Query 1: Opening knowledge
        if features.get("opening_name"):
            opening_query = (
                f"What are the key ideas and plans in {features['opening_name']}?"
            )
            opening_results = self.rag.retrieve_knowledge(opening_query, n_results=2)
            insights.extend(opening_results)

        # Query 2: Tactical motifs
        if summary.get("tactical_motifs"):
            for motif in summary["tactical_motifs"][:2]:  # Top 2 motifs
                motif_query = f"How to recognize and execute {motif}?"
                motif_results = self.rag.retrieve_knowledge(motif_query, n_results=1)
                insights.extend(motif_results)

        # Query 3: Common mistakes in phase
        if features.get("blunders_middlegame", 0) > 1:
            middlegame_query = "Common tactical mistakes in the middlegame"
            middlegame_results = self.rag.retrieve_knowledge(
                middlegame_query, n_results=2
            )
            insights.extend(middlegame_results)

        # Query 4: Endgame principles
        if features.get("blunders_endgame", 0) > 0:
            endgame_query = "Fundamental endgame principles and techniques"
            endgame_results = self.rag.retrieve_knowledge(endgame_query, n_results=2)
            insights.extend(endgame_results)

        return insights

    def _generate_coaching_report(
        self, summary: Dict, rag_insights: List[Dict], game_id: str
    ) -> CoachingReport:
        """
        Generate final coaching report

        TODO Phase 4: Integrate with LLM to generate natural language report
        For now, returns structured data
        """
        # Extract strategic insights from RAG
        strategic_insights = []
        for insight in rag_insights:
            if len(insight["text"]) > 50:  # Meaningful insight
                # Extract source from metadata
                source = "Unknown source"
                if "metadata" in insight:
                    metadata = insight["metadata"]
                    source = metadata.get(
                        "source",
                        metadata.get(
                            "book", metadata.get("filename", "Unknown source")
                        ),
                    )
                strategic_insights.append(f"From {source}: {insight['text'][:200]}...")

        # Generate training recommendations
        recommendations = summary.get("error_analysis", "")
        if summary.get("blunders", 0) > 2:
            recommendations = (
                "Focus on tactical training - daily tactics puzzles recommended"
            )

        report = CoachingReport(
            game_id=game_id,
            opening_analysis=summary["opening"],
            performance_summary=summary["performance_summary"],
            critical_moments=summary["critical_moments"],
            tactical_insights=", ".join(summary["tactical_motifs"])
            if summary["tactical_motifs"]
            else "No tactical motifs detected",
            strategic_insights="\n".join(strategic_insights[:3]),
            training_recommendations=[
                summary["error_analysis"],
                "Review critical moments and alternative lines",
                "Study similar positions from master games (see RAG insights)",
            ],
            rag_knowledge=[insight["text"][:150] for insight in rag_insights[:5]],
        )

        return report

    def print_report(self, report: CoachingReport):
        """Pretty print coaching report"""
        print("\n" + "=" * 70)
        player_info = f" ({self.player_color.upper()} player)" if self.player_color else ""
        print(f"🎯 COACHING REPORT - Game {report.game_id}{player_info}")
        print("=" * 70)

        print(f"\n📖 OPENING ANALYSIS")
        print(f"   {report.opening_analysis}")

        print(f"\n📊 PERFORMANCE SUMMARY")
        print(f"   {report.performance_summary}")

        print(f"\n⚡ TACTICAL INSIGHTS")
        print(f"   {report.tactical_insights}")

        print(f"\n🎓 STRATEGIC INSIGHTS (from chess books)")
        print(f"   {report.strategic_insights}")

        print(f"\n🔥 CRITICAL MOMENTS ({len(report.critical_moments)})")
        for i, moment in enumerate(report.critical_moments[:3], 1):
            move_num = moment.get("move_number", "?")
            move_played = moment.get("move_played", "?")
            # Handle both formats: 'evaluation_swing' from DB or 'evaluation_change' from summarizer
            eval_change = moment.get(
                "evaluation_swing", moment.get("evaluation_change", 0)
            )
            if isinstance(eval_change, str):
                eval_text = eval_change
            else:
                eval_text = f"{eval_change:.0f} centipawns"

            print(f"   {i}. Move {move_num}: {move_played}")
            print(f"      Evaluation swing: {eval_text}")

        print(f"\n💡 TRAINING RECOMMENDATIONS")
        for i, rec in enumerate(report.training_recommendations, 1):
            print(f"   {i}. {rec}")

        print(f"\n📚 RELEVANT CHESS KNOWLEDGE")
        for i, knowledge in enumerate(report.rag_knowledge[:3], 1):
            print(f"   {i}. {knowledge}...")

        print("\n" + "=" * 70 + "\n")


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Chess Coach Pipeline - Phase 2")
    parser.add_argument("--game-id", type=str, help="Analyze specific game")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample game")
    parser.add_argument("--player-color", type=str, choices=['white', 'black'], 
                        help="Analyze only WHITE or BLACK player (default: both)")

    args = parser.parse_args()

    # Initialize pipeline
    coach = AICoachPipeline(player_color=args.player_color)

    if args.demo or not args.game_id:
        # Demo: Get first game WITH features from database
        logger.info("🎮 Running demo mode - finding game with features...")
        from sqlalchemy import select

        stmt = select(Features.game_id).distinct().limit(1)
        result = coach.session.execute(stmt).first()

        if result:
            game_id = result[0]
            logger.info(f"Selected game with features: {game_id}")
        else:
            logger.error("No games with features found in database")
            logger.info("Please run feature generation first:")
            logger.info("  python src/scripts/generate_features_with_tactics.py")
            return
    else:
        game_id = args.game_id

    # Analyze game
    report = coach.analyze_game(game_id)

    if report:
        coach.print_report(report)
    else:
        logger.error("Failed to generate report")


if __name__ == "__main__":
    main()
