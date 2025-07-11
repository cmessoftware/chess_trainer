"""
Tactical Analysis Module for Chess Trainer

This module provides functionality for loading and analyzing chess tactics.
"""

import os
import pandas as pd
import json
from typing import List, Dict, Any
import streamlit as st


def load_all_tactics(data_dir: str = "data/tactics") -> List[Dict[str, Any]]:
    """
    Load all tactics from the data directory.

    Args:
        data_dir: Directory containing tactics files

    Returns:
        List of tactics dictionaries
    """
    tactics = []

    # Get the absolute path to the data directory
    if not os.path.isabs(data_dir):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )  # Go up from src/scripts/
        data_dir = os.path.join(base_dir, data_dir)

    if not os.path.exists(data_dir):
        st.warning(f"Tactics directory not found: {data_dir}")
        return []

    # Look for tactics files
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)

        try:
            if filename.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tactics.extend(data)
                    else:
                        tactics.append(data)

            elif filename.endswith(".csv"):
                df = pd.read_csv(file_path)
                tactics.extend(df.to_dict("records"))

        except Exception as e:
            st.warning(f"Could not load tactics file {filename}: {str(e)}")

    return tactics


def filter_tactics_by_theme(
    tactics: List[Dict[str, Any]], theme: str
) -> List[Dict[str, Any]]:
    """
    Filter tactics by theme.

    Args:
        tactics: List of tactics dictionaries
        theme: Theme to filter by

    Returns:
        Filtered list of tactics
    """
    if not theme or theme.lower() == "all":
        return tactics

    filtered = []
    for tactic in tactics:
        # Check different possible fields for theme information
        theme_fields = ["theme", "themes", "category", "type", "tags"]
        for field in theme_fields:
            if field in tactic:
                value = tactic[field]
                if isinstance(value, str) and theme.lower() in value.lower():
                    filtered.append(tactic)
                    break
                elif isinstance(value, list) and any(
                    theme.lower() in str(t).lower() for t in value
                ):
                    filtered.append(tactic)
                    break

    return filtered


def filter_tactics_by_difficulty(
    tactics: List[Dict[str, Any]], difficulty: str
) -> List[Dict[str, Any]]:
    """
    Filter tactics by difficulty level.

    Args:
        tactics: List of tactics dictionaries
        difficulty: Difficulty level to filter by

    Returns:
        Filtered list of tactics
    """
    if not difficulty or difficulty.lower() == "all":
        return tactics

    filtered = []
    for tactic in tactics:
        # Check different possible fields for difficulty information
        difficulty_fields = ["difficulty", "level", "rating", "elo"]
        for field in difficulty_fields:
            if field in tactic:
                value = tactic[field]
                if isinstance(value, str) and difficulty.lower() in value.lower():
                    filtered.append(tactic)
                    break
                elif isinstance(value, (int, float)):
                    # Map numeric ratings to difficulty levels
                    if difficulty.lower() == "easy" and value < 1200:
                        filtered.append(tactic)
                        break
                    elif difficulty.lower() == "medium" and 1200 <= value < 1800:
                        filtered.append(tactic)
                        break
                    elif difficulty.lower() == "hard" and value >= 1800:
                        filtered.append(tactic)
                        break

    return filtered


def get_tactic_themes(tactics: List[Dict[str, Any]]) -> List[str]:
    """
    Extract all unique themes from tactics.

    Args:
        tactics: List of tactics dictionaries

    Returns:
        List of unique themes
    """
    themes = set()

    for tactic in tactics:
        theme_fields = ["theme", "themes", "category", "type", "tags"]
        for field in theme_fields:
            if field in tactic:
                value = tactic[field]
                if isinstance(value, str):
                    themes.add(value)
                elif isinstance(value, list):
                    themes.update(str(t) for t in value)

    return sorted(list(themes))


def get_tactic_difficulties(tactics: List[Dict[str, Any]]) -> List[str]:
    """
    Extract all unique difficulty levels from tactics.

    Args:
        tactics: List of tactics dictionaries

    Returns:
        List of unique difficulty levels
    """
    difficulties = set()

    for tactic in tactics:
        difficulty_fields = ["difficulty", "level", "rating", "elo"]
        for field in difficulty_fields:
            if field in tactic:
                value = tactic[field]
                if isinstance(value, str):
                    difficulties.add(value)
                elif isinstance(value, (int, float)):
                    # Convert numeric ratings to difficulty levels
                    if value < 1200:
                        difficulties.add("Easy")
                    elif value < 1800:
                        difficulties.add("Medium")
                    else:
                        difficulties.add("Hard")

    return sorted(list(difficulties))


def analyze_tactics_performance(tactics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze tactics performance and provide statistics.

    Args:
        tactics: List of tactics dictionaries

    Returns:
        Dictionary with performance statistics
    """
    if not tactics:
        return {
            "total_tactics": 0,
            "themes": [],
            "difficulties": [],
            "average_rating": 0,
        }

    analysis = {
        "total_tactics": len(tactics),
        "themes": get_tactic_themes(tactics),
        "difficulties": get_tactic_difficulties(tactics),
    }

    # Calculate average rating if available
    ratings = []
    for tactic in tactics:
        for field in ["rating", "elo"]:
            if field in tactic and isinstance(tactic[field], (int, float)):
                ratings.append(tactic[field])
                break

    analysis["average_rating"] = sum(ratings) / len(ratings) if ratings else 0

    return analysis


# Sample tactics data for testing when no files are available
SAMPLE_TACTICS = [
    {
        "id": 1,
        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        "moves": ["Qh4+", "g3", "Qxe4+"],
        "theme": "Fork",
        "difficulty": "Easy",
        "rating": 1000,
        "description": "Simple fork tactic",
    },
    {
        "id": 2,
        "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 1 4",
        "moves": ["Nxe4", "dxe4", "Qh4+"],
        "theme": "Pin",
        "difficulty": "Medium",
        "rating": 1400,
        "description": "Pin the king to win material",
    },
    {
        "id": 3,
        "fen": "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 w - - 4 6",
        "moves": ["Ng5", "h6", "Nxf7"],
        "theme": "Sacrifice",
        "difficulty": "Hard",
        "rating": 1800,
        "description": "Knight sacrifice for checkmate",
    },
]


def get_sample_tactics() -> List[Dict[str, Any]]:
    """
    Get sample tactics for testing purposes.

    Returns:
        List of sample tactics
    """
    return SAMPLE_TACTICS.copy()
