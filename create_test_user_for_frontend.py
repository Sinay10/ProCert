#!/usr/bin/env python3

import requests
import boto3
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

# Test user credentials
TEST_EMAIL = "demo.user@procert.test"
TEST_PASSWORD = "TestUser123!"
TEST_FIRST_NAME = "Demo"
TEST_LAST_NAME = "User"

def create_test_user():
    """Create a test user account through the registration API."""
    print("🔧 Creating test user account...")
    print(f"   Email: {TEST_EMAIL}")
    print(f"   Password: {TEST_PASSWORD}")
    
    try:
        # Register the user
        register_response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": f"{TEST_FIRST_NAME} {TEST_LAST_NAME}"
            },
            timeout=30
        )
        
        if register_response.status_code in [200, 201]:
            print("   ✅ User registered successfully")
        elif register_response.status_code in [400, 409] and ("already exists" in register_response.text or "User already exists" in register_response.text):
            print("   ℹ️  User already exists, proceeding with login")
        else:
            print(f"   ❌ Registration failed: {register_response.status_code}")
            print(f"   Response: {register_response.text}")
            return None, None
        
        # Login to get JWT token and user ID
        print("   🔑 Logging in to get JWT token...")
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            user_id = login_data.get('user_id')
            jwt_token = login_data.get('tokens', {}).get('access_token')
            
            print(f"   ✅ Login successful!")
            print(f"   User ID: {user_id}")
            print(f"   JWT Token: {'Yes' if jwt_token else 'No'}")
            
            return user_id, jwt_token
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Error creating user: {str(e)}")
        return None, None

def create_realistic_study_data(user_id):
    """Create realistic study progress data for the test user."""
    print(f"\n📚 Creating realistic study data for user: {user_id}")
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
    
    # Create diverse progress data across different AWS services
    progress_entries = []
    
    # EC2 - Mixed performance (some weak areas)
    ec2_scores = [65, 70, 55, 75, 60, 80]  # Average ~67% (needs improvement)
    for i, score in enumerate(ec2_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-ec2-{i+1}#{user_id}#SAA',
            'content_id': f'demo-ec2-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(300, 1200),  # 5-20 minutes
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 14))).isoformat()
        })
    
    # S3 - Strong performance
    s3_scores = [85, 90, 88, 92, 87, 95]  # Average ~89% (strong area)
    for i, score in enumerate(s3_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-s3-{i+1}#{user_id}#SAA',
            'content_id': f'demo-s3-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(240, 900),
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 10))).isoformat()
        })
    
    # VPC - Weak area (needs significant improvement)
    vpc_scores = [45, 50, 40, 55, 48, 52]  # Average ~48% (weak area)
    for i, score in enumerate(vpc_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-vpc-{i+1}#{user_id}#SAA',
            'content_id': f'demo-vpc-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(600, 1800),  # Longer time (struggling)
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
        })
    
    # IAM - Moderate performance
    iam_scores = [72, 78, 70, 75, 73, 80]  # Average ~75% (decent)
    for i, score in enumerate(iam_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-iam-{i+1}#{user_id}#SAA',
            'content_id': f'demo-iam-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(360, 1080),
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 12))).isoformat()
        })
    
    # Lambda - Good performance (recent improvement)
    lambda_scores = [82, 85, 88, 90, 87]  # Average ~86% (improving)
    for i, score in enumerate(lambda_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-lambda-{i+1}#{user_id}#SAA',
            'content_id': f'demo-lambda-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(300, 900),
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 5))).isoformat()
        })
    
    # RDS - Needs work
    rds_scores = [58, 62, 55, 65, 60]  # Average ~60% (needs improvement)
    for i, score in enumerate(rds_scores):
        progress_entries.append({
            'user_id': user_id,
            'content_id_certification': f'demo-rds-{i+1}#{user_id}#SAA',
            'content_id': f'demo-rds-{i+1}#{user_id}',
            'certification_type': 'SAA',
            'progress_type': 'answered',
            'score': Decimal(str(score)),
            'time_spent': random.randint(480, 1440),
            'timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 8))).isoformat()
        })
    
    # Store all progress entries
    try:
        for entry in progress_entries:
            progress_table.put_item(Item=entry)
        
        print(f"   ✅ Created {len(progress_entries)} progress entries")
        print("   📊 Performance Summary:")
        print("      🟢 S3: ~89% (Strong - should get advanced content recommendations)")
        print("      🟢 Lambda: ~86% (Good - recent improvement)")
        print("      🟡 IAM: ~75% (Moderate)")
        print("      🟡 EC2: ~67% (Needs improvement)")
        print("      🟠 RDS: ~60% (Needs work)")
        print("      🔴 VPC: ~48% (Weak area - should get focused recommendations)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating progress data: {str(e)}")
        return False

def test_recommendations_with_auth(user_id, jwt_token):
    """Test the recommendation endpoints with the new user."""
    print(f"\n🧪 Testing recommendation endpoints...")
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    test_endpoints = [
        {
            'name': 'Get Recommendations',
            'url': f"{API_BASE_URL}/recommendations/{user_id}",
            'params': {'certification_type': 'SAA', 'limit': '10'}
        },
        {
            'name': 'Get Study Path',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/study-path",
            'params': {'certification_type': 'SAA'}
        },
        {
            'name': 'Get Weak Areas',
            'url': f"{API_BASE_URL}/recommendations/{user_id}/weak-areas",
            'params': {'certification_type': 'SAA'}
        }
    ]
    
    results = []
    for endpoint in test_endpoints:
        try:
            response = requests.get(
                endpoint['url'],
                params=endpoint.get('params', {}),
                headers=headers,
                timeout=15
            )
            
            print(f"   🧪 {endpoint['name']}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'recommendations' in data:
                    recs = data.get('recommendations', [])
                    print(f"      ✅ {len(recs)} recommendations generated")
                    for i, rec in enumerate(recs[:3]):
                        print(f"         {i+1}. {rec.get('type', 'unknown')} - Priority: {rec.get('priority', 'unknown')}")
                elif 'study_path' in data:
                    path = data.get('study_path', {})
                    phases = path.get('phases', [])
                    print(f"      ✅ Study path with {len(phases)} phases")
                elif 'weak_areas' in data:
                    weak_areas = data.get('weak_areas', [])
                    print(f"      ✅ {len(weak_areas)} weak areas identified")
                
                results.append(True)
            else:
                print(f"      ❌ Failed: {response.text}")
                results.append(False)
                
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            results.append(False)
    
    return all(results)

def main():
    print("🚀 Creating Test User for Frontend Recommendation Testing")
    print("=" * 60)
    
    # Step 1: Create user account
    user_id, jwt_token = create_test_user()
    if not user_id or not jwt_token:
        print("\n❌ Failed to create test user")
        return
    
    # Step 2: Wait a moment for user creation to propagate
    print("\n⏳ Waiting for user creation to propagate...")
    time.sleep(3)
    
    # Step 3: Create study data
    if not create_realistic_study_data(user_id):
        print("\n❌ Failed to create study data")
        return
    
    # Step 4: Wait for data consistency
    print("\n⏳ Waiting for data consistency...")
    time.sleep(5)
    
    # Step 5: Test the endpoints
    api_success = test_recommendations_with_auth(user_id, jwt_token)
    
    # Step 6: Provide instructions
    print("\n" + "=" * 60)
    print("✅ TEST USER CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📧 Email: {TEST_EMAIL}")
    print(f"🔑 Password: {TEST_PASSWORD}")
    print(f"🆔 User ID: {user_id}")
    print(f"🌐 API Status: {'✅ Working' if api_success else '⚠️  Partial'}")
    
    print("\n📋 TESTING INSTRUCTIONS:")
    print("1. Go to your website and sign in with the credentials above")
    print("2. Navigate to the 'Study Path' page")
    print("3. You should see personalized recommendations based on:")
    print("   • VPC networking (weak area - ~48% avg)")
    print("   • RDS databases (needs improvement - ~60% avg)")
    print("   • EC2 compute (moderate - ~67% avg)")
    print("   • S3 storage (strong area - ~89% avg)")
    print("4. The study path should show a progression from weak to strong areas")
    print("5. Try different certification types in the dropdown")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("• Should see 'review' recommendations for VPC (weak area)")
    print("• Should see 'content' recommendations for RDS improvement")
    print("• Should see 'advanced' recommendations for S3 (strong area)")
    print("• Study path should prioritize VPC and RDS topics first")
    print("• Analytics should show clear strengths/weaknesses breakdown")
    
    if not api_success:
        print("\n⚠️  Note: Some API endpoints may need a few minutes to fully activate.")
        print("   If you see mock data initially, try refreshing after 2-3 minutes.")

if __name__ == "__main__":
    main()