"""
Feature Summarizer - Phase 2 Implementation

Converts raw ML features into human-readable summaries for LLM coaching prompts.

This module bridges the gap between numerical features and natural language coaching.

Example:
    >>> summarizer = FeatureSummarizer()
    >>> summary = summarizer.summarize_game(game_features)
    >>> print(summary['opening'])
    "Italian Game - Giuoco Piano (C54). Solid opening choice."
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureSummarizer:
    """
    Summarizes chess game features for LLM coaching.
    
    Converts numerical features into interpretable text summaries that can be
    used in LLM prompts for generating coaching reports.
    """
    
    def __init__(self):
        """Initialize the feature summarizer."""
        self.tactical_motifs_map = {
            'fork': 'Fork patterns',
            'pin': 'Pin tactics',
            'skewer': 'Skewer motifs',
            'discovered_attack': 'Discovered attacks',
            'double_attack': 'Double attacks'
        }
        
        self.positional_themes_map = {
            'king_safety': 'King safety concerns',
            'piece_activity': 'Piece activity and coordination',
            'pawn_structure': 'Pawn structure weaknesses',
            'control_center': 'Central control'
        }
    
    def summarize_game(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw game features into coaching summary.
        
        Args:
            features: Dictionary with ML features from the game
                Expected keys:
                - opening_name: str
                - avg_centipawn_loss: float
                - blunders: int
                - mistakes: int
                - inaccuracies: int
                - tactical_motifs: List[str]
                - critical_moments: List[Dict]
                
        Returns:
            Dictionary with coaching-friendly summaries:
            {
                "opening": str,
                "performance_summary": str,
                "critical_moments": List[Dict],
                "patterns_detected": List[str],
                "tactical_motifs": List[str],
                "positional_themes": List[str],
                "error_analysis": str
            }
        """
        logger.info("Summarizing game features for LLM coaching...")
        
        summary = {
            "opening": self._summarize_opening(features),
            "performance_summary": self._summarize_performance(features),
            "critical_moments": self._summarize_critical_moments(features),
            "patterns_detected": self._detect_patterns(features),
            "tactical_motifs": self._summarize_tactical_motifs(features),
            "positional_themes": self._summarize_positional_themes(features),
            "error_analysis": self._analyze_errors(features)
        }
        
        return summary
    
    def _summarize_opening(self, features: Dict[str, Any]) -> str:
        """Summarize opening phase."""
        opening_name = features.get('opening_name', 'Unknown opening')
        opening_eval = features.get('opening_evaluation', 0.0)
        
        evaluation = "balanced"
        if opening_eval > 50:
            evaluation = "advantageous"
        elif opening_eval < -50:
            evaluation = "challenging"
        
        return f"{opening_name}. Position after opening: {evaluation}."
    
    def _summarize_performance(self, features: Dict[str, Any]) -> str:
        """Summarize overall performance metrics."""
        avg_cpl = features.get('avg_centipawn_loss', 0.0)
        accuracy = features.get('accuracy', 0.0)
        
        if avg_cpl < 30:
            level = "Excellent"
        elif avg_cpl < 60:
            level = "Good"
        elif avg_cpl < 100:
            level = "Fair"
        else:
            level = "Needs improvement"
        
        return (
            f"{level} performance overall. "
            f"Average centipawn loss: {avg_cpl:.1f}. "
            f"Move accuracy: {accuracy:.1f}%."
        )
    
    def _summarize_critical_moments(self, features: Dict[str, Any]) -> List[Dict]:
        """Identify and summarize critical game moments."""
        critical_moments = features.get('critical_moments', [])
        
        summaries = []
        for moment in critical_moments[:5]:  # Top 5 critical moments
            move_num = moment.get('move_number', 0)
            eval_swing = moment.get('evaluation_swing', 0.0)
            best_move = moment.get('best_move', 'N/A')
            move_played = moment.get('move_played', 'N/A')
            
            summary = {
                "move_number": move_num,
                "description": f"Critical moment at move {move_num}",
                "evaluation_change": f"{eval_swing:.1f} centipawns",
                "best_continuation": best_move,
                "move_played": move_played,
                "severity": self._classify_severity(eval_swing)
            }
            summaries.append(summary)
        
        return summaries
    
    def _classify_severity(self, eval_swing: float) -> str:
        """Classify the severity of an evaluation swing."""
        if abs(eval_swing) < 100:
            return "minor"
        elif abs(eval_swing) < 300:
            return "moderate"
        elif abs(eval_swing) < 500:
            return "serious"
        else:
            return "critical"
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[str]:
        """Detect recurring patterns in the game."""
        patterns = []
        
        # Time pressure patterns
        if features.get('time_trouble', False):
            patterns.append("Time management issues in critical positions")
        
        # Material imbalances
        if features.get('material_imbalance', 0) > 300:
            patterns.append("Significant material advantage")
        elif features.get('material_imbalance', 0) < -300:
            patterns.append("Significant material disadvantage")
        
        # Repeated mistakes in phase
        blunders_opening = features.get('blunders_opening', 0)
        blunders_middlegame = features.get('blunders_middlegame', 0)
        blunders_endgame = features.get('blunders_endgame', 0)
        
        if blunders_opening > 1:
            patterns.append("Recurring errors in opening phase")
        if blunders_middlegame > 2:
            patterns.append("Tactical oversights in middlegame")
        if blunders_endgame > 1:
            patterns.append("Endgame technique needs improvement")
        
        return patterns
    
    def _summarize_tactical_motifs(self, features: Dict[str, Any]) -> List[str]:
        """Summarize tactical motifs present in the game."""
        motifs = features.get('tactical_motifs', [])
        
        return [self.tactical_motifs_map.get(motif, motif) for motif in motifs]
    
    def _summarize_positional_themes(self, features: Dict[str, Any]) -> List[str]:
        """Summarize positional themes."""
        themes = features.get('positional_themes', [])
        
        return [self.positional_themes_map.get(theme, theme) for theme in themes]
    
    def _analyze_errors(self, features: Dict[str, Any]) -> str:
        """Analyze player errors."""
        blunders = features.get('blunders', 0)
        mistakes = features.get('mistakes', 0)
        inaccuracies = features.get('inaccuracies', 0)
        
        total_errors = blunders + mistakes + inaccuracies
        
        if total_errors == 0:
            return "Nearly flawless performance with no significant errors."
        
        error_breakdown = []
        if blunders > 0:
            error_breakdown.append(f"{blunders} blunder(s)")
        if mistakes > 0:
            error_breakdown.append(f"{mistakes} mistake(s)")
        if inaccuracies > 0:
            error_breakdown.append(f"{inaccuracies} inaccuracy(ies)")
        
        return f"Total errors: {total_errors} - " + ", ".join(error_breakdown) + "."
    
    def summarize_player_history(self, 
                                  games_df: pd.DataFrame, 
                                  player_id: str = None) -> Dict[str, Any]:
        """
        Aggregate patterns from multiple games to create player profile.
        
        Args:
            games_df: DataFrame with multiple game features
            player_id: Optional player identifier
            
        Returns:
            Player profile summary with:
            - most_frequent_mistakes
            - strengths
            - weaknesses
            - training_recommendations
        """
        logger.info(f"Analyzing player history: {len(games_df)} games")
        
        # Calculate aggregate statistics
        avg_cpl = games_df['avg_centipawn_loss'].mean()
        total_blunders = games_df['blunders'].sum()
        total_mistakes = games_df['mistakes'].sum()
        
        # Identify weaknesses
        weaknesses = []
        if avg_cpl > 80:
            weaknesses.append("High average centipawn loss")
        if games_df['blunders_endgame'].mean() > 0.5:
            weaknesses.append("Endgame errors")
        if games_df['time_trouble'].mean() > 0.3:
            weaknesses.append("Time management")
        
        # Identify strengths
        strengths = []
        if games_df['accuracy'].mean() > 85:
            strengths.append("High move accuracy")
        if games_df['tactical_motifs'].apply(len).mean() > 3:
            strengths.append("Strong tactical awareness")
        
        profile = {
            "player_id": player_id,
            "games_analyzed": len(games_df),
            "average_centipawn_loss": avg_cpl,
            "total_blunders": int(total_blunders),
            "total_mistakes": int(total_mistakes),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "most_frequent_errors": self._find_frequent_errors(games_df),
            "training_recommendations": self._generate_training_recommendations(weaknesses)
        }
        
        return profile
    
    def _find_frequent_errors(self, games_df: pd.DataFrame) -> List[str]:
        """Find most frequent types of errors across games."""
        # TODO: Implement error frequency analysis
        return ["Tactical oversights in middlegame", "King safety neglect"]
    
    def _generate_training_recommendations(self, weaknesses: List[str]) -> List[str]:
        """Generate training recommendations based on weaknesses."""
        recommendations_map = {
            "High average centipawn loss": "Practice calculating variations deeper",
            "Endgame errors": "Study fundamental endgames (rook, pawn endings)",
            "Time management": "Practice time control with clock",
            "Tactical oversights": "Daily tactical puzzles (20-30 min)",
            "King safety neglect": "Study classical attacking games"
        }
        
        return [recommendations_map.get(w, f"Focus on: {w}") for w in weaknesses]


# Example usage
if __name__ == "__main__":
    # Example game features
    example_features = {
        'opening_name': 'Italian Game - Giuoco Piano (C54)',
        'opening_evaluation': 15.0,
        'avg_centipawn_loss': 45.0,
        'accuracy': 88.5,
        'blunders': 1,
        'mistakes': 2,
        'inaccuracies': 3,
        'blunders_opening': 0,
        'blunders_middlegame': 1,
        'blunders_endgame': 0,
        'time_trouble': False,
        'material_imbalance': 0,
        'tactical_motifs': ['fork', 'pin'],
        'positional_themes': ['king_safety', 'piece_activity'],
        'critical_moments': [
            {
                'move_number': 15,
                'evaluation_swing': -250.0,
                'best_move': 'Nf3',
                'move_played': 'Ng5'
            }
        ]
    }
    
    # Create summarizer and test
    summarizer = FeatureSummarizer()
    summary = summarizer.summarize_game(example_features)
    
    print("=" * 70)
    print("GAME SUMMARY")
    print("=" * 70)
    print(f"\nOpening: {summary['opening']}")
    print(f"\nPerformance: {summary['performance_summary']}")
    print(f"\nError Analysis: {summary['error_analysis']}")
    print(f"\nPatterns: {', '.join(summary['patterns_detected'])}")
    print(f"\nTactical Motifs: {', '.join(summary['tactical_motifs'])}")
    print(f"\nCritical Moments: {len(summary['critical_moments'])} identified")
