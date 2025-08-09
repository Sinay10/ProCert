#!/usr/bin/env python3
"""
Example usage of the StorageManager class.

This script demonstrates how to use the StorageManager to store and retrieve
content metadata and user progress data.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import (
    StorageManager, ContentMetadata, UserProgress,
    ContentType, CertificationType, DifficultyLevel, ProgressType
)


def main():
    """Demonstrate StorageManager usage."""
    
    # Initialize StorageManager with your DynamoDB table names
    # In a real application, these would come from environment variables
    storage_manager = StorageManager(
        content_metadata_table_name='procert-content-metadata-123456789012',
        user_progress_table_name='procert-user-progress-123456789012',
        region_name='us-east-1'
    )
    
    print("StorageManager Example")
    print("=" * 50)
    
    # Example 1: Store content metadata
    print("\n1. Storing content metadata...")
    
    content_metadata = ContentMetadata(
        content_id='example-content-001',
        title='AWS Lambda Best Practices Guide',
        content_type=ContentType.STUDY_GUIDE,
        certification_type=CertificationType.SAA,
        category='Compute',
        subcategory='Serverless',
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        tags=['lambda', 'serverless', 'compute', 'aws'],
        version='1.0',
        source_file='lambda-best-practices.pdf',
        source_bucket='procert-materials-saa',
        chunk_count=8,
        question_count=15
    )
    
    try:
        content_id = storage_manager.store_content_metadata(content_metadata)
        print(f"✓ Successfully stored content: {content_id}")
    except Exception as e:
        print(f"✗ Error storing content: {e}")
        return
    
    # Example 2: Retrieve content metadata
    print("\n2. Retrieving content metadata...")
    
    try:
        retrieved_content = storage_manager.retrieve_content_by_id(
            content_id, 
            CertificationType.SAA
        )
        
        if retrieved_content:
            print(f"✓ Retrieved content: {retrieved_content.title}")
            print(f"  - Category: {retrieved_content.category}")
            print(f"  - Difficulty: {retrieved_content.difficulty_level.value}")
            print(f"  - Tags: {', '.join(retrieved_content.tags)}")
        else:
            print("✗ Content not found")
    except Exception as e:
        print(f"✗ Error retrieving content: {e}")
    
    # Example 3: Store user progress
    print("\n3. Storing user progress...")
    
    user_progress = UserProgress(
        user_id='user-example-123',
        content_id=content_id,
        progress_type=ProgressType.COMPLETED,
        score=87.5,
        time_spent=2400,  # 40 minutes in seconds
        session_id='session-abc-456'
    )
    
    try:
        success = storage_manager.store_user_progress(
            user_progress.user_id,
            user_progress
        )
        
        if success:
            print(f"✓ Successfully stored user progress")
        else:
            print("✗ Failed to store user progress")
    except Exception as e:
        print(f"✗ Error storing user progress: {e}")
    
    # Example 4: Retrieve user progress
    print("\n4. Retrieving user progress...")
    
    try:
        progress_list = storage_manager.get_user_progress(
            user_progress.user_id,
            CertificationType.SAA
        )
        
        if progress_list:
            for progress in progress_list:
                print(f"✓ Found progress for content: {progress.content_id}")
                print(f"  - Type: {progress.progress_type.value}")
                print(f"  - Score: {progress.score}%")
                print(f"  - Time spent: {progress.time_spent // 60} minutes")
        else:
            print("✗ No progress found for user")
    except Exception as e:
        print(f"✗ Error retrieving user progress: {e}")
    
    # Example 5: Update content metadata
    print("\n5. Updating content metadata...")
    
    try:
        updates = {
            'title': 'AWS Lambda Best Practices Guide - Updated',
            'tags': ['lambda', 'serverless', 'compute', 'aws', 'updated'],
            'chunk_count': 10
        }
        
        success = storage_manager.update_content_metadata(
            content_id,
            CertificationType.SAA,
            updates
        )
        
        if success:
            print("✓ Successfully updated content metadata")
            
            # Retrieve updated content to verify
            updated_content = storage_manager.retrieve_content_by_id(
                content_id,
                CertificationType.SAA
            )
            
            if updated_content:
                print(f"  - New title: {updated_content.title}")
                print(f"  - New version: {updated_content.version}")
                print(f"  - New chunk count: {updated_content.chunk_count}")
        else:
            print("✗ Failed to update content metadata")
    except Exception as e:
        print(f"✗ Error updating content: {e}")
    
    # Example 6: Query content by certification type
    print("\n6. Querying content by certification type...")
    
    try:
        saa_content = storage_manager.retrieve_content_by_certification(
            CertificationType.SAA,
            limit=10
        )
        
        print(f"✓ Found {len(saa_content)} SAA content items:")
        for content in saa_content:
            print(f"  - {content.title} (v{content.version})")
    except Exception as e:
        print(f"✗ Error querying content by certification: {e}")
    
    print("\n" + "=" * 50)
    print("Example completed!")


if __name__ == '__main__':
    main()