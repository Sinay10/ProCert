"""
Integration tests for the Enhanced Progress Tracking Lambda function.

These tests verify the Lambda function's API endpoints and integration
with the progress tracking service.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock the Lambda context
class MockLambdaContext:
    def __init__(self):
        self.function_name = 'test-progress-function'
        self.function_version = '1'
        self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-progress-function'
        self.memory_limit_in_mb = 128
        self.remaining_time_in_millis = 30000
        self.log_group_name = '/aws/lambda/test-progress-function'
        self.log_stream_name = '2023/01/01/[$LATEST]test'
        self.aws_request_id = 'test-request-id'

class TestProgressLambdaIntegration(unittest.TestCase):
    """Integration tests for progress tracking Lambda function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context = MockLambdaContext()
        
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
        
        from main import lambda_handler
        self.lambda_handler = lambda_handler
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
    
    def test_record_interaction_success(self):
        """Test successful interaction recording."""
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_tracker.record_interaction.return_value = True
        mock_tracker.check_achievements.return_value = []
        
        # Import and set the mock tracker
        from main import set_progress_tracker
        set_progress_tracker(mock_tracker)
        
        # Create test event
        event = {
            'httpMethod': 'POST',
            'path': '/api/progress/user-123/interaction',
            'body': json.dumps({
                'user_id': 'user-123',
                'content_id': 'content-456',
                'interaction_type': 'answered',
                'score': 85.0,
                'time_spent': 300,
                'additional_data': {'session_id': 'session-789'}
            })
        }
        
        # Call Lambda handler
        response = self.lambda_handler(event, self.context)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
        self.assertIn('new_achievements', body)
        
        # Verify progress tracker was called
        mock_tracker.record_interaction.assert_called_once()
        mock_tracker.check_achievements.assert_called_once_with('user-123')
    
    @patch('progress_lambda_src.main.progress_tracker')
    def test_record_interaction_missing_fields(self, mock_tracker):
        """Test interaction recording with missing required fields."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/progress/user-123/interaction',
            'body': json.dumps({
                'user_id': 'user-123',
                # Missing content_id and interaction_type
                'score': 85.0
            })
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertIn('content_id and interaction_type are required', body['error']['message'])
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_get_analytics_success(self, mock_tracker_class):
        """Test successful analytics retrieval."""
        from shared.interfaces import PerformanceMetrics
        
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_analytics = PerformanceMetrics(
            user_id='user-123',
            total_content_viewed=50,
            total_questions_answered=30,
            average_score=85.0,
            time_spent_total=7200,
            completion_rate=60.0
        )
        mock_tracker.get_performance_analytics.return_value = mock_analytics
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/analytics',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['user_id'], 'user-123')
        self.assertEqual(body['certification_type'], 'SAA')
        self.assertEqual(body['average_score'], 85.0)
        self.assertEqual(body['completion_rate'], 60.0)
        self.assertEqual(body['time_spent_total_hours'], 2.0)  # 7200 seconds = 2 hours
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_get_trends_success(self, mock_tracker_class):
        """Test successful trends retrieval."""
        from shared.models import PerformanceTrend, CertificationType
        
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_trend = PerformanceTrend(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            date=datetime.utcnow(),
            metrics={'avg_score': 85.0, 'total_time': 300},
            category_breakdown={'EC2': {'count': 5, 'avg_score': 85.0}},
            difficulty_breakdown={'intermediate': {'count': 5, 'avg_score': 85.0}}
        )
        mock_tracker.get_performance_trends.return_value = [mock_trend]
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/trends',
            'queryStringParameters': {
                'certification_type': 'SAA',
                'days': '30'
            }
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['user_id'], 'user-123')
        self.assertEqual(body['certification_type'], 'SAA')
        self.assertEqual(body['period_days'], 30)
        self.assertEqual(len(body['trends']), 1)
        
        trend_data = body['trends'][0]
        self.assertEqual(trend_data['certification_type'], 'SAA')
        self.assertIn('metrics', trend_data)
        self.assertIn('category_breakdown', trend_data)
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_get_readiness_success(self, mock_tracker_class):
        """Test successful readiness assessment."""
        from shared.models import CertificationReadiness, CertificationType
        
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_readiness = CertificationReadiness(
            user_id='user-123',
            certification_type=CertificationType.SAA,
            readiness_score=75.0,
            estimated_study_time_hours=40,
            weak_areas=['IAM', 'VPC'],
            strong_areas=['EC2', 'S3'],
            recommended_actions=['Take practice exam', 'Review IAM policies'],
            confidence_level='medium',
            predicted_pass_probability=80.0
        )
        mock_tracker.calculate_certification_readiness.return_value = mock_readiness
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/readiness',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['user_id'], 'user-123')
        self.assertEqual(body['certification_type'], 'SAA')
        self.assertEqual(body['readiness_score'], 75.0)
        self.assertEqual(body['estimated_study_time_hours'], 40)
        self.assertEqual(body['confidence_level'], 'medium')
        self.assertIn('IAM', body['weak_areas'])
        self.assertIn('EC2', body['strong_areas'])
    
    @patch('progress_lambda_src.main.progress_tracker')
    def test_get_readiness_missing_certification(self, mock_tracker):
        """Test readiness assessment without certification type."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/readiness',
            'queryStringParameters': {}
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('certification_type is required', body['error']['message'])
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_get_achievements_success(self, mock_tracker_class):
        """Test successful achievements retrieval."""
        from shared.models import Achievement, CertificationType
        
        # Mock progress tracker instance
        mock_tracker = Mock()
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
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/achievements',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['user_id'], 'user-123')
        self.assertEqual(body['certification_type'], 'SAA')
        self.assertEqual(body['total_points'], 70)
        self.assertEqual(body['total_achievements'], 1)
        
        achievement_data = body['achievements'][0]
        self.assertEqual(achievement_data['title'], '7-Day Study Streak')
        self.assertEqual(achievement_data['achievement_type'], 'streak')
        self.assertEqual(achievement_data['badge_icon'], '🔥')
        self.assertEqual(achievement_data['points'], 70)
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_get_dashboard_success(self, mock_tracker_class):
        """Test successful dashboard data retrieval."""
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_dashboard_data = {
            'user_id': 'user-123',
            'generated_at': datetime.utcnow().isoformat(),
            'overall_analytics': {
                'completion_rate': 60.0,
                'average_score': 85.0,
                'total_time_hours': 2.0
            },
            'activity_summary': {
                'study_streak_days': 7,
                'total_interactions': 50
            },
            'certification_progress': {
                'SAA': {
                    'analytics': {'completion_rate': 60.0},
                    'readiness': {'score': 75.0}
                }
            },
            'achievements': [],
            'study_streak': 7,
            'total_points': 350,
            'recommendations': ['Keep up the great work!']
        }
        mock_tracker.get_dashboard_data.return_value = mock_dashboard_data
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/dashboard',
            'queryStringParameters': {}
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['user_id'], 'user-123')
        self.assertIn('overall_analytics', body)
        self.assertIn('activity_summary', body)
        self.assertIn('certification_progress', body)
        self.assertIn('achievements', body)
        self.assertEqual(body['study_streak'], 7)
        self.assertEqual(body['total_points'], 350)
    
    def test_invalid_endpoint(self):
        """Test handling of invalid endpoints."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/invalid',
            'queryStringParameters': {}
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertIn('Endpoint not found', body['error']['message'])
    
    def test_missing_user_id(self):
        """Test handling of missing user ID."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/analytics',  # No user ID in path
            'queryStringParameters': {}
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('user_id is required', body['error']['message'])
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_invalid_certification_type(self, mock_tracker_class):
        """Test handling of invalid certification type."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/analytics',
            'queryStringParameters': {
                'certification_type': 'INVALID'
            }
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('Invalid certification type', body['error']['message'])
    
    @patch('shared.progress_tracker.ProgressTracker')
    def test_service_error_handling(self, mock_tracker_class):
        """Test handling of service errors."""
        # Mock progress tracker instance
        mock_tracker = Mock()
        mock_tracker.get_performance_analytics.side_effect = Exception("Database error")
        mock_tracker_class.return_value = mock_tracker
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/progress/user-123/analytics',
            'queryStringParameters': {}
        }
        
        response = self.lambda_handler(event, self.context)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('Failed to get analytics', body['error']['message'])


if __name__ == '__main__':
    unittest.main()