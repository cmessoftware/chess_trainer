#!/usr/bin/env python3
"""
List games with complete feature analysis
"""
import os
import argparse
from sqlalchemy import create_engine, text

def main():
    parser = argparse.ArgumentParser(description='List games with complete feature analysis')
    parser.add_argument(
        '--source',
        type=str,
        help='Filter by game source (e.g., stockfish, personal, elite, novice, fide)',
        default=None
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of games to show (default: 20)',
        default=20
    )
    parser.add_argument(
        '--player',
        type=str,
        help='Filter by player name (exact match, searches in both white_player and black_player)',
        default=None
    )
    args = parser.parse_args()

    db_url = os.getenv('CHESS_TRAINER_DB_URL', 
        'postgresql://chess:chess_pass@localhost:5432/chess_trainer_db')

    engine = create_engine(db_url)

    # Build query with optional filters
    where_clauses = []
    if args.source:
        where_clauses.append("g.source = :source")
    if args.player:
        where_clauses.append("(g.white_player = :player OR g.black_player = :player)")
    
    where_clause = ""
    if where_clauses:
        where_clause = "AND " + " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        f.game_id,
        COUNT(*) as total_moves,
        COUNT(f.score_diff) as moves_with_score,
        COUNT(f.error_label) as moves_with_errors,
        SUM(CASE WHEN f.player_color = 1 THEN 1 ELSE 0 END) as white_moves,
        SUM(CASE WHEN f.player_color = 0 THEN 1 ELSE 0 END) as black_moves,
        MAX(g.white_player) as white,
        MAX(g.black_player) as black,
        MAX(g.opening) as opening,
        MAX(g.source) as source
    FROM features f
    LEFT JOIN games g ON f.game_id = g.game_id
    WHERE 1=1 {where_clause}
    GROUP BY f.game_id
    HAVING COUNT(f.score_diff) > 0  -- Only games with actual analysis
    ORDER BY COUNT(f.score_diff) DESC
    LIMIT :limit;
    """

    print("\n" + "="*80)
    filters = []
    if args.source:
        filters.append(f"Source: {args.source.upper()}")
    if args.player:
        filters.append(f"Player: {args.player}")
    
    if filters:
        print(f"🎯 GAMES WITH COMPLETE FEATURE ANALYSIS - {', '.join(filters)}")
    else:
        print("🎯 GAMES WITH COMPLETE FEATURE ANALYSIS - All Games")
    print("="*80 + "\n")

    with engine.connect() as conn:
        params = {'limit': args.limit}
        if args.source:
            params['source'] = args.source
        if args.player:
            params['player'] = args.player
        
        result = conn.execute(text(query), params)
        games = result.fetchall()
        
        if not games:
            print("❌ No games found with score_diff data!")
            if args.source:
                print(f"\nNo games found for source '{args.source}'")
                print("Try without --source filter or use: stockfish, personal, elite, novice, fide")
            if args.player:
                print(f"\nNo games found for player '{args.player}'")
                print("Try a different player name or without --player filter")
            print("\nYou may need to run feature generation:")
            print("   python src/scripts/generate_features_with_tactics.py")
        else:
            print(f"Found {len(games)} games with analysis:\n")
            for i, game in enumerate(games, 1):
                game_id, total, with_score, with_errors, white_moves, black_moves, white, black, opening, source = game
                completeness = (with_score / total * 100) if total > 0 else 0
                print(f"{i}. Opening: {opening or 'Unknown'}")
                print(f"   Players: {white} (W) vs {black} (B)")
                print(f"   Source: {source or 'Unknown'}")
                print(f"   Analysis: {with_score}/{total} moves ({completeness:.0f}% complete)")
                print(f"   Colors: WHITE={white_moves} moves, BLACK={black_moves} moves")
                print(f"   Game ID: {game_id}")
                print()

    print("="*80)
    print("\n💡 To analyze a specific game:")
    print("   python test_coach_pipeline.py --game-id <GAME_ID> --player-color white")
    print("\n💡 To filter results:")
    print("   python list_analyzed_games.py --source stockfish")
    print("   python list_analyzed_games.py --player sergio")
    print("   python list_analyzed_games.py --source personal --player magnus --limit 10")
    print()

if __name__ == '__main__':
    main()
