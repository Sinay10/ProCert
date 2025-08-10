"""
Storage Manager implementation for the ProCert content management system.

This module provides the concrete implementation of the IStorageManager interface,
handling data persistence across DynamoDB, OpenSearch, and S3 storage systems.
"""

import os
import boto3
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from botocore.exceptions import ClientError, BotoCoreError

from .interfaces import IStorageManager
from .models import (
    ContentMetadata, QuestionAnswer, UserProgress, VectorDocument,
    ContentType, CertificationType, DifficultyLevel, ProgressType,
    validate_model
)
from .exceptions import (
    DynamoDBException, StorageException, ValidationException,
    InputValidationException, create_storage_exception
)
from .retry_utils import retry_aws_operation, with_aws_retries
from .validation_utils import (
    validate_content_id, validate_user_id, validate_certification_type,
    validate_string, validate_integer, sanitize_text_content
)


logger = logging.getLogger(__name__)


class StorageManager(IStorageManager):
    """
    Concrete implementation of storage management for content metadata and user progress.
    
    This class handles all interactions with DynamoDB tables for storing and retrieving
    content metadata, user progress, and maintaining relationships between content items.
    """
    
    def __init__(self, 
                 content_metadata_table_name: str,
                 user_progress_table_name: str,
                 region_name: str = 'us-east-1'):
        """
        Initialize the StorageManager with DynamoDB table names.
        
        Args:
            content_metadata_table_name: Name of the content metadata DynamoDB table
            user_progress_table_name: Name of the user progress DynamoDB table
            region_name: AWS region name
            
        Raises:
            ValidationException: If table names are invalid
            StorageException: If initialization fails
        """
        try:
            # Validate input parameters
            self.content_metadata_table_name = validate_string(
                content_metadata_table_name, "content_metadata_table_name", 
                min_length=1, max_length=255
            )
            self.user_progress_table_name = validate_string(
                user_progress_table_name, "user_progress_table_name", 
                min_length=1, max_length=255
            )
            self.region_name = validate_string(
                region_name, "region_name", min_length=1, max_length=50
            )
            
            # Initialize DynamoDB client and resources with retry logic
            self._initialize_dynamodb_resources()
            
            logger.info(f"StorageManager initialized with tables: {content_metadata_table_name}, {user_progress_table_name}")
            
        except InputValidationException as e:
            logger.error(f"Invalid parameters for StorageManager initialization: {e}")
            raise ValidationException(f"StorageManager initialization failed: {e.message}", details=e.details)
        except Exception as e:
            logger.error(f"Failed to initialize StorageManager: {e}")
            raise StorageException(f"StorageManager initialization failed: {str(e)}")
    
    @retry_aws_operation(max_retries=3)
    def _initialize_dynamodb_resources(self):
        """Initialize DynamoDB resources with retry logic."""
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            self.content_metadata_table = self.dynamodb.Table(self.content_metadata_table_name)
            self.user_progress_table = self.dynamodb.Table(self.user_progress_table_name)
            
            # Test connectivity by describing tables
            self.content_metadata_table.load()
            self.user_progress_table.load()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise StorageException(f"DynamoDB table not found: {e}")
            else:
                raise create_storage_exception('dynamodb', 'initialization', e)
        except Exception as e:
            raise StorageException(f"Failed to initialize DynamoDB resources: {str(e)}")
    
    def store_content_metadata(self, metadata: ContentMetadata) -> str:
        """
        Store content metadata in DynamoDB with versioning support.
        
        Args:
            metadata: ContentMetadata instance to store
            
        Returns:
            Stored content ID
            
        Raises:
            ValidationException: If metadata validation fails
            DynamoDBException: If DynamoDB operation fails
            StorageException: For other storage-related errors
        """
        if metadata is None:
            raise ValidationException("Content metadata cannot be None")
        
        try:
            # Validate metadata before storing
            validate_model(metadata)
            
            # Additional input validation
            validate_content_id(metadata.content_id)
            validate_certification_type(metadata.certification_type)
            
            # Sanitize text fields
            sanitized_metadata = self._sanitize_content_metadata(metadata)
            
            # Prepare item for DynamoDB with retry logic
            item = self._prepare_metadata_item(sanitized_metadata)
            
            # Check if content already exists for versioning
            existing_content = self._get_existing_content_version_safe(
                sanitized_metadata.content_id, 
                sanitized_metadata.certification_type
            )
            
            if existing_content:
                # Increment version for existing content
                item['version'] = self._increment_version(existing_content.get('version', '1.0'))
                item['updated_at'] = datetime.utcnow().isoformat()
                logger.info(f"Updating existing content {sanitized_metadata.content_id} to version {item['version']}")
            else:
                # New content, use provided version or default
                item['version'] = sanitized_metadata.version
                logger.info(f"Creating new content {sanitized_metadata.content_id} version {item['version']}")
            
            # Store in DynamoDB with retry logic
            self._store_metadata_item_with_retry(item)
            
            logger.info(f"Successfully stored content metadata: {sanitized_metadata.content_id}")
            return sanitized_metadata.content_id
            
        except ValidationException:
            raise  # Re-raise validation exceptions as-is
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error storing content metadata: {error_code} - {str(e)}")
            raise create_storage_exception('dynamodb', 'store_content_metadata', e)
        except Exception as e:
            logger.error(f"Unexpected error storing content metadata: {str(e)}")
            raise StorageException(f"Failed to store content metadata: {str(e)}")
    
    @retry_aws_operation(max_retries=3)
    def _store_metadata_item_with_retry(self, item: Dict[str, Any]):
        """Store metadata item with retry logic."""
        try:
            response = self.content_metadata_table.put_item(Item=item)
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['ValidationException', 'ConditionalCheckFailedException']:
                # These are not retryable
                raise
            logger.warning(f"Retryable DynamoDB error in store operation: {error_code}")
            raise
    
    def _sanitize_content_metadata(self, metadata: ContentMetadata) -> ContentMetadata:
        """Sanitize content metadata fields."""
        try:
            # Create a copy with sanitized text fields
            sanitized_title = sanitize_text_content(metadata.title)
            sanitized_category = sanitize_text_content(metadata.category)
            sanitized_subcategory = sanitize_text_content(metadata.subcategory) if metadata.subcategory else None
            
            # Validate sanitized fields
            if not sanitized_title:
                raise ValidationException("Content title cannot be empty after sanitization")
            
            if not sanitized_category:
                raise ValidationException("Content category cannot be empty after sanitization")
            
            # Create new metadata instance with sanitized fields
            return ContentMetadata(
                content_id=metadata.content_id,
                title=sanitized_title,
                content_type=metadata.content_type,
                certification_type=metadata.certification_type,
                category=sanitized_category,
                subcategory=sanitized_subcategory,
                difficulty_level=metadata.difficulty_level,
                tags=metadata.tags,
                created_at=metadata.created_at,
                updated_at=metadata.updated_at,
                version=metadata.version,
                source_file=metadata.source_file,
                source_bucket=metadata.source_bucket,
                chunk_count=metadata.chunk_count,
                question_count=metadata.question_count
            )
            
        except Exception as e:
            logger.error(f"Error sanitizing content metadata: {e}")
            raise ValidationException(f"Failed to sanitize content metadata: {str(e)}")
    
    def _get_existing_content_version_safe(self, content_id: str, certification_type: CertificationType) -> Optional[Dict[str, Any]]:
        """Get existing content item for versioning with error handling."""
        try:
            return with_aws_retries(
                self._get_existing_content_version,
                content_id,
                certification_type,
                max_retries=2
            )
        except Exception as e:
            logger.warning(f"Could not retrieve existing content version: {e}")
            return None
    
    def retrieve_content_by_id(self, content_id: str, certification_type: Optional[CertificationType] = None) -> Optional[ContentMetadata]:
        """
        Retrieve content metadata by ID and optionally by certification type.
        
        Args:
            content_id: Content identifier
            certification_type: Optional certification type filter
            
        Returns:
            ContentMetadata if found, None otherwise
        """
        try:
            if certification_type:
                # Query specific certification type
                response = self.content_metadata_table.get_item(
                    Key={
                        'content_id': content_id,
                        'certification_type': certification_type.value
                    }
                )
                
                if 'Item' in response:
                    return self._item_to_content_metadata(response['Item'])
            else:
                # Query all certification types for this content_id
                response = self.content_metadata_table.query(
                    KeyConditionExpression='content_id = :content_id',
                    ExpressionAttributeValues={':content_id': content_id},
                    Limit=1
                )
                
                if response['Items']:
                    return self._item_to_content_metadata(response['Items'][0])
            
            logger.info(f"Content not found: {content_id}")
            return None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error retrieving content: {error_code} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving content: {str(e)}")
            return None
    
    def retrieve_content_by_certification(self, certification_type: CertificationType, limit: int = 50) -> List[ContentMetadata]:
        """
        Retrieve content by certification type using GSI.
        
        Args:
            certification_type: Type of certification
            limit: Maximum number of results
            
        Returns:
            List of ContentMetadata instances
        """
        try:
            response = self.content_metadata_table.query(
                IndexName='CertificationTypeIndex',
                KeyConditionExpression='certification_type = :cert_type',
                ExpressionAttributeValues={':cert_type': certification_type.value},
                Limit=limit
            )
            
            content_list = []
            for item in response['Items']:
                try:
                    content = self._item_to_content_metadata(item)
                    content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(content_list)} content items for certification {certification_type.value}")
            return content_list
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error retrieving content by certification: {error_code} - {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving content by certification: {str(e)}")
            return []
    
    def retrieve_content_by_category(self, category: str, certification_type: Optional[CertificationType] = None, limit: int = 50) -> List[ContentMetadata]:
        """
        Retrieve content by category, optionally filtered by certification type.
        
        Args:
            category: Content category
            certification_type: Optional certification type filter
            limit: Maximum number of results
            
        Returns:
            List of ContentMetadata instances
        """
        try:
            if certification_type:
                # Use CertificationTypeIndex to filter by both certification and category
                response = self.content_metadata_table.query(
                    IndexName='CertificationTypeIndex',
                    KeyConditionExpression='certification_type = :cert_type AND category = :category',
                    ExpressionAttributeValues={
                        ':cert_type': certification_type.value,
                        ':category': category
                    },
                    Limit=limit
                )
            else:
                # Scan all items filtering by category (less efficient but necessary)
                response = self.content_metadata_table.scan(
                    FilterExpression='category = :category',
                    ExpressionAttributeValues={':category': category},
                    Limit=limit
                )
            
            content_list = []
            for item in response['Items']:
                try:
                    content = self._item_to_content_metadata(item)
                    content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(content_list)} content items for category {category}")
            return content_list
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error retrieving content by category: {error_code} - {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving content by category: {str(e)}")
            return []
    
    def update_content_metadata(self, content_id: str, certification_type: CertificationType, updates: Dict[str, Any]) -> bool:
        """
        Update content metadata with versioning support.
        
        Args:
            content_id: Content identifier
            certification_type: Certification type
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate update fields
            allowed_fields = {
                'title', 'category', 'subcategory', 'difficulty_level', 'tags',
                'chunk_count', 'question_count', 'source_file', 'source_bucket'
            }
            
            invalid_fields = set(updates.keys()) - allowed_fields
            if invalid_fields:
                logger.error(f"Invalid update fields: {invalid_fields}")
                return False
            
            # Prepare update expression
            update_expression_parts = []
            expression_attribute_values = {}
            
            for field, value in updates.items():
                if field == 'difficulty_level' and isinstance(value, DifficultyLevel):
                    value = value.value
                elif field == 'tags' and not isinstance(value, list):
                    logger.error(f"Tags must be a list, got {type(value)}")
                    return False
                
                update_expression_parts.append(f"{field} = :{field}")
                expression_attribute_values[f":{field}"] = value
            
            # Always update the updated_at timestamp and increment version
            update_expression_parts.extend(['updated_at = :updated_at', 'version = :version'])
            expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat()
            
            # Get current version to increment
            existing_item = self.content_metadata_table.get_item(
                Key={
                    'content_id': content_id,
                    'certification_type': certification_type.value
                }
            )
            
            if 'Item' not in existing_item:
                logger.error(f"Content not found for update: {content_id}")
                return False
            
            current_version = existing_item['Item'].get('version', '1.0')
            new_version = self._increment_version(current_version)
            expression_attribute_values[':version'] = new_version
            
            update_expression = 'SET ' + ', '.join(update_expression_parts)
            
            # Perform update
            response = self.content_metadata_table.update_item(
                Key={
                    'content_id': content_id,
                    'certification_type': certification_type.value
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='UPDATED_NEW'
            )
            
            logger.info(f"Successfully updated content {content_id} to version {new_version}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error updating content metadata: {error_code} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating content metadata: {str(e)}")
            return False
    
    def store_user_progress(self, user_id: str, progress: UserProgress) -> bool:
        """
        Store user progress data with relationship tracking.
        
        Args:
            user_id: User identifier
            progress: UserProgress data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate progress data
            validate_model(progress)
            
            # Get content metadata to determine certification type
            content = self.retrieve_content_by_id(progress.content_id)
            if not content:
                logger.error(f"Content not found for progress tracking: {progress.content_id}")
                return False
            
            # Prepare composite sort key: content_id#certification_type
            content_id_certification = f"{progress.content_id}#{content.certification_type.value}"
            
            # Prepare item for DynamoDB (convert float to Decimal for DynamoDB compatibility)
            item = {
                'user_id': user_id,
                'content_id_certification': content_id_certification,
                'content_id': progress.content_id,
                'certification_type': content.certification_type.value,
                'progress_type': progress.progress_type.value,
                'score': Decimal(str(progress.score)) if progress.score is not None else None,
                'time_spent': progress.time_spent,
                'timestamp': progress.timestamp.isoformat(),
                'session_id': progress.session_id
            }
            
            # Store in DynamoDB
            response = self.user_progress_table.put_item(Item=item)
            
            logger.info(f"Successfully stored user progress: {user_id} -> {progress.content_id}")
            return True
            
        except ValueError as e:
            logger.error(f"Validation error storing user progress: {str(e)}")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error storing user progress: {error_code} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing user progress: {str(e)}")
            return False
    
    def get_user_progress(self, user_id: str, certification_type: Optional[CertificationType] = None) -> List[UserProgress]:
        """
        Retrieve user progress data, optionally filtered by certification type.
        
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
    
    def delete_content_metadata(self, content_id: str, certification_type: CertificationType) -> bool:
        """
        Delete content metadata (soft delete by marking as inactive).
        
        Args:
            content_id: Content identifier
            certification_type: Certification type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Mark as inactive instead of hard delete to preserve relationships
            response = self.content_metadata_table.update_item(
                Key={
                    'content_id': content_id,
                    'certification_type': certification_type.value
                },
                UpdateExpression='SET is_active = :inactive, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':inactive': False,
                    ':updated_at': datetime.utcnow().isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            
            logger.info(f"Successfully marked content as inactive: {content_id}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error deleting content metadata: {error_code} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting content metadata: {str(e)}")
            return False
    
    def get_content_versions(self, content_id: str, certification_type: CertificationType) -> List[Dict[str, Any]]:
        """
        Get version history for content item.
        
        Args:
            content_id: Content identifier
            certification_type: Certification type
            
        Returns:
            List of version information dictionaries
        """
        try:
            # For now, we only store the current version in the main table
            # In a full implementation, we might have a separate versions table
            response = self.content_metadata_table.get_item(
                Key={
                    'content_id': content_id,
                    'certification_type': certification_type.value
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                return [{
                    'version': item.get('version', '1.0'),
                    'created_at': item.get('created_at'),
                    'updated_at': item.get('updated_at'),
                    'is_current': True
                }]
            
            return []
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB error retrieving content versions: {error_code} - {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving content versions: {str(e)}")
            return []
    
    # Helper methods
    
    def _prepare_metadata_item(self, metadata: ContentMetadata) -> Dict[str, Any]:
        """Convert ContentMetadata to DynamoDB item format."""
        item = metadata.to_dict()
        
        # Add additional fields for DynamoDB
        item['is_active'] = True
        
        # Ensure all enum values are converted to strings
        if isinstance(item.get('content_type'), ContentType):
            item['content_type'] = item['content_type'].value
        if isinstance(item.get('certification_type'), CertificationType):
            item['certification_type'] = item['certification_type'].value
        if isinstance(item.get('difficulty_level'), DifficultyLevel):
            item['difficulty_level'] = item['difficulty_level'].value
        
        return item
    
    def _item_to_content_metadata(self, item: Dict[str, Any]) -> ContentMetadata:
        """Convert DynamoDB item to ContentMetadata instance."""
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
    
    def _get_existing_content_version(self, content_id: str, certification_type: CertificationType) -> Optional[Dict[str, Any]]:
        """Get existing content item for versioning."""
        try:
            response = self.content_metadata_table.get_item(
                Key={
                    'content_id': content_id,
                    'certification_type': certification_type.value
                }
            )
            return response.get('Item')
        except Exception:
            return None
    
    def _increment_version(self, current_version: str) -> str:
        """Increment semantic version number."""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                patch = int(parts[2]) if len(parts) > 2 else 0
                return f"{major}.{minor}.{patch + 1}"
            else:
                return "1.0.1"
        except (ValueError, IndexError):
            return "1.0.1"
    
    # Vector storage integration
    
    def store_vector_embeddings(self, embeddings: List[VectorDocument]) -> bool:
        """
        Store vector embeddings in OpenSearch with certification-aware indexing.
        
        Args:
            embeddings: List of VectorDocument instances
            
        Returns:
            True if successful
        """
        try:
            # Import here to avoid circular imports
            from .vector_storage_service import VectorStorageService
            
            # Initialize vector storage service if not already done
            if not hasattr(self, '_vector_service'):
                # These would typically come from environment variables
                opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT', '')
                opensearch_index = os.environ.get('OPENSEARCH_INDEX', 'procert-vector-collection')
                
                if not opensearch_endpoint:
                    logger.error("OPENSEARCH_ENDPOINT environment variable not set")
                    return False
                
                self._vector_service = VectorStorageService(
                    opensearch_endpoint=opensearch_endpoint,
                    index_name=opensearch_index,
                    region_name=self.region_name
                )
            
            # Store vector documents with certification-aware indexing
            return self._vector_service.store_vector_documents(embeddings, use_certification_indices=True)
            
        except Exception as e:
            logger.error(f"Error storing vector embeddings: {e}")
            return False
    
    def search_vector_embeddings(self, query_embedding: List[float], 
                               certification_type: Optional[CertificationType] = None,
                               filters: Optional[Dict[str, Any]] = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search vector embeddings with certification filtering.
        
        Args:
            query_embedding: Query vector embedding
            certification_type: Optional certification type filter
            filters: Additional search filters
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            # Import here to avoid circular imports
            from .vector_storage_service import VectorStorageService
            
            # Initialize vector storage service if not already done
            if not hasattr(self, '_vector_service'):
                opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT', '')
                opensearch_index = os.environ.get('OPENSEARCH_INDEX', 'procert-vector-collection')
                
                if not opensearch_endpoint:
                    logger.error("OPENSEARCH_ENDPOINT environment variable not set")
                    return []
                
                self._vector_service = VectorStorageService(
                    opensearch_endpoint=opensearch_endpoint,
                    index_name=opensearch_index,
                    region_name=self.region_name
                )
            
            return self._vector_service.search_by_certification(
                query_embedding=query_embedding,
                certification_type=certification_type,
                filters=filters,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error searching vector embeddings: {e}")
            return []