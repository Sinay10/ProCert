"""
Example usage of the Recommendation Engine Service.

This script demonstrates how to use the recommendation engine to get personalized
study recommendations, identify weak areas, and generate study paths.
"""

import json
import boto3
from datetime import datetime, timedelta
from shared.recommendation_engine import RecommendationEngine
from shared.models import CertificationType, StudyRecommendation


def main():
    """Demonstrate recommendation engine functionality."""
    print("ProCert Recommendation Engine Example")
    print("=" * 50)
    
    # Initialize the recommendation engine
    # Note: In a real deployment, these would be actual DynamoDB table names
    recommendation_engine = RecommendationEngine(
        user_progress_table_name='procert-user-progress-123456789012',
        content_metadata_table_name='procert-content-metadata-123456789012',
        recommendations_table_name='procert-recommendations-123456789012',
        region_name='us-east-1'
    )
    
    user_id = 'example-user-123'
    certification_type = CertificationType.SAA
    
    print(f"\n1. Getting personalized recommendations for user: {user_id}")
    print(f"   Target certification: {certification_type.value}")
    
    try:
        # Get personalized recommendations
        recommendations = recommendation_engine.get_personalized_recommendations(
            user_id=user_id,
            certification_type=certification_type,
            limit=5
        )
        
        print(f"\n   Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec.type.title()} - Priority: {rec.priority}")
            print(f"      Reasoning: {rec.reasoning}")
            print(f"      Estimated time: {rec.estimated_time_minutes} minutes")
            if rec.content_id:
                print(f"      Content ID: {rec.content_id}")
            print()
        
    except Exception as e:
        print(f"   Error getting recommendations: {str(e)}")
    
    print("\n2. Identifying weak areas")
    
    try:
        # Identify weak areas
        weak_areas = recommendation_engine.identify_weak_areas(
            user_id=user_id,
            certification_type=certification_type
        )
        
        print(f"   Analysis: {weak_areas.get('analysis', 'No analysis available')}")
        
        if weak_areas.get('weak_categories'):
            print("   Weak categories:")
            for weak_cat in weak_areas['weak_categories']:
                print(f"   - {weak_cat['category']}: {weak_cat['avg_score']:.1f}% average")
        
        if weak_areas.get('recommendations'):
            print("   Recommendations:")
            for rec in weak_areas['recommendations'][:3]:  # Show first 3
                print(f"   - {rec}")
        
    except Exception as e:
        print(f"   Error identifying weak areas: {str(e)}")
    
    print("\n3. Getting content difficulty progression")
    
    try:
        # Get content difficulty progression
        progression = recommendation_engine.get_content_difficulty_progression(
            user_id=user_id,
            certification_type=certification_type
        )
        
        print(f"   Current level: {progression['current_level']}")
        print(f"   Recommended level: {progression['recommended_level']}")
        print(f"   Overall readiness: {progression.get('overall_readiness', 0):.2f}")
        
        if progression.get('progression_path'):
            print("   Progression path:")
            for step in progression['progression_path'][:3]:  # Show first 3 steps
                print(f"   - {step}")
        
    except Exception as e:
        print(f"   Error getting progression: {str(e)}")
    
    print("\n4. Generating personalized study path")
    
    try:
        # Generate study path
        study_path = recommendation_engine.generate_study_path(
            user_id=user_id,
            certification_type=certification_type
        )
        
        print(f"   Total estimated time: {study_path.get('total_estimated_hours', 0)} hours")
        
        if study_path.get('study_phases'):
            print("   Study phases:")
            for phase in study_path['study_phases']:
                print(f"   Phase {phase['phase']}: {phase['title']}")
                print(f"   - Estimated time: {phase['estimated_time_hours']} hours")
                print(f"   - Topics: {', '.join(phase.get('topics', []))}")
                print()
        
        if study_path.get('milestones'):
            print("   Milestones:")
            for milestone in study_path['milestones'][:3]:  # Show first 3
                print(f"   - {milestone['milestone']} ({milestone['estimated_completion_hours']}h)")
        
    except Exception as e:
        print(f"   Error generating study path: {str(e)}")
    
    print("\n5. Recording recommendation feedback")
    
    try:
        # Create a sample recommendation for feedback
        sample_rec = StudyRecommendation(
            recommendation_id='sample-rec-123',
            user_id=user_id,
            type='content',
            priority=8,
            reasoning='Example recommendation for feedback',
            estimated_time_minutes=30
        )
        
        # Record feedback
        success = recommendation_engine.record_recommendation_feedback(
            user_id=user_id,
            recommendation_id=sample_rec.recommendation_id,
            action='accepted',
            feedback_data={'rating': 5, 'comment': 'Very helpful!'}
        )
        
        print(f"   Feedback recorded successfully: {success}")
        
    except Exception as e:
        print(f"   Error recording feedback: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Recommendation Engine Example Complete!")
    print("\nNote: This example uses mock data and may not return actual results")
    print("without proper DynamoDB tables and user progress data.")


if __name__ == '__main__':
    main()