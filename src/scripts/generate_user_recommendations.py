"""
Generate Personalized Training Recommendations for Chess Trainer Users.

This script creates personalized training recommendations for specific users
using the Training Recommender system with Survivorship Bias integration.

Target Users:
- cmess4401
- cmess1315

Usage:
    python generate_user_recommendations.py
"""

import os
import sys
from datetime import datetime
import json

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Use existing environment variable or default
if not os.environ.get('CHESS_TRAINER_DB_URL'):
    os.environ['CHESS_TRAINER_DB_URL'] = 'postgresql://chess:chess_pass@localhost:5432/chess_trainer_db'

from training.training_recommender import (
    TrainingRecommender, 
    UserProfile, 
    TrainingPriority
)

def create_user_profile_cmess4401() -> UserProfile:
    """
    Create user profile for cmess4401.
    Based on typical intermediate chess player patterns.
    """
    return UserProfile(
        user_id="cmess4401",
        skill_level="intermediate",
        preferred_openings=[
            "Sicilian Defense", 
            "Queen's Gambit", 
            "Italian Game",
            "French Defense"
        ],
        common_mistakes=[
            "time management in complex positions",
            "endgame technique",
            "tactical oversights",
            "opening preparation depth"
        ],
        time_available=75,  # 75 minutes per training session
        focus_areas=["opening", "tactics", "endgame", "middlegame"]
    )

def create_user_profile_cmess1315() -> UserProfile:
    """
    Create user profile for cmess1315.
    Based on typical beginner-intermediate chess player patterns.
    """
    return UserProfile(
        user_id="cmess1315",
        skill_level="beginner",
        preferred_openings=[
            "Italian Game",
            "Queen's Gambit",
            "London System",
            "King's Indian Defense"
        ],
        common_mistakes=[
            "hanging pieces",
            "weak pawn structures",
            "poor piece development",
            "king safety neglect"
        ],
        time_available=60,  # 60 minutes per training session
        focus_areas=["opening", "tactics", "fundamentals"]
    )

def generate_recommendations_for_user(user_profile: UserProfile, recommender: TrainingRecommender):
    """Generate and display recommendations for a specific user."""
    
    print(f"\n{'='*70}")
    print(f"🎯 PERSONALIZED TRAINING RECOMMENDATIONS FOR {user_profile.user_id.upper()}")
    print(f"{'='*70}")
    
    print(f"\n👤 USER PROFILE:")
    print(f"   User ID: {user_profile.user_id}")
    print(f"   Skill Level: {user_profile.skill_level.title()}")
    print(f"   Available Time: {user_profile.time_available} minutes per session")
    print(f"   Preferred Openings: {', '.join(user_profile.preferred_openings)}")
    print(f"   Focus Areas: {', '.join(user_profile.focus_areas)}")
    print(f"   Common Challenges: {', '.join(user_profile.common_mistakes)}")
    
    # Generate recommendations
    recommendations = recommender.generate_user_recommendations(
        user_profile, 
        include_emergency=True
    )
    
    print(f"\n📋 TRAINING RECOMMENDATIONS GENERATED: {len(recommendations)}")
    
    # Group by priority
    priority_groups = {}
    total_time = 0
    
    for rec in recommendations:
        priority = rec.priority.value
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(rec)
        total_time += rec.estimated_time
    
    print(f"⏱️  Total Estimated Training Time: {total_time} minutes ({total_time/60:.1f} hours)")
    
    # Display recommendations by priority
    priority_order = ['EMERGENCY', 'HIGH', 'MEDIUM', 'LOW']
    priority_icons = {
        'EMERGENCY': '🚨',
        'HIGH': '🔥', 
        'MEDIUM': '📚',
        'LOW': '💡'
    }
    
    for priority in priority_order:
        if priority in priority_groups:
            recs = priority_groups[priority]
            print(f"\n{priority_icons[priority]} {priority} PRIORITY ({len(recs)} recommendations):")
            
            for i, rec in enumerate(recs, 1):
                print(f"\n   {i}. {rec.title}")
                print(f"      Category: {rec.category}")
                print(f"      Time: {rec.estimated_time} minutes")
                print(f"      Description: {rec.description}")
                print(f"      Source: {rec.source}")
                
                # Show exercises (first 2 only for brevity)
                if rec.exercises:
                    print(f"      Key Exercises:")
                    for j, exercise in enumerate(rec.exercises[:2], 1):
                        print(f"        {j}. {exercise}")
                    if len(rec.exercises) > 2:
                        print(f"        ... and {len(rec.exercises) - 2} more exercises")
                
                # Show success criteria (first 2 only)
                if rec.success_criteria:
                    print(f"      Success Goals:")
                    for j, criterion in enumerate(rec.success_criteria[:2], 1):
                        print(f"        • {criterion}")
                    if len(rec.success_criteria) > 2:
                        print(f"        • ... and {len(rec.success_criteria) - 2} more goals")
    
    return recommendations

def export_user_training_plan(user_profile: UserProfile, recommendations, recommender: TrainingRecommender):
    """Export training plan for a specific user."""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"training_plan_{user_profile.user_id}_{timestamp}.json"
    
    print(f"\n💾 EXPORTING TRAINING PLAN...")
    
    success = recommender.export_training_plan(recommendations, filename)
    
    if success:
        print(f"   ✅ Training plan exported successfully!")
        print(f"   📄 File: {filename}")
        
        # Show export summary
        emergency_count = len([r for r in recommendations if r.priority == TrainingPriority.EMERGENCY])
        high_count = len([r for r in recommendations if r.priority == TrainingPriority.HIGH])
        total_time = sum(r.estimated_time for r in recommendations)
        
        print(f"   📊 Export Summary:")
        print(f"      • Total Recommendations: {len(recommendations)}")
        print(f"      • Emergency Items: {emergency_count}")
        print(f"      • High Priority Items: {high_count}")
        print(f"      • Total Training Time: {total_time} minutes")
        
        return filename
    else:
        print(f"   ❌ Export failed!")
        return None

def main():
    """Main function to generate recommendations for both users."""
    
    print("🏗️  CHESS TRAINER - PERSONALIZED TRAINING RECOMMENDATIONS")
    print("=" * 80)
    print(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target Users: cmess4401, cmess1315")
    print()
    
    try:
        # Initialize the Training Recommender system
        print("🔧 Initializing Training Recommender System...")
        recommender = TrainingRecommender()
        
        # Run survivorship bias analysis first
        print("📊 Running Survivorship Bias Analysis...")
        analysis_results = recommender.analyze_survivorship_patterns()
        
        if analysis_results:
            alerts = analysis_results.get('alerts', [])
            critical_alerts = [a for a in alerts if a.get('criticality') == 'CRITICAL']
            print(f"   ✅ Analysis completed - {len(alerts)} alerts ({len(critical_alerts)} critical)")
        else:
            print("   ⚠️  Analysis completed with limited data")
        
        # Check emergency status
        emergency_status = recommender.get_emergency_status()
        print(f"   🚨 System Status: {emergency_status['status']}")
        
        if emergency_status['requires_immediate_action']:
            print("   ⚡ IMMEDIATE ACTION REQUIRED - Emergency protocols activated!")
        
        # Generate recommendations for cmess4401
        print(f"\n🎯 Processing User 1: cmess4401...")
        user1_profile = create_user_profile_cmess4401()
        user1_recommendations = generate_recommendations_for_user(user1_profile, recommender)
        user1_export = export_user_training_plan(user1_profile, user1_recommendations, recommender)
        
        # Generate recommendations for cmess1315
        print(f"\n🎯 Processing User 2: cmess1315...")
        user2_profile = create_user_profile_cmess1315()
        user2_recommendations = generate_recommendations_for_user(user2_profile, recommender)
        user2_export = export_user_training_plan(user2_profile, user2_recommendations, recommender)
        
        # Final summary
        print(f"\n{'='*80}")
        print("🏆 GENERATION COMPLETE - SUMMARY")
        print(f"{'='*80}")
        
        print(f"\n👥 USER RECOMMENDATIONS:")
        print(f"   cmess4401: {len(user1_recommendations)} recommendations ({sum(r.estimated_time for r in user1_recommendations)} minutes)")
        print(f"   cmess1315: {len(user2_recommendations)} recommendations ({sum(r.estimated_time for r in user2_recommendations)} minutes)")
        
        print(f"\n📄 EXPORTED FILES:")
        if user1_export:
            print(f"   ✅ {user1_export}")
        if user2_export:
            print(f"   ✅ {user2_export}")
        
        print(f"\n🎯 PRIORITY DISTRIBUTION:")
        
        all_recommendations = user1_recommendations + user2_recommendations
        priority_counts = {}
        for rec in all_recommendations:
            priority = rec.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority in ['EMERGENCY', 'HIGH', 'MEDIUM', 'LOW']:
            count = priority_counts.get(priority, 0)
            if count > 0:
                icon = {'EMERGENCY': '🚨', 'HIGH': '🔥', 'MEDIUM': '📚', 'LOW': '💡'}[priority]
                print(f"   {icon} {priority}: {count}")
        
        print(f"\n✨ Both users now have personalized training plans ready!")
        print("   Users can begin training immediately with their customized recommendations.")
        
        if emergency_status['requires_immediate_action']:
            print("\n🚨 IMPORTANT: Emergency training protocols are active!")
            print("   Users should prioritize EMERGENCY and HIGH priority recommendations first.")
        
    except Exception as e:
        print(f"\n❌ ERROR during recommendation generation:")
        print(f"   Error: {e}")
        print(f"   Type: {type(e).__name__}")
        
        import traceback
        print(f"\n🔍 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()