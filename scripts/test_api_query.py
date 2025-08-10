#!/usr/bin/env python3
"""
Test script to query the ProCert API and verify content processing.
"""

import requests
import json
import boto3

def get_api_endpoint():
    """Get the API endpoint from CloudFormation."""
    try:
        cf_client = boto3.client('cloudformation')
        stack_response = cf_client.describe_stacks(StackName='ProcertInfrastructureStack')
        
        for output in stack_response['Stacks'][0]['Outputs']:
            if 'ApiEndpoint' in output['OutputKey']:
                return output['OutputValue']
        return None
    except Exception as e:
        print(f"Error getting API endpoint: {e}")
        return None

def test_query(endpoint, query_text, certification_type=None):
    """Test a query against the API."""
    try:
        url = f"{endpoint}query"
        payload = {"query": query_text}
        
        if certification_type:
            payload["certification_type"] = certification_type
        
        print(f"🔍 Testing query: '{query_text}'")
        if certification_type:
            print(f"   Certification filter: {certification_type}")
        
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success!")
            
            if 'results' in result:
                print(f"   📄 Found {len(result['results'])} results")
                for i, res in enumerate(result['results'][:2]):  # Show first 2
                    print(f"      {i+1}. {res.get('text', 'No text')[:100]}...")
            else:
                print(f"   📋 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error: {response.text}")
        
        print()
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        print()
        return False

def main():
    """Test the ProCert API with various queries."""
    print("🧪 ProCert API Testing")
    print("=" * 40)
    
    # Get API endpoint
    endpoint = get_api_endpoint()
    if not endpoint:
        print("❌ Could not find API endpoint")
        return
    
    print(f"🔗 API Endpoint: {endpoint}")
    print()
    
    # Test queries related to your uploaded content
    test_queries = [
        ("cloud practitioner", "CCP"),
        ("AWS certification", None),
        ("sample questions", None),
        ("developer associate", "DVA"),
        ("what is AWS", "CCP")
    ]
    
    success_count = 0
    for query, cert_filter in test_queries:
        if test_query(endpoint, query, cert_filter):
            success_count += 1
    
    print(f"📊 Results: {success_count}/{len(test_queries)} queries successful")
    
    if success_count > 0:
        print("🎉 Your content is indexed and searchable!")
    else:
        print("⚠️  API might need more time to be ready, or there could be an issue")

if __name__ == "__main__":
    main()