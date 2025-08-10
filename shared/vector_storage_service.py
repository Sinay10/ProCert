"""
Enhanced Vector Storage Service for certification-aware content management.

This module provides advanced vector storage capabilities with certification-specific
metadata, improved chunking strategies, and optimized search indices.
"""

import boto3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from opensearchpy.exceptions import RequestError, ConnectionError

from .interfaces import IStorageManager
from .models import (
    VectorDocument, ContentMetadata, CertificationType, ContentType, 
    DifficultyLevel, get_certification_level, validate_model
)
from .exceptions import (
    VectorStorageException, OpenSearchException, ValidationException,
    InitializationException, IndexException, create_storage_exception
)
from .retry_utils import retry_opensearch_operation, with_retries
from .validation_utils import (
    validate_string, validate_integer, validate_list, validate_embedding_vector,
    sanitize_text_content
)


logger = logging.getLogger(__name__)


class VectorStorageService:
    """
    Enhanced vector storage service with certification-aware capabilities.
    
    This service provides:
    - Certification-specific document indexing
    - Advanced chunking strategies that preserve certification context
    - Optimized search indices for certification filtering
    - Metadata preservation and enhancement
    """
    
    def __init__(self, opensearch_endpoint: str, index_name: str, region_name: str = 'us-east-1'):
        """
        Initialize the VectorStorageService.
        
        Args:
            opensearch_endpoint: OpenSearch serverless endpoint
            index_name: Base index name for vector storage
            region_name: AWS region name
            
        Raises:
            ValidationException: If input parameters are invalid
            InitializationException: If service initialization fails
        """
        try:
            # Validate input parameters
            self.opensearch_endpoint = validate_string(
                opensearch_endpoint, "opensearch_endpoint", min_length=1, max_length=500
            )
            self.base_index_name = validate_string(
                index_name, "index_name", min_length=1, max_length=255,
                pattern=r'^[a-z0-9\-_]+$'
            )
            self.region_name = validate_string(
                region_name, "region_name", min_length=1, max_length=50
            )
            
            # Initialize OpenSearch client with retry logic
            self._init_opensearch_client()
            
            logger.info(f"VectorStorageService initialized with endpoint: {opensearch_endpoint}")
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize VectorStorageService: {e}")
            raise InitializationException(f"VectorStorageService initialization failed: {str(e)}")
    
    def _init_opensearch_client(self):
        """Initialize OpenSearch client with proper authentication and error handling."""
        try:
            # Validate endpoint format
            if not self.opensearch_endpoint.startswith('https://'):
                raise ValidationException("OpenSearch endpoint must start with https://")
            
            host = self.opensearch_endpoint.replace("https://", "")
            if not host:
                raise ValidationException("Invalid OpenSearch endpoint format")
            
            # Get AWS credentials with error handling
            try:
                credentials = boto3.Session().get_credentials()
                if not credentials:
                    raise InitializationException("AWS credentials not found")
            except Exception as e:
                raise InitializationException(f"Failed to get AWS credentials: {str(e)}")
            
            # Create authentication
            auth = AWSV4SignerAuth(credentials, self.region_name, 'aoss')
            
            # Initialize OpenSearch client with enhanced configuration
            self.opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_timeout=30,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection with retry logic
            self._test_opensearch_connectivity()
            
            logger.info("OpenSearch client initialized successfully")
            
        except ValidationException:
            raise
        except InitializationException:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch client: {e}")
            raise InitializationException(f"OpenSearch client initialization failed: {str(e)}")
    
    @retry_opensearch_operation(max_retries=3)
    def _test_opensearch_connectivity(self):
        """Test OpenSearch connectivity with retry logic."""
        try:
            info_response = self.opensearch_client.info()
            if not info_response:
                raise OpenSearchException("OpenSearch info response is empty")
            logger.debug(f"OpenSearch connectivity test successful: {info_response.get('version', {}).get('number', 'unknown')}")
        except Exception as e:
            logger.error(f"OpenSearch connectivity test failed: {e}")
            raise OpenSearchException(f"Failed to connect to OpenSearch: {str(e)}")
    
    def store_vector_documents(self, vector_docs: List[VectorDocument], 
                             use_certification_indices: bool = True) -> bool:
        """
        Store vector documents with certification-aware indexing.
        
        Args:
            vector_docs: List of VectorDocument instances to store
            use_certification_indices: Whether to use certification-specific indices
            
        Returns:
            True if successful, False otherwise
        """
        if not vector_docs:
            logger.warning("No vector documents provided for storage")
            return True
        
        try:
            # Validate all documents first
            for doc in vector_docs:
                validate_model(doc)
            
            # Group documents by certification type for batch processing
            cert_groups = self._group_documents_by_certification(vector_docs)
            
            success_count = 0
            total_count = len(vector_docs)
            
            for cert_type, docs in cert_groups.items():
                index_name = self._get_index_name(cert_type, use_certification_indices)
                
                # Ensure index exists with proper mapping
                self._ensure_index_exists(index_name, cert_type)
                
                # Batch store documents
                if self._batch_store_documents(docs, index_name):
                    success_count += len(docs)
                    logger.info(f"Successfully stored {len(docs)} documents for {cert_type} in index {index_name}")
                else:
                    logger.error(f"Failed to store documents for {cert_type}")
            
            success_rate = success_count / total_count
            logger.info(f"Vector storage completed: {success_count}/{total_count} documents stored ({success_rate:.2%})")
            
            return success_rate > 0.8  # Consider successful if >80% stored
            
        except Exception as e:
            logger.error(f"Error storing vector documents: {e}")
            return False
    
    def create_certification_aware_chunks(self, content_metadata: ContentMetadata, 
                                        text: str, embeddings: List[List[float]],
                                        chunk_texts: List[str]) -> List[VectorDocument]:
        """
        Create VectorDocument instances with enhanced certification-aware metadata.
        
        Args:
            content_metadata: Source content metadata
            text: Original full text
            embeddings: List of embedding vectors
            chunk_texts: List of text chunks
            
        Returns:
            List of VectorDocument instances with enhanced metadata
        """
        if len(embeddings) != len(chunk_texts):
            raise ValueError("Number of embeddings must match number of text chunks")
        
        vector_docs = []
        certification_level = get_certification_level(content_metadata.certification_type)
        
        for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            # Create enhanced metadata for this chunk
            chunk_metadata = {
                'extraction_method': 'certification_aware_chunking',
                'question_count': content_metadata.question_count or 0,
                'total_chunks': len(chunk_texts),
                'version': content_metadata.version,
                'language': 'en',  # Default to English, could be detected
                'chunk_position': i / len(chunk_texts),  # Relative position in document
                'chunk_overlap_info': self._calculate_chunk_overlap_info(i, len(chunk_texts))
            }
            
            # Merge with existing metadata
            chunk_metadata.update(content_metadata.to_dict().get('metadata', {}))
            
            vector_doc = VectorDocument(
                document_id=f"{content_metadata.content_id}-chunk-{i}",
                content_id=content_metadata.content_id,
                chunk_index=i,
                text=chunk_text,
                vector_embedding=embedding,
                certification_type=content_metadata.certification_type,
                certification_level=certification_level,
                content_type=content_metadata.content_type,
                category=content_metadata.category,
                subcategory=content_metadata.subcategory,
                difficulty_level=content_metadata.difficulty_level,
                tags=content_metadata.tags.copy(),
                source_file=content_metadata.source_file,
                source_bucket=content_metadata.source_bucket,
                chunk_size=len(chunk_text),
                processed_at=datetime.utcnow(),
                metadata=chunk_metadata
            )
            
            vector_docs.append(vector_doc)
        
        logger.info(f"Created {len(vector_docs)} certification-aware vector documents for {content_metadata.certification_type.value}")
        return vector_docs
    
    def search_by_certification(self, query_embedding: List[float], 
                              certification_type: Optional[CertificationType] = None,
                              filters: Optional[Dict[str, Any]] = None,
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform certification-aware vector search.
        
        Args:
            query_embedding: Query vector embedding
            certification_type: Optional certification type filter
            filters: Additional search filters
            limit: Maximum number of results
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            # Determine which indices to search
            if certification_type:
                indices = [self._get_index_name(certification_type.value, True)]
            else:
                # Search across all certification indices
                indices = self._get_all_certification_indices()
            
            # Build search query
            search_body = self._build_certification_search_query(
                query_embedding, certification_type, filters, limit
            )
            
            results = []
            for index_name in indices:
                try:
                    if self.opensearch_client.indices.exists(index=index_name):
                        response = self.opensearch_client.search(
                            index=index_name,
                            body=search_body,
                            size=limit
                        )
                        
                        for hit in response['hits']['hits']:
                            result = {
                                'document_id': hit['_source']['document_id'],
                                'content_id': hit['_source']['content_id'],
                                'text': hit['_source']['text'],
                                'score': hit['_score'],
                                'certification_type': hit['_source']['certification_type'],
                                'certification_level': hit['_source'].get('certification_level', ''),
                                'category': hit['_source'].get('category', ''),
                                'difficulty_level': hit['_source'].get('difficulty_level', ''),
                                'tags': hit['_source'].get('tags', []),
                                'metadata': hit['_source'].get('metadata', {}),
                                'index': index_name
                            }
                            results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Error searching index {index_name}: {e}")
                    continue
            
            # Sort by score and limit results
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in certification-aware search: {e}")
            return []
    
    def get_certification_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored content by certification type.
        
        Returns:
            Dictionary with certification statistics
        """
        try:
            stats = {}
            indices = self._get_all_certification_indices()
            
            for index_name in indices:
                if self.opensearch_client.indices.exists(index=index_name):
                    # Get document count
                    count_response = self.opensearch_client.count(index=index_name)
                    doc_count = count_response['count']
                    
                    # Get certification type from index name
                    cert_type = self._extract_cert_type_from_index(index_name)
                    
                    if doc_count > 0:
                        # Get aggregation data
                        agg_body = {
                            "size": 0,
                            "aggs": {
                                "content_types": {"terms": {"field": "content_type"}},
                                "difficulty_levels": {"terms": {"field": "difficulty_level"}},
                                "categories": {"terms": {"field": "category"}},
                                "avg_chunk_size": {"avg": {"field": "chunk_size"}}
                            }
                        }
                        
                        agg_response = self.opensearch_client.search(
                            index=index_name, body=agg_body
                        )
                        
                        stats[cert_type] = {
                            'document_count': doc_count,
                            'content_types': {
                                bucket['key']: bucket['doc_count'] 
                                for bucket in agg_response['aggregations']['content_types']['buckets']
                            },
                            'difficulty_levels': {
                                bucket['key']: bucket['doc_count'] 
                                for bucket in agg_response['aggregations']['difficulty_levels']['buckets']
                            },
                            'categories': {
                                bucket['key']: bucket['doc_count'] 
                                for bucket in agg_response['aggregations']['categories']['buckets']
                            },
                            'avg_chunk_size': agg_response['aggregations']['avg_chunk_size']['value']
                        }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting certification statistics: {e}")
            return {}
    
    # Private helper methods
    
    def _group_documents_by_certification(self, vector_docs: List[VectorDocument]) -> Dict[str, List[VectorDocument]]:
        """Group documents by certification type."""
        groups = {}
        for doc in vector_docs:
            cert_type = doc.certification_type.value
            if cert_type not in groups:
                groups[cert_type] = []
            groups[cert_type].append(doc)
        return groups
    
    def _get_index_name(self, certification_type: str, use_certification_indices: bool) -> str:
        """Get the appropriate index name for a certification type."""
        if use_certification_indices and certification_type != 'GENERAL':
            return f"{self.base_index_name}-{certification_type.lower()}"
        return self.base_index_name
    
    def _get_all_certification_indices(self) -> List[str]:
        """Get all possible certification index names."""
        indices = [self.base_index_name]  # Base index
        
        # Add certification-specific indices
        for cert_type in CertificationType:
            if cert_type != CertificationType.GENERAL:
                indices.append(f"{self.base_index_name}-{cert_type.value.lower()}")
        
        return indices
    
    def _extract_cert_type_from_index(self, index_name: str) -> str:
        """Extract certification type from index name."""
        if index_name == self.base_index_name:
            return 'GENERAL'
        
        # Extract from pattern: base_index_name-cert_type
        parts = index_name.split('-')
        if len(parts) > 1:
            return parts[-1].upper()
        
        return 'UNKNOWN'
    
    def _ensure_index_exists(self, index_name: str, certification_type: str):
        """Ensure the index exists with proper mapping."""
        try:
            if not self.opensearch_client.indices.exists(index=index_name):
                logger.info(f"Creating certification-specific index: {index_name}")
                
                # Use the enhanced mapping from the index setup
                index_body = self._get_enhanced_index_mapping(certification_type)
                self.opensearch_client.indices.create(index=index_name, body=index_body)
                
                logger.info(f"Successfully created index: {index_name}")
                
        except RequestError as e:
            if 'resource_already_exists_exception' not in str(e):
                logger.error(f"Error creating index {index_name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating index {index_name}: {e}")
            raise
    
    def _get_enhanced_index_mapping(self, certification_type: str) -> Dict[str, Any]:
        """Get enhanced index mapping for certification-specific indices."""
        return {
            'settings': {
                'index': {
                    'knn': True,
                    'number_of_shards': 1,  # Single shard for certification-specific indices
                    'number_of_replicas': 0
                }
            },
            'mappings': {
                'properties': {
                    # Vector field for semantic search
                    'vector_field': {
                        'type': 'knn_vector',
                        'dimension': 1536,
                        'method': {
                            'name': 'hnsw',
                            'space_type': 'l2',
                            'engine': 'nmslib'
                        }
                    },
                    # Core document fields
                    'document_id': {'type': 'keyword'},
                    'content_id': {'type': 'keyword'},
                    'chunk_index': {'type': 'integer'},
                    'text': {'type': 'text', 'analyzer': 'standard'},
                    
                    # Certification-specific metadata fields
                    'certification_type': {'type': 'keyword'},
                    'certification_level': {'type': 'keyword'},
                    
                    # Content classification fields
                    'content_type': {'type': 'keyword'},
                    'category': {'type': 'keyword'},
                    'subcategory': {'type': 'keyword'},
                    'difficulty_level': {'type': 'keyword'},
                    'tags': {'type': 'keyword'},
                    
                    # Source and processing metadata
                    'source_file': {'type': 'keyword'},
                    'source_bucket': {'type': 'keyword'},
                    'chunk_size': {'type': 'integer'},
                    'processed_at': {'type': 'date'},
                    
                    # Nested metadata object
                    'metadata': {
                        'type': 'object',
                        'properties': {
                            'extraction_method': {'type': 'keyword'},
                            'question_count': {'type': 'integer'},
                            'total_chunks': {'type': 'integer'},
                            'version': {'type': 'keyword'},
                            'language': {'type': 'keyword'},
                            'chunk_position': {'type': 'float'},
                            'chunk_overlap_info': {'type': 'object'}
                        }
                    }
                }
            }
        }
    
    def _batch_store_documents(self, docs: List[VectorDocument], index_name: str) -> bool:
        """Store documents in batches for better performance."""
        try:
            batch_size = 50  # Optimal batch size for OpenSearch
            success_count = 0
            
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i + batch_size]
                
                # Prepare bulk request
                bulk_body = []
                for doc in batch:
                    # Index action
                    bulk_body.append({
                        "index": {
                            "_index": index_name,
                            "_id": doc.document_id
                        }
                    })
                    
                    # Document body with vector field renamed for OpenSearch
                    doc_body = doc.to_dict()
                    doc_body['vector_field'] = doc_body.pop('vector_embedding')
                    bulk_body.append(doc_body)
                
                # Execute bulk request
                response = self.opensearch_client.bulk(body=bulk_body)
                
                # Check for errors
                if response.get('errors'):
                    for item in response['items']:
                        if 'index' in item and item['index'].get('status', 200) >= 400:
                            logger.error(f"Error indexing document: {item['index'].get('error', 'Unknown error')}")
                        else:
                            success_count += 1
                else:
                    success_count += len(batch)
                
                logger.debug(f"Processed batch {i//batch_size + 1}: {len(batch)} documents")
            
            logger.info(f"Batch storage completed: {success_count}/{len(docs)} documents stored in {index_name}")
            return success_count == len(docs)
            
        except Exception as e:
            logger.error(f"Error in batch document storage: {e}")
            return False
    
    def _build_certification_search_query(self, query_embedding: List[float], 
                                        certification_type: Optional[CertificationType],
                                        filters: Optional[Dict[str, Any]], 
                                        limit: int) -> Dict[str, Any]:
        """Build optimized search query for certification-aware search."""
        # Base KNN query
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "vector_field": {
                                    "vector": query_embedding,
                                    "k": limit * 2  # Get more candidates for filtering
                                }
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "_source": {
                "excludes": ["vector_field"]  # Don't return the large vector field
            }
        }
        
        # Add certification type filter
        if certification_type:
            query["query"]["bool"]["filter"].append({
                "term": {"certification_type": certification_type.value}
            })
        
        # Add additional filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query["query"]["bool"]["filter"].append({
                        "terms": {field: value}
                    })
                else:
                    query["query"]["bool"]["filter"].append({
                        "term": {field: value}
                    })
        
        return query
    
    def _calculate_chunk_overlap_info(self, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """Calculate overlap information for a chunk."""
        return {
            'has_previous': chunk_index > 0,
            'has_next': chunk_index < total_chunks - 1,
            'is_first': chunk_index == 0,
            'is_last': chunk_index == total_chunks - 1,
            'relative_position': chunk_index / max(1, total_chunks - 1) if total_chunks > 1 else 0
        }