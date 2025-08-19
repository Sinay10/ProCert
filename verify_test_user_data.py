#!/usr/bin/env python3

import requests
import boto3
import json
import time
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"

# Test user credentials
TEST_EMAIL = "demo.user@procert.test"
TEST_PASSWORD = "TestUser123!"
USER_ID = "d4384468-f001-70d2-7965-7315969fa3e1"

def get_jwt_token():
    """Get JWT token for the test user."""
    try:
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
            return login_data.get('tokens', {}).get('access_token')
        else:
            print(f"Login failed: {login_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return None

def verify_progress_data():
    """Verify that progress data exists in DynamoDB."""
    print("🔍 Verifying progress data in DynamoDB...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        progress_table = dynamodb.Table(f'procert-user-progress-{ACCOUNT_ID}')
        
        # Query for user's progress data
        response = progress_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(USER_ID)
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} progress records")
        
        if items:
            # Group by service and calculate averages
            services = {}
            for item in items:
                content_id = item.get('content_id', '')
                score = float(item.get('score', 0))
                
                # Extract service name from content_id
                service = 'unknown'
                if 'ec2' in content_id.lower():
                    service = 'EC2'
                elif 's3' in content_id.lower():
                    service = 'S3'
                elif 'vpc' in content_id.lower():
                    service = 'VPC'
                elif 'iam' in content_id.lower():
                    service = 'IAM'
                elif 'lambda' in content_id.lower():
                    service = 'Lambda'
                elif 'rds' in content_id.lower():
                    service = 'RDS'
                
                if service not in services:
                    services[service] = []
                services[service].append(score)
            
            print("   📊 Performance by service:")
            for service, scores in services.items():
                avg_score = sum(scores) / len(scores)
                print(f"      {service}: {avg_score:.1f}% (from {len(scores)} records)")
        
        return len(items) > 0
        
    except Exception as e:
        print(f"   ❌ Error verifying data: {str(e)}")
        return False

def test_recommendations_detailed(jwt_token):
    """Test recommendations with detailed output."""
    print("\n🧪 Testing recommendation endpoints with detailed output...")
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    # Test recommendations
    try:
        print("   📋 Testing Get Recommendations...")
        response = requests.get(
            f"{API_BASE_URL}/recommendations/{USER_ID}",
            params={'certification_type': 'SAA', 'limit': '10'},
            headers=headers,
            timeout=15
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"      Recommendations: {len(recommendations)}")
            
            if recommendations:
                for i, rec in enumerate(recommendations):
                    print(f"         {i+1}. Type: {rec.get('type')}")
                    print(f"            Priority: {rec.get('priority')}")
                    print(f"            Reasoning: {rec.get('reasoning', 'No reasoning')[:100]}...")
            else:
                print("      ⚠️  No recommendations generated")
                print("      This might indicate:")
                print("         - Data needs more time to process")
                print("         - Recommendation algorithm needs adjustment")
                print("         - Missing content metadata")
        else:
            print(f"      ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"      ❌ Error: {str(e)}")
    
    # Test weak areas
    try:
        print("\n   🎯 Testing Get Weak Areas...")
        response = requests.get(
            f"{API_BASE_URL}/recommendations/{USER_ID}/weak-areas",
            params={'certification_type': 'SAA'},
            headers=headers,
            timeout=15
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            weak_areas = data.get('weak_areas', [])
            print(f"      Weak areas: {len(weak_areas)}")
            
            for area in weak_areas[:5]:  # Show first 5
                print(f"         - {area}")
        else:
            print(f"      ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"      ❌ Error: {str(e)}")

def wait_and_retry_recommendations(jwt_token, max_attempts=3):
    """Wait and retry recommendations to see if they get generated."""
    print(f"\n⏳ Waiting for recommendation algorithm to process data...")
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    for attempt in range(max_attempts):
        print(f"\n   Attempt {attempt + 1}/{max_attempts}")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/recommendations/{USER_ID}",
                params={'certification_type': 'SAA', 'limit': '10'},
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                if recommendations:
                    print(f"   ✅ Success! Generated {len(recommendations)} recommendations")
                    for i, rec in enumerate(recommendations[:3]):
                        print(f"      {i+1}. {rec.get('type')} - Priority: {rec.get('priority')}")
                        print(f"         {rec.get('reasoning', 'No reasoning')[:80]}...")
                    return True
                else:
                    print(f"   ⏳ Still no recommendations, waiting 10 seconds...")
                    if attempt < max_attempts - 1:
                        time.sleep(10)
            else:
                print(f"   ❌ API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    print("   ⚠️  No recommendations generated after all attempts")
    return False

def main():
    print("🔍 Verifying Test User Data and Recommendations")
    print("=" * 60)
    
    # Step 1: Get JWT token
    jwt_token = get_jwt_token()
    if not jwt_token:
        print("❌ Failed to get JWT token")
        return
    
    print("✅ JWT token obtained")
    
    # Step 2: Verify progress data exists
    if not verify_progress_data():
        print("❌ No progress data found")
        return
    
    # Step 3: Test recommendations immediately
    test_recommendations_detailed(jwt_token)
    
    # Step 4: Wait and retry if no recommendations
    success = wait_and_retry_recommendations(jwt_token)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RECOMMENDATIONS ARE WORKING!")
        print("You can now test the frontend with:")
        print(f"📧 Email: {TEST_EMAIL}")
        print(f"🔑 Password: {TEST_PASSWORD}")
    else:
        print("⚠️  RECOMMENDATIONS NOT GENERATING YET")
        print("This could be normal - the algorithm might need more time.")
        print("You can still test the frontend, which will show mock data")
        print("and you can see the real data structure.")
        print(f"📧 Email: {TEST_EMAIL}")
        print(f"🔑 Password: {TEST_PASSWORD}")

if __name__ == "__main__":
    main()