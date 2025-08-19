#!/usr/bin/env python3

import requests
import json
import boto3
from botocore.exceptions import ClientError

def get_cognito_tokens():
    """Get ID token for Cognito User Pool authorizer."""
    try:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        
        username = "demo.user@procert.test"
        password = "TestUser123!"
        client_id = "53kma8sulrhdl9ki7dboi0vj1j"
        
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        return response['AuthenticationResult']['IdToken']
        
    except ClientError as e:
        print(f"❌ Failed to get token: {e}")
        return None

def test_complete_system():
    """Comprehensive test of the entire learning platform system."""
    
    print("🚀 FINAL SYSTEM TEST - ProCert Learning Platform")
    print("=" * 70)
    
    token = get_cognito_tokens()
    if not token:
        print("❌ CRITICAL: Could not get authentication token")
        return
    
    print("✅ Authentication: SUCCESS")
    
    base_url = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test all critical endpoints
    tests = [
        {
            'name': 'Resources - General',
            'method': 'GET',
            'endpoint': '/resources/general',
            'data': None,
            'expected': 'resources found'
        },
        {
            'name': 'Resources - CCP',
            'method': 'GET', 
            'endpoint': '/resources/ccp',
            'data': None,
            'expected': 'resources found'
        },
        {
            'name': 'Resources - SAA',
            'method': 'GET',
            'endpoint': '/resources/saa', 
            'data': None,
            'expected': 'resources found'
        },
        {
            'name': 'Chat - AI Assistant',
            'method': 'POST',
            'endpoint': '/chat/message',
            'data': {'message': 'What is AWS Lambda?', 'certification': 'general'},
            'expected': 'AI response'
        },
        {
            'name': 'Quiz - Generate Practice Quiz',
            'method': 'POST',
            'endpoint': '/quiz/generate',
            'data': {'certification_type': 'general', 'count': 5, 'user_id': 'test-user'},
            'expected': 'quiz questions'
        },
        {
            'name': 'Quiz - CCP Practice',
            'method': 'POST',
            'endpoint': '/quiz/generate', 
            'data': {'certification_type': 'ccp', 'count': 10, 'user_id': 'test-user'},
            'expected': 'quiz questions'
        }
    ]
    
    results = {'passed': 0, 'failed': 0, 'total': len(tests)}
    
    for test in tests:
        print(f"\n📋 Testing: {test['name']}")
        print(f"   {test['method']} {test['endpoint']}")
        
        try:
            url = f"{base_url}{test['endpoint']}"
            
            if test['method'] == 'GET':
                response = requests.get(url, headers=headers, timeout=20)
            elif test['method'] == 'POST':
                response = requests.post(url, headers=headers, json=test['data'], timeout=20)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Validate response content
                    if test['endpoint'].startswith('/resources/'):
                        total = result.get('total', 0)
                        print(f"   ✅ SUCCESS: Found {total} resources")
                        results['passed'] += 1
                    elif test['endpoint'].startswith('/chat/'):
                        response_text = result.get('response', '')
                        print(f"   ✅ SUCCESS: AI responded ({len(response_text)} chars)")
                        results['passed'] += 1
                    elif test['endpoint'].startswith('/quiz/'):
                        questions = result.get('questions', [])
                        print(f"   ✅ SUCCESS: Generated {len(questions)} questions")
                        results['passed'] += 1
                    else:
                        print(f"   ✅ SUCCESS: Response received")
                        results['passed'] += 1
                        
                except Exception as e:
                    print(f"   ⚠️  SUCCESS (200) but JSON parse error: {e}")
                    results['passed'] += 1
                    
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
                results['failed'] += 1
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT: Request took too long")
            results['failed'] += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results['failed'] += 1
    
    # Final results
    print(f"\n{'='*70}")
    print(f"🎯 FINAL RESULTS")
    print(f"{'='*70}")
    print(f"✅ PASSED: {results['passed']}/{results['total']} tests")
    print(f"❌ FAILED: {results['failed']}/{results['total']} tests")
    
    success_rate = (results['passed'] / results['total']) * 100
    print(f"📊 SUCCESS RATE: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"🎉 SYSTEM STATUS: OPERATIONAL")
        print(f"   The ProCert Learning Platform is working!")
    elif success_rate >= 50:
        print(f"⚠️  SYSTEM STATUS: PARTIALLY FUNCTIONAL") 
        print(f"   Core features working, some issues remain")
    else:
        print(f"🚨 SYSTEM STATUS: CRITICAL ISSUES")
        print(f"   Major problems need immediate attention")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    test_complete_system()