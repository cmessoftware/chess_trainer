#!/usr/bin/env python3
"""
Pipeline Helper Module

This module provides database operations for the pipeline using the repository pattern
with SQLAlchemy, replacing hardcoded queries in run_pipeline.sh.
"""

import warnings
import sys
import os
import logging
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Tuple, Optional
from sqlalchemy import select, func, distinct, and_, not_

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress all SQLAlchemy and database connection messages
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)

# Import database modules with complete output suppression
warnings.filterwarnings("ignore", category=UserWarning)

# Redirect all stdout/stderr during imports and database operations
f_out = io.StringIO()
f_err = io.StringIO()

with redirect_stdout(f_out), redirect_stderr(f_err):
    from db.session import get_session
    from db.models.games import Games
    from db.models.analyzed_tacticals import Analyzed_tacticals


class PipelineRepository:
    """Repository class for pipeline-specific database operations."""

    def __init__(self, session_factory=get_session):
        self.session_factory = session_factory

    def get_available_sources(self) -> List[str]:
        """
        Get all distinct sources from the games table.

        Returns:
            List[str]: List of available sources, sorted alphabetically
        """
        with self.session_factory() as session:
            try:
                stmt = select(distinct(Games.source)).where(
                    Games.source.is_not(None)
                ).order_by(Games.source)

                result = session.execute(stmt).scalars().all()
                return [source for source in result if source]
            except Exception as e:
                session.rollback()
                raise e

    def count_games_by_source(self, source: str) -> int:
        """
        Count total games for a specific source.

        Args:
            source (str): The source to count games for

        Returns:
            int: Number of games for the source
        """
        with self.session_factory() as session:
            try:
                stmt = select(func.count(Games.game_id)).where(
                    Games.source == source
                )

                result = session.execute(stmt).scalar()
                return result or 0
            except Exception as e:
                session.rollback()
                raise e

    def count_unanalyzed_games_by_source(self, source: str) -> int:
        """
        Count games for a specific source that haven't been analyzed for tactics.

        Args:
            source (str): The source to count unanalyzed games for

        Returns:
            int: Number of unanalyzed games for the source
        """
        with self.session_factory() as session:
            try:
                # Subquery to get analyzed game IDs
                analyzed_subquery = select(Analyzed_tacticals.game_id)

                # Count games that are not in the analyzed_tacticals table
                stmt = select(func.count(Games.game_id)).where(
                    and_(
                        Games.source == source,
                        not_(Games.game_id.in_(analyzed_subquery))
                    )
                )

                result = session.execute(stmt).scalar()
                return result or 0
            except Exception as e:
                session.rollback()
                raise e

    def count_games_missing_tactical_by_source(self, source: str) -> int:
        """
        Count games for a specific source that have features but are missing tactical data.

        Args:
            source: The source to count games for

        Returns:
            int: Count of games missing tactical features
        """
        from db.models.features import Features

        with self.session_factory() as session:
            stmt = select(func.count(distinct(Features.game_id))).select_from(
                Features
            ).join(
                Games, Features.game_id == Games.game_id
            ).where(
                and_(
                    Games.source == source,
                    Features.fen.is_not(None),
                    Features.move_uci.is_not(None),
                    Features.score_diff.is_(None)
                )
            )

            result = session.execute(stmt).scalar()
            return result or 0

    def get_pipeline_stats(self) -> dict:
        """
        Get comprehensive pipeline statistics.

        Returns:
            dict: Statistics including sources, total games, analyzed games, etc.
        """
        with self.session_factory() as session:
            try:
                stats = {}

                # Get all sources
                sources = self.get_available_sources()
                stats['sources'] = sources

                # Get total games count
                total_games_stmt = select(func.count(Games.game_id))
                stats['total_games'] = session.execute(
                    total_games_stmt).scalar() or 0

                # Get total analyzed games count
                total_analyzed_stmt = select(
                    func.count(Analyzed_tacticals.game_id))
                stats['total_analyzed'] = session.execute(
                    total_analyzed_stmt).scalar() or 0

                # Get stats per source
                source_stats = {}
                for source in sources:
                    source_stats[source] = {
                        'total_games': self.count_games_by_source(source),
                        'unanalyzed_games': self.count_unanalyzed_games_by_source(source)
                    }
                    source_stats[source]['analyzed_games'] = (
                        source_stats[source]['total_games'] -
                        source_stats[source]['unanalyzed_games']
                    )

                stats['source_stats'] = source_stats

                return stats
            except Exception as e:
                session.rollback()
                raise e

    def has_unanalyzed_games(self, source: str) -> bool:
        """
        Check if a source has any unanalyzed games.

        Args:
            source (str): The source to check

        Returns:
            bool: True if there are unanalyzed games, False otherwise
        """
        return self.count_unanalyzed_games_by_source(source) > 0

    def get_sources_with_unanalyzed_games(self) -> List[Tuple[str, int]]:
        """
        Get sources that have unanalyzed games along with their counts.

        Returns:
            List[Tuple[str, int]]: List of (source, unanalyzed_count) tuples
        """
        sources = self.get_available_sources()
        sources_with_unanalyzed = []

        for source in sources:
            unanalyzed_count = self.count_unanalyzed_games_by_source(source)
            if unanalyzed_count > 0:
                sources_with_unanalyzed.append((source, unanalyzed_count))

        return sources_with_unanalyzed


class PipelineHelper:
    """Helper class for pipeline operations using the repository."""

    def __init__(self):
        self.repository = PipelineRepository()

    def get_sources_for_batch_processing(self) -> List[str]:
        """
        Get sources that need batch processing (have unanalyzed games).

        Returns:
            List[str]: List of sources with unanalyzed games
        """
        sources_with_unanalyzed = self.repository.get_sources_with_unanalyzed_games()
        return [source for source, _ in sources_with_unanalyzed]

    def calculate_batches_needed(self, source: str, batch_size: int = 10000) -> int:
        """
        Calculate number of batches needed for a source.

        Args:
            source (str): The source to calculate batches for
            batch_size (int): Size of each batch (default: 10000)

        Returns:
            int: Number of batches needed
        """
        unanalyzed_count = self.repository.count_unanalyzed_games_by_source(
            source)
        if unanalyzed_count == 0:
            return 0
        return (unanalyzed_count + batch_size - 1) // batch_size

    def print_pipeline_summary(self):
        """Print a summary of the pipeline state."""
        stats = self.repository.get_pipeline_stats()

        print(f"📊 Pipeline Summary:")
        print(f"   Total games: {stats['total_games']}")
        print(f"   Total analyzed: {stats['total_analyzed']}")
        print(f"   Available sources: {', '.join(stats['sources'])}")
        print()

        for source, source_stat in stats['source_stats'].items():
            print(f"   {source}:")
            print(f"     Total: {source_stat['total_games']}")
            print(f"     Analyzed: {source_stat['analyzed_games']}")
            print(f"     Unanalyzed: {source_stat['unanalyzed_games']}")


def main():
    """Command-line interface for pipeline helper operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Helper CLI")
    parser.add_argument("--operation", required=True, choices=[
        'get-sources',
        'count-games',
        'count-unanalyzed',
        'count-missing-tactical',
        'pipeline-stats',
        'sources-with-unanalyzed'
    ], help="Operation to perform")
    parser.add_argument(
        "--source", help="Source name for source-specific operations")
    parser.add_argument("--format", choices=['plain', 'space-separated'],
                        default='plain', help="Output format")

    args = parser.parse_args()

    helper = PipelineHelper()
    repository = helper.repository

    try:
        if args.operation == 'get-sources':
            sources = repository.get_available_sources()
            if args.format == 'space-separated':
                print(' '.join(sources))
            else:
                for source in sources:
                    print(source)

        elif args.operation == 'count-games':
            if not args.source:
                print("Error: --source required for count-games operation",
                      file=sys.stderr)
                sys.exit(1)
            count = repository.count_games_by_source(args.source)
            print(count)

        elif args.operation == 'count-unanalyzed':
            if not args.source:
                print(
                    "Error: --source required for count-unanalyzed operation", file=sys.stderr)
                sys.exit(1)
            count = repository.count_unanalyzed_games_by_source(args.source)
            print(count)

        elif args.operation == 'count-missing-tactical':
            if not args.source:
                print(
                    "Error: --source required for count-missing-tactical operation", file=sys.stderr)
                sys.exit(1)
            count = repository.count_games_missing_tactical_by_source(
                args.source)
            print(count)

        elif args.operation == 'pipeline-stats':
            helper.print_pipeline_summary()

        elif args.operation == 'sources-with-unanalyzed':
            sources_with_unanalyzed = repository.get_sources_with_unanalyzed_games()
            if args.format == 'space-separated':
                sources = [source for source, _ in sources_with_unanalyzed]
                print(' '.join(sources))
            else:
                for source, count in sources_with_unanalyzed:
                    print(f"{source}: {count}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
