#!/usr/bin/env python3
"""
Comprehensive system testing for ProCert Learning Platform
Tests individual AWS components when API Gateway is not accessible
"""

import boto3
import json
import time
from datetime import datetime
import uuid

class ProCertSystemTester:
    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp')
        self.lambda_client = boto3.client('lambda')
        self.dynamodb = boto3.resource('dynamodb')
        self.s3_client = boto3.client('s3')
        
        # Configuration (update these with your actual resource names)
        self.user_pool_id = None  # Will be discovered
        self.client_id = None     # Will be discovered
        self.bucket_name = None   # Will be discovered
        
    def discover_resources(self):
        """Discover AWS resources for testing"""
        print("🔍 Discovering AWS resources...")
        
        try:
            # Find Cognito User Pool
            user_pools = self.cognito_client.list_user_pools(MaxResults=50)
            for pool in user_pools['UserPools']:
                if 'procert' in pool['Name'].lower():
                    self.user_pool_id = pool['Id']
                    print(f"✅ Found User Pool: {pool['Name']} ({pool['Id']})")
                    break
            
            if self.user_pool_id:
                # Find User Pool Client
                clients = self.cognito_client.list_user_pool_clients(
                    UserPoolId=self.user_pool_id
                )
                if clients['UserPoolClients']:
                    self.client_id = clients['UserPoolClients'][0]['ClientId']
                    print(f"✅ Found User Pool Client: {self.client_id}")
            
            # List Lambda functions
            functions = self.lambda_client.list_functions()
            procert_functions = [f for f in functions['Functions'] 
                               if 'procert' in f['FunctionName'].lower()]
            print(f"✅ Found {len(procert_functions)} ProCert Lambda functions")
            for func in procert_functions:
                print(f"  - {func['FunctionName']}")
            
            # List DynamoDB tables
            tables = self.dynamodb.meta.client.list_tables()
            procert_tables = [t for t in tables['TableNames'] 
                            if 'procert' in t.lower()]
            print(f"✅ Found {len(procert_tables)} ProCert DynamoDB tables")
            for table in procert_tables:
                print(f"  - {table}")
                
        except Exception as e:
            print(f"❌ Error discovering resources: {str(e)}")
    
    def test_cognito_user_creation(self):
        """Test creating users directly in Cognito"""
        print("\n👤 Testing Cognito User Creation")
        
        if not self.user_pool_id:
            print("❌ User Pool ID not found")
            return False
        
        try:
            # Create a test user
            test_email = f"test.{int(time.time())}@example.com"
            
            response = self.cognito_client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=test_email,
                UserAttributes=[
                    {'Name': 'email', 'Value': test_email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'given_name', 'Value': 'Test'},
                    {'Name': 'family_name', 'Value': 'User'}
                ],
                TemporaryPassword='TempPass123!',
                MessageAction='SUPPRESS'
            )
            
            print(f"✅ Created user: {test_email}")
            print(f"User Status: {response['User']['UserStatus']}")
            
            # Set permanent password
            self.cognito_client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=test_email,
                Password='TestPass123!',
                Permanent=True
            )
            
            print("✅ Set permanent password")
            return True
            
        except Exception as e:
            print(f"❌ Cognito user creation failed: {str(e)}")
            return False
    
    def test_lambda_functions_directly(self):
        """Test Lambda functions by invoking them directly"""
        print("\n⚡ Testing Lambda Functions Directly")
        
        # Get actual function names
        try:
            functions = self.lambda_client.list_functions()
            procert_functions = [f for f in functions['Functions'] 
                               if 'procert' in f['FunctionName'].lower()]
            
            # Look for chat-related function
            chat_function = None
            for func in procert_functions:
                if 'chat' in func['FunctionName'].lower():
                    chat_function = func['FunctionName']
                    break
            
            if chat_function:
                print(f"Found chat function: {chat_function}")
                
                chat_payload = {
                    "body": json.dumps({
                        "message": "What is Amazon EC2?",
                        "certification": "SAA",
                        "user_id": "test-user"
                    }),
                    "headers": {"Content-Type": "application/json"}
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=chat_function,
                    Payload=json.dumps(chat_payload)
                )
                
                result = json.loads(response['Payload'].read())
                print(f"✅ Chat function invoked successfully")
                print(f"Status Code: {result.get('statusCode', 'Unknown')}")
                
                if 'body' in result:
                    body = json.loads(result['body'])
                    if 'response' in body:
                        print(f"Response preview: {body['response'][:100]}...")
            else:
                print("⚠️ No chat function found")
                print("Available functions:")
                for func in procert_functions:
                    print(f"  - {func['FunctionName']}")
            
        except Exception as e:
            print(f"❌ Lambda function test failed: {str(e)}")
    
    def test_dynamodb_tables(self):
        """Test DynamoDB table access and operations"""
        print("\n🗄️ Testing DynamoDB Tables")
        
        try:
            # Get actual table names
            tables = self.dynamodb.meta.client.list_tables()
            procert_tables = [t for t in tables['TableNames'] 
                            if 'procert' in t.lower()]
            
            # Find user profiles table
            profiles_table_name = None
            for table_name in procert_tables:
                if 'user-profiles' in table_name:
                    profiles_table_name = table_name
                    break
            
            if profiles_table_name:
                print(f"Found user profiles table: {profiles_table_name}")
                profiles_table = self.dynamodb.Table(profiles_table_name)
                
                # Try to put a test profile
                test_profile = {
                    'user_id': f'test-user-{int(time.time())}',
                    'email': 'test@example.com',
                    'name': 'Test User',
                    'target_certifications': ['SAA'],
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                }
                
                profiles_table.put_item(Item=test_profile)
                print("✅ Successfully wrote to user profiles table")
                
                # Try to read it back
                response = profiles_table.get_item(
                    Key={'user_id': test_profile['user_id']}
                )
                
                if 'Item' in response:
                    print("✅ Successfully read from user profiles table")
                else:
                    print("⚠️ Could not read back the test profile")
            else:
                print("⚠️ No user profiles table found")
                print("Available tables:")
                for table in procert_tables:
                    print(f"  - {table}")
                
        except Exception as e:
            print(f"❌ DynamoDB test failed: {str(e)}")
    
    def test_s3_content_access(self):
        """Test S3 content bucket access"""
        print("\n📦 Testing S3 Content Access")
        
        try:
            # Find ProCert S3 buckets
            buckets = self.s3_client.list_buckets()
            procert_buckets = [b['Name'] for b in buckets['Buckets'] 
                             if 'procert' in b['Name'].lower()]
            
            if procert_buckets:
                self.bucket_name = procert_buckets[0]  # Use first found bucket
                print(f"Found S3 bucket: {self.bucket_name}")
                
                # List objects in the bucket
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    MaxKeys=10
                )
                
                if 'Contents' in response:
                    print(f"✅ S3 bucket accessible, found {len(response['Contents'])} objects")
                    for obj in response['Contents'][:5]:  # Show first 5
                        print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                else:
                    print("⚠️ S3 bucket is empty or no objects found")
                
                # Try to upload a test file
                test_content = {
                    "test": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Test content upload"
                }
                
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=f"test/test-{int(time.time())}.json",
                    Body=json.dumps(test_content),
                    ContentType='application/json'
                )
                
                print("✅ Successfully uploaded test content to S3")
            else:
                print("⚠️ No ProCert S3 buckets found")
                print("Available buckets:")
                for bucket in buckets['Buckets'][:10]:  # Show first 10
                    print(f"  - {bucket['Name']}")
            
        except Exception as e:
            print(f"❌ S3 test failed: {str(e)}")
    
    def test_api_gateway_alternatives(self):
        """Test API Gateway by checking CloudFormation or CDK outputs"""
        print("\n🌐 Checking API Gateway Configuration")
        
        try:
            # Try to find API Gateway via CloudFormation
            cf_client = boto3.client('cloudformation')
            stacks = cf_client.list_stacks(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
            )
            
            procert_stacks = [s for s in stacks['StackSummaries'] 
                            if 'procert' in s['StackName'].lower()]
            
            if procert_stacks:
                print(f"✅ Found {len(procert_stacks)} ProCert CloudFormation stacks")
                for stack in procert_stacks:
                    print(f"  - {stack['StackName']} ({stack['StackStatus']})")
                    
                    # Get stack outputs
                    try:
                        outputs = cf_client.describe_stacks(
                            StackName=stack['StackName']
                        )['Stacks'][0].get('Outputs', [])
                        
                        for output in outputs:
                            if 'api' in output['OutputKey'].lower():
                                print(f"    API Output: {output['OutputKey']} = {output['OutputValue']}")
                    except Exception as e:
                        print(f"    Could not get stack outputs: {str(e)}")
            else:
                print("⚠️ No ProCert CloudFormation stacks found")
                
        except Exception as e:
            print(f"❌ CloudFormation check failed: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all system tests"""
        print("🧪 ProCert System Component Testing")
        print("=" * 60)
        
        # Check AWS credentials
        try:
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"✅ AWS credentials configured for account: {identity['Account']}")
        except Exception as e:
            print(f"❌ AWS credentials issue: {str(e)}")
            return
        
        # Run tests
        self.discover_resources()
        self.test_cognito_user_creation()
        self.test_lambda_functions_directly()
        self.test_dynamodb_tables()
        self.test_s3_content_access()
        self.test_api_gateway_alternatives()
        
        print("\n" + "=" * 60)
        print("🏁 System component testing completed")
        print("Next steps:")
        print("1. Fix API Gateway 403 issues")
        print("2. Upload sample content to S3")
        print("3. Test end-to-end user flows")
        print("4. Run performance tests")

def main():
    tester = ProCertSystemTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()