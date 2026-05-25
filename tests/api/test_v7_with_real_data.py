"""
Test V7 pipeline with real database data.

Usage:
    python test_v7_with_real_data.py [game_id]

If no game_id provided, uses first available game from database.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.database import DATABASE_URL
from src.api.models.database_models import Games, Features
from src.api import models
from src.api.services.analysis_pipeline import generate_validated_feedback, create_v7_repos
from src.api.services.analysis_pipeline.integration_example import LLMClientWrapper


def main():
    """Test V7 pipeline with real data."""
    # Get game_id from command line
    if len(sys.argv) < 2:
        print("❌ Usage: python test_v7_with_real_data.py <game_id>")
        print("\nExample:")
        print("  python test_v7_with_real_data.py aec7f86c...")
        return
    
    game_id = sys.argv[1]

    print("="*60)
    print("🧪 TESTING V7 PIPELINE WITH REAL DATA")
    print("="*60)
    print(f"Game ID: {game_id}")

    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if game has features
        features_count = db.query(Features).filter(
            Features.game_id == game_id
        ).count()

        if features_count == 0:
            print(f"\n❌ Game {game_id} has no features in database")
            print("   Run feature extraction first")
            return

        print(f"\n✅ Game has {features_count} moves with features")

        # Create V7 repository adapter
        print("\n🔧 Creating V7 repository adapter...")
        repos = create_v7_repos(db, models)

        # Create mock LLM client (replace with real OpenAI client when ready)
        print("🔧 Creating mock LLM client...")
        mock_llm_client = type(
            "MockLLMClient",
            (),
            {
                "complete": lambda self, prompt: (
                    "Diagnosis: Error detectado en esta jugada según análisis\n"
                    "Better move: Se recomienda considerar alternativa más precisa\n"
                    "Training rule: Evaluar todas las consecuencias antes de mover"
                )
            },
        )()
        llm_client = LLMClientWrapper(mock_llm_client)

        # Generate V7 feedback
        print(f"\n🚀 Generating V7 feedback for game {game_id}...")
        print("   Threshold: 90 cp_loss")
        print("   Max items: 10")

        result = generate_validated_feedback(
            game_id,
            repos=repos,
            llm_client=llm_client,
            cp_loss_threshold=90,
            max_items=10,
        )

        # Display results
        print("\n" + "="*60)
        print("📊 V7 PIPELINE RESULTS")
        print("="*60)

        print(f"\nGame ID: {result['game_id']}")
        print(f"\n📈 Statistics:")
        print(f"   Moves analyzed: {result['stats']['num_moves_analyzed']}")
        print(f"   Critical moves: {result['stats']['num_critical']}")
        print(f"   ML/Stockfish disagreements: {result['stats']['num_disagreements']}")

        if result['critical_feedback']:
            print(f"\n🔍 Critical Moves Details:")
            for i, feedback in enumerate(result['critical_feedback'], 1):
                print(f"\n   {i}. Ply {feedback['ply']} - {feedback['final_label'].upper()}")
                print(f"      Model disagreement: {feedback['model_disagreement']}")
                
                # Display explanation
                expl = feedback['explanation']
                print(f"      {expl['diagnosis']}")
                print(f"      {expl['better_move']}")
                print(f"      {expl['training_rule']}")

                # Display pack details (validator)
                pack = feedback.get('pack', {})
                validator = pack.get('validator', {})
                if validator:
                    print(f"      Validator: predicted={validator.get('predicted_label')}, "
                          f"stockfish={validator.get('stockfish_label')}, "
                          f"cp_loss={validator.get('cp_loss')}")
        else:
            print("\n✅ No critical moves detected (all moves below threshold)")

        print("\n" + "="*60)
        print("✅ V7 PIPELINE TEST COMPLETED SUCCESSFULLY")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error testing V7 pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
