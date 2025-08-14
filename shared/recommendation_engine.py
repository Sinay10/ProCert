"""
Recommendation Engine implementation for the ProCert Learning Platform.

This module provides ML-based personalized study recommendations, weak area identification,
content difficulty progression, and study path generation based on user performance data.
"""

import os
import boto3
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from botocore.exceptions import ClientError
import math

# Try to import ML libraries, fallback to basic math if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from .models import (
    StudyRecommendation, UserProgress, ContentMetadata, CertificationType, 
    DifficultyLevel, ContentType, ProgressType, validate_model
)
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    ML-based recommendation engine for personalized study recommendations.
    
    This class analyzes user performance data to provide intelligent recommendations
    for study content, identify weak areas, and generate personalized study paths.
    """
    
    def __init__(self, 
                 user_progress_table_name: str,
                 content_metadata_table_name: str,
                 recommendations_table_name: str,
                 region_name: str = 'us-east-1'):
        """
        Initialize the RecommendationEngine.
        
        Args:
            user_progress_table_name: Name of the user progress DynamoDB table
            content_metadata_table_name: Name of the content metadata DynamoDB table
            recommendations_table_name: Name of the recommendations DynamoDB table
            region_name: AWS region name
        """
        self.user_progress_table_name = user_progress_table_name
        self.content_metadata_table_name = content_metadata_table_name
        self.recommendations_table_name = recommendations_table_name
        self.region_name = region_name
        
        # Initialize DynamoDB client and resources
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.user_progress_table = self.dynamodb.Table(user_progress_table_name)
        self.content_metadata_table = self.dynamodb.Table(content_metadata_table_name)
        self.recommendations_table = self.dynamodb.Table(recommendations_table_name)
        
        # Initialize progress tracker for data access
        self.progress_tracker = ProgressTracker(
            user_progress_table_name=user_progress_table_name,
            content_metadata_table_name=content_metadata_table_name,
            region_name=region_name
        )
        
        logger.info(f"RecommendationEngine initialized with tables: {user_progress_table_name}, {content_metadata_table_name}, {recommendations_table_name}")
    
    def get_personalized_recommendations(self, user_id: str, 
                                       certification_type: Optional[CertificationType] = None,
                                       limit: int = 10) -> List[StudyRecommendation]:
        """
        Get personalized study recommendations for a user.
        
        Args:
            user_id: User identifier
            certification_type: Optional certification type filter
            limit: Maximum number of recommendations to return
            
        Returns:
            List of StudyRecommendation instances
        """
        try:
            # Get user progress data
            user_progress = self.progress_tracker.get_user_progress(user_id, certification_type)
            
            if not user_progress:
                # New user - provide foundational recommendations
                return self._generate_foundational_recommendations(user_id, certification_type, limit)
            
            # Analyze user performance
            performance_analysis = self._analyze_user_performance(user_progress, certification_type)
            
            # Generate recommendations based on analysis
            recommendations = []
            
            # 1. Weak area recommendations (high priority)
            weak_area_recs = self._generate_weak_area_recommendations(
                user_id, performance_analysis, certification_type, limit // 2
            )
            recommendations.extend(weak_area_recs)
            
            # 2. Progression recommendations (medium priority)
            if len(recommendations) < limit:
                progression_recs = self._generate_progression_recommendations(
                    user_id, performance_analysis, certification_type, limit - len(recommendations)
            )
            recommendations.extend(progression_recs)
            
            # 3. Review recommendations (lower priority)
            if len(recommendations) < limit:
                review_recs = self._generate_review_recommendations(
                    user_id, performance_analysis, certification_type, limit - len(recommendations)
                )
                recommendations.extend(review_recs)
            
            # Apply advanced ML-based scoring if available
            recommendations = self._advanced_recommendation_scoring(recommendations, performance_analysis)
            
            # Limit results
            recommendations = recommendations[:limit]
            
            # Store recommendations in database
            self._store_recommendations(recommendations)
            
            logger.info(f"Generated {len(recommendations)} personalized recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return []
    
    def identify_weak_areas(self, user_id: str, 
                          certification_type: Optional[CertificationType] = None) -> Dict[str, Any]:
        """
        Identify weak areas from user performance data.
        
        Args:
            user_id: User identifier
            certification_type: Optional certification type filter
            
        Returns:
            Dictionary with weak areas analysis
        """
        try:
            # Get user progress data
            user_progress = self.progress_tracker.get_user_progress(user_id, certification_type)
            
            if not user_progress:
                return {
                    'weak_areas': [],
                    'analysis': 'Insufficient data for analysis',
                    'recommendations': ['Start with foundational topics', 'Take diagnostic quizzes']
                }
            
            # Analyze performance by category and difficulty
            category_performance = defaultdict(lambda: {'scores': [], 'attempts': 0, 'avg_score': 0.0})
            difficulty_performance = defaultdict(lambda: {'scores': [], 'attempts': 0, 'avg_score': 0.0})
            
            for progress in user_progress:
                if progress.score is not None:
                    # Get content metadata
                    content = self._get_content_metadata(progress.content_id)
                    if content:
                        # Category analysis
                        cat_perf = category_performance[content.category]
                        cat_perf['scores'].append(progress.score)
                        cat_perf['attempts'] += 1
                        
                        # Difficulty analysis
                        diff_perf = difficulty_performance[content.difficulty_level.value]
                        diff_perf['scores'].append(progress.score)
                        diff_perf['attempts'] += 1
            
            # Calculate averages and identify weak areas
            weak_categories = []
            weak_difficulties = []
            
            for category, perf in category_performance.items():
                if perf['scores']:
                    avg_score = sum(perf['scores']) / len(perf['scores'])
                    perf['avg_score'] = avg_score
                    
                    # Consider weak if average score < 70% and sufficient attempts
                    if avg_score < 70.0 and perf['attempts'] >= 3:
                        weak_categories.append({
                            'category': category,
                            'avg_score': avg_score,
                            'attempts': perf['attempts'],
                            'severity': 'high' if avg_score < 50 else 'medium'
                        })
            
            for difficulty, perf in difficulty_performance.items():
                if perf['scores']:
                    avg_score = sum(perf['scores']) / len(perf['scores'])
                    perf['avg_score'] = avg_score
                    
                    if avg_score < 70.0 and perf['attempts'] >= 3:
                        weak_difficulties.append({
                            'difficulty': difficulty,
                            'avg_score': avg_score,
                            'attempts': perf['attempts'],
                            'severity': 'high' if avg_score < 50 else 'medium'
                        })
            
            # Generate recommendations
            recommendations = []
            for weak_cat in weak_categories:
                recommendations.append(f"Focus on {weak_cat['category']} topics")
                recommendations.append(f"Practice more {weak_cat['category']} questions")
            
            for weak_diff in weak_difficulties:
                if weak_diff['difficulty'] == 'beginner':
                    recommendations.append("Review fundamental concepts")
                elif weak_diff['difficulty'] == 'intermediate':
                    recommendations.append("Practice intermediate-level problems")
                else:
                    recommendations.append("Study advanced topics with guided examples")
            
            return {
                'weak_categories': weak_categories,
                'weak_difficulties': weak_difficulties,
                'category_performance': dict(category_performance),
                'difficulty_performance': dict(difficulty_performance),
                'recommendations': recommendations[:10],  # Limit recommendations
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error identifying weak areas: {str(e)}")
            return {
                'weak_areas': [],
                'analysis': f'Error during analysis: {str(e)}',
                'recommendations': []
            }
    
    def get_content_difficulty_progression(self, user_id: str,
                                         certification_type: Optional[CertificationType] = None) -> Dict[str, Any]:
        """
        Get content difficulty progression recommendations.
        
        Args:
            user_id: User identifier
            certification_type: Optional certification type filter
            
        Returns:
            Dictionary with progression recommendations
        """
        try:
            # Get user progress data
            user_progress = self.progress_tracker.get_user_progress(user_id, certification_type)
            
            if not user_progress:
                return {
                    'current_level': 'beginner',
                    'recommended_level': 'beginner',
                    'progression_path': ['Start with beginner content', 'Build foundational knowledge'],
                    'readiness_score': 0.0
                }
            
            # Analyze performance by difficulty level
            difficulty_scores = defaultdict(list)
            
            for progress in user_progress:
                if progress.score is not None:
                    content = self._get_content_metadata(progress.content_id)
                    if content:
                        difficulty_scores[content.difficulty_level.value].append(progress.score)
            
            # Calculate readiness for each level
            level_readiness = {}
            for level in ['beginner', 'intermediate', 'advanced']:
                if level in difficulty_scores:
                    scores = difficulty_scores[level]
                    avg_score = sum(scores) / len(scores)
                    # Calculate consistency score
                    consistency = self._calculate_consistency(scores)
                    readiness = (avg_score / 100.0) * consistency
                    level_readiness[level] = {
                        'avg_score': avg_score,
                        'attempts': len(scores),
                        'consistency': consistency,
                        'readiness': readiness
                    }
                else:
                    level_readiness[level] = {
                        'avg_score': 0.0,
                        'attempts': 0,
                        'consistency': 0.0,
                        'readiness': 0.0
                    }
            
            # Determine current and recommended levels
            current_level = 'beginner'
            if level_readiness['intermediate']['readiness'] > 0.7:
                current_level = 'intermediate'
            if level_readiness['advanced']['readiness'] > 0.7:
                current_level = 'advanced'
            
            # Recommend next level
            recommended_level = current_level
            if current_level == 'beginner' and level_readiness['beginner']['readiness'] > 0.8:
                recommended_level = 'intermediate'
            elif current_level == 'intermediate' and level_readiness['intermediate']['readiness'] > 0.8:
                recommended_level = 'advanced'
            
            # Generate progression path
            progression_path = []
            if recommended_level != current_level:
                progression_path.append(f"Ready to advance from {current_level} to {recommended_level}")
                progression_path.append(f"Start with easier {recommended_level} content")
                progression_path.append(f"Gradually increase {recommended_level} difficulty")
            else:
                progression_path.append(f"Continue practicing {current_level} level content")
                progression_path.append(f"Focus on consistency in {current_level} topics")
                if level_readiness[current_level]['readiness'] < 0.7:
                    progression_path.append("Review fundamental concepts")
            
            return {
                'current_level': current_level,
                'recommended_level': recommended_level,
                'level_readiness': level_readiness,
                'progression_path': progression_path,
                'overall_readiness': level_readiness[current_level]['readiness'],
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting content progression: {str(e)}")
            return {
                'current_level': 'beginner',
                'recommended_level': 'beginner',
                'progression_path': [f'Error during analysis: {str(e)}'],
                'readiness_score': 0.0
            }
    
    def generate_study_path(self, user_id: str, certification_type: CertificationType) -> Dict[str, Any]:
        """
        Generate personalized study path based on certification goals.
        
        Args:
            user_id: User identifier
            certification_type: Target certification type
            
        Returns:
            Dictionary with personalized study path
        """
        try:
            # Get user progress and weak areas
            user_progress = self.progress_tracker.get_user_progress(user_id, certification_type)
            weak_areas = self.identify_weak_areas(user_id, certification_type)
            progression = self.get_content_difficulty_progression(user_id, certification_type)
            
            # Get available content for certification
            available_content = self._get_content_by_certification(certification_type)
            
            # Generate study path phases
            study_phases = []
            
            # Phase 1: Address weak areas
            if weak_areas['weak_categories']:
                weak_phase = {
                    'phase': 1,
                    'title': 'Address Weak Areas',
                    'description': 'Focus on areas where performance is below average',
                    'estimated_time_hours': len(weak_areas['weak_categories']) * 4,
                    'topics': [cat['category'] for cat in weak_areas['weak_categories']],
                    'priority': 'high',
                    'content_suggestions': []
                }
                
                # Find content for weak categories
                for weak_cat in weak_areas['weak_categories']:
                    category_content = [c for c in available_content if c.category == weak_cat['category']]
                    weak_phase['content_suggestions'].extend([
                        {
                            'content_id': c.content_id,
                            'title': c.title,
                            'difficulty': c.difficulty_level.value,
                            'type': c.content_type.value
                        }
                        for c in category_content[:3]  # Limit to 3 per category
                    ])
                
                study_phases.append(weak_phase)
            
            # Phase 2: Skill building based on current level
            current_level = progression['current_level']
            skill_phase = {
                'phase': 2,
                'title': f'Build {current_level.title()} Skills',
                'description': f'Strengthen {current_level} level understanding',
                'estimated_time_hours': 8,
                'topics': self._get_core_topics_for_certification(certification_type),
                'priority': 'medium',
                'content_suggestions': []
            }
            
            # Find content at current level
            level_content = [
                c for c in available_content 
                if c.difficulty_level.value == current_level
            ]
            skill_phase['content_suggestions'] = [
                {
                    'content_id': c.content_id,
                    'title': c.title,
                    'difficulty': c.difficulty_level.value,
                    'type': c.content_type.value
                }
                for c in level_content[:5]
            ]
            
            study_phases.append(skill_phase)
            
            # Phase 3: Advanced preparation (if ready)
            if progression['recommended_level'] != current_level:
                advanced_phase = {
                    'phase': 3,
                    'title': f'Advance to {progression["recommended_level"].title()}',
                    'description': f'Progress to {progression["recommended_level"]} level content',
                    'estimated_time_hours': 12,
                    'topics': self._get_advanced_topics_for_certification(certification_type),
                    'priority': 'low',
                    'content_suggestions': []
                }
                
                # Find advanced content
                advanced_content = [
                    c for c in available_content 
                    if c.difficulty_level.value == progression['recommended_level']
                ]
                advanced_phase['content_suggestions'] = [
                    {
                        'content_id': c.content_id,
                        'title': c.title,
                        'difficulty': c.difficulty_level.value,
                        'type': c.content_type.value
                    }
                    for c in advanced_content[:5]
                ]
                
                study_phases.append(advanced_phase)
            
            # Calculate total estimated time
            total_time = sum(phase['estimated_time_hours'] for phase in study_phases)
            
            # Generate milestones
            milestones = []
            completed_time = 0
            for phase in study_phases:
                completed_time += phase['estimated_time_hours']
                milestones.append({
                    'milestone': f"Complete {phase['title']}",
                    'estimated_completion_hours': completed_time,
                    'description': phase['description']
                })
            
            return {
                'user_id': user_id,
                'certification_type': certification_type.value,
                'study_phases': study_phases,
                'total_estimated_hours': total_time,
                'milestones': milestones,
                'current_progress': {
                    'completed_phases': 0,
                    'current_phase': 1,
                    'overall_progress_percent': 0.0
                },
                'generated_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating study path: {str(e)}")
            return {
                'user_id': user_id,
                'certification_type': certification_type.value,
                'study_phases': [],
                'error': str(e)
            }
    
    def record_recommendation_feedback(self, user_id: str, recommendation_id: str, 
                                     action: str, feedback_data: Dict[str, Any] = None) -> bool:
        """
        Record user feedback on recommendations for continuous improvement.
        
        Args:
            user_id: User identifier
            recommendation_id: Recommendation identifier
            action: User action ('accepted', 'rejected', 'completed', 'skipped')
            feedback_data: Optional additional feedback data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update recommendation with feedback
            update_expression = "SET feedback_action = :action, feedback_timestamp = :timestamp"
            expression_values = {
                ':action': action,
                ':timestamp': datetime.utcnow().isoformat()
            }
            
            if feedback_data:
                update_expression += ", feedback_data = :feedback_data"
                expression_values[':feedback_data'] = feedback_data
            
            if action == 'completed':
                update_expression += ", is_completed = :completed"
                expression_values[':completed'] = True
            
            response = self.recommendations_table.update_item(
                Key={
                    'user_id': user_id,
                    'recommendation_id': recommendation_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Recorded feedback for recommendation {recommendation_id}: {action}")
            return True
            
        except ClientError as e:
            logger.error(f"Error recording recommendation feedback: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error recording feedback: {str(e)}")
            return False
    
    # Helper methods
    
    def _analyze_user_performance(self, user_progress: List[UserProgress], 
                                certification_type: Optional[CertificationType]) -> Dict[str, Any]:
        """Analyze user performance patterns."""
        analysis = {
            'total_interactions': len(user_progress),
            'avg_score': 0.0,
            'category_performance': defaultdict(list),
            'difficulty_performance': defaultdict(list),
            'recent_activity': [],
            'learning_velocity': 0.0
        }
        
        scores = []
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        
        for progress in user_progress:
            if progress.score is not None:
                scores.append(progress.score)
                
                # Get content metadata for categorization
                content = self._get_content_metadata(progress.content_id)
                if content:
                    analysis['category_performance'][content.category].append(progress.score)
                    analysis['difficulty_performance'][content.difficulty_level.value].append(progress.score)
            
            # Track recent activity
            if progress.timestamp >= recent_cutoff:
                analysis['recent_activity'].append(progress)
        
        # Calculate averages
        if scores:
            analysis['avg_score'] = sum(scores) / len(scores)
        
        # Calculate learning velocity (interactions per day over last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_interactions = [p for p in user_progress if p.timestamp >= thirty_days_ago]
        analysis['learning_velocity'] = len(recent_interactions) / 30.0
        
        return analysis
    
    def _generate_foundational_recommendations(self, user_id: str, 
                                             certification_type: Optional[CertificationType],
                                             limit: int) -> List[StudyRecommendation]:
        """Generate foundational recommendations for new users."""
        recommendations = []
        
        # Get beginner content
        beginner_content = self._get_content_by_difficulty(DifficultyLevel.BEGINNER, certification_type)
        
        for i, content in enumerate(beginner_content[:limit]):
            rec = StudyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                type='content',
                priority=9 - i,  # Decreasing priority
                content_id=content.content_id,
                certification_type=certification_type.value if certification_type else None,
                category=content.category,
                reasoning=f"Start with foundational {content.category} concepts",
                estimated_time_minutes=30,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_weak_area_recommendations(self, user_id: str, performance_analysis: Dict[str, Any],
                                          certification_type: Optional[CertificationType],
                                          limit: int) -> List[StudyRecommendation]:
        """Generate recommendations for weak areas."""
        recommendations = []
        
        # Find categories with low performance
        weak_categories = []
        for category, scores in performance_analysis['category_performance'].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score < 70.0:  # Consider weak if below 70%
                    weak_categories.append((category, avg_score))
        
        # Sort by lowest score first
        weak_categories.sort(key=lambda x: x[1])
        
        for i, (category, avg_score) in enumerate(weak_categories[:limit]):
            # Find content for this weak category
            category_content = self._get_content_by_category(category, certification_type)
            
            if category_content:
                content = category_content[0]  # Take first available content
                
                rec = StudyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type='review',
                    priority=8 - i,  # High priority for weak areas
                    content_id=content.content_id,
                    certification_type=certification_type.value if certification_type else None,
                    category=category,
                    reasoning=f"Review {category} - current average: {avg_score:.1f}%",
                    estimated_time_minutes=45,
                    expires_at=datetime.utcnow() + timedelta(days=3)
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_progression_recommendations(self, user_id: str, performance_analysis: Dict[str, Any],
                                            certification_type: Optional[CertificationType],
                                            limit: int) -> List[StudyRecommendation]:
        """Generate progression recommendations."""
        recommendations = []
        
        # Find areas where user is performing well and can advance
        strong_categories = []
        for category, scores in performance_analysis['category_performance'].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score >= 80.0:  # Consider strong if above 80%
                    strong_categories.append((category, avg_score))
        
        # Sort by highest score first
        strong_categories.sort(key=lambda x: x[1], reverse=True)
        
        for i, (category, avg_score) in enumerate(strong_categories[:limit]):
            # Find intermediate/advanced content for this category
            category_content = self._get_content_by_category(category, certification_type)
            intermediate_content = [c for c in category_content if c.difficulty_level == DifficultyLevel.INTERMEDIATE]
            
            if intermediate_content:
                content = intermediate_content[0]
                
                rec = StudyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type='content',
                    priority=6 - i,  # Medium priority
                    content_id=content.content_id,
                    certification_type=certification_type.value if certification_type else None,
                    category=category,
                    reasoning=f"Advance in {category} - you're performing well ({avg_score:.1f}%)",
                    estimated_time_minutes=40,
                    expires_at=datetime.utcnow() + timedelta(days=5)
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_review_recommendations(self, user_id: str, performance_analysis: Dict[str, Any],
                                       certification_type: Optional[CertificationType],
                                       limit: int) -> List[StudyRecommendation]:
        """Generate review recommendations for reinforcement."""
        recommendations = []
        
        # Recommend quiz practice for categories with moderate performance
        moderate_categories = []
        for category, scores in performance_analysis['category_performance'].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if 70.0 <= avg_score < 85.0:  # Moderate performance
                    moderate_categories.append((category, avg_score))
        
        for i, (category, avg_score) in enumerate(moderate_categories[:limit]):
            rec = StudyRecommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                type='quiz',
                priority=4 - i,  # Lower priority
                certification_type=certification_type.value if certification_type else None,
                category=category,
                reasoning=f"Practice {category} questions to reinforce knowledge",
                estimated_time_minutes=20,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _store_recommendations(self, recommendations: List[StudyRecommendation]) -> None:
        """Store recommendations in DynamoDB."""
        try:
            with self.recommendations_table.batch_writer() as batch:
                for rec in recommendations:
                    # Convert to DynamoDB format
                    item = rec.to_dict()
                    
                    # Convert datetime strings to ensure proper format
                    if item.get('expires_at'):
                        # Add TTL for automatic cleanup
                        expires_dt = datetime.fromisoformat(item['expires_at'])
                        item['ttl'] = int(expires_dt.timestamp())
                    
                    batch.put_item(Item=item)
            
            logger.info(f"Stored {len(recommendations)} recommendations in database")
            
        except Exception as e:
            logger.error(f"Error storing recommendations: {str(e)}")
    
    def _get_content_metadata(self, content_id: str) -> Optional[ContentMetadata]:
        """Get content metadata by ID."""
        return self.progress_tracker._get_content_metadata(content_id)
    
    def _get_content_by_difficulty(self, difficulty: DifficultyLevel, 
                                 certification_type: Optional[CertificationType]) -> List[ContentMetadata]:
        """Get content by difficulty level."""
        try:
            if certification_type:
                response = self.content_metadata_table.query(
                    IndexName='CertificationTypeIndex',
                    KeyConditionExpression='certification_type = :cert_type',
                    FilterExpression='difficulty_level = :difficulty',
                    ExpressionAttributeValues={
                        ':cert_type': certification_type.value,
                        ':difficulty': difficulty.value
                    }
                )
            else:
                response = self.content_metadata_table.scan(
                    FilterExpression='difficulty_level = :difficulty',
                    ExpressionAttributeValues={':difficulty': difficulty.value}
                )
            
            content_list = []
            for item in response['Items']:
                try:
                    content = ContentMetadata.from_dict(item)
                    content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {str(e)}")
                    continue
            
            return content_list
            
        except Exception as e:
            logger.error(f"Error retrieving content by difficulty: {str(e)}")
            return []
    
    def _get_content_by_category(self, category: str, 
                               certification_type: Optional[CertificationType]) -> List[ContentMetadata]:
        """Get content by category."""
        return self.progress_tracker._get_content_by_category(category, certification_type)
    
    def _get_content_by_certification(self, certification_type: CertificationType) -> List[ContentMetadata]:
        """Get all content for a certification type."""
        try:
            response = self.content_metadata_table.query(
                IndexName='CertificationTypeIndex',
                KeyConditionExpression='certification_type = :cert_type',
                ExpressionAttributeValues={':cert_type': certification_type.value}
            )
            
            content_list = []
            for item in response['Items']:
                try:
                    content = ContentMetadata.from_dict(item)
                    content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {str(e)}")
                    continue
            
            return content_list
            
        except Exception as e:
            logger.error(f"Error retrieving content by certification: {str(e)}")
            return []
    
    def _get_core_topics_for_certification(self, certification_type: CertificationType) -> List[str]:
        """Get core topics for a certification type."""
        # This could be enhanced with a more sophisticated topic mapping
        core_topics_map = {
            CertificationType.SAA: ['EC2', 'S3', 'VPC', 'IAM', 'RDS', 'Lambda'],
            CertificationType.DVA: ['Lambda', 'API Gateway', 'DynamoDB', 'S3', 'CloudFormation', 'CodePipeline'],
            CertificationType.SOA: ['CloudWatch', 'Systems Manager', 'EC2', 'Auto Scaling', 'ELB', 'CloudFormation'],
            CertificationType.CCP: ['Cloud Concepts', 'Security', 'Technology', 'Billing and Pricing']
        }
        
        return core_topics_map.get(certification_type, ['General AWS Topics'])
    
    def _get_advanced_topics_for_certification(self, certification_type: CertificationType) -> List[str]:
        """Get advanced topics for a certification type."""
        advanced_topics_map = {
            CertificationType.SAA: ['Advanced Networking', 'Hybrid Architecture', 'Cost Optimization', 'Security Best Practices'],
            CertificationType.DVA: ['Advanced Lambda', 'Microservices', 'CI/CD Best Practices', 'Performance Optimization'],
            CertificationType.SOA: ['Advanced Monitoring', 'Automation', 'Disaster Recovery', 'Performance Tuning'],
            CertificationType.CCP: ['Advanced Cloud Concepts', 'Compliance', 'Advanced Security', 'Cost Management']
        }
        
        return advanced_topics_map.get(certification_type, ['Advanced AWS Topics'])
    
    def _calculate_consistency(self, scores: List[float]) -> float:
        """Calculate consistency score using available math libraries."""
        if len(scores) <= 1:
            return 1.0
        
        if HAS_NUMPY:
            # Use NumPy for more accurate calculations
            scores_array = np.array(scores)
            std_dev = np.std(scores_array)
            return max(0.0, 1.0 - (std_dev / 100.0))
        else:
            # Fallback to manual calculation
            mean = sum(scores) / len(scores)
            variance = sum((x - mean) ** 2 for x in scores) / len(scores)
            std_dev = math.sqrt(variance)
            return max(0.0, 1.0 - (std_dev / 100.0))
    
    def _calculate_performance_similarity(self, user_performance: Dict[str, Any], 
                                        other_performance: Dict[str, Any]) -> float:
        """Calculate similarity between user performance patterns."""
        if HAS_SKLEARN and HAS_NUMPY:
            # Use advanced ML similarity calculation
            return self._ml_performance_similarity(user_performance, other_performance)
        else:
            # Use simple correlation-based similarity
            return self._simple_performance_similarity(user_performance, other_performance)
    
    def _ml_performance_similarity(self, user_perf: Dict[str, Any], 
                                 other_perf: Dict[str, Any]) -> float:
        """Advanced ML-based performance similarity using scikit-learn."""
        try:
            # Get common categories
            common_categories = set(user_perf.keys()) & set(other_perf.keys())
            if len(common_categories) < 2:
                return 0.0
            
            # Create feature vectors
            user_vector = [user_perf[cat]['avg_score'] for cat in common_categories]
            other_vector = [other_perf[cat]['avg_score'] for cat in common_categories]
            
            # Calculate cosine similarity
            user_array = np.array(user_vector).reshape(1, -1)
            other_array = np.array(other_vector).reshape(1, -1)
            
            similarity = cosine_similarity(user_array, other_array)[0][0]
            return max(0.0, similarity)
            
        except Exception as e:
            logger.warning(f"ML similarity calculation failed, using fallback: {str(e)}")
            return self._simple_performance_similarity(user_perf, other_perf)
    
    def _simple_performance_similarity(self, user_perf: Dict[str, Any], 
                                     other_perf: Dict[str, Any]) -> float:
        """Simple correlation-based performance similarity."""
        try:
            # Get common categories
            common_categories = set(user_perf.keys()) & set(other_perf.keys())
            if len(common_categories) < 2:
                return 0.0
            
            # Calculate Pearson correlation coefficient manually
            user_scores = [user_perf[cat]['avg_score'] for cat in common_categories]
            other_scores = [other_perf[cat]['avg_score'] for cat in common_categories]
            
            n = len(user_scores)
            sum_user = sum(user_scores)
            sum_other = sum(other_scores)
            sum_user_sq = sum(x * x for x in user_scores)
            sum_other_sq = sum(x * x for x in other_scores)
            sum_products = sum(user_scores[i] * other_scores[i] for i in range(n))
            
            numerator = n * sum_products - sum_user * sum_other
            denominator = math.sqrt((n * sum_user_sq - sum_user * sum_user) * 
                                  (n * sum_other_sq - sum_other * sum_other))
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            return max(0.0, correlation)
            
        except Exception as e:
            logger.warning(f"Simple similarity calculation failed: {str(e)}")
            return 0.0
    
    def _advanced_recommendation_scoring(self, recommendations: List[StudyRecommendation],
                                       user_performance: Dict[str, Any]) -> List[StudyRecommendation]:
        """Apply advanced ML-based scoring if libraries are available."""
        if not HAS_SKLEARN or not HAS_NUMPY:
            # Return recommendations with basic priority scoring
            return recommendations
        
        try:
            # Advanced feature engineering for recommendation scoring
            for rec in recommendations:
                # Calculate advanced priority score based on multiple factors
                base_priority = rec.priority
                
                # Factor 1: Performance gap severity
                if rec.category and rec.category in user_performance:
                    perf_data = user_performance[rec.category]
                    avg_score = perf_data.get('avg_score', 50.0)
                    gap_severity = max(0, (70.0 - avg_score) / 70.0)  # Normalized gap
                    
                    # Factor 2: Learning velocity in this category
                    attempts = perf_data.get('attempts', 1)
                    velocity_factor = min(1.0, attempts / 10.0)  # More attempts = higher velocity
                    
                    # Factor 3: Consistency factor
                    scores = perf_data.get('scores', [avg_score])
                    consistency = self._calculate_consistency(scores)
                    
                    # Combine factors using weighted scoring
                    advanced_score = (
                        base_priority * 0.4 +  # Base priority weight
                        gap_severity * 10 * 0.3 +  # Performance gap weight
                        (1 - velocity_factor) * 5 * 0.2 +  # Velocity weight (inverse)
                        (1 - consistency) * 3 * 0.1  # Consistency weight (inverse)
                    )
                    
                    rec.priority = min(10, max(1, int(advanced_score)))
            
            return sorted(recommendations, key=lambda x: x.priority, reverse=True)
            
        except Exception as e:
            logger.warning(f"Advanced scoring failed, using basic scoring: {str(e)}")
            return recommendations