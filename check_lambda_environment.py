#!/usr/bin/env python3
"""
Check the Lambda function's environment variables and configuration.
"""

import json
import boto3

def check_lambda_environment():
    """Check the quiz Lambda function's environment and configuration."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = "ProcertInfrastructureStac-ProcertQuizLambda8FDECDE-4RIY4fDPbKM4"
    
    try:
        # Get function configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print("🔍 Quiz Lambda Configuration")
        print("=" * 40)
        print(f"Function Name: {response['FunctionName']}")
        print(f"Runtime: {response['Runtime']}")
        print(f"Handler: {response['Handler']}")
        print(f"Timeout: {response['Timeout']} seconds")
        print(f"Memory: {response['MemorySize']} MB")
        
        # Check environment variables
        env_vars = response.get('Environment', {}).get('Variables', {})
        print(f"\n📋 Environment Variables ({len(env_vars)} total):")
        
        expected_vars = [
            'QUIZ_SESSIONS_TABLE',
            'USER_PROGRESS_TABLE', 
            'CONTENT_METADATA_TABLE',
            'OPENSEARCH_ENDPOINT',
            'OPENSEARCH_INDEX',
            'AWS_REGION'
        ]
        
        for var in expected_vars:
            value = env_vars.get(var, 'NOT SET')
            status = "✅" if var in env_vars else "❌"
            print(f"  {status} {var}: {value}")
        
        # Check if there are any other environment variables
        other_vars = {k: v for k, v in env_vars.items() if k not in expected_vars}
        if other_vars:
            print(f"\n📋 Other Environment Variables:")
            for key, value in other_vars.items():
                print(f"  • {key}: {value}")
        
        # Check IAM role and permissions
        role_arn = response.get('Role')
        print(f"\n🔐 IAM Role: {role_arn}")
        
        # Test a simple invocation to see if it works
        print(f"\n🧪 Testing Simple Lambda Invocation...")
        
        test_event = {
            'httpMethod': 'GET',
            'path': '/quiz/test',
            'requestContext': {
                'authorizer': {
                    'user_id': 'test-user-env-check'
                }
            }
        }
        
        invoke_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(invoke_response['Payload'].read())
        print(f"  Status Code: {invoke_response['StatusCode']}")
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            print(f"  Response: {body}")
        else:
            print(f"  Raw Response: {result}")
        
    except Exception as e:
        print(f"❌ Error checking Lambda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_lambda_environment()