"""
Unit tests for the VectorStorageService with certification-aware capabilities.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

import sys
import os

# Add shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared.vector_storage_service import VectorStorageService
from shared.models import (
    VectorDocument, ContentMetadata, CertificationType, 
    ContentType, DifficultyLevel
)


class TestVectorStorageService(unittest.TestCase):
    """Test cases for VectorStorageService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.opensearch_endpoint = "https://test-endpoint.us-east-1.aoss.amazonaws.com"
        self.index_name = "test-index"
        self.region_name = "us-east-1"
        
        # Mock OpenSearch client
        self.mock_opensearch_client = Mock()
        
        with patch('shared.vector_storage_service.OpenSearch') as mock_opensearch:
            mock_opensearch.return_value = self.mock_opensearch_client
            self.vector_service = VectorStorageService(
                opensearch_endpoint=self.opensearch_endpoint,
                index_name=self.index_name,
                region_name=self.region_name
            )
    
    def test_initialization(self):
        """Test VectorStorageService initialization."""
        self.assertEqual(self.vector_service.opensearch_endpoint, self.opensearch_endpoint)
        self.assertEqual(self.vector_service.base_index_name, self.index_name)
        self.assertEqual(self.vector_service.region_name, self.region_name)
    
    def test_create_certification_aware_chunks(self):
        """Test creation of certification-aware vector documents."""
        # Create test content metadata
        content_metadata = ContentMetadata(
            content_id="test-content-1",
            title="AWS SAA Study Guide",
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.SAA,
            category="Solutions Architecture",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=["aws", "architecture"],
            source_file="saa-guide.pdf",
            source_bucket="test-bucket",
            chunk_count=3,
            question_count=5
        )
        
        # Test data
        text = "This is a test document about AWS Solutions Architecture."
        chunk_texts = ["Chunk 1 text", "Chunk 2 text", "Chunk 3 text"]
        embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        
        # Create vector documents
        vector_docs = self.vector_service.create_certification_aware_chunks(
            content_metadata=content_metadata,
            text=text,
            embeddings=embeddings,
            chunk_texts=chunk_texts
        )
        
        # Verify results
        self.assertEqual(len(vector_docs), 3)
        
        for i, doc in enumerate(vector_docs):
            self.assertEqual(doc.content_id, "test-content-1")
            self.assertEqual(doc.chunk_index, i)
            self.assertEqual(doc.certification_type, CertificationType.SAA)
            self.assertEqual(doc.certification_level, "associate")
            self.assertEqual(doc.content_type, ContentType.STUDY_GUIDE)
            self.assertEqual(doc.category, "Solutions Architecture")
            self.assertEqual(doc.difficulty_level, DifficultyLevel.INTERMEDIATE)
            self.assertEqual(doc.tags, ["aws", "architecture"])
            self.assertEqual(doc.source_file, "saa-guide.pdf")
            self.assertEqual(doc.source_bucket, "test-bucket")
            self.assertEqual(len(doc.vector_embedding), 1536)
            
            # Check metadata
            self.assertIn('extraction_method', doc.metadata)
            self.assertIn('total_chunks', doc.metadata)
            self.assertEqual(doc.metadata['total_chunks'], 3)
    
    def test_group_documents_by_certification(self):
        """Test grouping of documents by certification type."""
        # Create test vector documents
        saa_doc = VectorDocument(
            document_id="saa-doc-1",
            content_id="content-1",
            chunk_index=0,
            text="SAA content",
            vector_embedding=[0.1] * 1536,
            certification_type=CertificationType.SAA
        )
        
        dva_doc = VectorDocument(
            document_id="dva-doc-1",
            content_id="content-2",
            chunk_index=0,
            text="DVA content",
            vector_embedding=[0.2] * 1536,
            certification_type=CertificationType.DVA
        )
        
        general_doc = VectorDocument(
            document_id="general-doc-1",
            content_id="content-3",
            chunk_index=0,
            text="General content",
            vector_embedding=[0.3] * 1536,
            certification_type=CertificationType.GENERAL
        )
        
        vector_docs = [saa_doc, dva_doc, general_doc]
        
        # Group documents
        groups = self.vector_service._group_documents_by_certification(vector_docs)
        
        # Verify grouping
        self.assertEqual(len(groups), 3)
        self.assertIn('SAA', groups)
        self.assertIn('DVA', groups)
        self.assertIn('GENERAL', groups)
        self.assertEqual(len(groups['SAA']), 1)
        self.assertEqual(len(groups['DVA']), 1)
        self.assertEqual(len(groups['GENERAL']), 1)
    
    def test_get_index_name(self):
        """Test index name generation for different certification types."""
        # Test certification-specific indices
        saa_index = self.vector_service._get_index_name('SAA', True)
        self.assertEqual(saa_index, 'test-index-saa')
        
        dva_index = self.vector_service._get_index_name('DVA', True)
        self.assertEqual(dva_index, 'test-index-dva')
        
        # Test general index
        general_index = self.vector_service._get_index_name('GENERAL', True)
        self.assertEqual(general_index, 'test-index')
        
        # Test when certification indices are disabled
        base_index = self.vector_service._get_index_name('SAA', False)
        self.assertEqual(base_index, 'test-index')
    
    def test_get_all_certification_indices(self):
        """Test getting all possible certification index names."""
        indices = self.vector_service._get_all_certification_indices()
        
        # Should include base index and all certification-specific indices
        self.assertIn('test-index', indices)
        self.assertIn('test-index-saa', indices)
        self.assertIn('test-index-dva', indices)
        self.assertIn('test-index-ccp', indices)
        
        # Should not include general certification as separate index
        self.assertNotIn('test-index-general', indices)
    
    def test_extract_cert_type_from_index(self):
        """Test extraction of certification type from index name."""
        # Test certification-specific indices
        self.assertEqual(
            self.vector_service._extract_cert_type_from_index('test-index-saa'),
            'SAA'
        )
        self.assertEqual(
            self.vector_service._extract_cert_type_from_index('test-index-dva'),
            'DVA'
        )
        
        # Test base index
        self.assertEqual(
            self.vector_service._extract_cert_type_from_index('test-index'),
            'GENERAL'
        )
    
    @patch('shared.vector_storage_service.validate_model')
    def test_store_vector_documents_success(self, mock_validate):
        """Test successful storage of vector documents."""
        # Mock validation
        mock_validate.return_value = True
        
        # Mock OpenSearch operations
        self.mock_opensearch_client.indices.exists.return_value = True
        self.mock_opensearch_client.bulk.return_value = {'errors': False, 'items': []}
        
        # Create test documents
        vector_docs = [
            VectorDocument(
                document_id="test-doc-1",
                content_id="content-1",
                chunk_index=0,
                text="Test content",
                vector_embedding=[0.1] * 1536,
                certification_type=CertificationType.SAA
            )
        ]
        
        # Store documents
        result = self.vector_service.store_vector_documents(vector_docs)
        
        # Verify success
        self.assertTrue(result)
        mock_validate.assert_called()
        self.mock_opensearch_client.bulk.assert_called()
    
    def test_store_vector_documents_empty_list(self):
        """Test storage with empty document list."""
        result = self.vector_service.store_vector_documents([])
        self.assertTrue(result)  # Should return True for empty list
    
    @patch('shared.vector_storage_service.validate_model')
    def test_store_vector_documents_validation_error(self, mock_validate):
        """Test storage with validation errors."""
        # Mock validation to raise error
        mock_validate.side_effect = ValueError("Validation failed")
        
        # Create test documents
        vector_docs = [
            VectorDocument(
                document_id="invalid-doc",
                content_id="",  # Invalid empty content_id
                chunk_index=0,
                text="Test content",
                vector_embedding=[0.1] * 1536,
                certification_type=CertificationType.SAA
            )
        ]
        
        # Store documents
        result = self.vector_service.store_vector_documents(vector_docs)
        
        # Verify failure
        self.assertFalse(result)
    
    def test_build_certification_search_query(self):
        """Test building of certification-aware search queries."""
        query_embedding = [0.1] * 1536
        
        # Test with certification filter
        query = self.vector_service._build_certification_search_query(
            query_embedding=query_embedding,
            certification_type=CertificationType.SAA,
            filters={'category': 'Security'},
            limit=10
        )
        
        # Verify query structure
        self.assertIn('query', query)
        self.assertIn('bool', query['query'])
        self.assertIn('must', query['query']['bool'])
        self.assertIn('filter', query['query']['bool'])
        
        # Check KNN query
        knn_query = query['query']['bool']['must'][0]
        self.assertIn('knn', knn_query)
        self.assertEqual(knn_query['knn']['vector_field']['vector'], query_embedding)
        
        # Check filters
        filters = query['query']['bool']['filter']
        cert_filter = next((f for f in filters if 'certification_type' in f.get('term', {})), None)
        self.assertIsNotNone(cert_filter)
        self.assertEqual(cert_filter['term']['certification_type'], 'SAA')
        
        category_filter = next((f for f in filters if 'category' in f.get('term', {})), None)
        self.assertIsNotNone(category_filter)
        self.assertEqual(category_filter['term']['category'], 'Security')
    
    def test_calculate_chunk_overlap_info(self):
        """Test calculation of chunk overlap information."""
        # Test first chunk
        first_chunk_info = self.vector_service._calculate_chunk_overlap_info(0, 5)
        self.assertFalse(first_chunk_info['has_previous'])
        self.assertTrue(first_chunk_info['has_next'])
        self.assertTrue(first_chunk_info['is_first'])
        self.assertFalse(first_chunk_info['is_last'])
        self.assertEqual(first_chunk_info['relative_position'], 0.0)
        
        # Test middle chunk
        middle_chunk_info = self.vector_service._calculate_chunk_overlap_info(2, 5)
        self.assertTrue(middle_chunk_info['has_previous'])
        self.assertTrue(middle_chunk_info['has_next'])
        self.assertFalse(middle_chunk_info['is_first'])
        self.assertFalse(middle_chunk_info['is_last'])
        self.assertEqual(middle_chunk_info['relative_position'], 0.5)
        
        # Test last chunk
        last_chunk_info = self.vector_service._calculate_chunk_overlap_info(4, 5)
        self.assertTrue(last_chunk_info['has_previous'])
        self.assertFalse(last_chunk_info['has_next'])
        self.assertFalse(last_chunk_info['is_first'])
        self.assertTrue(last_chunk_info['is_last'])
        self.assertEqual(last_chunk_info['relative_position'], 1.0)
        
        # Test single chunk
        single_chunk_info = self.vector_service._calculate_chunk_overlap_info(0, 1)
        self.assertFalse(single_chunk_info['has_previous'])
        self.assertFalse(single_chunk_info['has_next'])
        self.assertTrue(single_chunk_info['is_first'])
        self.assertTrue(single_chunk_info['is_last'])
        self.assertEqual(single_chunk_info['relative_position'], 0)


if __name__ == '__main__':
    unittest.main()