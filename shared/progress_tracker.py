"""
Progress Tracker implementation for the ProCert content management system.

This module provides the concrete implementation of the IProgressTracker interface,
handling user progress tracking, interaction recording, and performance analytics.
"""

import os
import boto3
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from collections import defaultdict
from botocore.exceptions import ClientError

from .interfaces import IProgressTracker, InteractionData, PerformanceMetrics
from .models import (
    UserProgress, ContentMetadata, CertificationType, ProgressType,
    validate_model
)


logger = logging.getLogger(__name__)


class ProgressTracker(IProgressTracker):
    """
    Concrete implementation of progress tracking for user interactions and analytics.
    
    This class handles recording user interactions with content, calculating progress
    metrics, and providing comprehensive analytics for user performance tracking.
    """
    
    def __init__(self, 
                 user_progress_table_name: str,
                 content_metadata_table_name: str,
                 region_name: str = 'us-east-1'):
        """
        Initialize the ProgressTracker with DynamoDB table names.
        
        Args:
            user_progress_table_name: Name of the user progress DynamoDB table
            content_metadata_table_name: Name of the content metadata DynamoDB table
            region_name: AWS region name
        """
        self.user_progress_table_name = user_progress_table_name
        self.content_metadata_table_name = content_metadata_table_name
        self.region_name = region_name
        
        # Initialize DynamoDB client and resources
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.user_progress_table = self.dynamodb.Table(user_progress_table_name)
        self.content_metadata_table = self.dynamodb.Table(content_metadata_table_name)
        
        logger.info(f"ProgressTracker initialized with tables: {user_progress_table_name}, {content_metadata_table_name}")
    
    def record_interaction(self, user_id: str, content_id: str, interaction: InteractionData) -> bool:
        """
        Record a user interaction with content.
        
        Args:
            user_id: User identifier
            content_id: Content identifier
            interaction: Interaction data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get content metadata to determine certification type
            content = self._get_content_metadata(content_id)
            if not content:
                logger.error(f"Content not found for interaction recording: {content_id}")
                return False
            
            # Create UserProgress instance from interaction data
            progress_type = self._map_interaction_to_progress_type(interaction.interaction_type)
            
            user_progress = UserProgress(
                user_id=user_id,
                content_id=content_id,
                progress_type=progress_type,
                score=interaction.score,
                time_spent=interaction.time_spent,
                timestamp=datetime.utcnow(),
                session_id=interaction.additional_data.get('session_id', '')
            )
            
            # Validate progress data
            validate_model(user_progress)
            
            # Prepare composite sort key: content_id#certification_type#timestamp
            timestamp_str = user_progress.timestamp.isoformat()
            content_id_cert_time = f"{content_id}#{content.certification_type.value}#{timestamp_str}"
            
            # Prepare item for DynamoDB
            item = {
                'user_id': user_id,
                'content_id_cert_time': content_id_cert_time,
                'content_id': content_id,
                'certification_type': content.certification_type.value,
                'progress_type': progress_type.value,
                'score': Decimal(str(interaction.score)) if interaction.score is not None else None,
                'time_spent': interaction.time_spent,
                'timestamp': timestamp_str,
                'session_id': user_progress.session_id,
                'interaction_type': interaction.interaction_type,
                'additional_data': interaction.additional_data
            }
            
            # Use conditional write to prevent duplicate interactions
            condition_expression = 'attribute_not_exists(content_id_cert_time)'
            
            try:
                response = self.user_progress_table.put_item(
                    Item=item,
                    ConditionExpression=condition_expression
                )
                
                logger.info(f"Successfully recorded interaction: {user_id} -> {content_id} ({interaction.interaction_type})")
                return True
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    # Duplicate interaction, update existing record instead
                    return self._update_existing_interaction(user_id, content_id_cert_time, interaction)
                else:
                    raise
            
        except ValueError as e:
            logger.error(f"Validation error recording interaction: {str(e)}")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error recording interaction: {error_code} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error recording interaction: {str(e)}")
            return False
    
    def get_user_progress(self, user_id: str, certification_type: Optional[CertificationType] = None) -> List[UserProgress]:
        """
        Get user progress data, optionally filtered by certification type.
        
        Args:
            user_id: User identifier
            certification_type: Optional certification type filter
            
        Returns:
            List of UserProgress instances
        """
        try:
            if certification_type:
                # Use GSI to filter by user and certification type
                response = self.user_progress_table.query(
                    IndexName='UserCertificationIndex',
                    KeyConditionExpression='user_id = :user_id AND certification_type = :cert_type',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':cert_type': certification_type.value
                    }
                )
            else:
                # Query all progress for user
                response = self.user_progress_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': user_id}
                )
            
            progress_list = []
            for item in response['Items']:
                try:
                    progress = self._item_to_user_progress(item)
                    progress_list.append(progress)
                except Exception as e:
                    logger.warning(f"Failed to parse progress item: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(progress_list)} progress items for user {user_id}")
            return progress_list
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error retrieving user progress: {error_code} - {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving user progress: {str(e)}")
            return []
    
    def calculate_completion_rate(self, user_id: str, category: str, 
                                certification_type: Optional[CertificationType] = None) -> float:
        """
        Calculate completion rate for a category.
        
        Args:
            user_id: User identifier
            category: Content category
            certification_type: Optional certification type filter
            
        Returns:
            Completion rate as percentage (0-100)
        """
        try:
            # Get all content in the category
            total_content = self._get_content_by_category(category, certification_type)
            if not total_content:
                logger.info(f"No content found for category {category}")
                return 0.0
            
            # Get user progress for the category
            user_progress = self.get_user_progress(user_id, certification_type)
            
            # Filter progress by category and find completed content
            completed_content_ids = set()
            for progress in user_progress:
                if progress.progress_type == ProgressType.COMPLETED:
                    # Check if this content belongs to the category
                    content = self._get_content_metadata(progress.content_id)
                    if content and content.category == category:
                        completed_content_ids.add(progress.content_id)
            
            # Calculate completion rate
            total_count = len(total_content)
            completed_count = len(completed_content_ids)
            completion_rate = (completed_count / total_count) * 100 if total_count > 0 else 0.0
            
            logger.info(f"Completion rate for user {user_id}, category {category}: {completion_rate:.2f}% ({completed_count}/{total_count})")
            return completion_rate
            
        except Exception as e:
            logger.error(f"Error calculating completion rate: {str(e)}")
            return 0.0
    
    def get_performance_analytics(self, user_id: str, 
                                certification_type: Optional[CertificationType] = None) -> PerformanceMetrics:
        """
        Get comprehensive performance analytics for a user.
        
        Args:
            user_id: User identifier
            certification_type: Optional certification type filter
            
        Returns:
            PerformanceMetrics instance
        """
        try:
            # Get all user progress
            user_progress = self.get_user_progress(user_id, certification_type)
            
            # Initialize metrics
            total_content_viewed = 0
            total_questions_answered = 0
            total_time_spent = 0
            scores = []
            completed_content = set()
            
            # Process progress data
            for progress in user_progress:
                total_time_spent += progress.time_spent
                
                if progress.progress_type == ProgressType.VIEWED:
                    total_content_viewed += 1
                elif progress.progress_type == ProgressType.ANSWERED:
                    total_questions_answered += 1
                    if progress.score is not None:
                        scores.append(progress.score)
                elif progress.progress_type == ProgressType.COMPLETED:
                    completed_content.add(progress.content_id)
            
            # Calculate average score
            average_score = sum(scores) / len(scores) if scores else 0.0
            
            # Calculate completion rate (overall)
            total_available_content = self._get_total_content_count(certification_type)
            completion_rate = (len(completed_content) / total_available_content * 100) if total_available_content > 0 else 0.0
            
            metrics = PerformanceMetrics(
                user_id=user_id,
                total_content_viewed=total_content_viewed,
                total_questions_answered=total_questions_answered,
                average_score=average_score,
                time_spent_total=total_time_spent,
                completion_rate=completion_rate
            )
            
            logger.info(f"Generated performance analytics for user {user_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error generating performance analytics: {str(e)}")
            return PerformanceMetrics(
                user_id=user_id,
                total_content_viewed=0,
                total_questions_answered=0,
                average_score=0.0,
                time_spent_total=0,
                completion_rate=0.0
            )
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary for specified period.
        
        Args:
            user_id: User identifier
            days: Number of days to include
            
        Returns:
            Dictionary with activity summary data
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get user progress within date range
            user_progress = self.get_user_progress(user_id)
            
            # Filter by date range
            recent_progress = [
                p for p in user_progress 
                if start_date <= p.timestamp <= end_date
            ]
            
            # Group by date and certification type
            daily_activity = defaultdict(lambda: defaultdict(int))
            certification_activity = defaultdict(int)
            category_activity = defaultdict(int)
            
            for progress in recent_progress:
                date_key = progress.timestamp.date().isoformat()
                daily_activity[date_key][progress.progress_type.value] += 1
                
                # Get content metadata for certification and category info
                content = self._get_content_metadata(progress.content_id)
                if content:
                    certification_activity[content.certification_type.value] += 1
                    category_activity[content.category] += 1
            
            # Calculate streaks
            study_streak = self._calculate_study_streak(user_progress, end_date)
            
            # Calculate weekly averages
            weeks_in_period = max(1, days // 7)
            weekly_avg_time = sum(p.time_spent for p in recent_progress) / weeks_in_period / 60  # minutes
            weekly_avg_interactions = len(recent_progress) / weeks_in_period
            
            summary = {
                'user_id': user_id,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_interactions': len(recent_progress),
                'daily_activity': dict(daily_activity),
                'certification_breakdown': dict(certification_activity),
                'category_breakdown': dict(category_activity),
                'study_streak_days': study_streak,
                'weekly_avg_time_minutes': round(weekly_avg_time, 2),
                'weekly_avg_interactions': round(weekly_avg_interactions, 2),
                'most_active_certification': max(certification_activity.items(), key=lambda x: x[1])[0] if certification_activity else None,
                'most_active_category': max(category_activity.items(), key=lambda x: x[1])[0] if category_activity else None
            }
            
            logger.info(f"Generated activity summary for user {user_id} ({days} days)")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating activity summary: {str(e)}")
            return {
                'user_id': user_id,
                'period_days': days,
                'error': str(e)
            }
    
    # Helper methods
    
    def _get_content_metadata(self, content_id: str) -> Optional[ContentMetadata]:
        """Get content metadata by ID."""
        try:
            # Query all certification types for this content_id
            response = self.content_metadata_table.query(
                KeyConditionExpression='content_id = :content_id',
                ExpressionAttributeValues={':content_id': content_id},
                Limit=1
            )
            
            if response['Items']:
                return self._item_to_content_metadata(response['Items'][0])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving content metadata: {str(e)}")
            return None
    
    def _get_content_by_category(self, category: str, certification_type: Optional[CertificationType] = None) -> List[ContentMetadata]:
        """Get all content in a specific category."""
        try:
            if certification_type:
                response = self.content_metadata_table.query(
                    IndexName='CertificationTypeIndex',
                    KeyConditionExpression='certification_type = :cert_type',
                    FilterExpression='category = :category',
                    ExpressionAttributeValues={
                        ':cert_type': certification_type.value,
                        ':category': category
                    }
                )
            else:
                response = self.content_metadata_table.scan(
                    FilterExpression='category = :category',
                    ExpressionAttributeValues={':category': category}
                )
            
            content_list = []
            for item in response['Items']:
                try:
                    content = self._item_to_content_metadata(item)
                    content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {str(e)}")
                    continue
            
            return content_list
            
        except Exception as e:
            logger.error(f"Error retrieving content by category: {str(e)}")
            return []
    
    def _get_total_content_count(self, certification_type: Optional[CertificationType] = None) -> int:
        """Get total count of available content."""
        try:
            if certification_type:
                response = self.content_metadata_table.query(
                    IndexName='CertificationTypeIndex',
                    KeyConditionExpression='certification_type = :cert_type',
                    ExpressionAttributeValues={':cert_type': certification_type.value},
                    Select='COUNT'
                )
            else:
                response = self.content_metadata_table.scan(Select='COUNT')
            
            return response['Count']
            
        except Exception as e:
            logger.error(f"Error getting total content count: {str(e)}")
            return 0
    
    def _map_interaction_to_progress_type(self, interaction_type: str) -> ProgressType:
        """Map interaction type to progress type enum."""
        interaction_mapping = {
            'view': ProgressType.VIEWED,
            'viewed': ProgressType.VIEWED,
            'answer': ProgressType.ANSWERED,
            'answered': ProgressType.ANSWERED,
            'complete': ProgressType.COMPLETED,
            'completed': ProgressType.COMPLETED,
            'finish': ProgressType.COMPLETED,
            'finished': ProgressType.COMPLETED
        }
        
        return interaction_mapping.get(interaction_type.lower(), ProgressType.VIEWED)
    
    def _update_existing_interaction(self, user_id: str, content_id_cert_time: str, interaction: InteractionData) -> bool:
        """Update existing interaction record."""
        try:
            update_expression_parts = []
            expression_attribute_values = {}
            
            if interaction.score is not None:
                update_expression_parts.append('score = :score')
                expression_attribute_values[':score'] = Decimal(str(interaction.score))
            
            if interaction.time_spent > 0:
                update_expression_parts.append('time_spent = time_spent + :time_spent')
                expression_attribute_values[':time_spent'] = interaction.time_spent
            
            if interaction.additional_data:
                update_expression_parts.append('additional_data = :additional_data')
                expression_attribute_values[':additional_data'] = interaction.additional_data
            
            # Always update timestamp
            update_expression_parts.append('timestamp = :timestamp')
            expression_attribute_values[':timestamp'] = datetime.utcnow().isoformat()
            
            if not update_expression_parts:
                return True  # Nothing to update
            
            update_expression = 'SET ' + ', '.join(update_expression_parts)
            
            response = self.user_progress_table.update_item(
                Key={
                    'user_id': user_id,
                    'content_id_cert_time': content_id_cert_time
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated existing interaction: {user_id} -> {content_id_cert_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating existing interaction: {str(e)}")
            return False
    
    def _calculate_study_streak(self, user_progress: List[UserProgress], end_date: datetime) -> int:
        """Calculate consecutive days of study activity."""
        try:
            # Get unique study dates
            study_dates = set()
            for progress in user_progress:
                study_dates.add(progress.timestamp.date())
            
            if not study_dates:
                return 0
            
            # Sort dates in descending order
            sorted_dates = sorted(study_dates, reverse=True)
            
            # Calculate streak from most recent date
            streak = 0
            expected_date = end_date.date()
            
            for study_date in sorted_dates:
                if study_date == expected_date:
                    streak += 1
                    expected_date = expected_date - timedelta(days=1)
                elif study_date == expected_date + timedelta(days=1) and streak == 0:
                    # Handle case where end_date is not a study day but we want to count from the most recent study day
                    streak += 1
                    expected_date = study_date - timedelta(days=1)
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating study streak: {str(e)}")
            return 0
    
    def _item_to_content_metadata(self, item: Dict[str, Any]) -> ContentMetadata:
        """Convert DynamoDB item to ContentMetadata instance."""
        from .models import ContentMetadata
        return ContentMetadata.from_dict(item)
    
    def _item_to_user_progress(self, item: Dict[str, Any]) -> UserProgress:
        """Convert DynamoDB item to UserProgress instance."""
        # Convert Decimal back to float for score
        score = item.get('score')
        if score is not None and isinstance(score, Decimal):
            score = float(score)
        
        return UserProgress(
            user_id=item['user_id'],
            content_id=item['content_id'],
            progress_type=ProgressType(item['progress_type']),
            score=score,
            time_spent=item.get('time_spent', 0),
            timestamp=datetime.fromisoformat(item['timestamp']),
            session_id=item.get('session_id', '')
        )