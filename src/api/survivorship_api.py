"""
API Endpoint for Survivorship Bias Analysis.

This module provides HTTP API access to the Survivorship Bias Analyzer.
"""

from flask import Flask, jsonify, request
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent  # Go up from src/api to src/
sys.path.insert(0, str(src_path))

from analysis.survivorship_bias import SurvivorshipBiasAnalyzer
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/analysis/survivorship", methods=["GET"])
def analyze_survivorship_bias():
    """
    Analyze survivorship bias patterns in the chess dataset.

    Query Parameters:
    - source: Filter by data source (novice, elite, personal, etc.) [optional]
    - format: Response format (json, summary) [default: json]

    Returns:
    JSON response with survivorship bias analysis results.
    """
    try:
        # Get query parameters
        source_filter = request.args.get("source", None)
        response_format = request.args.get("format", "json")

        logger.info(
            f"Starting survivorship bias analysis via API - source: {source_filter or 'ALL'}"
        )

        # Initialize analyzer
        db_url = os.environ.get("CHESS_TRAINER_DB_URL")
        analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)

        # Perform analysis
        results = analyzer.analyze_dataset(source_filter=source_filter)

        # Format response based on requested format
        if response_format == "summary":
            return jsonify(
                {
                    "status": "success",
                    "summary": {
                        "total_games": results["dataset_overview"].get(
                            "total_games", 0
                        ),
                        "alerts_generated": len(results.get("alerts", [])),
                        "critical_alerts": len(
                            [
                                alert
                                for alert in results.get("alerts", [])
                                if alert.get("criticality") == "CRITICAL"
                            ]
                        ),
                        "emergency_action_required": results.get(
                            "emergency_plan", {}
                        ).get("requires_immediate_attention", False),
                        "data_sources": list(
                            results["dataset_overview"].get("sources", {}).keys()
                        ),
                    },
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            )
        else:
            # Full JSON response
            return jsonify(
                {
                    "status": "success",
                    "data": results,
                    "metadata": {
                        "source_filter": source_filter,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                        "analyzer_version": "1.0.0",
                    },
                }
            )

    except Exception as e:
        logger.error(f"Error in survivorship bias analysis API: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/analysis/survivorship/health", methods=["GET"])
def health_check():
    """Health check endpoint for the survivorship bias analyzer."""
    try:
        # Test database connection
        db_url = os.environ.get("CHESS_TRAINER_DB_URL")
        analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)
        analyzer._init_db_connection()

        return jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "analyzer": "ready",
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            ),
            503,
        )


@app.route("/analysis/survivorship/sources", methods=["GET"])
def get_available_sources():
    """Get available data sources for survivorship bias analysis."""
    try:
        db_url = os.environ.get("CHESS_TRAINER_DB_URL")
        analyzer = SurvivorshipBiasAnalyzer(db_url=db_url)

        # Quick analysis to get sources
        results = analyzer.analyze_dataset()
        sources = results["dataset_overview"].get("sources", {})

        return jsonify(
            {
                "status": "success",
                "sources": [
                    {"name": source, "game_count": count, "available": count > 0}
                    for source, count in sources.items()
                ],
                "total_sources": len(sources),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting available sources: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return (
        jsonify(
            {
                "status": "error",
                "error": "Endpoint not found",
                "available_endpoints": [
                    "/analysis/survivorship",
                    "/analysis/survivorship/health",
                    "/analysis/survivorship/sources",
                ],
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }
        ),
        404,
    )


if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
