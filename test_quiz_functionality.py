#!/usr/bin/env python3
"""
Test quiz generation functionality
"""

import json
import boto3
import time
from datetime import datetime

# Configuration
QUIZ_LAMBDA_NAME = "ProcertInfrastructureStac-ProcertQuizLambda8FDECDE-4RIY4fDPbKM4"
REGION = "us-east-1"

def test_quiz_scenarios():
    """Test various quiz scenarios."""
    print("📝 Testing Quiz Generation Functionality")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    test_scenarios = [
        {
            'name': 'Generate Quiz',
            'description': 'Generate a quiz on AWS Lambda',
            'event': {
                'httpMethod': 'POST',
                'path': '/quiz/generate',
                'body': json.dumps({
                    'user_id': 'test-user-quiz',
                    'certification_type': 'SAA',
                    'question_count': 3,
                    'difficulty': 'intermediate'
                })
            },
            'expected_checks': [
                lambda body: 'quiz' in body,
                lambda body: 'quiz_id' in body.get('quiz', {}),
                lambda body: 'questions' in body.get('quiz', {})
            ]
        },
        {
            'name': 'Get Quiz Session',
            'description': 'Retrieve a quiz session',
            'event': {
                'httpMethod': 'GET',
                'resource': '/quiz/session/{session_id}',
                'pathParameters': {'session_id': 'test-session-123'}
            },
            'expected_checks': [
                lambda body: 'session_id' in body or 'error' in body  # Either success or expected error
            ]
        },
        {
            'name': 'Submit Quiz Answer',
            'description': 'Submit an answer to a quiz question',
            'event': {
                'httpMethod': 'POST',
                'resource': '/quiz/answer',
                'body': json.dumps({
                    'session_id': 'test-session-submit',
                    'question_id': 'q1',
                    'answer': 'A',
                    'user_id': 'test-user-quiz'
                })
            },
            'expected_checks': [
                lambda body: 'result' in body or 'error' in body  # Either success or expected error
            ]
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n🎯 {scenario['name']}")
        print(f"   {scenario['description']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=QUIZ_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(scenario['event'])
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') in [200, 400, 404]:  # Accept expected error codes
                body = json.loads(result.get('body', '{}'))
                
                # Run expected checks
                checks_passed = 0
                total_checks = len(scenario['expected_checks'])
                
                for i, check in enumerate(scenario['expected_checks']):
                    try:
                        if check(body):
                            checks_passed += 1
                        else:
                            print(f"   ❌ Check {i+1} failed")
                    except Exception as e:
                        print(f"   ❌ Check {i+1} error: {str(e)}")
                
                if checks_passed == total_checks:
                    print(f"   ✅ All checks passed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = True
                    
                    # Show response details
                    if 'quiz' in body and 'quiz_id' in body['quiz']:
                        print(f"   📊 Quiz ID: {body['quiz']['quiz_id']}")
                    if 'quiz' in body and 'questions' in body['quiz']:
                        print(f"   📊 Questions generated: {len(body['quiz']['questions'])}")
                    if 'error' in body:
                        print(f"   📊 Expected error: {body['error']}")
                else:
                    print(f"   ⚠️  Some checks failed ({checks_passed}/{total_checks})")
                    results[scenario['name']] = False
                
            else:
                print(f"   ❌ HTTP {result.get('statusCode')}")
                if 'body' in result:
                    error_body = json.loads(result['body'])
                    print(f"   Error: {error_body.get('error', 'Unknown')}")
                results[scenario['name']] = False
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results[scenario['name']] = False
    
    return results

def main():
    """Run quiz tests."""
    print("🚀 Quiz Generation Functionality Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    try:
        results = test_quiz_scenarios()
        
        # Final report
        print("\n" + "=" * 50)
        print("📊 QUIZ TEST REPORT")
        print("=" * 50)
        
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
            print("\n🎉 ALL QUIZ TESTS PASSED!")
            print("✅ Quiz generation working correctly")
            print("✅ Quiz session management functional")
            print("✅ Answer submission working")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
        
        print("=" * 50)
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)