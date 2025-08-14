"""
Unit tests for the RecommendationEngine class.

Tests cover ML-based recommendation logic, weak area identification,
content difficulty progression, and study path generation.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from shared.recommendation_engine import RecommendationEngine
from shared.models import (
    StudyRecommendation, UserProgress, ContentMetadata, CertificationType,
    DifficultyLevel, ContentType, ProgressType
)


class TestRecommendationEngine:
    """Test cases for RecommendationEngine class."""
    
    @pytest.fixture
    def mock_tables(self):
        """Mock DynamoDB tables."""
        mock_user_progress_table = Mock()
        mock_content_metadata_table = Mock()
        mock_recommendations_table = Mock()
        
        return {
            'user_progress': mock_user_progress_table,
            'content_metadata': mock_content_metadata_table,
            'recommendations': mock_recommendations_table
        }
    
    @pytest.fixture
    def mock_progress_tracker(self):
        """Mock ProgressTracker."""
        return Mock()
    
    @pytest.fixture
    def recommendation_engine(self, mock_tables, mock_progress_tracker):
        """Create RecommendationEngine instance with mocked dependencies."""
        with patch('shared.recommendation_engine.boto3.resource') as mock_resource:
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            
            # Configure table mocks
            mock_dynamodb.Table.side_effect = lambda name: {
                'test-user-progress': mock_tables['user_progress'],
                'test-content-metadata': mock_tables['content_metadata'],
                'test-recommendations': mock_tables['recommendations']
            }.get(name, Mock())
            
            with patch('shared.recommendation_engine.ProgressTracker') as mock_pt_class:
                mock_pt_class.return_value = mock_progress_tracker
                
                engine = RecommendationEngine(
                    user_progress_table_name='test-user-progress',
                    content_metadata_table_name='test-content-metadata',
                    recommendations_table_name='test-recommendations',
                    region_name='us-east-1'
                )
                
                return engine
    
    @pytest.fixture
    def sample_user_progress(self):
        """Sample user progress data."""
        return [
            UserProgress(
                user_id='test-user',
                content_id='content-1',
                progress_type=ProgressType.ANSWERED,
                score=85.0,
                time_spent=300,
                timestamp=datetime.utcnow() - timedelta(days=1)
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-2',
                progress_type=ProgressType.ANSWERED,
                score=65.0,
                time_spent=450,
                timestamp=datetime.utcnow() - timedelta(days=2)
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-3',
                progress_type=ProgressType.COMPLETED,
                score=90.0,
                time_spent=600,
                timestamp=datetime.utcnow() - timedelta(days=3)
            )
        ]
    
    @pytest.fixture
    def sample_content_metadata(self):
        """Sample content metadata."""
        return [
            ContentMetadata(
                content_id='content-1',
                title='EC2 Basics',
                content_type=ContentType.STUDY_GUIDE,
                certification_type=CertificationType.SAA,
                category='EC2',
                difficulty_level=DifficultyLevel.BEGINNER
            ),
            ContentMetadata(
                content_id='content-2',
                title='S3 Advanced',
                content_type=ContentType.STUDY_GUIDE,
                certification_type=CertificationType.SAA,
                category='S3',
                difficulty_level=DifficultyLevel.INTERMEDIATE
            ),
            ContentMetadata(
                content_id='content-3',
                title='VPC Fundamentals',
                content_type=ContentType.STUDY_GUIDE,
                certification_type=CertificationType.SAA,
                category='VPC',
                difficulty_level=DifficultyLevel.BEGINNER
            )
        ]
    
    def test_initialization(self, recommendation_engine):
        """Test RecommendationEngine initialization."""
        assert recommendation_engine.user_progress_table_name == 'test-user-progress'
        assert recommendation_engine.content_metadata_table_name == 'test-content-metadata'
        assert recommendation_engine.recommendations_table_name == 'test-recommendations'
        assert recommendation_engine.region_name == 'us-east-1'
    
    def test_get_personalized_recommendations_new_user(self, recommendation_engine, mock_progress_tracker):
        """Test recommendations for new user with no progress."""
        # Mock empty progress
        mock_progress_tracker.get_user_progress.return_value = []
        
        # Mock beginner content
        beginner_content = [
            ContentMetadata(
                content_id='beginner-1',
                title='AWS Basics',
                content_type=ContentType.STUDY_GUIDE,
                certification_type=CertificationType.SAA,
                category='Fundamentals',
                difficulty_level=DifficultyLevel.BEGINNER
            )
        ]
        
        with patch.object(recommendation_engine, '_get_content_by_difficulty', return_value=beginner_content):
            with patch.object(recommendation_engine, '_store_recommendations'):
                recommendations = recommendation_engine.get_personalized_recommendations(
                    'new-user', CertificationType.SAA, 5
                )
        
        assert len(recommendations) == 1
        assert recommendations[0].type == 'content'
        assert recommendations[0].priority == 9
        assert 'foundational' in recommendations[0].reasoning.lower()
    
    def test_get_personalized_recommendations_existing_user(self, recommendation_engine, mock_progress_tracker,
                                                          sample_user_progress, sample_content_metadata):
        """Test recommendations for existing user with progress."""
        # Mock user progress
        mock_progress_tracker.get_user_progress.return_value = sample_user_progress
        
        # Mock content metadata retrieval
        content_map = {content.content_id: content for content in sample_content_metadata}
        mock_progress_tracker._get_content_metadata.side_effect = lambda cid: content_map.get(cid)
        
        # Mock content retrieval methods
        with patch.object(recommendation_engine, '_get_content_by_category', return_value=sample_content_metadata[:1]):
            with patch.object(recommendation_engine, '_store_recommendations'):
                recommendations = recommendation_engine.get_personalized_recommendations(
                    'test-user', CertificationType.SAA, 5
                )
        
        assert len(recommendations) > 0
        assert all(isinstance(rec, StudyRecommendation) for rec in recommendations)
        assert all(rec.user_id == 'test-user' for rec in recommendations)
    
    def test_identify_weak_areas_no_data(self, recommendation_engine, mock_progress_tracker):
        """Test weak area identification with no user data."""
        mock_progress_tracker.get_user_progress.return_value = []
        
        weak_areas = recommendation_engine.identify_weak_areas('test-user', CertificationType.SAA)
        
        assert weak_areas['weak_areas'] == []
        assert 'Insufficient data' in weak_areas['analysis']
        assert len(weak_areas['recommendations']) > 0
    
    def test_identify_weak_areas_with_data(self, recommendation_engine, mock_progress_tracker,
                                         sample_user_progress, sample_content_metadata):
        """Test weak area identification with user data."""
        # Mock user progress with low scores in S3
        low_score_progress = [
            UserProgress(
                user_id='test-user',
                content_id='content-s3-1',
                progress_type=ProgressType.ANSWERED,
                score=45.0,
                time_spent=300,
                timestamp=datetime.utcnow()
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-s3-2',
                progress_type=ProgressType.ANSWERED,
                score=55.0,
                time_spent=400,
                timestamp=datetime.utcnow()
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-s3-3',
                progress_type=ProgressType.ANSWERED,
                score=60.0,
                time_spent=350,
                timestamp=datetime.utcnow()
            )
        ]
        
        mock_progress_tracker.get_user_progress.return_value = low_score_progress
        
        # Mock content metadata for S3 category
        s3_content = ContentMetadata(
            content_id='content-s3-1',
            title='S3 Basics',
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.SAA,
            category='S3',
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        mock_progress_tracker._get_content_metadata.return_value = s3_content
        
        weak_areas = recommendation_engine.identify_weak_areas('test-user', CertificationType.SAA)
        
        assert len(weak_areas['weak_categories']) > 0
        assert weak_areas['weak_categories'][0]['category'] == 'S3'
        assert weak_areas['weak_categories'][0]['avg_score'] < 70.0
        assert len(weak_areas['recommendations']) > 0
    
    def test_get_content_difficulty_progression_no_data(self, recommendation_engine, mock_progress_tracker):
        """Test content difficulty progression with no data."""
        mock_progress_tracker.get_user_progress.return_value = []
        
        progression = recommendation_engine.get_content_difficulty_progression('test-user', CertificationType.SAA)
        
        assert progression['current_level'] == 'beginner'
        assert progression['recommended_level'] == 'beginner'
        assert progression['readiness_score'] == 0.0
        assert len(progression['progression_path']) > 0
    
    def test_get_content_difficulty_progression_with_data(self, recommendation_engine, mock_progress_tracker,
                                                        sample_content_metadata):
        """Test content difficulty progression with user data."""
        # Create progress with good beginner scores
        beginner_progress = [
            UserProgress(
                user_id='test-user',
                content_id='content-1',
                progress_type=ProgressType.ANSWERED,
                score=85.0,
                time_spent=300,
                timestamp=datetime.utcnow()
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-2',
                progress_type=ProgressType.ANSWERED,
                score=88.0,
                time_spent=350,
                timestamp=datetime.utcnow()
            ),
            UserProgress(
                user_id='test-user',
                content_id='content-3',
                progress_type=ProgressType.ANSWERED,
                score=82.0,
                time_spent=320,
                timestamp=datetime.utcnow()
            )
        ]
        
        mock_progress_tracker.get_user_progress.return_value = beginner_progress
        
        # Mock content metadata
        content_map = {content.content_id: content for content in sample_content_metadata}
        mock_progress_tracker._get_content_metadata.side_effect = lambda cid: content_map.get(cid)
        
        progression = recommendation_engine.get_content_difficulty_progression('test-user', CertificationType.SAA)
        
        assert progression['current_level'] in ['beginner', 'intermediate']
        assert 'level_readiness' in progression
        assert len(progression['progression_path']) > 0
    
    def test_generate_study_path(self, recommendation_engine, mock_progress_tracker, sample_content_metadata):
        """Test study path generation."""
        # Mock dependencies
        mock_progress_tracker.get_user_progress.return_value = []
        
        with patch.object(recommendation_engine, 'identify_weak_areas') as mock_weak_areas:
            mock_weak_areas.return_value = {
                'weak_categories': [{'category': 'S3', 'avg_score': 60.0}],
                'weak_difficulties': []
            }
            
            with patch.object(recommendation_engine, 'get_content_difficulty_progression') as mock_progression:
                mock_progression.return_value = {
                    'current_level': 'beginner',
                    'recommended_level': 'intermediate'
                }
                
                with patch.object(recommendation_engine, '_get_content_by_certification', return_value=sample_content_metadata):
                    with patch.object(recommendation_engine, '_get_core_topics_for_certification', return_value=['EC2', 'S3']):
                        with patch.object(recommendation_engine, '_get_advanced_topics_for_certification', return_value=['Advanced S3']):
                            study_path = recommendation_engine.generate_study_path('test-user', CertificationType.SAA)
        
        assert study_path['user_id'] == 'test-user'
        assert study_path['certification_type'] == CertificationType.SAA.value
        assert len(study_path['study_phases']) > 0
        assert study_path['total_estimated_hours'] > 0
        assert len(study_path['milestones']) > 0
    
    def test_record_recommendation_feedback_success(self, recommendation_engine, mock_tables):
        """Test successful recommendation feedback recording."""
        # Mock successful update
        mock_tables['recommendations'].update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        success = recommendation_engine.record_recommendation_feedback(
            'test-user', 'rec-123', 'accepted', {'rating': 5}
        )
        
        assert success is True
        mock_tables['recommendations'].update_item.assert_called_once()
    
    def test_record_recommendation_feedback_failure(self, recommendation_engine, mock_tables):
        """Test recommendation feedback recording failure."""
        # Mock DynamoDB error
        from botocore.exceptions import ClientError
        mock_tables['recommendations'].update_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Test error'}},
            'UpdateItem'
        )
        
        success = recommendation_engine.record_recommendation_feedback(
            'test-user', 'rec-123', 'rejected'
        )
        
        assert success is False
    
    def test_analyze_user_performance(self, recommendation_engine, sample_user_progress, sample_content_metadata):
        """Test user performance analysis."""
        # Mock content metadata retrieval
        content_map = {content.content_id: content for content in sample_content_metadata}
        
        with patch.object(recommendation_engine, '_get_content_metadata') as mock_get_content:
            mock_get_content.side_effect = lambda cid: content_map.get(cid)
            
            analysis = recommendation_engine._analyze_user_performance(sample_user_progress, CertificationType.SAA)
        
        assert analysis['total_interactions'] == len(sample_user_progress)
        assert analysis['avg_score'] > 0
        assert len(analysis['category_performance']) > 0
        assert analysis['learning_velocity'] >= 0
    
    def test_generate_foundational_recommendations(self, recommendation_engine, sample_content_metadata):
        """Test foundational recommendations generation."""
        with patch.object(recommendation_engine, '_get_content_by_difficulty', return_value=sample_content_metadata):
            recommendations = recommendation_engine._generate_foundational_recommendations(
                'new-user', CertificationType.SAA, 3
            )
        
        assert len(recommendations) <= 3
        assert all(rec.type == 'content' for rec in recommendations)
        assert all(rec.priority >= 7 for rec in recommendations)  # High priority for foundational
        assert all('foundational' in rec.reasoning.lower() for rec in recommendations)
    
    def test_generate_weak_area_recommendations(self, recommendation_engine, sample_content_metadata):
        """Test weak area recommendations generation."""
        performance_analysis = {
            'category_performance': {
                'S3': [45.0, 55.0, 60.0],  # Weak area
                'EC2': [85.0, 90.0, 88.0]  # Strong area
            }
        }
        
        with patch.object(recommendation_engine, '_get_content_by_category', return_value=sample_content_metadata[:1]):
            recommendations = recommendation_engine._generate_weak_area_recommendations(
                'test-user', performance_analysis, CertificationType.SAA, 5
            )
        
        assert len(recommendations) > 0
        assert all(rec.type == 'review' for rec in recommendations)
        assert all(rec.priority >= 7 for rec in recommendations)  # High priority for weak areas
    
    def test_generate_progression_recommendations(self, recommendation_engine, sample_content_metadata):
        """Test progression recommendations generation."""
        performance_analysis = {
            'category_performance': {
                'EC2': [85.0, 90.0, 88.0],  # Strong area - ready for progression
                'S3': [45.0, 55.0, 60.0]   # Weak area - not ready
            }
        }
        
        with patch.object(recommendation_engine, '_get_content_by_category', return_value=sample_content_metadata):
            recommendations = recommendation_engine._generate_progression_recommendations(
                'test-user', performance_analysis, CertificationType.SAA, 5
            )
        
        assert len(recommendations) > 0
        assert all(rec.type == 'content' for rec in recommendations)
        assert all(rec.priority <= 6 for rec in recommendations)  # Medium priority for progression
    
    def test_store_recommendations(self, recommendation_engine, mock_tables):
        """Test storing recommendations in DynamoDB."""
        recommendations = [
            StudyRecommendation(
                recommendation_id='rec-1',
                user_id='test-user',
                type='content',
                priority=8,
                reasoning='Test recommendation',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
        ]
        
        # Mock batch writer context manager
        mock_batch_writer = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_batch_writer)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tables['recommendations'].batch_writer.return_value = mock_context_manager
        
        recommendation_engine._store_recommendations(recommendations)
        
        mock_batch_writer.put_item.assert_called_once()
    
    def test_get_core_topics_for_certification(self, recommendation_engine):
        """Test getting core topics for certification."""
        topics = recommendation_engine._get_core_topics_for_certification(CertificationType.SAA)
        
        assert len(topics) > 0
        assert 'EC2' in topics
        assert 'S3' in topics
    
    def test_get_advanced_topics_for_certification(self, recommendation_engine):
        """Test getting advanced topics for certification."""
        topics = recommendation_engine._get_advanced_topics_for_certification(CertificationType.SAA)
        
        assert len(topics) > 0
        assert any('Advanced' in topic for topic in topics)
    
    def test_error_handling_in_recommendations(self, recommendation_engine, mock_progress_tracker):
        """Test error handling in recommendation generation."""
        # Mock exception in progress tracker
        mock_progress_tracker.get_user_progress.side_effect = Exception("Database error")
        
        recommendations = recommendation_engine.get_personalized_recommendations(
            'test-user', CertificationType.SAA, 5
        )
        
        # Should return empty list on error, not raise exception
        assert recommendations == []
    
    def test_recommendation_expiration(self, recommendation_engine):
        """Test that recommendations have proper expiration dates."""
        with patch.object(recommendation_engine, '_get_content_by_difficulty', return_value=[]):
            recommendations = recommendation_engine._generate_foundational_recommendations(
                'test-user', CertificationType.SAA, 1
            )
        
        if recommendations:
            rec = recommendations[0]
            assert rec.expires_at is not None
            assert rec.expires_at > datetime.utcnow()
    
    def test_recommendation_priority_ordering(self, recommendation_engine, sample_content_metadata):
        """Test that recommendations are properly prioritized."""
        performance_analysis = {
            'category_performance': {
                'S3': [45.0, 55.0],      # Weak - should be high priority
                'EC2': [85.0, 90.0],     # Strong - should be medium priority
                'VPC': [75.0, 78.0]      # Moderate - should be lower priority
            }
        }
        
        with patch.object(recommendation_engine, '_get_content_by_category', return_value=sample_content_metadata[:1]):
            weak_recs = recommendation_engine._generate_weak_area_recommendations(
                'test-user', performance_analysis, CertificationType.SAA, 5
            )
            
            progression_recs = recommendation_engine._generate_progression_recommendations(
                'test-user', performance_analysis, CertificationType.SAA, 5
            )
        
        # Weak area recommendations should have higher priority than progression
        if weak_recs and progression_recs:
            assert max(rec.priority for rec in weak_recs) > max(rec.priority for rec in progression_recs)


if __name__ == '__main__':
    pytest.main([__file__])