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
    Achievement, PerformanceTrend, CertificationReadiness,
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
            
            # Prepare composite sort key: content_id#certification_type (matching table schema)
            timestamp_str = user_progress.timestamp.isoformat()
            content_id_certification = f"{content_id}#{content.certification_type.value}"
            
            # Prepare item for DynamoDB
            item = {
                'user_id': user_id,
                'content_id_certification': content_id_certification,
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
            condition_expression = 'attribute_not_exists(content_id_certification)'
            
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
                    return self._update_existing_interaction(user_id, content_id_certification, interaction)
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
            # Since the table has a composite key (content_id, certification_type),
            # we need to scan for the content_id or use a GSI
            # First, try to find it by scanning (not ideal but works for now)
            response = self.content_metadata_table.scan(
                FilterExpression='content_id = :content_id',
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
    
    def _update_existing_interaction(self, user_id: str, content_id_certification: str, interaction: InteractionData) -> bool:
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
                    'content_id_certification': content_id_certification
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated existing interaction: {user_id} -> {content_id_certification}")
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
    
    def get_performance_trends(self, user_id: str, certification_type: Optional[CertificationType] = None, 
                             days: int = 30) -> List[PerformanceTrend]:
        """
        Get performance trends over time with detailed breakdowns.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            days: Number of days to include
            
        Returns:
            List of PerformanceTrend instances
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get user progress within date range
            user_progress = self.get_user_progress(user_id, certification_type)
            
            # Filter by date range
            recent_progress = [
                p for p in user_progress 
                if start_date <= p.timestamp <= end_date
            ]
            
            # Group by date
            daily_data = defaultdict(list)
            for progress in recent_progress:
                date_key = progress.timestamp.date()
                daily_data[date_key].append(progress)
            
            trends = []
            for date, progress_list in daily_data.items():
                # Calculate daily metrics
                scores = [p.score for p in progress_list if p.score is not None]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                total_time = sum(p.time_spent for p in progress_list)
                completed_count = len([p for p in progress_list if p.progress_type == ProgressType.COMPLETED])
                
                # Category breakdown
                category_breakdown = defaultdict(lambda: {'count': 0, 'avg_score': 0.0, 'time_spent': 0})
                difficulty_breakdown = defaultdict(lambda: {'count': 0, 'avg_score': 0.0, 'time_spent': 0})
                
                for progress in progress_list:
                    content = self._get_content_metadata(progress.content_id)
                    if content:
                        # Category breakdown
                        cat_data = category_breakdown[content.category]
                        cat_data['count'] += 1
                        cat_data['time_spent'] += progress.time_spent
                        if progress.score is not None:
                            current_avg = cat_data['avg_score']
                            cat_data['avg_score'] = (current_avg * (cat_data['count'] - 1) + progress.score) / cat_data['count']
                        
                        # Difficulty breakdown
                        diff_data = difficulty_breakdown[content.difficulty_level.value]
                        diff_data['count'] += 1
                        diff_data['time_spent'] += progress.time_spent
                        if progress.score is not None:
                            current_avg = diff_data['avg_score']
                            diff_data['avg_score'] = (current_avg * (diff_data['count'] - 1) + progress.score) / diff_data['count']
                
                # Create trend instance
                cert_type = certification_type or CertificationType.GENERAL
                trend = PerformanceTrend(
                    user_id=user_id,
                    certification_type=cert_type,
                    date=datetime.combine(date, datetime.min.time()),
                    metrics={
                        'avg_score': avg_score,
                        'total_time': total_time,
                        'completed_count': completed_count,
                        'total_interactions': len(progress_list)
                    },
                    category_breakdown=dict(category_breakdown),
                    difficulty_breakdown=dict(difficulty_breakdown)
                )
                trends.append(trend)
            
            # Sort by date
            trends.sort(key=lambda x: x.date)
            
            logger.info(f"Generated {len(trends)} performance trends for user {user_id}")
            return trends
            
        except Exception as e:
            logger.error(f"Error generating performance trends: {str(e)}")
            return []
    
    def calculate_certification_readiness(self, user_id: str, certification_type: CertificationType) -> CertificationReadiness:
        """
        Calculate certification readiness assessment with estimated study time.
        
        Args:
            user_id: User identifier
            certification_type: Target certification type
            
        Returns:
            CertificationReadiness instance
        """
        try:
            # Get user progress for the certification
            user_progress = self.get_user_progress(user_id, certification_type)
            
            if not user_progress:
                return CertificationReadiness(
                    user_id=user_id,
                    certification_type=certification_type,
                    readiness_score=0.0,
                    estimated_study_time_hours=100,  # Default estimate
                    weak_areas=["All areas need attention"],
                    strong_areas=[],
                    recommended_actions=["Start with foundational topics", "Take diagnostic quiz"],
                    confidence_level="low",
                    predicted_pass_probability=10.0
                )
            
            # Calculate performance metrics by category
            category_performance = defaultdict(lambda: {'scores': [], 'completed': 0, 'total': 0})
            
            for progress in user_progress:
                content = self._get_content_metadata(progress.content_id)
                if content:
                    cat_perf = category_performance[content.category]
                    cat_perf['total'] += 1
                    if progress.score is not None:
                        cat_perf['scores'].append(progress.score)
                    if progress.progress_type == ProgressType.COMPLETED:
                        cat_perf['completed'] += 1
            
            # Analyze weak and strong areas
            weak_areas = []
            strong_areas = []
            category_scores = {}
            
            for category, perf in category_performance.items():
                if perf['scores']:
                    avg_score = sum(perf['scores']) / len(perf['scores'])
                    completion_rate = (perf['completed'] / perf['total']) * 100 if perf['total'] > 0 else 0
                    
                    # Combined score (70% performance, 30% completion)
                    combined_score = (avg_score * 0.7) + (completion_rate * 0.3)
                    category_scores[category] = combined_score
                    
                    if combined_score < 60:
                        weak_areas.append(category)
                    elif combined_score > 80:
                        strong_areas.append(category)
            
            # Calculate overall readiness score
            if category_scores:
                readiness_score = sum(category_scores.values()) / len(category_scores)
            else:
                readiness_score = 0.0
            
            # Determine confidence level
            if readiness_score >= 80:
                confidence_level = "high"
                predicted_pass_probability = min(95.0, readiness_score + 10)
            elif readiness_score >= 60:
                confidence_level = "medium"
                predicted_pass_probability = readiness_score + 5
            else:
                confidence_level = "low"
                predicted_pass_probability = max(10.0, readiness_score - 10)
            
            # Estimate study time based on readiness using realistic certification data
            # Base study hours represent the middle of the range for each certification
            base_study_hours = {
                # Foundational Level
                CertificationType.CCP: 30,   # 20-40 hours range
                CertificationType.AIP: 30,   # 20-40 hours range
                
                # Associate Level
                CertificationType.SAA: 100,  # 80-120 hours range
                CertificationType.DVA: 90,   # 70-110 hours range
                CertificationType.SOA: 90,   # 70-110 hours range
                CertificationType.DEA: 115,  # 90-140 hours range
                CertificationType.MLA: 115,  # 90-140 hours range
                
                # Professional Level
                CertificationType.SAP: 160,  # 120-200+ hours range
                CertificationType.DOP: 160,  # 120-200+ hours range
                
                # Specialty Level
                CertificationType.SCS: 140,  # 100-180 hours range
                CertificationType.ANS: 140,  # 100-180 hours range
                CertificationType.MLS: 160   # 120-200+ hours range
            }.get(certification_type, 80)
            
            # Adjust based on current readiness
            readiness_factor = max(0.2, (100 - readiness_score) / 100)
            estimated_study_time_hours = int(base_study_hours * readiness_factor)
            
            # Generate certification-specific recommendations
            recommended_actions = []
            cert_level = self._get_certification_level(certification_type)
            
            if readiness_score < 40:
                if cert_level == "foundational":
                    recommended_actions.extend([
                        "Start with AWS Cloud Practitioner Essentials course",
                        "Focus on basic cloud concepts and AWS services overview",
                        "Complete hands-on labs for core services"
                    ])
                elif cert_level == "associate":
                    recommended_actions.extend([
                        "Review foundational AWS concepts first",
                        "Complete extensive hands-on labs - practice is crucial",
                        "Focus on core services for your certification track"
                    ])
                else:  # professional/specialty
                    recommended_actions.extend([
                        "Ensure you have solid Associate-level knowledge first",
                        "Focus on advanced concepts and real-world scenarios",
                        "Complete complex multi-service labs and case studies"
                    ])
                
                recommended_actions.extend([
                    "Complete more practice questions",
                    f"Review weak areas: {', '.join(weak_areas[:3])}"
                ])
                
            elif readiness_score < 70:
                recommended_actions.extend([
                    "Take practice exams to identify knowledge gaps",
                    "Review incorrect answers thoroughly",
                    "Focus on hands-on experience with AWS services"
                ])
                
                if cert_level in ["professional", "specialty"]:
                    recommended_actions.append("Study advanced scenarios and troubleshooting")
                
                if weak_areas:
                    recommended_actions.append(f"Prioritize studying: {', '.join(weak_areas[:2])}")
                    
            else:
                recommended_actions.extend([
                    "Take full-length practice exams under timed conditions",
                    "Review AWS exam strategies and question formats",
                    "Schedule your certification exam"
                ])
                
                if cert_level == "foundational":
                    recommended_actions.append("Consider pursuing an Associate-level certification next")
                elif cert_level == "associate":
                    recommended_actions.append("Consider Professional or Specialty certifications")
                
            # Add certification-specific advice
            if certification_type == CertificationType.SAA:
                if readiness_score < 70:
                    recommended_actions.append("Focus on architectural best practices and cost optimization")
            elif certification_type == CertificationType.DVA:
                if readiness_score < 70:
                    recommended_actions.append("Practice with AWS SDKs and API development")
            elif certification_type == CertificationType.SOA:
                if readiness_score < 70:
                    recommended_actions.append("Focus on monitoring, troubleshooting, and automation")
            elif certification_type in [CertificationType.SAP, CertificationType.DOP]:
                if readiness_score < 80:
                    recommended_actions.append("Ensure deep hands-on experience with complex scenarios")
            elif certification_type == CertificationType.MLS:
                if readiness_score < 70:
                    recommended_actions.append("Strengthen ML theory and AWS ML services integration")
            
            if not weak_areas:
                weak_areas = ["Continue practicing all areas"]
            if not strong_areas:
                strong_areas = ["Build foundational knowledge first"]
            
            return CertificationReadiness(
                user_id=user_id,
                certification_type=certification_type,
                readiness_score=readiness_score,
                estimated_study_time_hours=estimated_study_time_hours,
                weak_areas=weak_areas,
                strong_areas=strong_areas,
                recommended_actions=recommended_actions,
                confidence_level=confidence_level,
                predicted_pass_probability=predicted_pass_probability
            )
            
        except Exception as e:
            logger.error(f"Error calculating certification readiness: {str(e)}")
            return CertificationReadiness(
                user_id=user_id,
                certification_type=certification_type,
                readiness_score=0.0,
                estimated_study_time_hours=100,
                weak_areas=["Error calculating readiness"],
                strong_areas=[],
                recommended_actions=["Please try again later"],
                confidence_level="low",
                predicted_pass_probability=0.0
            )
    
    def check_achievements(self, user_id: str) -> List[Achievement]:
        """
        Check for new achievements and milestones based on user progress.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of newly earned Achievement instances
        """
        try:
            new_achievements = []
            
            # Get user progress and activity summary
            user_progress = self.get_user_progress(user_id)
            activity_summary = self.get_user_activity_summary(user_id, days=365)  # Full year
            
            if not user_progress:
                return new_achievements
            
            # Check streak achievements
            current_streak = activity_summary.get('study_streak_days', 0)
            streak_milestones = [3, 7, 14, 30, 60, 100]
            
            for milestone in streak_milestones:
                if current_streak >= milestone:
                    achievement_id = f"{user_id}_streak_{milestone}"
                    # Check if already earned (in a real implementation, this would query the database)
                    achievement = Achievement(
                        achievement_id=achievement_id,
                        user_id=user_id,
                        achievement_type="streak",
                        title=f"{milestone}-Day Study Streak",
                        description=f"Studied for {milestone} consecutive days",
                        criteria={"streak_days": milestone},
                        badge_icon="🔥",
                        points=milestone * 10
                    )
                    new_achievements.append(achievement)
            
            # Check score achievements
            scores = [p.score for p in user_progress if p.score is not None]
            if scores:
                avg_score = sum(scores) / len(scores)
                
                score_milestones = [
                    (70, "Good Student", "Maintained 70% average score", "📚", 100),
                    (80, "Great Student", "Maintained 80% average score", "🎓", 200),
                    (90, "Excellent Student", "Maintained 90% average score", "🏆", 500),
                    (95, "Master Student", "Maintained 95% average score", "👑", 1000)
                ]
                
                for threshold, title, description, icon, points in score_milestones:
                    if avg_score >= threshold:
                        achievement_id = f"{user_id}_score_{threshold}"
                        achievement = Achievement(
                            achievement_id=achievement_id,
                            user_id=user_id,
                            achievement_type="score",
                            title=title,
                            description=description,
                            criteria={"min_avg_score": threshold},
                            badge_icon=icon,
                            points=points
                        )
                        new_achievements.append(achievement)
            
            # Check completion achievements
            completed_content = len([p for p in user_progress if p.progress_type == ProgressType.COMPLETED])
            completion_milestones = [
                (10, "Getting Started", "Completed 10 pieces of content", "🌱", 50),
                (50, "Making Progress", "Completed 50 pieces of content", "🚀", 250),
                (100, "Dedicated Learner", "Completed 100 pieces of content", "💪", 500),
                (250, "Content Master", "Completed 250 pieces of content", "🎯", 1000)
            ]
            
            for threshold, title, description, icon, points in completion_milestones:
                if completed_content >= threshold:
                    achievement_id = f"{user_id}_completion_{threshold}"
                    achievement = Achievement(
                        achievement_id=achievement_id,
                        user_id=user_id,
                        achievement_type="completion",
                        title=title,
                        description=description,
                        criteria={"min_completed": threshold},
                        badge_icon=icon,
                        points=points
                    )
                    new_achievements.append(achievement)
            
            # Check time-based achievements
            total_time_hours = sum(p.time_spent for p in user_progress) / 3600  # Convert to hours
            time_milestones = [
                (10, "Time Invested", "Studied for 10 hours total", "⏰", 100),
                (50, "Serious Student", "Studied for 50 hours total", "📖", 300),
                (100, "Dedicated Scholar", "Studied for 100 hours total", "🎓", 600),
                (200, "Study Champion", "Studied for 200 hours total", "🏆", 1200)
            ]
            
            for threshold, title, description, icon, points in time_milestones:
                if total_time_hours >= threshold:
                    achievement_id = f"{user_id}_time_{threshold}"
                    achievement = Achievement(
                        achievement_id=achievement_id,
                        user_id=user_id,
                        achievement_type="time",
                        title=title,
                        description=description,
                        criteria={"min_hours": threshold},
                        badge_icon=icon,
                        points=points
                    )
                    new_achievements.append(achievement)
            
            logger.info(f"Found {len(new_achievements)} potential achievements for user {user_id}")
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")
            return []
    
    def get_user_achievements(self, user_id: str, certification_type: Optional[CertificationType] = None) -> List[Achievement]:
        """
        Get all achievements earned by a user.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            
        Returns:
            List of Achievement instances
        """
        try:
            # In a real implementation, this would query a dedicated achievements table
            # For now, we'll return the achievements that would be earned based on current progress
            return self.check_achievements(user_id)
            
        except Exception as e:
            logger.error(f"Error retrieving user achievements: {str(e)}")
            return []
    
    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data aggregation for progress visualization.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with dashboard data including progress, trends, achievements
        """
        try:
            # Get basic analytics
            overall_analytics = self.get_performance_analytics(user_id)
            activity_summary = self.get_user_activity_summary(user_id, days=30)
            
            # Get certification-specific data
            certification_data = {}
            for cert_type in CertificationType:
                if cert_type == CertificationType.GENERAL:
                    continue
                
                cert_analytics = self.get_performance_analytics(user_id, cert_type)
                cert_readiness = self.calculate_certification_readiness(user_id, cert_type)
                
                certification_data[cert_type.value] = {
                    'analytics': {
                        'completion_rate': cert_analytics.completion_rate,
                        'average_score': cert_analytics.average_score,
                        'total_time': cert_analytics.time_spent_total,
                        'content_viewed': cert_analytics.total_content_viewed,
                        'questions_answered': cert_analytics.total_questions_answered
                    },
                    'readiness': {
                        'score': cert_readiness.readiness_score,
                        'confidence': cert_readiness.confidence_level,
                        'estimated_hours': cert_readiness.estimated_study_time_hours,
                        'weak_areas': cert_readiness.weak_areas,
                        'strong_areas': cert_readiness.strong_areas,
                        'pass_probability': cert_readiness.predicted_pass_probability
                    }
                }
            
            # Get recent trends
            trends = self.get_performance_trends(user_id, days=30)
            trend_data = []
            for trend in trends:
                trend_data.append({
                    'date': trend.date.isoformat(),
                    'metrics': trend.metrics,
                    'category_breakdown': trend.category_breakdown
                })
            
            # Get achievements
            achievements = self.get_user_achievements(user_id)
            achievement_data = []
            for achievement in achievements:
                achievement_data.append({
                    'title': achievement.title,
                    'description': achievement.description,
                    'type': achievement.achievement_type,
                    'badge_icon': achievement.badge_icon,
                    'points': achievement.points,
                    'earned_at': achievement.earned_at.isoformat()
                })
            
            dashboard_data = {
                'user_id': user_id,
                'generated_at': datetime.utcnow().isoformat(),
                'overall_analytics': {
                    'completion_rate': overall_analytics.completion_rate,
                    'average_score': overall_analytics.average_score,
                    'total_time_hours': overall_analytics.time_spent_total / 3600,
                    'content_viewed': overall_analytics.total_content_viewed,
                    'questions_answered': overall_analytics.total_questions_answered
                },
                'activity_summary': activity_summary,
                'certification_progress': certification_data,
                'performance_trends': trend_data,
                'achievements': achievement_data,
                'study_streak': activity_summary.get('study_streak_days', 0),
                'total_points': sum(a.points for a in achievements),
                'recommendations': self._generate_dashboard_recommendations(user_id, certification_data)
            }
            
            logger.info(f"Generated comprehensive dashboard data for user {user_id}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return {
                'user_id': user_id,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _get_certification_level(self, certification_type: CertificationType) -> str:
        """Get the certification level (foundational, associate, professional, specialty)."""
        foundational = [CertificationType.CCP, CertificationType.AIP]
        associate = [CertificationType.SAA, CertificationType.DVA, CertificationType.SOA, 
                    CertificationType.DEA, CertificationType.MLA]
        professional = [CertificationType.SAP, CertificationType.DOP]
        specialty = [CertificationType.SCS, CertificationType.ANS, CertificationType.MLS]
        
        if certification_type in foundational:
            return "foundational"
        elif certification_type in associate:
            return "associate"
        elif certification_type in professional:
            return "professional"
        elif certification_type in specialty:
            return "specialty"
        else:
            return "general"
    
    def _generate_dashboard_recommendations(self, user_id: str, certification_data: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations for the dashboard."""
        recommendations = []
        
        try:
            # Find the certification with highest readiness score
            best_cert = None
            best_score = 0
            
            for cert_code, data in certification_data.items():
                readiness_score = data['readiness']['score']
                if readiness_score > best_score:
                    best_score = readiness_score
                    best_cert = cert_code
            
            if best_cert and best_score > 70:
                recommendations.append(f"You're doing great with {best_cert}! Consider taking a practice exam.")
            elif best_cert and best_score > 40:
                recommendations.append(f"Focus on {best_cert} - you're making good progress.")
            else:
                recommendations.append("Start with foundational topics to build your knowledge base.")
            
            # Check for weak areas across certifications
            all_weak_areas = set()
            for cert_code, data in certification_data.items():
                all_weak_areas.update(data['readiness']['weak_areas'])
            
            if all_weak_areas and 'All areas need attention' not in all_weak_areas:
                most_common_weak = list(all_weak_areas)[:2]  # Top 2 weak areas
                recommendations.append(f"Consider focusing on: {', '.join(most_common_weak)}")
            
            # Study streak recommendations
            activity_summary = self.get_user_activity_summary(user_id, days=7)
            streak = activity_summary.get('study_streak_days', 0)
            
            if streak == 0:
                recommendations.append("Start a study streak today! Even 15 minutes makes a difference.")
            elif streak < 7:
                recommendations.append(f"Great {streak}-day streak! Try to reach 7 days.")
            else:
                recommendations.append(f"Amazing {streak}-day streak! Keep up the momentum.")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            recommendations.append("Keep studying and practicing to improve your skills!")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
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