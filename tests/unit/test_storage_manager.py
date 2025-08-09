"""
Unit tests for the StorageManager class.

This module contains comprehensive tests for all StorageManager functionality
including content metadata storage, user progress tracking, versioning, and error handling.
"""

import pytest
import boto3
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import json

# Import the classes we're testing
from shared.storage_manager import StorageManager
from shared.models import (
    ContentMetadata, UserProgress, VectorDocument,
    ContentType, CertificationType, DifficultyLevel, ProgressType
)


@pytest.fixture
def mock_dynamodb_tables():
    """Create mock DynamoDB tables for testing."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create content metadata table
        content_table = dynamodb.create_table(
            TableName='test-content-metadata',
            KeySchema=[
                {'AttributeName': 'content_id', 'KeyType': 'HASH'},
                {'AttributeName': 'certification_type', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'content_id', 'AttributeType': 'S'},
                {'AttributeName': 'certification_type', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'},
                {'AttributeName': 'content_type', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'CertificationTypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'certification_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'category', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'ContentTypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'content_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # Create user progress table
        progress_table = dynamodb.create_table(
            TableName='test-user-progress',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'content_id_certification', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'content_id_certification', 'AttributeType': 'S'},
                {'AttributeName': 'certification_type', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserCertificationIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'certification_type', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'ProgressTimeIndex',
                    'KeySchema': [
                        {'AttributeName': 'certification_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        yield dynamodb, content_table, progress_table


@pytest.fixture
def storage_manager(mock_dynamodb_tables):
    """Create StorageManager instance with mock tables."""
    dynamodb, content_table, progress_table = mock_dynamodb_tables
    return StorageManager(
        content_metadata_table_name='test-content-metadata',
        user_progress_table_name='test-user-progress',
        region_name='us-east-1'
    )


@pytest.fixture
def sample_content_metadata():
    """Create sample ContentMetadata for testing."""
    return ContentMetadata(
        content_id='test-content-001',
        title='AWS Lambda Best Practices',
        content_type=ContentType.STUDY_GUIDE,
        certification_type=CertificationType.SAA,
        category='Compute',
        subcategory='Serverless',
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        tags=['lambda', 'serverless', 'aws'],
        version='1.0',
        source_file='lambda-guide.pdf',
        source_bucket='procert-materials-saa',
        chunk_count=5,
        question_count=10
    )


@pytest.fixture
def sample_user_progress():
    """Create sample UserProgress for testing."""
    return UserProgress(
        user_id='user-123',
        content_id='test-content-001',
        progress_type=ProgressType.COMPLETED,
        score=85.5,
        time_spent=1800,  # 30 minutes
        session_id='session-456'
    )


class TestStorageManagerContentMetadata:
    """Test cases for content metadata operations."""
    
    def test_store_content_metadata_success(self, storage_manager, sample_content_metadata):
        """Test successful storage of content metadata."""
        content_id = storage_manager.store_content_metadata(sample_content_metadata)
        
        assert content_id == sample_content_metadata.content_id
        
        # Verify the content was stored
        retrieved = storage_manager.retrieve_content_by_id(content_id, sample_content_metadata.certification_type)
        assert retrieved is not None
        assert retrieved.title == sample_content_metadata.title
        assert retrieved.certification_type == sample_content_metadata.certification_type
    
    def test_store_content_metadata_versioning(self, storage_manager, sample_content_metadata):
        """Test content versioning when storing duplicate content."""
        # Store initial version
        content_id = storage_manager.store_content_metadata(sample_content_metadata)
        
        # Store updated version
        updated_metadata = ContentMetadata(
            content_id=sample_content_metadata.content_id,
            title='AWS Lambda Best Practices - Updated',
            content_type=sample_content_metadata.content_type,
            certification_type=sample_content_metadata.certification_type,
            category=sample_content_metadata.category,
            version='1.0'  # Same version, should be incremented
        )
        
        storage_manager.store_content_metadata(updated_metadata)
        
        # Retrieve and verify version was incremented
        retrieved = storage_manager.retrieve_content_by_id(content_id, sample_content_metadata.certification_type)
        assert retrieved is not None
        assert retrieved.version == '1.0.1'
        assert retrieved.title == 'AWS Lambda Best Practices - Updated'
    
    def test_store_content_metadata_validation_error(self, storage_manager):
        """Test storage with invalid metadata."""
        invalid_metadata = ContentMetadata(
            content_id='',  # Invalid empty content_id
            title='Test Content',
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.SAA,
            category='Test'
        )
        
        with pytest.raises(ValueError):
            storage_manager.store_content_metadata(invalid_metadata)
    
    def test_retrieve_content_by_id_success(self, storage_manager, sample_content_metadata):
        """Test successful retrieval of content by ID."""
        # Store content first
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Retrieve by ID and certification type
        retrieved = storage_manager.retrieve_content_by_id(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type
        )
        
        assert retrieved is not None
        assert retrieved.content_id == sample_content_metadata.content_id
        assert retrieved.title == sample_content_metadata.title
        assert retrieved.certification_type == sample_content_metadata.certification_type
    
    def test_retrieve_content_by_id_not_found(self, storage_manager):
        """Test retrieval of non-existent content."""
        retrieved = storage_manager.retrieve_content_by_id('non-existent', CertificationType.SAA)
        assert retrieved is None
    
    def test_retrieve_content_by_certification(self, storage_manager, sample_content_metadata):
        """Test retrieval of content by certification type."""
        # Store multiple content items
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Create another content item with different certification
        dva_content = ContentMetadata(
            content_id='test-content-002',
            title='DynamoDB Guide',
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.DVA,
            category='Database'
        )
        storage_manager.store_content_metadata(dva_content)
        
        # Retrieve SAA content
        saa_content = storage_manager.retrieve_content_by_certification(CertificationType.SAA)
        assert len(saa_content) == 1
        assert saa_content[0].certification_type == CertificationType.SAA
        
        # Retrieve DVA content
        dva_content_list = storage_manager.retrieve_content_by_certification(CertificationType.DVA)
        assert len(dva_content_list) == 1
        assert dva_content_list[0].certification_type == CertificationType.DVA
    
    def test_retrieve_content_by_category(self, storage_manager, sample_content_metadata):
        """Test retrieval of content by category."""
        # Store content
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Retrieve by category
        compute_content = storage_manager.retrieve_content_by_category('Compute')
        assert len(compute_content) == 1
        assert compute_content[0].category == 'Compute'
        
        # Retrieve by category with certification filter
        compute_saa_content = storage_manager.retrieve_content_by_category(
            'Compute', 
            CertificationType.SAA
        )
        assert len(compute_saa_content) == 1
        assert compute_saa_content[0].certification_type == CertificationType.SAA
    
    def test_update_content_metadata_success(self, storage_manager, sample_content_metadata):
        """Test successful update of content metadata."""
        # Store initial content
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Update content
        updates = {
            'title': 'Updated Lambda Guide',
            'tags': ['lambda', 'serverless', 'updated'],
            'chunk_count': 7
        }
        
        success = storage_manager.update_content_metadata(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type,
            updates
        )
        
        assert success is True
        
        # Verify updates
        retrieved = storage_manager.retrieve_content_by_id(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type
        )
        assert retrieved.title == 'Updated Lambda Guide'
        assert retrieved.tags == ['lambda', 'serverless', 'updated']
        assert retrieved.chunk_count == 7
        assert retrieved.version == '1.0.1'  # Version should be incremented
    
    def test_update_content_metadata_invalid_fields(self, storage_manager, sample_content_metadata):
        """Test update with invalid fields."""
        # Store initial content
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Try to update with invalid field
        updates = {
            'invalid_field': 'some_value',
            'title': 'Updated Title'
        }
        
        success = storage_manager.update_content_metadata(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type,
            updates
        )
        
        assert success is False
    
    def test_update_content_metadata_not_found(self, storage_manager):
        """Test update of non-existent content."""
        updates = {'title': 'Updated Title'}
        
        success = storage_manager.update_content_metadata(
            'non-existent',
            CertificationType.SAA,
            updates
        )
        
        assert success is False
    
    def test_delete_content_metadata(self, storage_manager, sample_content_metadata):
        """Test soft delete of content metadata."""
        # Store content
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Delete content
        success = storage_manager.delete_content_metadata(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type
        )
        
        assert success is True
        
        # Content should still exist but marked as inactive
        # Note: In this test, we can't easily verify the is_active flag
        # without modifying the retrieve method to include it
    
    def test_get_content_versions(self, storage_manager, sample_content_metadata):
        """Test retrieval of content version history."""
        # Store content
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Get versions
        versions = storage_manager.get_content_versions(
            sample_content_metadata.content_id,
            sample_content_metadata.certification_type
        )
        
        assert len(versions) == 1
        assert versions[0]['version'] == '1.0'
        assert versions[0]['is_current'] is True


class TestStorageManagerUserProgress:
    """Test cases for user progress operations."""
    
    def test_store_user_progress_success(self, storage_manager, sample_content_metadata, sample_user_progress):
        """Test successful storage of user progress."""
        # Store content metadata first (required for progress tracking)
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Store user progress
        success = storage_manager.store_user_progress(
            sample_user_progress.user_id,
            sample_user_progress
        )
        
        assert success is True
        
        # Verify progress was stored
        progress_list = storage_manager.get_user_progress(sample_user_progress.user_id)
        assert len(progress_list) == 1
        assert progress_list[0].content_id == sample_user_progress.content_id
        assert progress_list[0].score == sample_user_progress.score
    
    def test_store_user_progress_content_not_found(self, storage_manager, sample_user_progress):
        """Test storing progress for non-existent content."""
        success = storage_manager.store_user_progress(
            sample_user_progress.user_id,
            sample_user_progress
        )
        
        assert success is False
    
    def test_store_user_progress_validation_error(self, storage_manager, sample_content_metadata):
        """Test storing invalid user progress."""
        # Store content metadata first
        storage_manager.store_content_metadata(sample_content_metadata)
        
        # Create invalid progress (empty user_id)
        invalid_progress = UserProgress(
            user_id='',  # Invalid empty user_id
            content_id=sample_content_metadata.content_id,
            progress_type=ProgressType.VIEWED
        )
        
        success = storage_manager.store_user_progress('', invalid_progress)
        assert success is False
    
    def test_get_user_progress_all(self, storage_manager, sample_content_metadata, sample_user_progress):
        """Test retrieval of all user progress."""
        # Store content and progress
        storage_manager.store_content_metadata(sample_content_metadata)
        storage_manager.store_user_progress(sample_user_progress.user_id, sample_user_progress)
        
        # Retrieve all progress for user
        progress_list = storage_manager.get_user_progress(sample_user_progress.user_id)
        
        assert len(progress_list) == 1
        assert progress_list[0].user_id == sample_user_progress.user_id
        assert progress_list[0].content_id == sample_user_progress.content_id
        assert progress_list[0].progress_type == sample_user_progress.progress_type
    
    def test_get_user_progress_by_certification(self, storage_manager, sample_content_metadata, sample_user_progress):
        """Test retrieval of user progress filtered by certification."""
        # Store content and progress
        storage_manager.store_content_metadata(sample_content_metadata)
        storage_manager.store_user_progress(sample_user_progress.user_id, sample_user_progress)
        
        # Retrieve progress filtered by certification
        progress_list = storage_manager.get_user_progress(
            sample_user_progress.user_id,
            CertificationType.SAA
        )
        
        assert len(progress_list) == 1
        assert progress_list[0].content_id == sample_user_progress.content_id
        
        # Try with different certification (should return empty)
        dva_progress = storage_manager.get_user_progress(
            sample_user_progress.user_id,
            CertificationType.DVA
        )
        
        assert len(dva_progress) == 0
    
    def test_get_user_progress_empty(self, storage_manager):
        """Test retrieval of progress for user with no progress."""
        progress_list = storage_manager.get_user_progress('non-existent-user')
        assert len(progress_list) == 0


class TestStorageManagerHelperMethods:
    """Test cases for helper methods."""
    
    def test_increment_version(self, storage_manager):
        """Test version increment logic."""
        assert storage_manager._increment_version('1.0') == '1.0.1'
        assert storage_manager._increment_version('1.0.0') == '1.0.1'
        assert storage_manager._increment_version('2.1.5') == '2.1.6'
        assert storage_manager._increment_version('invalid') == '1.0.1'
        assert storage_manager._increment_version('') == '1.0.1'
    
    def test_prepare_metadata_item(self, storage_manager, sample_content_metadata):
        """Test conversion of ContentMetadata to DynamoDB item."""
        item = storage_manager._prepare_metadata_item(sample_content_metadata)
        
        assert item['content_id'] == sample_content_metadata.content_id
        assert item['title'] == sample_content_metadata.title
        assert item['content_type'] == sample_content_metadata.content_type.value
        assert item['certification_type'] == sample_content_metadata.certification_type.value
        assert item['is_active'] is True
    
    def test_item_to_content_metadata(self, storage_manager, sample_content_metadata):
        """Test conversion of DynamoDB item to ContentMetadata."""
        # Convert to item and back
        item = storage_manager._prepare_metadata_item(sample_content_metadata)
        converted = storage_manager._item_to_content_metadata(item)
        
        assert converted.content_id == sample_content_metadata.content_id
        assert converted.title == sample_content_metadata.title
        assert converted.content_type == sample_content_metadata.content_type
        assert converted.certification_type == sample_content_metadata.certification_type


class TestStorageManagerErrorHandling:
    """Test cases for error handling scenarios."""
    
    @patch('shared.storage_manager.boto3.resource')
    def test_dynamodb_client_error(self, mock_boto3):
        """Test handling of DynamoDB client errors."""
        # Mock DynamoDB to raise ClientError
        mock_table = Mock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.return_value = mock_resource
        
        storage_manager = StorageManager('test-table', 'test-progress-table')
        
        sample_metadata = ContentMetadata(
            content_id='test',
            title='Test',
            content_type=ContentType.STUDY_GUIDE,
            certification_type=CertificationType.SAA,
            category='Test'
        )
        
        # Should handle error gracefully
        with pytest.raises(RuntimeError):
            storage_manager.store_content_metadata(sample_metadata)
    
    def test_vector_storage_placeholder(self, storage_manager):
        """Test vector storage placeholder method."""
        # Create sample vector documents
        vectors = [
            VectorDocument(
                document_id='doc-1',
                content_id='content-1',
                chunk_index=0,
                text='Sample text',
                vector_embedding=[0.1] * 1536,
                certification_type=CertificationType.SAA
            )
        ]
        
        # Should return True (placeholder implementation)
        result = storage_manager.store_vector_embeddings(vectors)
        assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])