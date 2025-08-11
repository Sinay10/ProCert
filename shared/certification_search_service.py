"""
Certification-aware search service for enhanced content discovery.

This module provides advanced search capabilities that leverage certification-specific
metadata and indices for improved relevance and filtering.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .interfaces import ISearchService, SearchResult
from .models import ContentMetadata, CertificationType
from .vector_storage_service import VectorStorageService
from .storage_manager import StorageManager


logger = logging.getLogger(__name__)


class CertificationSearchService(ISearchService):
    """
    Enhanced search service with certification-aware capabilities.
    
    This service provides:
    - Certification-scoped semantic search
    - Fallback to general content when certification-specific results are insufficient
    - Category and tag-based filtering within certification scope
    - Hybrid search combining vector similarity and metadata filtering
    """
    
    def __init__(self, vector_service: VectorStorageService, storage_manager: StorageManager):
        """
        Initialize the CertificationSearchService.
        
        Args:
            vector_service: VectorStorageService instance for semantic search
            storage_manager: StorageManager instance for metadata operations
        """
        self.vector_service = vector_service
        self.storage_manager = storage_manager
        
        logger.info("CertificationSearchService initialized")
    
    def semantic_search(self, query: str, certification_type: Optional[CertificationType] = None,
                       filters: Dict[str, Any] = None, limit: int = 10) -> List[SearchResult]:
        """
        Perform certification-aware semantic search using vector embeddings.
        
        Args:
            query: Search query text
            certification_type: Filter by certification type
            filters: Additional filters (category, difficulty_level, tags, etc.)
            limit: Maximum number of results
            
        Returns:
            List of SearchResult instances ranked by relevance
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Perform certification-scoped search
            results = []
            
            if certification_type:
                # Search within specific certification
                cert_results = self.vector_service.search_by_certification(
                    query_embedding=query_embedding,
                    certification_type=certification_type,
                    filters=filters,
                    limit=limit
                )
                results.extend(cert_results)
                
                # If insufficient results, fallback to general content
                if len(cert_results) < limit // 2:
                    general_results = self.vector_service.search_by_certification(
                        query_embedding=query_embedding,
                        certification_type=CertificationType.GENERAL,
                        filters=filters,
                        limit=limit - len(cert_results)
                    )
                    results.extend(general_results)
            else:
                # Search across all certifications
                all_results = self.vector_service.search_by_certification(
                    query_embedding=query_embedding,
                    certification_type=None,
                    filters=filters,
                    limit=limit
                )
                results.extend(all_results)
            
            # Convert to SearchResult objects and enhance with metadata
            search_results = self._convert_to_search_results(results, query)
            
            # Apply post-processing and ranking
            final_results = self._post_process_results(search_results, certification_type, filters)
            
            logger.info(f"Semantic search completed: {len(final_results)} results for query '{query[:50]}...'")
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_related_content(self, content_id: str, limit: int = 5) -> List[ContentMetadata]:
        """
        Get content related to a specific item using certification context.
        
        Args:
            content_id: Reference content ID
            limit: Maximum number of results
            
        Returns:
            List of related ContentMetadata instances
        """
        try:
            # Get the reference content metadata
            reference_content = self.storage_manager.retrieve_content_by_id(content_id)
            if not reference_content:
                logger.warning(f"Reference content not found: {content_id}")
                return []
            
            # Search for related content within the same certification
            filters = {
                'category': reference_content.category,
                'content_type': reference_content.content_type.value
            }
            
            # Exclude the reference content itself
            filters['exclude_content_id'] = content_id
            
            # Use the content title/category as search query
            search_query = f"{reference_content.title} {reference_content.category}"
            
            search_results = self.semantic_search(
                query=search_query,
                certification_type=reference_content.certification_type,
                filters=filters,
                limit=limit
            )
            
            # Convert search results to ContentMetadata
            related_content = []
            for result in search_results:
                content = self.storage_manager.retrieve_content_by_id(result.content_id)
                if content:
                    related_content.append(content)
            
            logger.info(f"Found {len(related_content)} related content items for {content_id}")
            return related_content
            
        except Exception as e:
            logger.error(f"Error getting related content: {e}")
            return []
    
    def search_by_category(self, category: str, certification_type: Optional[CertificationType] = None,
                          limit: int = 20) -> List[ContentMetadata]:
        """
        Search content by category with optional certification filtering.
        
        Args:
            category: Content category to search
            certification_type: Optional certification type filter
            limit: Maximum number of results
            
        Returns:
            List of ContentMetadata instances
        """
        try:
            if certification_type:
                # Use storage manager for direct category search within certification
                results = self.storage_manager.retrieve_content_by_category(
                    category=category,
                    certification_type=certification_type,
                    limit=limit
                )
            else:
                # Search across all certifications
                results = self.storage_manager.retrieve_content_by_category(
                    category=category,
                    certification_type=None,
                    limit=limit
                )
            
            logger.info(f"Category search completed: {len(results)} results for category '{category}'")
            return results
            
        except Exception as e:
            logger.error(f"Error in category search: {e}")
            return []
    
    def get_user_recommended_content(self, user_id: str, limit: int = 10) -> List[ContentMetadata]:
        """
        Get personalized content recommendations based on user progress.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of recommended ContentMetadata instances
        """
        try:
            # Get user progress to understand their certification focus and performance
            user_progress = self.storage_manager.get_user_progress(user_id)
            
            if not user_progress:
                # New user - recommend foundational content
                return self._get_foundational_recommendations(limit)
            
            # Analyze user progress to determine recommendations
            cert_focus = self._analyze_user_certification_focus(user_progress)
            weak_areas = self._identify_weak_areas(user_progress)
            
            recommendations = []
            
            # Recommend content for weak areas
            for area in weak_areas[:3]:  # Top 3 weak areas
                area_content = self.search_by_category(
                    category=area['category'],
                    certification_type=cert_focus,
                    limit=3
                )
                recommendations.extend(area_content)
            
            # Fill remaining slots with related content
            if len(recommendations) < limit:
                remaining = limit - len(recommendations)
                additional_content = self.storage_manager.retrieve_content_by_certification(
                    certification_type=cert_focus,
                    limit=remaining
                )
                recommendations.extend(additional_content)
            
            logger.info(f"Generated {len(recommendations)} personalized recommendations for user {user_id}")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating user recommendations: {e}")
            return []
    
    def get_certification_content_overview(self, certification_type: CertificationType) -> Dict[str, Any]:
        """
        Get an overview of available content for a specific certification.
        
        Args:
            certification_type: Certification type to analyze
            
        Returns:
            Dictionary with content statistics and categories
        """
        try:
            # Get all content for the certification
            all_content = self.storage_manager.retrieve_content_by_certification(
                certification_type=certification_type,
                limit=1000  # Large limit to get comprehensive view
            )
            
            # Analyze content distribution
            overview = {
                'certification_type': certification_type.value,
                'total_content_items': len(all_content),
                'content_types': {},
                'categories': {},
                'difficulty_levels': {},
                'recent_additions': []
            }
            
            # Categorize content
            for content in all_content:
                # Content types
                content_type = content.content_type.value
                overview['content_types'][content_type] = overview['content_types'].get(content_type, 0) + 1
                
                # Categories
                category = content.category
                overview['categories'][category] = overview['categories'].get(category, 0) + 1
                
                # Difficulty levels
                difficulty = content.difficulty_level.value
                overview['difficulty_levels'][difficulty] = overview['difficulty_levels'].get(difficulty, 0) + 1
            
            # Get recent additions (last 30 days)
            recent_cutoff = datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)  # 30 days ago
            overview['recent_additions'] = [
                content for content in all_content 
                if content.created_at.timestamp() > recent_cutoff
            ][:10]  # Limit to 10 most recent
            
            # Get vector storage statistics
            vector_stats = self.vector_service.get_certification_statistics()
            if certification_type.value in vector_stats:
                overview['vector_statistics'] = vector_stats[certification_type.value]
            
            logger.info(f"Generated content overview for {certification_type.value}")
            return overview
            
        except Exception as e:
            logger.error(f"Error generating certification overview: {e}")
            return {}
    
    # Private helper methods
    
    def _generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query."""
        try:
            import boto3
            import json
            
            bedrock_runtime = boto3.client('bedrock-runtime')
            
            body = json.dumps({"inputText": query})
            response = bedrock_runtime.invoke_model(
                body=body,
                modelId="amazon.titan-embed-text-v1",
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            return response_body.get("embedding")
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return None
    
    def _convert_to_search_results(self, raw_results: List[Dict[str, Any]], query: str) -> List[SearchResult]:
        """Convert raw search results to SearchResult objects."""
        search_results = []
        
        for result in raw_results:
            search_result = SearchResult(
                content_id=result['content_id'],
                title=result.get('metadata', {}).get('title', f"Content {result['content_id']}"),
                text=result['text'],
                score=result['score'],
                metadata={
                    'certification_type': result['certification_type'],
                    'certification_level': result.get('certification_level', ''),
                    'category': result.get('category', ''),
                    'difficulty_level': result.get('difficulty_level', ''),
                    'tags': result.get('tags', []),
                    'chunk_index': result.get('chunk_index', 0),
                    'source_index': result.get('index', '')
                }
            )
            search_results.append(search_result)
        
        return search_results
    
    def _post_process_results(self, results: List[SearchResult], 
                            certification_type: Optional[CertificationType],
                            filters: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """Apply post-processing and re-ranking to search results."""
        # Remove duplicates based on content_id
        seen_content = set()
        unique_results = []
        
        for result in results:
            if result.content_id not in seen_content:
                seen_content.add(result.content_id)
                unique_results.append(result)
        
        # Apply certification-specific boosting
        if certification_type:
            for result in unique_results:
                if result.metadata.get('certification_type') == certification_type.value:
                    result.score *= 1.2  # Boost exact certification matches
                elif result.metadata.get('certification_type') == 'GENERAL':
                    result.score *= 0.9  # Slight penalty for general content
        
        # Sort by adjusted score
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        return unique_results
    
    def _get_foundational_recommendations(self, limit: int) -> List[ContentMetadata]:
        """Get foundational content recommendations for new users."""
        foundational_certs = [CertificationType.CCP, CertificationType.AIP]
        recommendations = []
        
        for cert_type in foundational_certs:
            cert_content = self.storage_manager.retrieve_content_by_certification(
                certification_type=cert_type,
                limit=limit // len(foundational_certs)
            )
            recommendations.extend(cert_content)
        
        return recommendations[:limit]
    
    def _analyze_user_certification_focus(self, user_progress: List) -> Optional[CertificationType]:
        """Analyze user progress to determine their primary certification focus."""
        if not user_progress:
            return None
        
        # Count progress by certification type
        cert_counts = {}
        for progress in user_progress:
            # Extract certification from content_id or use a lookup
            # This would need to be implemented based on your progress tracking
            pass
        
        # Return the most common certification
        if cert_counts:
            most_common_cert = max(cert_counts, key=cert_counts.get)
            return CertificationType(most_common_cert)
        
        return None
    
    def _identify_weak_areas(self, user_progress: List) -> List[Dict[str, Any]]:
        """Identify areas where the user needs improvement."""
        # This would analyze user progress to identify categories with low scores
        # or areas where the user hasn't engaged much
        weak_areas = []
        
        # Placeholder implementation
        common_weak_areas = [
            {'category': 'Security', 'reason': 'Low average score'},
            {'category': 'Networking', 'reason': 'Limited engagement'},
            {'category': 'Storage', 'reason': 'Recent poor performance'}
        ]
        
        return common_weak_areas