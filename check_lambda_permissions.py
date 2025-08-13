#!/usr/bin/env python3
"""
Check Lambda function permissions to see if API Gateway can invoke it.
"""

import boto3
import json

def check_lambda_permissions():
    """Check Lambda function permissions."""
    print("🔐 Checking Lambda Function Permissions...")
    
    lambda_client = boto3.client('lambda')
    
    # Find the quiz Lambda function
    functions = lambda_client.list_functions()['Functions']
    quiz_function = None
    profile_function = None
    
    for func in functions:
        if 'QuizLambda' in func['FunctionName']:
            quiz_function = func['FunctionName']
        elif 'UserProfileLambda' in func['FunctionName']:
            profile_function = func['FunctionName']
    
    if not quiz_function:
        print("❌ Quiz Lambda function not found!")
        return
    
    print(f"Found Quiz Lambda function: {quiz_function}")
    if profile_function:
        print(f"Found Profile Lambda function: {profile_function}")
    
    # Check permissions for both functions
    for func_name, func_type in [(quiz_function, "Quiz"), (profile_function, "Profile")]:
        if not func_name:
            continue
            
        print(f"\n📋 Checking {func_type} Lambda permissions...")
        
        try:
            # Get the function policy
            policy_response = lambda_client.get_policy(FunctionName=func_name)
            policy = json.loads(policy_response['Policy'])
            
            print(f"   Policy found with {len(policy.get('Statement', []))} statements:")
            
            for i, statement in enumerate(policy.get('Statement', [])):
                print(f"   Statement {i+1}:")
                print(f"      Effect: {statement.get('Effect')}")
                print(f"      Principal: {statement.get('Principal')}")
                print(f"      Action: {statement.get('Action')}")
                print(f"      Resource: {statement.get('Resource')}")
                
                # Check if this is an API Gateway permission
                if 'apigateway' in str(statement.get('Principal', '')):
                    print(f"      ✅ API Gateway permission found")
                else:
                    print(f"      ⚠️  Not an API Gateway permission")
                    
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"   ❌ No resource policy found for {func_type} Lambda!")
        except Exception as e:
            print(f"   ❌ Error checking {func_type} Lambda permissions: {e}")

if __name__ == "__main__":
    check_lambda_permissions()