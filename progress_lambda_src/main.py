"""
Enhanced Progress Tracking Lambda Function

This Lambda function provides enhanced progress tracking and analytics capabilities
for the ProCert Learning Platform, including real-time interaction recording,
performance analytics, achievement tracking, and certification readiness assessment.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError

# Import shared modules
from shared.progress_tracker import ProgressTracker
from shared.interfaces import InteractionData
from shared.models import CertificationType, validate_model

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services
progress_tracker = None

def initialize_services():
    """Initialize services with environment variables."""
    global progress_tracker
    
    if progress_tracker is None:
        user_progress_table = os.environ.get('USER_PROGRESS_TABLE_NAME')
        content_metadata_table = os.environ.get('CONTENT_METADATA_TABLE_NAME')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if not user_progress_table or not content_metadata_table:
            raise ValueError("Required environment variables not set")
        
        progress_tracker = ProgressTracker(
            user_progress_table_name=user_progress_table,
            content_metadata_table_name=content_metadata_table,
            region_name=region
        )
        
        logger.info("Progress tracking services initialized")

def set_progress_tracker(tracker):
    """Set progress tracker for testing purposes."""
    global progress_tracker
    progress_tracker = tracker

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for enhanced progress tracking operations.
    
    Supported operations:
    - record_interaction: Record user interaction with content
    - get_performance_analytics: Get comprehensive performance analytics
    - get_performance_trends: Get performance trends over time
    - calculate_certification_readiness: Calculate certification readiness
    - check_achievements: Check for new achievements
    - get_dashboard_data: Get comprehensive dashboard data
    """
    try:
        initialize_services()
        
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
        else:
            body = {}
        
        # Extract user_id from path or body
        user_id = None
        if '/progress/' in path:
            path_parts = path.split('/')
            if len(path_parts) > 2:
                user_id = path_parts[2]
        
        if not user_id:
            user_id = body.get('user_id') or query_params.get('user_id')
        
        if not user_id:
            return create_error_response(400, "user_id is required")
        
        # Route to appropriate handler
        if path.endswith('/interaction') and http_method == 'POST':
            return handle_record_interaction(body, user_id)
        elif path.endswith('/analytics') and http_method == 'GET':
            return handle_get_analytics(query_params, user_id)
        elif path.endswith('/trends') and http_method == 'GET':
            return handle_get_trends(query_params, user_id)
        elif path.endswith('/readiness') and http_method == 'GET':
            return handle_get_readiness(query_params, user_id)
        elif path.endswith('/achievements') and http_method == 'GET':
            return handle_get_achievements(query_params, user_id)
        elif path.endswith('/dashboard') and http_method == 'GET':
            return handle_get_dashboard(query_params, user_id)
        else:
            return create_error_response(404, f"Endpoint not found: {http_method} {path}")
    
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return create_error_response(500, "Internal server error")

def handle_record_interaction(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle recording user interaction with content."""
    try:
        # Validate required fields
        content_id = body.get('content_id')
        interaction_type = body.get('interaction_type')
        
        if not content_id or not interaction_type:
            return create_error_response(400, "content_id and interaction_type are required")
        
        # Create interaction data
        interaction = InteractionData(
            interaction_type=interaction_type,
            score=body.get('score'),
            time_spent=body.get('time_spent', 0),
            additional_data=body.get('additional_data', {})
        )
        
        # Record interaction
        success = progress_tracker.record_interaction(user_id, content_id, interaction)
        
        if success:
            # Check for new achievements
            new_achievements = progress_tracker.check_achievements(user_id)
            
            return create_success_response({
                'success': True,
                'message': 'Interaction recorded successfully',
                'new_achievements': [
                    {
                        'title': achievement.title,
                        'description': achievement.description,
                        'badge_icon': achievement.badge_icon,
                        'points': achievement.points
                    }
                    for achievement in new_achievements
                ]
            })
        else:
            return create_error_response(500, "Failed to record interaction")
    
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        return create_error_response(500, "Failed to record interaction")

def handle_get_analytics(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting performance analytics."""
    try:
        # Parse certification type if provided
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Get analytics
        analytics = progress_tracker.get_performance_analytics(user_id, certification_type)
        
        return create_success_response({
            'user_id': analytics.user_id,
            'certification_type': certification_type.value if certification_type else None,
            'total_content_viewed': analytics.total_content_viewed,
            'total_questions_answered': analytics.total_questions_answered,
            'average_score': analytics.average_score,
            'time_spent_total_hours': analytics.time_spent_total / 3600,
            'completion_rate': analytics.completion_rate
        })
    
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return create_error_response(500, "Failed to get analytics")

def handle_get_trends(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting performance trends."""
    try:
        # Parse parameters
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        days = int(query_params.get('days', 30))
        if days < 1 or days > 365:
            return create_error_response(400, "days must be between 1 and 365")
        
        # Get trends
        trends = progress_tracker.get_performance_trends(user_id, certification_type, days)
        
        trend_data = []
        for trend in trends:
            trend_data.append({
                'date': trend.date.isoformat(),
                'certification_type': trend.certification_type.value,
                'metrics': trend.metrics,
                'category_breakdown': trend.category_breakdown,
                'difficulty_breakdown': trend.difficulty_breakdown
            })
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value if certification_type else None,
            'period_days': days,
            'trends': trend_data
        })
    
    except ValueError as e:
        return create_error_response(400, str(e))
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return create_error_response(500, "Failed to get trends")

def handle_get_readiness(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting certification readiness assessment."""
    try:
        # Parse certification type (required)
        cert_param = query_params.get('certification_type')
        if not cert_param:
            return create_error_response(400, "certification_type is required")
        
        try:
            certification_type = CertificationType(cert_param.upper())
        except ValueError:
            return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Calculate readiness
        readiness = progress_tracker.calculate_certification_readiness(user_id, certification_type)
        
        return create_success_response({
            'user_id': readiness.user_id,
            'certification_type': readiness.certification_type.value,
            'readiness_score': readiness.readiness_score,
            'estimated_study_time_hours': readiness.estimated_study_time_hours,
            'weak_areas': readiness.weak_areas,
            'strong_areas': readiness.strong_areas,
            'recommended_actions': readiness.recommended_actions,
            'confidence_level': readiness.confidence_level,
            'predicted_pass_probability': readiness.predicted_pass_probability,
            'assessment_date': readiness.assessment_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating readiness: {str(e)}")
        return create_error_response(500, "Failed to calculate readiness")

def handle_get_achievements(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting user achievements."""
    try:
        # Parse certification type if provided
        certification_type = None
        cert_param = query_params.get('certification_type')
        if cert_param:
            try:
                certification_type = CertificationType(cert_param.upper())
            except ValueError:
                return create_error_response(400, f"Invalid certification type: {cert_param}")
        
        # Get achievements
        achievements = progress_tracker.get_user_achievements(user_id, certification_type)
        
        achievement_data = []
        for achievement in achievements:
            achievement_data.append({
                'achievement_id': achievement.achievement_id,
                'achievement_type': achievement.achievement_type,
                'title': achievement.title,
                'description': achievement.description,
                'badge_icon': achievement.badge_icon,
                'points': achievement.points,
                'earned_at': achievement.earned_at.isoformat(),
                'certification_type': achievement.certification_type.value if achievement.certification_type else None
            })
        
        return create_success_response({
            'user_id': user_id,
            'certification_type': certification_type.value if certification_type else None,
            'achievements': achievement_data,
            'total_points': sum(a.points for a in achievements),
            'total_achievements': len(achievements)
        })
    
    except Exception as e:
        logger.error(f"Error getting achievements: {str(e)}")
        return create_error_response(500, "Failed to get achievements")

def handle_get_dashboard(query_params: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Handle getting comprehensive dashboard data."""
    try:
        # Get dashboard data
        dashboard_data = progress_tracker.get_dashboard_data(user_id)
        
        return create_success_response(dashboard_data)
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return create_error_response(500, "Failed to get dashboard data")

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