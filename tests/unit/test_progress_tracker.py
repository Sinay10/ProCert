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


    @patch('shared.progress_tracker.ProgressTracker.get_user_progress')
    @patch('shared.progress_tracker.ProgressTracker._get_content_metadata')
    def test_get_performance_trends(self, mock_get_content, mock_get_progress):
        """Test performance trends calculation."""
        # Mock user progress data
        base_date = datetime.utcnow()
        user_progress = []
        
        # Create progress for last 3 days
        for i in range(3):
            progress_date = base_date - timedelta(days=i)
            progress = UserProgress(
                user_id='user-123',
                content_id=f'content-{i}',
                progress_type=ProgressType.ANSWERED,
                score=80.0 + i * 5,  # Increasing scores
                time_spent=300 + i * 60,  # Increasing time
                timestamp=progress_date
            )
            user_progress.append(progress)
        
        mock_get_progress.return_value = user_progress
        
        # Mock content metadata
        def mock_content_metadata(content_id):
            return ContentMetadata(
                content_id=content_id,
                title=f'Content {content_id}',
                content_type=ContentType.QUESTION,
                certification_type=CertificationType.SAA,
                category='EC2',
                difficulty_level=DifficultyLevel.INTERMEDIATE
            )
        
        mock_get_content.side_effect = mock_content_metadata
        
        # Test trends calculation
        trends = self.tracker.get_performance_trends('user-123', CertificationType.SAA, days=7)
        
        self.assertEqual(len(trends), 3)  # 3 days of data
        
        # Verify trend data structure
        for trend in trends:
            self.assertEqual(trend.user_id, 'user-123')
            self.assertEqual(trend.certification_type, CertificationType.SAA)
            self.assertIn('avg_score', trend.metrics)
            self.assertIn('total_time', trend.metrics)
            self.assertIn('EC2', trend.category_breakdown)
    
    @patch('shared.progress_tracker.ProgressTracker.get_user_progress')
    @patch('shared.progress_tracker.ProgressTracker._get_content_metadata')
    def test_calculate_certification_readiness(self, mock_get_content, mock_get_progress):
        """Test certification readiness calculation."""
        # Mock user progress with varied performance
        user_progress = [
            UserProgress(user_id='user-123', content_id='content-1', progress_type=ProgressType.ANSWERED, score=85.0),
            UserProgress(user_id='user-123', content_id='content-2', progress_type=ProgressType.ANSWERED, score=90.0),
            UserProgress(user_id='user-123', content_id='content-3', progress_type=ProgressType.COMPLETED, score=80.0),
            UserProgress(user_id='user-123', content_id='content-4', progress_type=ProgressType.VIEWED),
        ]
        mock_get_progress.return_value = user_progress
        
        # Mock content metadata with different categories
        def mock_content_metadata(content_id):
            categories = {'content-1': 'EC2', 'content-2': 'S3', 'content-3': 'EC2', 'content-4': 'IAM'}
            return ContentMetadata(
                content_id=content_id,
                title=f'Content {content_id}',
                content_type=ContentType.QUESTION,
                certification_type=CertificationType.SAA,
                category=categories.get(content_id, 'General'),
                difficulty_level=DifficultyLevel.INTERMEDIATE
            )
        
        mock_get_content.side_effect = mock_content_metadata
        
        # Test readiness calculation
        readiness = self.tracker.calculate_certification_readiness('user-123', CertificationType.SAA)
        
        self.assertEqual(readiness.user_id, 'user-123')
        self.assertEqual(readiness.certification_type, CertificationType.SAA)
        self.assertGreater(readiness.readiness_score, 0)
        self.assertGreater(readiness.estimated_study_time_hours, 0)
        self.assertIsInstance(readiness.weak_areas, list)
        self.assertIsInstance(readiness.strong_areas, list)
        self.assertIsInstance(readiness.recommended_actions, list)
        self.assertIn(readiness.confidence_level, ['low', 'medium', 'high'])
    
    @patch('shared.progress_tracker.ProgressTracker.get_user_progress')
    @patch('shared.progress_tracker.ProgressTracker.get_user_activity_summary')
    def test_check_achievements(self, mock_get_activity, mock_get_progress):
        """Test achievement checking logic."""
        # Mock user progress with high performance
        user_progress = []
        for i in range(15):  # 15 completed items for completion achievement
            progress = UserProgress(
                user_id='user-123',
                content_id=f'content-{i}',
                progress_type=ProgressType.COMPLETED,
                score=85.0,  # High score for score achievement
                time_spent=600  # 10 minutes each = 150 minutes total
            )
            user_progress.append(progress)
        
        mock_get_progress.return_value = user_progress
        
        # Mock activity summary with streak
        mock_get_activity.return_value = {
            'study_streak_days': 7,  # 7-day streak for streak achievement
            'total_interactions': 15
        }
        
        # Test achievement checking
        achievements = self.tracker.check_achievements('user-123')
        
        self.assertGreater(len(achievements), 0)
        
        # Check for different types of achievements
        achievement_types = [a.achievement_type for a in achievements]
        self.assertIn('completion', achievement_types)  # Should have completion achievement
        self.assertIn('score', achievement_types)  # Should have score achievement
        self.assertIn('streak', achievement_types)  # Should have streak achievement
        
        # Verify achievement structure
        for achievement in achievements:
            self.assertEqual(achievement.user_id, 'user-123')
            self.assertIsNotNone(achievement.title)
            self.assertIsNotNone(achievement.description)
            self.assertGreater(achievement.points, 0)
    
    @patch('shared.progress_tracker.ProgressTracker.get_performance_analytics')
    @patch('shared.progress_tracker.ProgressTracker.get_user_activity_summary')
    @patch('shared.progress_tracker.ProgressTracker.calculate_certification_readiness')
    @patch('shared.progress_tracker.ProgressTracker.get_performance_trends')
    @patch('shared.progress_tracker.ProgressTracker.get_user_achievements')
    def test_get_dashboard_data(self, mock_get_achievements, mock_get_trends, 
                               mock_get_readiness, mock_get_activity, mock_get_analytics):
        """Test comprehensive dashboard data generation."""
        # Mock all dependencies
        mock_analytics = PerformanceMetrics(
            user_id='user-123',
            total_content_viewed=50,
            total_questions_answered=30,
            average_score=85.0,
            time_spent_total=7200,  # 2 hours
            completion_rate=60.0
        )
        mock_get_analytics.return_value = mock_analytics
        
        mock_get_activity.return_value = {
            'study_streak_days': 5,
            'total_interactions': 50,
            'weekly_avg_time_minutes': 120
        }
        
        from shared.models import CertificationReadiness, Achievement
        mock_readiness = CertificationReadiness(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            readiness_score=75.0,
            estimated_study_time_hours=40,
            weak_areas=['IAM'],
            strong_areas=['EC2'],
            recommended_actions=['Take practice exam'],
            confidence_level='medium',
            predicted_pass_probability=80.0
        )
        mock_get_readiness.return_value = mock_readiness
        
        mock_get_trends.return_value = []
        
        mock_achievement = Achievement(
            achievement_id='test-achievement',
            user_id='user-123',
            achievement_type='streak',
            title='5-Day Streak',
            description='Studied for 5 consecutive days',
            criteria={'streak_days': 5},
            badge_icon='🔥',
            points=50
        )
        mock_get_achievements.return_value = [mock_achievement]
        
        # Test dashboard data generation
        dashboard_data = self.tracker.get_dashboard_data('user-123')
        
        self.assertEqual(dashboard_data['user_id'], 'user-123')
        self.assertIn('overall_analytics', dashboard_data)
        self.assertIn('activity_summary', dashboard_data)
        self.assertIn('certification_progress', dashboard_data)
        self.assertIn('performance_trends', dashboard_data)
        self.assertIn('achievements', dashboard_data)
        self.assertIn('study_streak', dashboard_data)
        self.assertIn('total_points', dashboard_data)
        self.assertIn('recommendations', dashboard_data)
        
        # Verify data structure
        self.assertEqual(dashboard_data['study_streak'], 5)
        self.assertEqual(dashboard_data['total_points'], 50)
        self.assertIsInstance(dashboard_data['recommendations'], list)
    
    def test_achievement_validation(self):
        """Test achievement model validation."""
        from shared.models import Achievement
        
        # Valid achievement
        valid_achievement = Achievement(
            achievement_id='test-123',
            user_id='user-123',
            achievement_type='streak',
            title='Test Achievement',
            description='Test description',
            criteria={'days': 7},
            points=100
        )
        
        self.assertTrue(valid_achievement.is_valid())
        
        # Invalid achievement (missing required fields)
        invalid_achievement = Achievement(
            achievement_id='',  # Empty ID
            user_id='user-123',
            achievement_type='invalid_type',  # Invalid type
            title='',  # Empty title
            description='Test description',
            criteria={},
            points=-10  # Negative points
        )
        
        self.assertFalse(invalid_achievement.is_valid())
        errors = invalid_achievement.validate()
        self.assertGreater(len(errors), 0)
    
    def test_certification_readiness_validation(self):
        """Test certification readiness model validation."""
        from shared.models import CertificationReadiness
        
        # Valid readiness assessment
        valid_readiness = CertificationReadiness(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            readiness_score=75.0,
            estimated_study_time_hours=40,
            weak_areas=['IAM'],
            strong_areas=['EC2'],
            recommended_actions=['Practice more'],
            confidence_level='medium',
            predicted_pass_probability=80.0
        )
        
        self.assertTrue(valid_readiness.is_valid())
        
        # Invalid readiness assessment
        invalid_readiness = CertificationReadiness(
            user_id='',  # Empty user ID
            certification_type=CertificationType.SAA,
            readiness_score=150.0,  # Invalid score > 100
            estimated_study_time_hours=-10,  # Negative hours
            weak_areas=[],
            strong_areas=[],
            recommended_actions=[],
            confidence_level='invalid',  # Invalid confidence level
            predicted_pass_probability=150.0  # Invalid probability > 100
        )
        
        self.assertFalse(invalid_readiness.is_valid())
        errors = invalid_readiness.validate()
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()