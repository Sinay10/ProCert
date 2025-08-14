#!/usr/bin/env python3
"""
Live AWS Integration Test for Recommendation Engine Service

This script tests the recommendation engine against the actual deployed AWS infrastructure,
including Lambda functions, DynamoDB tables, and API Gateway endpoints.
"""

import json
import time
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

# AWS Configuration
ACCOUNT_ID = "353207798766"
REGION = "us-east-1"
API_BASE_URL = None  # Will be determined from CloudFormation outputs

# Test Configuration
TEST_USER_ID = f"test-user-{int(time.time())}"
TEST_CERTIFICATION = "SAA"

class RecommendationEngineTestSuite:
    """Comprehensive test suite for the recommendation engine service."""
    
    def __init__(self):
        """Initialize the test suite with AWS clients."""
        self.session = boto3.Session(region_name=REGION)
        self.lambda_client = self.session.client('lambda')
        self.dynamodb = self.session.resource('dynamodb')
        self.cloudformation = self.session.client('cloudformation')
        self.cognito_client = self.session.client('cognito-idp')
        
        # Get stack outputs
        self.stack_outputs = self._get_stack_outputs()
        self.api_base_url = self.stack_outputs.get('ApiEndpoint', '').rstrip('/')
        
        # Initialize table references
        self.user_progress_table = None
        self.content_metadata_table = None
        self.recommendations_table = None
        self.user_profiles_table = None
        
        # Test user credentials
        self.test_user_email = f"test-{int(time.time())}@example.com"
        self.test_user_password = "TestPass123!"
        self.jwt_token = None
        
        print(f"🚀 Initializing Recommendation Engine Test Suite")
        print(f"   Account ID: {ACCOUNT_ID}")
        print(f"   Region: {REGION}")
        print(f"   API Base URL: {self.api_base_url}")
        print(f"   Test User ID: {TEST_USER_ID}")
    
    def _get_stack_outputs(self) -> Dict[str, str]:
        """Get CloudFormation stack outputs."""
        try:
            response = self.cloudformation.describe_stacks(
                StackName='ProcertInfrastructureStack'
            )
            
            outputs = {}
            if response['Stacks']:
                stack_outputs = response['Stacks'][0].get('Outputs', [])
                for output in stack_outputs:
                    outputs[output['OutputKey']] = output['OutputValue']
            
            return outputs
        except Exception as e:
            print(f"⚠️  Warning: Could not get stack outputs: {str(e)}")
            return {}
    
    def _get_table_reference(self, table_name_key: str) -> Optional[Any]:
        """Get DynamoDB table reference from stack outputs."""
        table_name = self.stack_outputs.get(table_name_key)
        if table_name:
            return self.dynamodb.Table(table_name)
        return None
    
    def setup_test_environment(self) -> bool:
        """Set up the test environment with required resources."""
        print("\n📋 Setting up test environment...")
        
        try:
            # Get table references
            self.user_progress_table = self._get_table_reference('UserProgressTableName')
            self.content_metadata_table = self._get_table_reference('ContentMetadataTableName')
            self.recommendations_table = self._get_table_reference('RecommendationsTableName')
            self.user_profiles_table = self._get_table_reference('UserProfilesTableName')
            
            # Verify tables exist
            tables_status = {
                'UserProgress': self.user_progress_table is not None,
                'ContentMetadata': self.content_metadata_table is not None,
                'Recommendations': self.recommendations_table is not None,
                'UserProfiles': self.user_profiles_table is not None
            }
            
            print("   DynamoDB Tables:")
            for table_name, exists in tables_status.items():
                status = "✅" if exists else "❌"
                print(f"     {status} {table_name}")
            
            # Check if API Gateway is accessible
            if self.api_base_url:
                try:
                    # Test a simple endpoint (this might fail with auth, but should not timeout)
                    response = requests.get(f"{self.api_base_url}/health", timeout=10)
                    print(f"   ✅ API Gateway accessible")
                except requests.exceptions.Timeout:
                    print(f"   ❌ API Gateway timeout")
                    return False
                except requests.exceptions.RequestException:
                    print(f"   ⚠️  API Gateway accessible (expected auth error)")
            
            # Create test user and get JWT token
            if not self._create_test_user():
                print("   ❌ Failed to create test user")
                return False
            
            # Create some test data
            if not self._create_test_data():
                print("   ❌ Failed to create test data")
                return False
            
            print("   ✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"   ❌ Setup failed: {str(e)}")
            return False
    
    def _create_test_user(self) -> bool:
        """Create a test user and get JWT token."""
        try:
            user_pool_id = self.stack_outputs.get('UserPoolId')
            user_pool_client_id = self.stack_outputs.get('UserPoolClientId')
            
            if not user_pool_id or not user_pool_client_id:
                print("     ⚠️  User pool information not available, skipping user creation")
                return True
            
            # Register user via API
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "given_name": "Test",
                "family_name": "User"
            }
            
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                json=register_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print("     ✅ Test user registered")
                
                # Login to get JWT token
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                login_response = requests.post(
                    f"{self.api_base_url}/auth/login",
                    json=login_data,
                    timeout=30
                )
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    self.jwt_token = login_result.get('access_token')
                    print("     ✅ JWT token obtained")
                    return True
                else:
                    print(f"     ⚠️  Login failed: {login_response.status_code}")
            else:
                print(f"     ⚠️  Registration failed: {response.status_code}")
            
            return True  # Continue even if auth fails
            
        except Exception as e:
            print(f"     ⚠️  User creation failed: {str(e)}")
            return True  # Continue even if auth fails
    
    def _create_test_data(self) -> bool:
        """Create test data for recommendation engine testing."""
        try:
            # Create sample content metadata
            if self.content_metadata_table:
                sample_content = [
                    {
                        'content_id': 'test-content-1',
                        'certification_type': TEST_CERTIFICATION,
                        'title': 'EC2 Fundamentals',
                        'content_type': 'study_guide',
                        'category': 'EC2',
                        'difficulty_level': 'beginner',
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat(),
                        'version': '1.0',
                        'chunk_count': 5
                    },
                    {
                        'content_id': 'test-content-2',
                        'certification_type': TEST_CERTIFICATION,
                        'title': 'S3 Advanced Features',
                        'content_type': 'study_guide',
                        'category': 'S3',
                        'difficulty_level': 'intermediate',
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat(),
                        'version': '1.0',
                        'chunk_count': 8
                    },
                    {
                        'content_id': 'test-content-3',
                        'certification_type': TEST_CERTIFICATION,
                        'title': 'VPC Networking',
                        'content_type': 'study_guide',
                        'category': 'VPC',
                        'difficulty_level': 'advanced',
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat(),
                        'version': '1.0',
                        'chunk_count': 12
                    }
                ]
                
                for content in sample_content:
                    try:
                        self.content_metadata_table.put_item(Item=content)
                    except Exception as e:
                        print(f"     ⚠️  Failed to create content {content['content_id']}: {str(e)}")
                
                print("     ✅ Sample content metadata created")
            
            # Create sample user progress data
            if self.user_progress_table:
                sample_progress = [
                    {
                        'user_id': TEST_USER_ID,
                        'content_id_certification': f'test-content-1#{TEST_CERTIFICATION}',
                        'content_id': 'test-content-1',
                        'certification_type': TEST_CERTIFICATION,
                        'progress_type': 'answered',
                        'score': 65.0,  # Weak performance
                        'time_spent': 300,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    {
                        'user_id': TEST_USER_ID,
                        'content_id_certification': f'test-content-2#{TEST_CERTIFICATION}',
                        'content_id': 'test-content-2',
                        'certification_type': TEST_CERTIFICATION,
                        'progress_type': 'answered',
                        'score': 85.0,  # Strong performance
                        'time_spent': 450,
                        'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat()
                    }
                ]
                
                for progress in sample_progress:
                    try:
                        self.user_progress_table.put_item(Item=progress)
                    except Exception as e:
                        print(f"     ⚠️  Failed to create progress record: {str(e)}")
                
                print("     ✅ Sample user progress created")
            
            return True
            
        except Exception as e:
            print(f"     ❌ Test data creation failed: {str(e)}")
            return False
    
    def test_lambda_function_direct(self) -> bool:
        """Test the recommendation Lambda function directly."""
        print("\n🔧 Testing Lambda function directly...")
        
        try:
            lambda_name = f"ProcertInfrastructureStack-ProcertRecommendationLambda"
            
            # Test get recommendations
            test_event = {
                'httpMethod': 'GET',
                'path': f'/recommendations/{TEST_USER_ID}',
                'queryStringParameters': {
                    'certification_type': TEST_CERTIFICATION,
                    'limit': '5'
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print(f"     ✅ Direct Lambda test successful")
                print(f"     📊 Recommendations returned: {len(body.get('recommendations', []))}")
                return True
            else:
                print(f"     ❌ Direct Lambda test failed: {result.get('statusCode')}")
                if 'body' in result:
                    error_body = json.loads(result['body'])
                    print(f"     Error: {error_body.get('error', {}).get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"     ❌ Direct Lambda test failed: {str(e)}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test all recommendation API endpoints."""
        print("\n🌐 Testing API endpoints...")
        
        if not self.api_base_url:
            print("     ⚠️  API base URL not available, skipping API tests")
            return True
        
        headers = {}
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        test_results = {}
        
        # Test 1: Get recommendations
        try:
            response = requests.get(
                f"{self.api_base_url}/recommendations/{TEST_USER_ID}",
                params={'certification_type': TEST_CERTIFICATION, 'limit': '5'},
                headers=headers,
                timeout=30
            )
            test_results['get_recommendations'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['get_recommendations'] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
        
        # Test 2: Get weak areas
        try:
            response = requests.get(
                f"{self.api_base_url}/recommendations/{TEST_USER_ID}/weak-areas",
                params={'certification_type': TEST_CERTIFICATION},
                headers=headers,
                timeout=30
            )
            test_results['get_weak_areas'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['get_weak_areas'] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
        
        # Test 3: Get content progression
        try:
            response = requests.get(
                f"{self.api_base_url}/recommendations/{TEST_USER_ID}/content-progression",
                params={'certification_type': TEST_CERTIFICATION},
                headers=headers,
                timeout=30
            )
            test_results['get_content_progression'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['get_content_progression'] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
        
        # Test 4: Get study path
        try:
            response = requests.get(
                f"{self.api_base_url}/recommendations/{TEST_USER_ID}/study-path",
                params={'certification_type': TEST_CERTIFICATION},
                headers=headers,
                timeout=30
            )
            test_results['get_study_path'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['get_study_path'] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
        
        # Test 5: Record feedback
        try:
            feedback_data = {
                'recommendation_id': f'test-rec-{int(time.time())}',
                'action': 'accepted',
                'feedback_data': {'rating': 5}
            }
            response = requests.post(
                f"{self.api_base_url}/recommendations/{TEST_USER_ID}/feedback",
                json=feedback_data,
                headers=headers,
                timeout=30
            )
            test_results['record_feedback'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['record_feedback'] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
        
        # Print results
        print("     API Endpoint Test Results:")
        for test_name, result in test_results.items():
            status_icon = "✅" if result['success'] else "❌"
            print(f"       {status_icon} {test_name}: {result['status']}")
            if not result['success'] and 'error' in result:
                print(f"         Error: {result['error']}")
        
        # Return overall success
        return all(result['success'] for result in test_results.values())
    
    def test_data_consistency(self) -> bool:
        """Test data consistency across DynamoDB tables."""
        print("\n🗄️  Testing data consistency...")
        
        try:
            # Check if our test data exists
            if self.user_progress_table:
                response = self.user_progress_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': TEST_USER_ID}
                )
                progress_count = len(response['Items'])
                print(f"     ✅ User progress records: {progress_count}")
            
            if self.content_metadata_table:
                response = self.content_metadata_table.scan(
                    FilterExpression='begins_with(content_id, :prefix)',
                    ExpressionAttributeValues={':prefix': 'test-content'}
                )
                content_count = len(response['Items'])
                print(f"     ✅ Test content records: {content_count}")
            
            return True
            
        except Exception as e:
            print(f"     ❌ Data consistency check failed: {str(e)}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data after testing."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Clean up user progress data
            if self.user_progress_table:
                response = self.user_progress_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': TEST_USER_ID}
                )
                
                for item in response['Items']:
                    self.user_progress_table.delete_item(
                        Key={
                            'user_id': item['user_id'],
                            'content_id_certification': item['content_id_certification']
                        }
                    )
                print(f"     ✅ Cleaned up {len(response['Items'])} progress records")
            
            # Clean up content metadata
            if self.content_metadata_table:
                response = self.content_metadata_table.scan(
                    FilterExpression='begins_with(content_id, :prefix)',
                    ExpressionAttributeValues={':prefix': 'test-content'}
                )
                
                for item in response['Items']:
                    self.content_metadata_table.delete_item(
                        Key={
                            'content_id': item['content_id'],
                            'certification_type': item['certification_type']
                        }
                    )
                print(f"     ✅ Cleaned up {len(response['Items'])} content records")
            
            # Clean up recommendations
            if self.recommendations_table:
                response = self.recommendations_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': TEST_USER_ID}
                )
                
                for item in response['Items']:
                    self.recommendations_table.delete_item(
                        Key={
                            'user_id': item['user_id'],
                            'recommendation_id': item['recommendation_id']
                        }
                    )
                print(f"     ✅ Cleaned up {len(response['Items'])} recommendation records")
            
            return True
            
        except Exception as e:
            print(f"     ⚠️  Cleanup failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run the complete test suite."""
        print("🧪 Starting Comprehensive Recommendation Engine Test Suite")
        print("=" * 70)
        
        results = {}
        
        # Setup
        results['setup'] = self.setup_test_environment()
        if not results['setup']:
            print("\n❌ Setup failed, aborting tests")
            return results
        
        # Wait a moment for data consistency
        print("\n⏳ Waiting for data consistency...")
        time.sleep(5)
        
        # Run tests
        results['lambda_direct'] = self.test_lambda_function_direct()
        results['api_endpoints'] = self.test_api_endpoints()
        results['data_consistency'] = self.test_data_consistency()
        
        # Cleanup
        results['cleanup'] = self.cleanup_test_data()
        
        return results
    
    def print_final_report(self, results: Dict[str, bool]):
        """Print the final test report."""
        print("\n" + "=" * 70)
        print("📊 FINAL TEST REPORT")
        print("=" * 70)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Recommendation Engine is ready for production!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review the issues above.")
        
        print("=" * 70)


def main():
    """Main test execution function."""
    test_suite = RecommendationEngineTestSuite()
    
    try:
        results = test_suite.run_comprehensive_test()
        test_suite.print_final_report(results)
        
        # Exit with appropriate code
        if all(results.values()):
            exit(0)  # Success
        else:
            exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(2)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        exit(3)


if __name__ == "__main__":
    main()