"""
Recommendation Engine Lambda Function

This Lambda function provides personalized study recommendations based on user performance data,
including weak area identification, content difficulty progression, and study path generation.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError

# Import shared modules
from shared.models import CertificationType, DifficultyLevel, ContentType
from shared.recommendation_engine import RecommendationEngine
from shared.interfaces import InteractionData

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services
recommendation_engine = None

def initialize_services():
    """Initialize services with environment variables."""
    global recommendation_engine
    
    if recommendation_engine is None:
        user_progress_table = os.environ.get('USER_PROGRESS_TABLE_NAME')
        content_metadata_table = os.environ.get('CONTENT_METADATA_TABLE_NAME')
        recommendations_table = os.environ.get('RECOMMENDATIONS_TABLE_NAME')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if not all([user_progress_table, content_metadata_table, recommendations_table]):
            raise ValueError("Required environment variables not set")
        
        recommendation_engine = RecommendationEngine(
            user_progress_table_name=user_progress_table,
            content_metadata_table_name=content_metadata_table,
            recommendations_table_name=recommendations_table,
            region_name=region
        )
        
        logger.info("Recommendation engine services initialized")

def set_recommendation_engine(engine):
    """Set recommendation engine for testing purposes."""
    global recommendation_engine
    recommendation_engine = engine

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for recommendation engine operations.
    
    Supported operations:
    - get_recommendations: Get personalized study recommendations
    - generate_study_path: Generate personalized study path
    - record_feedback: Record user feedback on recommendations
    - get_weak_areas: Identify weak areas from performance data
    - get_content_progression: Get content difficulty progression recommendations
    """
    try:
        initialize_services()
        
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
        else:
            body = {}
        
        # Extract user_id from path or body
        user_id = None
        if '/recommendations/' in path:
            path_parts = path.split('/')
            # Find the index of 'recommendations' and get the next part
            try:
                rec_index = path_parts.index('recommendations')
                if len(path_parts) > rec_index + 1:
                    user_id = path_parts[rec_index + 1]
            except ValueError:
                pass
        
        if not user_id:
            user_id = body.get('user_id') or query_params.get('user_id')
        
        if not user_id:
            return create_error_response(400, "user_id is required")
        
        # Route to appropriate handler
        if '/recommendations/' in path and http_method == 'GET':
            if path.endswith('/study-path'):
                return handle_get_study_path(query_params, user_id)
            elif path.endswith('/weak-areas'):
                return handle_get_weak_areas(query_params, user_id)
            elif path.endswith('/content-progression'):
                return handle_get_content_progression(query_params, user_id)
            elif path.split('/')[-1] == user_id:  # Just /recommendations/{user_id}
                return handle_get_recommendations(query_params, user_id)
            else:
                return create_error_response(404, f"Endpoint not found: {http_method} {path}")
        elif '/recommendations/' in path and path.endswith('/feedback') and http_method == 'POST':
            return handle_record_feedback(body, user_id)
        else:
            return create_error_response(404, f"Endpoint not found: {http_method} {path}")
    
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return create_error_response(500, "Internal server error")

def handle_get_recommendations(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting personalized study recommendations."""
    try:
        # Parse parameters
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        limit = int(query_params.get('limit', 10))
        if limit < 1 or limit > 50:
            return create_error_response(400, "limit must be between 1 and 50")
        
        # Get recommendations
        recommendations = recommendation_engine.get_personalized_recommendations(
            user_id, certification_type, limit
        )
        
        # Format response
        recommendation_data = []
        for rec in recommendations:
            recommendation_data.append({
                'recommendation_id': rec.recommendation_id,
                'type': rec.type,
                'priority': rec.priority,
                'content_id': rec.content_id,
                'reasoning': rec.reasoning,
                'estimated_time_minutes': rec.estimated_time_minutes,
                'created_at': rec.created_at.isoformat(),
                'expires_at': rec.expires_at.isoformat()
            })
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value if certification_type else None,
            'recommendations': recommendation_data,
            'total_count': len(recommendation_data)
        })
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return create_error_response(500, "Failed to get recommendations")

def handle_get_study_path(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting personalized study path."""
    try:
        # Parse certification type (required)
        cert_param = query_params.get('certification_type')
        if not cert_param:
            return create_error_response(400, "certification_type is required")
        
        try:
            certification_type = CertificationType(cert_param.upper())
        except ValueError:
            return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Generate study path
        study_path = recommendation_engine.generate_study_path(user_id, certification_type)
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value,
            'study_path': study_path
        })
    
    except Exception as e:
        logger.error(f"Error generating study path: {str(e)}")
        return create_error_response(500, "Failed to generate study path")

def handle_record_feedback(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle recording user feedback on recommendations."""
    try:
        # Validate required fields
        recommendation_id = body.get('recommendation_id')
        action = body.get('action')
        
        if not recommendation_id or not action:
            return create_error_response(400, "recommendation_id and action are required")
        
        if action not in ['accepted', 'rejected', 'completed', 'skipped']:
            return create_error_response(400, "action must be one of: accepted, rejected, completed, skipped")
        
        # Record feedback
        success = recommendation_engine.record_recommendation_feedback(
            user_id, recommendation_id, action, body.get('feedback_data', {})
        )
        
        if success:
            return create_success_response({
                'success': True,
                'message': 'Feedback recorded successfully'
            })
        else:
            return create_error_response(500, "Failed to record feedback")
    
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        return create_error_response(500, "Failed to record feedback")

def handle_get_weak_areas(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle identifying weak areas from user performance."""
    try:
        # Parse certification type if provided
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Get weak areas
        weak_areas = recommendation_engine.identify_weak_areas(user_id, certification_type)
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value if certification_type else None,
            'weak_areas': weak_areas
        })
    
    except Exception as e:
        logger.error(f"Error identifying weak areas: {str(e)}")
        return create_error_response(500, "Failed to identify weak areas")

def handle_get_content_progression(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting content difficulty progression recommendations."""
    try:
        # Parse certification type if provided
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Get content progression
        progression = recommendation_engine.get_content_difficulty_progression(user_id, certification_type)
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value if certification_type else None,
            'progression': progression
        })
    
    except Exception as e:
        logger.error(f"Error getting content progression: {str(e)}")
        return create_error_response(500, "Failed to get content progression")

def create_success_response(data: Any) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(data, default=str)
    }

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'error': {
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    }