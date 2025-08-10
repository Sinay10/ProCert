"""
Simplified unit tests for the ProgressTracker class.

This module contains focused tests for progress tracking functionality.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from shared.progress_tracker import ProgressTracker
from shared.interfaces import InteractionData, PerformanceMetrics
from shared.models import (
    UserProgress, ContentMetadata, CertificationType, ProgressType,
    ContentType, DifficultyLevel
)


class TestProgressTrackerSimple(unittest.TestCase):
    """Simplified test cases for ProgressTracker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker(
            user_progress_table_name='test-user-progress',
            content_metadata_table_name='test-content-metadata',
            region_name='us-east-1'
        )
        
        # Sample content metadata
        self.sample_content = ContentMetadata(
            content_id='content-123',
            title='Test Content',
            content_type=ContentType.QUESTION,
            certification_type=CertificationType.SAA,
            category='EC2',
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=['compute', 'instances']
        )
    
    def test_map_interaction_to_progress_type(self):
        """Test interaction type mapping to progress type."""
        test_cases = [
            ('view', ProgressType.VIEWED),
            ('viewed', ProgressType.VIEWED),
            ('answer', ProgressType.ANSWERED),
            ('answered', ProgressType.ANSWERED),
            ('complete', ProgressType.COMPLETED),
            ('completed', ProgressType.COMPLETED),
            ('finish', ProgressType.COMPLETED),
            ('finished', ProgressType.COMPLETED),
            ('unknown', ProgressType.VIEWED)  # Default case
        ]
        
        for interaction_type, expected_progress_type in test_cases:
            result = self.tracker._map_interaction_to_progress_type(interaction_type)
            self.assertEqual(result, expected_progress_type, 
                           f"Failed for interaction_type: {interaction_type}")
    
    @patch('shared.progress_tracker.ProgressTracker._get_content_metadata')
    def test_record_interaction_success(self, mock_get_content):
        """Test successful interaction recording."""
        # Mock content metadata retrieval
        mock_get_content.return_value = self.sample_content
        
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        self.tracker.user_progress_table = mock_table
        
        # Test interaction recording
        interaction = InteractionData(
            interaction_type='answered',
            score=85.0,
            time_spent=300,
            additional_data={'session_id': 'session-123'}
        )
        
        result = self.tracker.record_interaction('user-123', 'content-123', interaction)
        
        self.assertTrue(result)
        mock_get_content.assert_called_once_with('content-123')
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        
        self.assertEqual(item['user_id'], 'user-123')
        self.assertEqual(item['content_id'], 'content-123')
        self.assertEqual(item['certification_type'], 'SAA')
        self.assertEqual(item['progress_type'], 'answered')
        self.assertEqual(item['score'], Decimal('85.0'))
        self.assertEqual(item['time_spent'], 300)
        self.assertEqual(item['interaction_type'], 'answered')
    
    @patch('shared.progress_tracker.ProgressTracker._get_content_metadata')
    def test_record_interaction_content_not_found(self, mock_get_content):
        """Test interaction recording when content is not found."""
        # Mock content metadata retrieval to return None
        mock_get_content.return_value = None
        
        interaction = InteractionData(
            interaction_type='answered',
            score=85.0,
            time_spent=300
        )
        
        result = self.tracker.record_interaction('user-123', 'nonexistent-content', interaction)
        
        self.assertFalse(result)
        mock_get_content.assert_called_once_with('nonexistent-content')
    
    @patch('shared.progress_tracker.ProgressTracker._get_content_by_category')
    @patch('shared.progress_tracker.ProgressTracker.get_user_progress')
    @patch('shared.progress_tracker.ProgressTracker._get_content_metadata')
    def test_calculate_completion_rate(self, mock_get_content, mock_get_progress, mock_get_category):
        """Test completion rate calculation."""
        # Mock category content (5 items total)
        category_content = [
            ContentMetadata(content_id=f'content-{i}', title=f'Content {i}', 
                          content_type=ContentType.QUESTION, certification_type=CertificationType.SAA,
                          category='EC2') 
            for i in range(1, 6)
        ]
        mock_get_category.return_value = category_content
        
        # Mock user progress (2 completed items)
        user_progress = [
            UserProgress(user_id='user-123', content_id='content-1', progress_type=ProgressType.COMPLETED),
            UserProgress(user_id='user-123', content_id='content-2', progress_type=ProgressType.COMPLETED),
            UserProgress(user_id='user-123', content_id='content-3', progress_type=ProgressType.VIEWED),
            UserProgress(user_id='user-123', content_id='content-4', progress_type=ProgressType.ANSWERED)
        ]
        mock_get_progress.return_value = user_progress
        
        # Mock content metadata for completed items
        def mock_content_metadata(content_id):
            if content_id in ['content-1', 'content-2']:
                return ContentMetadata(content_id=content_id, title=f'Content {content_id}',
                                     content_type=ContentType.QUESTION, certification_type=CertificationType.SAA,
                                     category='EC2')
            return None
        
        mock_get_content.side_effect = mock_content_metadata
        
        # Test completion rate calculation
        completion_rate = self.tracker.calculate_completion_rate('user-123', 'EC2', CertificationType.SAA)
        
        # Expected: 2 completed out of 5 total = 40%
        self.assertEqual(completion_rate, 40.0)
        
        mock_get_category.assert_called_once_with('EC2', CertificationType.SAA)
        mock_get_progress.assert_called_once_with('user-123', CertificationType.SAA)
    
    @patch('shared.progress_tracker.ProgressTracker.get_user_progress')
    @patch('shared.progress_tracker.ProgressTracker._get_total_content_count')
    def test_get_performance_analytics(self, mock_get_total_count, mock_get_progress):
        """Test performance analytics generation."""
        # Mock user progress data
        user_progress = [
            UserProgress(user_id='user-123', content_id='content-1', progress_type=ProgressType.VIEWED, time_spent=120),
            UserProgress(user_id='user-123', content_id='content-2', progress_type=ProgressType.VIEWED, time_spent=180),
            UserProgress(user_id='user-123', content_id='content-3', progress_type=ProgressType.ANSWERED, score=85.0, time_spent=300),
            UserProgress(user_id='user-123', content_id='content-4', progress_type=ProgressType.ANSWERED, score=92.0, time_spent=240),
            UserProgress(user_id='user-123', content_id='content-5', progress_type=ProgressType.COMPLETED, time_spent=600),
            UserProgress(user_id='user-123', content_id='content-6', progress_type=ProgressType.COMPLETED, time_spent=450)
        ]
        mock_get_progress.return_value = user_progress
        mock_get_total_count.return_value = 10  # Total available content
        
        # Test analytics generation
        analytics = self.tracker.get_performance_analytics('user-123', CertificationType.SAA)
        
        self.assertIsInstance(analytics, PerformanceMetrics)
        self.assertEqual(analytics.user_id, 'user-123')
        self.assertEqual(analytics.total_content_viewed, 2)
        self.assertEqual(analytics.total_questions_answered, 2)
        self.assertEqual(analytics.average_score, 88.5)  # (85 + 92) / 2
        self.assertEqual(analytics.time_spent_total, 1890)  # Sum of all time_spent
        self.assertEqual(analytics.completion_rate, 20.0)  # 2 completed out of 10 total = 20%
    
    def test_calculate_study_streak(self):
        """Test study streak calculation."""
        # Create progress data for consecutive days
        end_date = datetime.utcnow()
        user_progress = []
        
        # Add progress for last 5 consecutive days
        for i in range(5):
            progress_date = end_date - timedelta(days=i)
            progress = UserProgress(
                user_id='user-123',
                content_id=f'content-{i}',
                progress_type=ProgressType.VIEWED,
                timestamp=progress_date
            )
            user_progress.append(progress)
        
        # Test streak calculation
        streak = self.tracker._calculate_study_streak(user_progress, end_date)
        self.assertEqual(streak, 5)
        
        # Test with gap in streak
        user_progress_with_gap = []
        for i in [0, 1, 3, 4]:  # Missing day 2
            progress_date = end_date - timedelta(days=i)
            progress = UserProgress(
                user_id='user-123',
                content_id=f'content-{i}',
                progress_type=ProgressType.VIEWED,
                timestamp=progress_date
            )
            user_progress_with_gap.append(progress)
        
        streak_with_gap = self.tracker._calculate_study_streak(user_progress_with_gap, end_date)
        self.assertEqual(streak_with_gap, 2)  # Only last 2 consecutive days
    
    def test_update_existing_interaction(self):
        """Test updating existing interaction records."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        self.tracker.user_progress_table = mock_table
        
        # Test interaction update
        interaction = InteractionData(
            interaction_type='answered',
            score=95.0,
            time_spent=180,
            additional_data={'attempt': 2}
        )
        
        result = self.tracker._update_existing_interaction('user-123', 'content-123#SAA#2023-01-01T00:00:00', interaction)
        
        self.assertTrue(result)
        mock_table.update_item.assert_called_once()
        
        # Verify update expression includes score, time_spent, additional_data, and timestamp
        call_args = mock_table.update_item.call_args
        update_expression = call_args[1]['UpdateExpression']
        
        self.assertIn('score = :score', update_expression)
        self.assertIn('time_spent = time_spent + :time_spent', update_expression)
        self.assertIn('additional_data = :additional_data', update_expression)
        self.assertIn('timestamp = :timestamp', update_expression)


if __name__ == '__main__':
    unittest.main()