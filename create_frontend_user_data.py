#!/usr/bin/env python3

import boto3
import json
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

# The user ID from the frontend
USER_ID = "54c86428-a031-70d7-9559-b8fffd09eb1d"
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

def create_user_progress_data():
    """Create some initial progress data for the frontend user."""
    print(f"🔧 Creating progress data for user: {USER_ID}")
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
    
    # Create some sample progress entries
    progress_entries = [
        # EC2 performance (moderate)
        {
            'user_id': USER_ID,
            'content_id_certification': f'frontend-ec2-1#{USER_ID}#SAA',
            'content_id': f'frontend-ec2-1#{USER_ID}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('75.0'),
            'time_spent': 900,  # 15 minutes in seconds
            'timestamp': datetime.utcnow().isoformat()
        },
        # S3 performance (good)
        {
            'user_id': USER_ID,
            'content_id_certification': f'frontend-s3-1#{USER_ID}#SAA',
            'content_id': f'frontend-s3-1#{USER_ID}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('85.0'),
            'time_spent': 1200,  # 20 minutes in seconds
            'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
        },
        # Another S3 entry
        {
            'user_id': USER_ID,
            'content_id_certification': f'frontend-s3-2#{USER_ID}#SAA',
            'content_id': f'frontend-s3-2#{USER_ID}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('90.0'),
            'time_spent': 1000,
            'timestamp': datetime.utcnow().isoformat()
        },
        # VPC performance (needs improvement)
        {
            'user_id': USER_ID,
            'content_id_certification': f'frontend-vpc-1#{USER_ID}#SAA',
            'content_id': f'frontend-vpc-1#{USER_ID}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal('60.0'),
            'time_spent': 1800,  # 30 minutes in seconds
            'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat()
        }
    ]
    
    try:
        for entry in progress_entries:
            progress_table.put_item(Item=entry)
            print(f"   ✅ Created progress entry: {entry['content_id']} - {entry['score']}%")
        
        print(f"   ✅ Successfully created {len(progress_entries)} progress entries")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating progress data: {str(e)}")
        return False

def test_recommendations_after_data_creation():
    """Test the recommendations endpoint after creating data."""
    import requests
    
    print(f"\n🧪 Testing recommendations after data creation...")
    
    # We still need a valid JWT token, so let's create a test user and get their token
    # For now, let's just test if the user exists in the system
    
    API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    try:
        # This will still fail without auth, but we can see if the error changes
        response = requests.get(
            f"{API_BASE_URL}/recommendations/{USER_ID}",
            params={'certification_type': 'SAA', 'limit': '10'},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("🚀 Setting up frontend user data")
    print("=" * 50)
    
    success = create_user_progress_data()
    
    if success:
        test_recommendations_after_data_creation()
        
        print("\n" + "=" * 50)
        print("✅ User data created successfully!")
        print("The frontend should now be able to get recommendations")
        print("(assuming the JWT token is valid)")
    else:
        print("\n" + "=" * 50)
        print("❌ Failed to create user data")