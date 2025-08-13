"""
Unit tests for the Enhanced Progress Tracking Lambda function handlers.

These tests focus on testing the individual handler functions with mocked dependencies.
"""

import json
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

class TestProgressLambdaHandlers(unittest.TestCase):
    """Unit tests for progress Lambda handler functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'USER_PROGRESS_TABLE_NAME': 'test-user-progress',
            'CONTENT_METADATA_TABLE_NAME': 'test-content-metadata',
            'AWS_REGION': 'us-east-1'
        })
        self.env_patcher.start()
        
        # Import after setting environment variables
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../progress_lambda_src'))
        
        from main import (
            handle_record_interaction, handle_get_analytics, handle_get_trends,
            handle_get_readiness, handle_get_achievements, handle_get_dashboard
        )
        
        self.handle_record_interaction = handle_record_interaction
        self.handle_get_analytics = handle_get_analytics
        self.handle_get_trends = handle_get_trends
        self.handle_get_readiness = handle_get_readiness
        self.handle_get_achievements = handle_get_achievements
        self.handle_get_dashboard = handle_get_dashboard
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
    
    @patch('main.progress_tracker')
    def test_handle_record_interaction_success(self, mock_tracker):
        """Test successful interaction recording handler."""
        # Mock progress tracker
        mock_tracker.record_interaction.return_value = True
        mock_tracker.check_achievements.return_value = []
        
        # Test data
        body = {
            'content_id': 'content-456',
            'interaction_type': 'answered',
            'score': 85.0,
            'time_spent': 300,
            'additional_data': {'session_id': 'session-789'}
        }
        user_id = 'user-123'
        
        # Call handler
        response = self.handle_record_interaction(body, user_id)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        
        response_body = json.loads(response['body'])
        self.assertTrue(response_body['success'])
        self.assertIn('new_achievements', response_body)
        
        # Verify progress tracker was called
        mock_tracker.record_interaction.assert_called_once()
        mock_tracker.check_achievements.assert_called_once_with('user-123')
    
    @patch('main.progress_tracker')
    def test_handle_record_interaction_missing_fields(self, mock_tracker):
        """Test interaction recording with missing required fields."""
        body = {
            'score': 85.0
            # Missing content_id and interaction_type
        }
        user_id = 'user-123'
        
        response = self.handle_record_interaction(body, user_id)
        
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('content_id and interaction_type are required', response_body['error']['message'])
    
    @patch('main.progress_tracker')
    def test_handle_get_analytics_success(self, mock_tracker):
        """Test successful analytics retrieval handler."""
        from shared.interfaces import PerformanceMetrics
        
        # Mock analytics data
        mock_analytics = PerformanceMetrics(
            user_id='user-123',
            total_content_viewed=50,
            total_questions_answered=30,
            average_score=85.0,
            time_spent_total=7200,
            completion_rate=60.0
        )
        mock_tracker.get_performance_analytics.return_value = mock_analytics
        
        query_params = {'certification_type': 'SAA'}
        user_id = 'user-123'
        
        response = self.handle_get_analytics(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response_body['user_id'], 'user-123')
        self.assertEqual(response_body['certification_type'], 'SAA')
        self.assertEqual(response_body['average_score'], 85.0)
        self.assertEqual(response_body['completion_rate'], 60.0)
        self.assertEqual(response_body['time_spent_total_hours'], 2.0)
    
    @patch('main.progress_tracker')
    def test_handle_get_analytics_invalid_certification(self, mock_tracker):
        """Test analytics retrieval with invalid certification type."""
        query_params = {'certification_type': 'INVALID'}
        user_id = 'user-123'
        
        response = self.handle_get_analytics(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('Invalid certification type', response_body['error']['message'])
    
    @patch('main.progress_tracker')
    def test_handle_get_trends_success(self, mock_tracker):
        """Test successful trends retrieval handler."""
        from shared.models import PerformanceTrend, CertificationType
        
        # Mock trend data
        mock_trend = PerformanceTrend(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            date=datetime.utcnow(),
            metrics={'avg_score': 85.0, 'total_time': 300},
            category_breakdown={'EC2': {'count': 5, 'avg_score': 85.0}},
            difficulty_breakdown={'intermediate': {'count': 5, 'avg_score': 85.0}}
        )
        mock_tracker.get_performance_trends.return_value = [mock_trend]
        
        query_params = {'certification_type': 'SAA', 'days': '30'}
        user_id = 'user-123'
        
        response = self.handle_get_trends(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response_body['user_id'], 'user-123')
        self.assertEqual(response_body['certification_type'], 'SAA')
        self.assertEqual(response_body['period_days'], 30)
        self.assertEqual(len(response_body['trends']), 1)
    
    @patch('main.progress_tracker')
    def test_handle_get_trends_invalid_days(self, mock_tracker):
        """Test trends retrieval with invalid days parameter."""
        query_params = {'days': '500'}  # > 365
        user_id = 'user-123'
        
        response = self.handle_get_trends(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('days must be between 1 and 365', response_body['error']['message'])
    
    @patch('main.progress_tracker')
    def test_handle_get_readiness_success(self, mock_tracker):
        """Test successful readiness assessment handler."""
        from shared.models import CertificationReadiness, CertificationType
        
        # Mock readiness data
        mock_readiness = CertificationReadiness(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            readiness_score=75.0,
            estimated_study_time_hours=40,
            weak_areas=['IAM', 'VPC'],
            strong_areas=['EC2', 'S3'],
            recommended_actions=['Take practice exam'],
            confidence_level='medium',
            predicted_pass_probability=80.0
        )
        mock_tracker.calculate_certification_readiness.return_value = mock_readiness
        
        query_params = {'certification_type': 'SAA'}
        user_id = 'user-123'
        
        response = self.handle_get_readiness(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response_body['user_id'], 'user-123')
        self.assertEqual(response_body['certification_type'], 'SAA')
        self.assertEqual(response_body['readiness_score'], 75.0)
        self.assertEqual(response_body['confidence_level'], 'medium')
    
    @patch('main.progress_tracker')
    def test_handle_get_readiness_missing_certification(self, mock_tracker):
        """Test readiness assessment without certification type."""
        query_params = {}
        user_id = 'user-123'
        
        response = self.handle_get_readiness(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('certification_type is required', response_body['error']['message'])
    
    @patch('main.progress_tracker')
    def test_handle_get_achievements_success(self, mock_tracker):
        """Test successful achievements retrieval handler."""
        from shared.models import Achievement, CertificationType
        
        # Mock achievement data
        mock_achievement = Achievement(
            achievement_id='user-123_streak_7',
            user_id='user-123',
            achievement_type='streak',
            title='7-Day Study Streak',
            description='Studied for 7 consecutive days',
            criteria={'streak_days': 7},
            certification_type=CertificationType.SAA,
            badge_icon='🔥',
            points=70
        )
        mock_tracker.get_user_achievements.return_value = [mock_achievement]
        
        query_params = {'certification_type': 'SAA'}
        user_id = 'user-123'
        
        response = self.handle_get_achievements(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response_body['user_id'], 'user-123')
        self.assertEqual(response_body['total_points'], 70)
        self.assertEqual(len(response_body['achievements']), 1)
        
        achievement_data = response_body['achievements'][0]
        self.assertEqual(achievement_data['title'], '7-Day Study Streak')
        self.assertEqual(achievement_data['points'], 70)
    
    @patch('main.progress_tracker')
    def test_handle_get_dashboard_success(self, mock_tracker):
        """Test successful dashboard data retrieval handler."""
        # Mock dashboard data
        mock_dashboard_data = {
            'user_id': 'user-123',
            'generated_at': datetime.utcnow().isoformat(),
            'overall_analytics': {
                'completion_rate': 60.0,
                'average_score': 85.0,
                'total_time_hours': 2.0
            },
            'study_streak': 7,
            'total_points': 350,
            'recommendations': ['Keep up the great work!']
        }
        mock_tracker.get_dashboard_data.return_value = mock_dashboard_data
        
        query_params = {}
        user_id = 'user-123'
        
        response = self.handle_get_dashboard(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response_body['user_id'], 'user-123')
        self.assertEqual(response_body['study_streak'], 7)
        self.assertEqual(response_body['total_points'], 350)
        self.assertIn('recommendations', response_body)
    
    @patch('main.progress_tracker')
    def test_error_handling(self, mock_tracker):
        """Test error handling in handlers."""
        # Mock service to raise exception
        mock_tracker.get_performance_analytics.side_effect = Exception("Database error")
        
        query_params = {}
        user_id = 'user-123'
        
        response = self.handle_get_analytics(query_params, user_id)
        
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('Failed to get analytics', response_body['error']['message'])


if __name__ == '__main__':
    unittest.main()