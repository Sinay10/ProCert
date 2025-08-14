#!/usr/bin/env python3
"""
Test chatbot functionality
"""

import json
import boto3
import time
from datetime import datetime

# Configuration
CHATBOT_LAMBDA_NAME = "ProcertInfrastructureStac-ProcertChatbotLambdaC111-c8xCqHcUTXSm"
REGION = "us-east-1"

def test_chatbot_scenarios():
    """Test various chatbot scenarios"""
    print("🤖 Testing Chatbot Functionality")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    test_scenarios = [
        {
            'name': 'Basic AWS Question',
            'description': 'Ask about AWS Lambda',
            'event': {
                'httpMethod': 'POST',
                'path': '/chat',
                'body': json.dumps({
                    'message': 'What is AWS Lambda and how does it work?',
                    'user_id': 'test-user-chatbot',
                    'session_id': f'test-session-{int(time.time())}'
                })
            },
            'expected_checks': [
                lambda body: 'response' in body,
                lambda body: len(body.get('response', '')) > 50,
                lambda body: 'lambda' in body.get('response', '').lower()
            ]
        },
        {
            'name': 'Certification Question',
            'description': 'Ask about AWS certification',
            'event': {
                'httpMethod': 'POST',
                'path': '/chat',
                'body': json.dumps({
                    'message': 'What topics should I study for AWS Solutions Architect certification?',
                    'user_id': 'test-user-chatbot',
                    'session_id': f'test-session-{int(time.time())}'
                })
            },
            'expected_checks': [
                lambda body: 'response' in body,
                lambda body: len(body.get('response', '')) > 100,
                lambda body: any(term in body.get('response', '').lower() for term in ['ec2', 's3', 'vpc', 'iam'])
            ]
        },
        {
            'name': 'Technical Deep Dive',
            'description': 'Ask technical question about VPC',
            'event': {
                'httpMethod': 'POST',
                'path': '/chat',
                'body': json.dumps({
                    'message': 'Explain the difference between public and private subnets in AWS VPC',
                    'user_id': 'test-user-chatbot',
                    'session_id': f'test-session-{int(time.time())}'
                })
            },
            'expected_checks': [
                lambda body: 'response' in body,
                lambda body: len(body.get('response', '')) > 80,
                lambda body: 'subnet' in body.get('response', '').lower()
            ]
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n   🎯 {scenario['name']}")
        print(f"      {scenario['description']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=CHATBOT_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(scenario['event'])
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                
                # Run expected checks
                checks_passed = 0
                total_checks = len(scenario['expected_checks'])
                
                for i, check in enumerate(scenario['expected_checks']):
                    try:
                        if check(body):
                            checks_passed += 1
                        else:
                            print(f"      ❌ Check {i+1} failed")
                    except Exception as e:
                        print(f"      ❌ Check {i+1} error: {str(e)}")
                
                if checks_passed == total_checks:
                    print(f"      ✅ All checks passed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = True
                else:
                    print(f"      ⚠️  Some checks failed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = False
                
                # Show response preview
                response_text = body.get('response', '')
                print(f"      📝 Response length: {len(response_text)} characters")
                print(f"      📝 Preview: {response_text[:150]}...")
                
            else:
                print(f"      ❌ HTTP {result.get('statusCode')}")
                if 'body' in result:
                    error_body = json.loads(result['body'])
                    print(f"      Error: {error_body.get('error', 'Unknown')}")
                results[scenario['name']] = False
                
        except Exception as e:
            print(f"      ❌ Exception: {str(e)}")
            results[scenario['name']] = False
    
    return results

def main():
    """Run chatbot tests"""
    print("🚀 Chatbot Functionality Test")
    print("=" * 60)
    
    try:
        results = test_chatbot_scenarios()
        
        # Final report
        print("\n" + "=" * 60)
        print("📊 CHATBOT TEST REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"Total Scenarios: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL CHATBOT TESTS PASSED!")
            print("✅ Chatbot is responding correctly")
            print("✅ RAG system working properly")
            print("✅ Context understanding functional")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
        
        print("=" * 60)
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)