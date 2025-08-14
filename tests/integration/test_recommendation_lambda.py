"""
Integration tests for the Recommendation Lambda function.

Tests the complete recommendation service including API endpoints,
data processing, and integration with DynamoDB.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from recommendation_lambda_src.main import (
    lambda_handler, handle_get_recommendations, handle_get_study_path,
    handle_record_feedback, handle_get_weak_areas, handle_get_content_progression,
    create_success_response, create_error_response
)
from shared.models import CertificationType, StudyRecommendation


class TestRecommendationLambda:
    """Integration tests for Recommendation Lambda function."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for Lambda."""
        return {
            'USER_PROGRESS_TABLE_NAME': 'test-progress',
            'CONTENT_METADATA_TABLE_NAME': 'test-content',
            'RECOMMENDATIONS_TABLE_NAME': 'test-recommendations'
        }
    
    @pytest.fixture
    def mock_recommendation_engine(self):
        """Mock RecommendationEngine for testing."""
        mock_engine = Mock()
        
        # Mock sample recommendations
        sample_recommendations = [
            StudyRecommendation(
                recommendation_id='rec-1',
                user_id='test-user',
                type='content',
                priority=8,
                content_id='content-1',
                reasoning='Review EC2 fundamentals',
                estimated_time_minutes=30,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            ),
            StudyRecommendation(
                recommendation_id='rec-2',
                user_id='test-user',
                type='quiz',
                priority=6,
                reasoning='Practice S3 questions',
                estimated_time_minutes=20,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=5)
            )
        ]
        
        mock_engine.get_personalized_recommendations.return_value = sample_recommendations
        mock_engine.generate_study_path.return_value = {
            'user_id': 'test-user',
            'certification_type': 'SAA',
            'study_phases': [
                {
                    'phase': 1,
                    'title': 'Foundation Phase',
                    'estimated_time_hours': 10,
                    'topics': ['EC2', 'S3']
                }
            ],
            'total_estimated_hours': 10
        }
        mock_engine.record_recommendation_feedback.return_value = True
        mock_engine.identify_weak_areas.return_value = {
            'weak_categories': [{'category': 'S3', 'avg_score': 65.0}],
            'recommendations': ['Focus on S3 topics']
        }
        mock_engine.get_content_difficulty_progression.return_value = {
            'current_level': 'beginner',
            'recommended_level': 'intermediate',
            'progression_path': ['Continue with beginner content']
        }
        
        return mock_engine
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.function_name = 'test-recommendation-lambda'
        context.function_version = '1'
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-recommendation-lambda'
        context.memory_limit_in_mb = 512
        context.remaining_time_in_millis = lambda: 30000
        return context
    
    def test_lambda_handler_get_recommendations(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test lambda handler for getting recommendations."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {
                'certification_type': 'SAA',
                'limit': '5'
            }
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'test-user'
        assert body['certification_type'] == 'SAA'
        assert len(body['recommendations']) == 2
        assert body['recommendations'][0]['type'] == 'content'
    
    def test_lambda_handler_get_study_path(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test lambda handler for getting study path."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user/study-path',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'test-user'
        assert body['certification_type'] == 'SAA'
        assert len(body['study_path']['study_phases']) == 1
    
    def test_lambda_handler_record_feedback(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test lambda handler for recording feedback."""
        event = {
            'httpMethod': 'POST',
            'path': '/api/recommendations/test-user/feedback',
            'body': json.dumps({
                'user_id': 'test-user',
                'recommendation_id': 'rec-1',
                'action': 'accepted',
                'feedback_data': {'rating': 5}
            })
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'successfully' in body['message']
    
    def test_lambda_handler_get_weak_areas(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test lambda handler for getting weak areas."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user/weak-areas',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'test-user'
        assert len(body['weak_areas']['weak_categories']) == 1
    
    def test_lambda_handler_get_content_progression(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test lambda handler for getting content progression."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user/content-progression',
            'queryStringParameters': {
                'certification_type': 'SAA'
            }
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'test-user'
        assert body['progression']['current_level'] == 'beginner'
    
    def test_lambda_handler_missing_user_id(self, lambda_context, mock_env_vars):
        """Test lambda handler with missing user_id."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'user_id is required' in body['error']['message']
    
    def test_lambda_handler_invalid_endpoint(self, lambda_context, mock_env_vars):
        """Test lambda handler with invalid endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/invalid/test-user',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            response = lambda_handler(event, lambda_context)
        
        # The path doesn't contain '/recommendations/' so user_id extraction fails, returning 400
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'user_id is required' in body['error']['message']
    
    def test_handle_get_recommendations_invalid_certification(self):
        """Test get recommendations with invalid certification type."""
        query_params = {
            'certification_type': 'INVALID',
            'limit': '5'
        }
        
        response = handle_get_recommendations(query_params, 'test-user')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid certification type' in body['error']['message']
    
    def test_handle_get_recommendations_invalid_limit(self):
        """Test get recommendations with invalid limit."""
        query_params = {
            'limit': '100'  # Too high
        }
        
        response = handle_get_recommendations(query_params, 'test-user')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'limit must be between 1 and 50' in body['error']['message']
    
    def test_handle_get_study_path_missing_certification(self):
        """Test get study path with missing certification type."""
        query_params = {}
        
        response = handle_get_study_path(query_params, 'test-user')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'certification_type is required' in body['error']['message']
    
    def test_handle_record_feedback_missing_fields(self):
        """Test record feedback with missing required fields."""
        body = {
            'recommendation_id': 'rec-1'
            # Missing action
        }
        
        response = handle_record_feedback(body, 'test-user')
        
        assert response['statusCode'] == 400
        body_response = json.loads(response['body'])
        assert 'recommendation_id and action are required' in body_response['error']['message']
    
    def test_handle_record_feedback_invalid_action(self):
        """Test record feedback with invalid action."""
        body = {
            'recommendation_id': 'rec-1',
            'action': 'invalid_action'
        }
        
        response = handle_record_feedback(body, 'test-user')
        
        assert response['statusCode'] == 400
        body_response = json.loads(response['body'])
        assert 'action must be one of' in body_response['error']['message']
    
    def test_create_success_response(self):
        """Test creating success response."""
        data = {'test': 'data'}
        response = create_success_response(data)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body == data
    
    def test_create_error_response(self):
        """Test creating error response."""
        response = create_error_response(400, 'Test error message')
        
        assert response['statusCode'] == 400
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error']['message'] == 'Test error message'
        assert 'timestamp' in body['error']
    
    def test_lambda_handler_exception_handling(self, lambda_context):
        """Test lambda handler exception handling."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {}
        }
        
        # Mock initialization to raise exception
        with patch('recommendation_lambda_src.main.initialize_services', side_effect=Exception('Test error')):
            response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Internal server error' in body['error']['message']
    
    def test_initialization_missing_env_vars(self):
        """Test initialization with missing environment variables."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('recommendation_lambda_src.main.recommendation_engine', None):
                from recommendation_lambda_src.main import initialize_services
                
                with pytest.raises(ValueError, match="Required environment variables not set"):
                    initialize_services()
    
    def test_recommendation_engine_error_handling(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test handling of recommendation engine errors."""
        # Mock engine to raise exception
        mock_recommendation_engine.get_personalized_recommendations.side_effect = Exception('Engine error')
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to get recommendations' in body['error']['message']
    
    def test_feedback_recording_failure(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test feedback recording failure handling."""
        # Mock engine to return failure
        mock_recommendation_engine.record_recommendation_feedback.return_value = False
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/recommendations/test-user/feedback',
            'body': json.dumps({
                'recommendation_id': 'rec-1',
                'action': 'accepted'
            })
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'Failed to record feedback' in body['error']['message']
    
    def test_cors_headers_present(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test that CORS headers are present in all responses."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        headers = response['headers']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'
    
    def test_response_serialization(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test that datetime objects are properly serialized in responses."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        # Should not raise JSON serialization error
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that datetime fields are serialized as strings
        if body['recommendations']:
            rec = body['recommendations'][0]
            assert isinstance(rec['created_at'], str)
            assert isinstance(rec['expires_at'], str)
    
    def test_query_parameter_parsing(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test proper parsing of query parameters."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/test-user',
            'queryStringParameters': {
                'certification_type': 'saa',  # lowercase
                'limit': '3'
            }
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['certification_type'] == 'SAA'  # Should be converted to uppercase
        
        # Verify the engine was called with correct parameters
        mock_recommendation_engine.get_personalized_recommendations.assert_called_once_with(
            'test-user', CertificationType.SAA, 3
        )
    
    def test_path_parameter_extraction(self, mock_recommendation_engine, lambda_context, mock_env_vars):
        """Test extraction of user_id from path parameters."""
        event = {
            'httpMethod': 'GET',
            'path': '/api/recommendations/user-123/weak-areas',
            'queryStringParameters': {}
        }
        
        with patch.dict('os.environ', mock_env_vars):
            with patch('recommendation_lambda_src.main.recommendation_engine', mock_recommendation_engine):
                response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == 'user-123'
        
        # Verify the engine was called with correct user_id
        mock_recommendation_engine.identify_weak_areas.assert_called_once_with('user-123', None)


if __name__ == '__main__':
    pytest.main([__file__])