"""
Unit tests for the CertificationSearchService with certification-aware capabilities.

This test suite covers:
- Certification-scoped search functionality
- Fallback to general content when certification-specific results are insufficient
- Category-based and tag-based search within certification scope
- Cross-certification content mixing prevention
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

import sys
import os

# Add shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared.certification_search_service import CertificationSearchService
from shared.interfaces import SearchResult
from shared.models import (
    ContentMetadata, CertificationType, ContentType, DifficultyLevel
)


class TestCertificationSearchService(unittest.TestCase):
    """Test cases for CertificationSearchService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_vector_service = Mock()
        self.mock_storage_manager = Mock()
        
        # Create service instance
        self.search_service = CertificationSearchService(
            vector_service=self.mock_vector_service,
            storage_manager=self.mock_storage_manager
        )
        
        # Test data
        self.sample_content_metadata = ContentMetadata(
            content_id="test-content-1",
            title="AWS SAA Security Best Practices",
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.SAA,
            category="Security",
            subcategory="IAM",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=["security", "iam", "best-practices"],
            source_file="saa-security.pdf",
            source_bucket="procert-materials-saa"
        )
        
        self.sample_search_results = [
            {
                'content_id': 'saa-content-1',
                'text': 'AWS IAM security best practices',
                'score': 0.95,
                'certification_type': 'SAA',
                'category': 'Security',
                'difficulty_level': 'intermediate',
                'tags': ['security', 'iam'],
                'metadata': {'title': 'IAM Security Guide'},
                'index': 'test-index-saa'
            },
            {
                'content_id': 'saa-content-2',
                'text': 'VPC security configurations',
                'score': 0.87,
                'certification_type': 'SAA',
                'category': 'Networking',
                'difficulty_level': 'advanced',
                'tags': ['vpc', 'security'],
                'metadata': {'title': 'VPC Security'},
                'index': 'test-index-saa'
            }
        ]
    
    @patch('shared.certification_search_service.logger')
    def test_initialization(self, mock_logger):
        """Test CertificationSearchService initialization."""
        service = CertificationSearchService(
            vector_service=self.mock_vector_service,
            storage_manager=self.mock_storage_manager
        )
        
        self.assertEqual(service.vector_service, self.mock_vector_service)
        self.assertEqual(service.storage_manager, self.mock_storage_manager)
        mock_logger.info.assert_called_with("CertificationSearchService initialized")
    
    @patch.object(CertificationSearchService, '_generate_query_embedding')
    @patch.object(CertificationSearchService, '_convert_to_search_results')
    @patch.object(CertificationSearchService, '_post_process_results')
    def test_semantic_search_with_certification_filter(self, mock_post_process, 
                                                      mock_convert, mock_embedding):
        """Test semantic search with certification-specific filtering."""
        # Setup mocks
        mock_embedding.return_value = [0.1] * 1536
        mock_convert.return_value = [
            SearchResult('content-1', 'Title 1', 'Text 1', 0.95, {'certification_type': 'SAA'})
        ]
        mock_post_process.return_value = [
            SearchResult('content-1', 'Title 1', 'Text 1', 0.95, {'certification_type': 'SAA'})
        ]
        
        # Return enough results to avoid fallback (limit // 2 = 5, so return 6 results)
        sufficient_results = self.sample_search_results * 3  # 6 results
        self.mock_vector_service.search_by_certification.return_value = sufficient_results
        
        # Execute search
        results = self.search_service.semantic_search(
            query="AWS security best practices",
            certification_type=CertificationType.SAA,
            filters={'category': 'Security'},
            limit=10
        )
        
        # Verify calls
        mock_embedding.assert_called_once_with("AWS security best practices")
        self.mock_vector_service.search_by_certification.assert_called_once_with(
            query_embedding=[0.1] * 1536,
            certification_type=CertificationType.SAA,
            filters={'category': 'Security'},
            limit=10
        )
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'content-1')
    
    @patch.object(CertificationSearchService, '_generate_query_embedding')
    @patch.object(CertificationSearchService, '_convert_to_search_results')
    @patch.object(CertificationSearchService, '_post_process_results')
    def test_semantic_search_fallback_to_general(self, mock_post_process, 
                                                mock_convert, mock_embedding):
        """Test fallback to general content when certification-specific results are insufficient."""
        # Setup mocks
        mock_embedding.return_value = [0.1] * 1536
        
        # Mock insufficient certification-specific results (less than limit // 2)
        cert_results = [self.sample_search_results[0]]  # Only 1 result
        general_results = [
            {
                'content_id': 'general-content-1',
                'text': 'General security principles',
                'score': 0.75,
                'certification_type': 'GENERAL',
                'category': 'Security',
                'difficulty_level': 'beginner',
                'tags': ['security', 'general'],
                'metadata': {'title': 'General Security'},
                'index': 'test-index'
            }
        ]
        
        # Configure mock to return different results for different calls
        self.mock_vector_service.search_by_certification.side_effect = [
            cert_results,  # First call for SAA-specific content
            general_results  # Second call for general content
        ]
        
        mock_convert.return_value = [
            SearchResult('content-1', 'Title 1', 'Text 1', 0.95, {'certification_type': 'SAA'}),
            SearchResult('general-1', 'General Title', 'General Text', 0.75, {'certification_type': 'GENERAL'})
        ]
        mock_post_process.return_value = [
            SearchResult('content-1', 'Title 1', 'Text 1', 0.95, {'certification_type': 'SAA'}),
            SearchResult('general-1', 'General Title', 'General Text', 0.75, {'certification_type': 'GENERAL'})
        ]
        
        # Execute search with limit of 10 (so limit // 2 = 5, and 1 result < 5)
        results = self.search_service.semantic_search(
            query="security practices",
            certification_type=CertificationType.SAA,
            limit=10
        )
        
        # Verify both calls were made
        self.assertEqual(self.mock_vector_service.search_by_certification.call_count, 2)
        
        # Verify first call for certification-specific content
        first_call = self.mock_vector_service.search_by_certification.call_args_list[0]
        self.assertEqual(first_call[1]['certification_type'], CertificationType.SAA)
        
        # Verify second call for general content
        second_call = self.mock_vector_service.search_by_certification.call_args_list[1]
        self.assertEqual(second_call[1]['certification_type'], CertificationType.GENERAL)
        self.assertEqual(second_call[1]['limit'], 9)  # 10 - 1 existing result
        
        # Verify results include both certification-specific and general content
        self.assertEqual(len(results), 2)
    
    @patch.object(CertificationSearchService, '_generate_query_embedding')
    def test_semantic_search_no_certification_filter(self, mock_embedding):
        """Test semantic search across all certifications when no filter is specified."""
        # Setup mocks
        mock_embedding.return_value = [0.1] * 1536
        self.mock_vector_service.search_by_certification.return_value = self.sample_search_results
        
        # Execute search without certification filter
        results = self.search_service.semantic_search(
            query="AWS best practices",
            limit=10
        )
        
        # Verify search across all certifications
        self.mock_vector_service.search_by_certification.assert_called_once_with(
            query_embedding=[0.1] * 1536,
            certification_type=None,
            filters=None,
            limit=10
        )
    
    def test_semantic_search_embedding_generation_failure(self):
        """Test handling of embedding generation failure."""
        with patch.object(self.search_service, '_generate_query_embedding', return_value=None):
            results = self.search_service.semantic_search("test query")
            self.assertEqual(results, [])
    
    def test_get_related_content_success(self):
        """Test successful retrieval of related content."""
        # Setup mock storage manager
        self.mock_storage_manager.retrieve_content_by_id.return_value = self.sample_content_metadata
        
        # Mock search results for related content
        with patch.object(self.search_service, 'semantic_search') as mock_search:
            mock_search.return_value = [
                SearchResult('related-1', 'Related Content 1', 'Text 1', 0.85, {}),
                SearchResult('related-2', 'Related Content 2', 'Text 2', 0.80, {})
            ]
            
            # Mock content retrieval for search results
            related_content = [
                ContentMetadata(
                    content_id="related-1",
                    title="Related Security Guide",
                    content_type=ContentType.STUDY_GUIDE,
                    certification_type=CertificationType.SAA,
                    category="Security"
                ),
                ContentMetadata(
                    content_id="related-2",
                    title="Advanced IAM Concepts",
                    content_type=ContentType.STUDY_GUIDE,
                    certification_type=CertificationType.SAA,
                    category="Security"
                )
            ]
            
            self.mock_storage_manager.retrieve_content_by_id.side_effect = [
                self.sample_content_metadata,  # Original content
                related_content[0],  # First related content
                related_content[1]   # Second related content
            ]
            
            # Execute
            results = self.search_service.get_related_content("test-content-1", limit=5)
            
            # Verify search was called with correct parameters
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            self.assertEqual(call_args[1]['certification_type'], CertificationType.SAA)
            self.assertIn('category', call_args[1]['filters'])
            self.assertEqual(call_args[1]['filters']['category'], 'Security')
            self.assertEqual(call_args[1]['filters']['exclude_content_id'], 'test-content-1')
            
            # Verify results
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].content_id, "related-1")
            self.assertEqual(results[1].content_id, "related-2")
    
    def test_get_related_content_reference_not_found(self):
        """Test handling when reference content is not found."""
        self.mock_storage_manager.retrieve_content_by_id.return_value = None
        
        results = self.search_service.get_related_content("nonexistent-content")
        self.assertEqual(results, [])
    
    def test_search_by_category_with_certification(self):
        """Test category-based search with certification filtering."""
        # Setup mock
        expected_results = [self.sample_content_metadata]
        self.mock_storage_manager.retrieve_content_by_category.return_value = expected_results
        
        # Execute
        results = self.search_service.search_by_category(
            category="Security",
            certification_type=CertificationType.SAA,
            limit=20
        )
        
        # Verify
        self.mock_storage_manager.retrieve_content_by_category.assert_called_once_with(
            category="Security",
            certification_type=CertificationType.SAA,
            limit=20
        )
        self.assertEqual(results, expected_results)
    
    def test_search_by_category_all_certifications(self):
        """Test category-based search across all certifications."""
        # Setup mock
        expected_results = [self.sample_content_metadata]
        self.mock_storage_manager.retrieve_content_by_category.return_value = expected_results
        
        # Execute
        results = self.search_service.search_by_category(
            category="Security",
            limit=20
        )
        
        # Verify
        self.mock_storage_manager.retrieve_content_by_category.assert_called_once_with(
            category="Security",
            certification_type=None,
            limit=20
        )
        self.assertEqual(results, expected_results)
    
    def test_get_user_recommended_content_new_user(self):
        """Test recommendations for new users with no progress."""
        # Setup mock for new user (no progress)
        self.mock_storage_manager.get_user_progress.return_value = None
        
        with patch.object(self.search_service, '_get_foundational_recommendations') as mock_foundational:
            foundational_content = [self.sample_content_metadata]
            mock_foundational.return_value = foundational_content
            
            # Execute
            results = self.search_service.get_user_recommended_content("new-user-123", limit=10)
            
            # Verify
            mock_foundational.assert_called_once_with(10)
            self.assertEqual(results, foundational_content)
    
    def test_get_user_recommended_content_existing_user(self):
        """Test recommendations for existing users based on progress."""
        # Setup mock user progress with actual data structure
        user_progress = [
            {'content_id': 'content-1', 'score': 0.6, 'category': 'Security'},
            {'content_id': 'content-2', 'score': 0.8, 'category': 'Networking'}
        ]
        self.mock_storage_manager.get_user_progress.return_value = user_progress
        
        with patch.object(self.search_service, '_analyze_user_certification_focus') as mock_analyze:
            with patch.object(self.search_service, '_identify_weak_areas') as mock_weak_areas:
                with patch.object(self.search_service, 'search_by_category') as mock_category_search:
                    with patch.object(self.mock_storage_manager, 'retrieve_content_by_certification') as mock_retrieve:
                        # Setup mocks
                        mock_analyze.return_value = CertificationType.SAA
                        mock_weak_areas.return_value = [
                            {'category': 'Security', 'reason': 'Low scores'},
                            {'category': 'Networking', 'reason': 'Limited engagement'}
                        ]
                        mock_category_search.return_value = [self.sample_content_metadata]
                        mock_retrieve.return_value = [self.sample_content_metadata]
                        
                        # Execute
                        results = self.search_service.get_user_recommended_content("existing-user-456", limit=10)
                        
                        # Verify analysis was performed
                        mock_analyze.assert_called_once_with(user_progress)
                        mock_weak_areas.assert_called_once_with(user_progress)
                        
                        # Verify category searches for weak areas
                        self.assertEqual(mock_category_search.call_count, 2)
                        
                        # Verify results
                        self.assertIsInstance(results, list)
    
    def test_get_certification_content_overview(self):
        """Test generation of certification content overview."""
        # Setup mock content
        mock_content = [
            ContentMetadata(
                content_id="content-1",
                title="Security Guide",
                content_type=ContentType.STUDY_GUIDE,
                certification_type=CertificationType.SAA,
                category="Security",
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                created_at=datetime.utcnow()
            ),
            ContentMetadata(
                content_id="content-2",
                title="Practice Questions",
                content_type=ContentType.QUESTION,
                certification_type=CertificationType.SAA,
                category="Networking",
                difficulty_level=DifficultyLevel.ADVANCED,
                created_at=datetime.utcnow()
            )
        ]
        
        self.mock_storage_manager.retrieve_content_by_certification.return_value = mock_content
        self.mock_vector_service.get_certification_statistics.return_value = {
            'SAA': {'document_count': 100, 'avg_chunk_size': 512}
        }
        
        # Execute
        overview = self.search_service.get_certification_content_overview(CertificationType.SAA)
        
        # Verify structure
        self.assertIn('certification_type', overview)
        self.assertIn('total_content_items', overview)
        self.assertIn('content_types', overview)
        self.assertIn('categories', overview)
        self.assertIn('difficulty_levels', overview)
        self.assertIn('recent_additions', overview)
        self.assertIn('vector_statistics', overview)
        
        # Verify content
        self.assertEqual(overview['certification_type'], 'SAA')
        self.assertEqual(overview['total_content_items'], 2)
        self.assertEqual(overview['content_types']['study_guide'], 1)
        self.assertEqual(overview['content_types']['question'], 1)
        self.assertEqual(overview['categories']['Security'], 1)
        self.assertEqual(overview['categories']['Networking'], 1)
    
    def test_convert_to_search_results(self):
        """Test conversion of raw search results to SearchResult objects."""
        raw_results = self.sample_search_results
        query = "test query"
        
        search_results = self.search_service._convert_to_search_results(raw_results, query)
        
        # Verify conversion
        self.assertEqual(len(search_results), 2)
        
        result1 = search_results[0]
        self.assertEqual(result1.content_id, 'saa-content-1')
        self.assertEqual(result1.title, 'IAM Security Guide')
        self.assertEqual(result1.text, 'AWS IAM security best practices')
        self.assertEqual(result1.score, 0.95)
        self.assertEqual(result1.metadata['certification_type'], 'SAA')
        self.assertEqual(result1.metadata['category'], 'Security')
        
        result2 = search_results[1]
        self.assertEqual(result2.content_id, 'saa-content-2')
        self.assertEqual(result2.score, 0.87)
    
    def test_post_process_results_certification_boosting(self):
        """Test post-processing with certification-specific score boosting."""
        # Create test results
        results = [
            SearchResult('saa-1', 'SAA Content', 'Text', 0.80, {'certification_type': 'SAA'}),
            SearchResult('general-1', 'General Content', 'Text', 0.85, {'certification_type': 'GENERAL'}),
            SearchResult('saa-2', 'SAA Content 2', 'Text', 0.75, {'certification_type': 'SAA'})
        ]
        
        # Process with SAA certification preference
        processed = self.search_service._post_process_results(
            results, CertificationType.SAA, None
        )
        
        # Verify SAA content is boosted (0.80 * 1.2 = 0.96, 0.75 * 1.2 = 0.90)
        # General content is penalized (0.85 * 0.9 = 0.765)
        # So order should be: SAA-1 (0.96), SAA-2 (0.90), General-1 (0.765)
        self.assertEqual(processed[0].content_id, 'saa-1')
        self.assertEqual(processed[1].content_id, 'saa-2')
        self.assertEqual(processed[2].content_id, 'general-1')
    
    def test_post_process_results_duplicate_removal(self):
        """Test removal of duplicate results based on content_id."""
        # Create test results with duplicates
        results = [
            SearchResult('content-1', 'Title 1', 'Text', 0.90, {}),
            SearchResult('content-2', 'Title 2', 'Text', 0.85, {}),
            SearchResult('content-1', 'Title 1 Duplicate', 'Text', 0.80, {}),  # Duplicate
        ]
        
        processed = self.search_service._post_process_results(results, None, None)
        
        # Verify duplicates are removed
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0].content_id, 'content-1')
        self.assertEqual(processed[1].content_id, 'content-2')
    
    @patch('boto3.client')
    def test_generate_query_embedding_success(self, mock_boto_client):
        """Test successful query embedding generation."""
        # Setup mock Bedrock client
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        
        # Mock response
        mock_response_body = Mock()
        mock_response_body.read.return_value = '{"embedding": [0.1, 0.2, 0.3]}'
        mock_bedrock.invoke_model.return_value = {"body": mock_response_body}
        
        # Execute
        embedding = self.search_service._generate_query_embedding("test query")
        
        # Verify
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        mock_bedrock.invoke_model.assert_called_once()
    
    @patch('boto3.client')
    def test_generate_query_embedding_failure(self, mock_boto_client):
        """Test handling of embedding generation failure."""
        # Setup mock to raise exception
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")
        
        # Execute
        embedding = self.search_service._generate_query_embedding("test query")
        
        # Verify failure handling
        self.assertIsNone(embedding)
    
    def test_get_foundational_recommendations(self):
        """Test foundational content recommendations for new users."""
        # Setup mock
        foundational_content = [self.sample_content_metadata]
        self.mock_storage_manager.retrieve_content_by_certification.return_value = foundational_content
        
        # Execute
        results = self.search_service._get_foundational_recommendations(limit=10)
        
        # Verify calls for foundational certifications
        self.assertEqual(self.mock_storage_manager.retrieve_content_by_certification.call_count, 2)
        
        # Verify CCP and AIP certifications are requested
        call_args = self.mock_storage_manager.retrieve_content_by_certification.call_args_list
        cert_types = [call[1]['certification_type'] for call in call_args]
        self.assertIn(CertificationType.CCP, cert_types)
        self.assertIn(CertificationType.AIP, cert_types)
    
    def test_identify_weak_areas(self):
        """Test identification of weak areas from user progress."""
        user_progress = []  # Mock progress data
        
        weak_areas = self.search_service._identify_weak_areas(user_progress)
        
        # Verify structure (placeholder implementation returns common weak areas)
        self.assertIsInstance(weak_areas, list)
        self.assertTrue(len(weak_areas) > 0)
        
        for area in weak_areas:
            self.assertIn('category', area)
            self.assertIn('reason', area)


if __name__ == '__main__':
    unittest.main()