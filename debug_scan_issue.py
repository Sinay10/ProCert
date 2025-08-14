#!/usr/bin/env python3
"""
Debug DynamoDB Scan Issue

This script specifically debugs why the DynamoDB scan is failing for some items.
"""

import boto3
import time
from datetime import datetime

# Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
TEST_USER_ID = f"scan-debug-{int(time.time())}"

def debug_scan_issue():
    """Debug the DynamoDB scan issue."""
    print("🔍 Debugging DynamoDB scan issue...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    content_table = dynamodb.Table(f'procert-content-metadata-{ACCOUNT_ID}')
    
    try:
        # Create a single test item first
        print("\n📝 Creating single test item...")
        
        test_content = {
            'content_id': f'scan-test-single-{TEST_USER_ID}',
            'certification_type': 'SAA',
            'title': 'Single Test Content',
            'content_type': 'study_guide',
            'category': 'TestCategory',
            'difficulty_level': 'beginner',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': 5
        }
        
        content_table.put_item(Item=test_content)
        print(f"   ✅ Created: {test_content['content_id']}")
        
        # Wait for consistency
        print("   ⏳ Waiting 2 seconds for consistency...")
        time.sleep(2)
        
        # Test different retrieval methods
        content_id = test_content['content_id']
        
        print(f"\n🔍 Testing retrieval methods for: {content_id}")
        
        # Method 1: Direct get_item
        print("   Method 1: Direct get_item")
        response = content_table.get_item(
            Key={
                'content_id': content_id,
                'certification_type': 'SAA'
            }
        )
        
        if 'Item' in response:
            print(f"      ✅ Found: {response['Item'].get('category', 'NO CATEGORY')}")
        else:
            print(f"      ❌ Not found")
        
        # Method 2: Scan with filter
        print("   Method 2: Scan with filter")
        response = content_table.scan(
            FilterExpression='content_id = :content_id',
            ExpressionAttributeValues={':content_id': content_id}
        )
        
        items = response.get('Items', [])
        print(f"      Found {len(items)} items")
        for item in items:
            print(f"         - {item.get('content_id', 'NO ID')}: {item.get('category', 'NO CATEGORY')}")
        
        # Method 3: Scan with filter and limit
        print("   Method 3: Scan with filter and limit=1")
        response = content_table.scan(
            FilterExpression='content_id = :content_id',
            ExpressionAttributeValues={':content_id': content_id},
            Limit=1
        )
        
        items = response.get('Items', [])
        print(f"      Found {len(items)} items")
        for item in items:
            print(f"         - {item.get('content_id', 'NO ID')}: {item.get('category', 'NO CATEGORY')}")
        
        # Now test with multiple items
        print(f"\n📝 Creating multiple test items...")
        
        content_items = []
        for i in range(1, 4):
            content = {
                'content_id': f'scan-test-multi-{i}-{TEST_USER_ID}',
                'certification_type': 'SAA',
                'title': f'Multi Test Content {i}',
                'content_type': 'study_guide',
                'category': 'MultiTestCategory',
                'difficulty_level': 'beginner',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'chunk_count': 5
            }
            content_items.append(content)
            content_table.put_item(Item=content)
            print(f"   ✅ Created: {content['content_id']}")
        
        # Wait for consistency
        print("   ⏳ Waiting 3 seconds for consistency...")
        time.sleep(3)
        
        # Test retrieval of each item
        print(f"\n🔍 Testing retrieval of multiple items...")
        
        for i, content in enumerate(content_items, 1):
            content_id = content['content_id']
            print(f"\n   Testing item {i}: {content_id}")
            
            # Direct get_item
            response = content_table.get_item(
                Key={
                    'content_id': content_id,
                    'certification_type': 'SAA'
                }
            )
            
            if 'Item' in response:
                print(f"      ✅ Direct get_item: {response['Item'].get('category', 'NO CATEGORY')}")
            else:
                print(f"      ❌ Direct get_item: Not found")
            
            # Scan with filter
            response = content_table.scan(
                FilterExpression='content_id = :content_id',
                ExpressionAttributeValues={':content_id': content_id},
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                print(f"      ✅ Scan: {items[0].get('category', 'NO CATEGORY')}")
            else:
                print(f"      ❌ Scan: Not found")
        
        # Check what's actually in the table
        print(f"\n🔍 Checking what's actually in the table...")
        
        response = content_table.scan(
            FilterExpression='begins_with(content_id, :prefix)',
            ExpressionAttributeValues={':prefix': f'scan-test-'}
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} items with scan-test prefix:")
        for item in items:
            print(f"      - {item.get('content_id', 'NO ID')}: {item.get('category', 'NO CATEGORY')}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        
        # Clean up single test item
        try:
            content_table.delete_item(Key={
                'content_id': test_content['content_id'],
                'certification_type': test_content['certification_type']
            })
        except Exception:
            pass
        
        # Clean up multiple test items
        for content in content_items:
            try:
                content_table.delete_item(Key={
                    'content_id': content['content_id'],
                    'certification_type': content['certification_type']
                })
            except Exception:
                pass
        
        print("   ✅ Cleanup complete")
        
    except Exception as e:
        print(f"   ❌ Debug failed: {str(e)}")

def main():
    """Run scan issue debugging."""
    print("🐛 Debugging DynamoDB Scan Issue")
    print("=" * 50)
    
    debug_scan_issue()
    
    print("\n" + "=" * 50)
    print("🔍 SCAN ISSUE DEBUG COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()