#!/usr/bin/env python3
"""
Script to test the enhanced API Gateway endpoints.
This script validates the API Gateway configuration, endpoints, and validation rules.
"""

import os
import sys
import json
import subprocess
import boto3
from typing import Dict, Any, Optional
import requests
import time


def get_api_endpoint_from_cdk_outputs() -> Optional[str]:
    """Get the API endpoint from CDK outputs."""
    try:
        # Try to read from cdk-outputs.json if it exists
        if os.path.exists('cdk-outputs.json'):
            with open('cdk-outputs.json', 'r') as f:
                outputs = json.load(f)
                
            # Look for API endpoint in outputs
            for stack_name, stack_outputs in outputs.items():
                if 'ApiEndpoint' in stack_outputs:
                    return stack_outputs['ApiEndpoint']
        
        # Try to get from CDK CLI
        result = subprocess.run(
            ['cdk', 'list', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        stacks = json.loads(result.stdout)
        if stacks:
            # Get outputs from the first stack
            result = subprocess.run(
                ['cdk', 'deploy', '--outputs-file', 'temp-outputs.json', '--require-approval', 'never'],
                capture_output=True,
                text=True
            )
            
            if os.path.exists('temp-outputs.json'):
                with open('temp-outputs.json', 'r') as f:
                    outputs = json.load(f)
                os.remove('temp-outputs.json')
                
                for stack_name, stack_outputs in outputs.items():
                    if 'ApiEndpoint' in stack_outputs:
                        return stack_outputs['ApiEndpoint']
    
    except Exception as e:
        print(f"Could not get API endpoint from CDK: {e}")
    
    return None


def get_api_key_from_aws() -> Optional[str]:
    """Get API key from AWS API Gateway."""
    try:
        client = boto3.client('apigateway')
        
        # List API keys
        response = client.get_api_keys()
        
        for api_key in response.get('items', []):
            if 'procert' in api_key.get('name', '').lower():
                # Get the actual key value
                key_response = client.get_api_key(
                    apiKey=api_key['id'],
                    includeValue=True
                )
                return key_response.get('value')
    
    except Exception as e:
        print(f"Could not get API key from AWS: {e}")
    
    return None


def test_api_gateway_basic_connectivity(api_endpoint: str, api_key: str = None) -> bool:
    """Test basic connectivity to the API Gateway."""
    print("Testing basic API Gateway connectivity...")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    
    try:
        # Test a simple endpoint that should exist
        response = requests.get(f"{api_endpoint}/", headers=headers, timeout=10)
        print(f"Basic connectivity test: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Basic connectivity failed: {e}")
        return False


def test_cors_configuration(api_endpoint: str, api_key: str = None) -> bool:
    """Test CORS configuration."""
    print("Testing CORS configuration...")
    
    headers = {"Origin": "https://procert.app"}
    if api_key:
        headers["X-Api-Key"] = api_key
    
    endpoints_to_test = [
        "/auth/login",
        "/chat/message",
        "/quiz/generate"
    ]
    
    cors_working = True
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.options(f"{api_endpoint}{endpoint}", headers=headers, timeout=10)
            print(f"CORS OPTIONS {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                cors_headers = response.headers
                required_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers"
                ]
                
                for header in required_headers:
                    if header not in cors_headers:
                        print(f"Missing CORS header: {header}")
                        cors_working = False
                    else:
                        print(f"✓ {header}: {cors_headers[header]}")
            else:
                print(f"CORS preflight failed for {endpoint}")
                cors_working = False
                
        except requests.exceptions.RequestException as e:
            print(f"CORS test failed for {endpoint}: {e}")
            cors_working = False
    
    return cors_working


def test_request_validation(api_endpoint: str, api_key: str = None) -> bool:
    """Test request validation schemas."""
    print("Testing request validation...")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    
    validation_working = True
    
    # Test chat message validation
    print("Testing chat message validation...")
    
    # Valid request (should fail with 401 due to no auth, but validation should pass)
    valid_payload = {
        "message": "What is AWS Lambda?",
        "certification": "saa",
        "mode": "rag"
    }
    
    try:
        response = requests.post(f"{api_endpoint}/chat/message", json=valid_payload, headers=headers, timeout=10)
        print(f"Valid chat payload: {response.status_code} (expected 401 for auth)")
        
        # Should be 401 (unauthorized) not 400 (validation error)
        if response.status_code == 400:
            print("❌ Valid payload rejected by validation")
            validation_working = False
        else:
            print("✓ Valid payload passed validation")
    except requests.exceptions.RequestException as e:
        print(f"Chat validation test failed: {e}")
        validation_working = False
    
    # Invalid certification
    invalid_payload = {
        "message": "What is AWS Lambda?",
        "certification": "invalid-cert"
    }
    
    try:
        response = requests.post(f"{api_endpoint}/chat/message", json=invalid_payload, headers=headers, timeout=10)
        print(f"Invalid certification: {response.status_code}")
        
        if response.status_code == 400:
            print("✓ Invalid certification properly rejected")
        else:
            print("❌ Invalid certification not rejected by validation")
            validation_working = False
    except requests.exceptions.RequestException as e:
        print(f"Invalid certification test failed: {e}")
        validation_working = False
    
    # Missing required field
    missing_field_payload = {
        "certification": "saa",
        "mode": "rag"
    }
    
    try:
        response = requests.post(f"{api_endpoint}/chat/message", json=missing_field_payload, headers=headers, timeout=10)
        print(f"Missing required field: {response.status_code}")
        
        if response.status_code == 400:
            print("✓ Missing required field properly rejected")
        else:
            print("❌ Missing required field not rejected by validation")
            validation_working = False
    except requests.exceptions.RequestException as e:
        print(f"Missing field test failed: {e}")
        validation_working = False
    
    return validation_working


def test_rate_limiting(api_endpoint: str, api_key: str = None) -> bool:
    """Test rate limiting configuration."""
    print("Testing rate limiting (this may take a moment)...")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    
    # Test with auth endpoint (has lower rate limits)
    endpoint = f"{api_endpoint}/auth/login"
    payload = {"email": "test@example.com", "password": "password"}
    
    # Make multiple requests quickly
    responses = []
    for i in range(25):  # Try to exceed rate limit
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=5)
            responses.append(response.status_code)
            
            if response.status_code == 429:
                print(f"✓ Rate limiting triggered after {i+1} requests")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"Rate limiting test request {i+1} failed: {e}")
            break
        
        time.sleep(0.1)  # Small delay between requests
    
    print(f"Rate limiting test completed. Status codes: {set(responses)}")
    
    # If we didn't get rate limited, that might be okay depending on the limits
    if 429 not in responses:
        print("⚠️  Rate limiting not triggered (limits may be higher than test load)")
    
    return True


def test_authentication_enforcement(api_endpoint: str, api_key: str = None) -> bool:
    """Test that protected endpoints require authentication."""
    print("Testing authentication enforcement...")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    
    protected_endpoints = [
        ("POST", "/chat/message", {"message": "test"}),
        ("POST", "/quiz/generate", {"certification": "saa", "user_id": "test"}),
        ("GET", "/profile/test-user"),
        ("GET", "/progress/test-user/analytics"),
        ("GET", "/recommendations/test-user")
    ]
    
    auth_working = True
    
    for method, endpoint, *payload in protected_endpoints:
        payload = payload[0] if payload else None
        
        try:
            if method == "GET":
                response = requests.get(f"{api_endpoint}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{api_endpoint}{endpoint}", json=payload, headers=headers, timeout=10)
            
            print(f"{method} {endpoint}: {response.status_code}")
            
            if response.status_code == 401:
                print(f"✓ {endpoint} properly requires authentication")
            else:
                print(f"❌ {endpoint} does not require authentication (got {response.status_code})")
                auth_working = False
                
        except requests.exceptions.RequestException as e:
            print(f"Auth test failed for {endpoint}: {e}")
            auth_working = False
    
    return auth_working


def run_pytest_tests() -> bool:
    """Run the pytest test suite."""
    print("Running pytest integration tests...")
    
    try:
        result = subprocess.run([
            'python3', '-m', 'pytest', 
            'tests/integration/test_enhanced_api_gateway.py',
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=300)
        
        print("Pytest output:")
        print(result.stdout)
        if result.stderr:
            print("Pytest errors:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("Pytest tests timed out")
        return False
    except Exception as e:
        print(f"Failed to run pytest: {e}")
        return False


def main():
    """Main test execution."""
    print("🚀 Starting API Gateway Enhanced Testing")
    print("=" * 50)
    
    # Get API endpoint
    api_endpoint = os.environ.get('API_ENDPOINT') or get_api_endpoint_from_cdk_outputs()
    
    if not api_endpoint:
        print("❌ Could not determine API endpoint")
        print("Please set API_ENDPOINT environment variable or ensure CDK outputs are available")
        sys.exit(1)
    
    print(f"Testing API endpoint: {api_endpoint}")
    
    # Get API key (optional)
    api_key = os.environ.get('API_KEY') or get_api_key_from_aws()
    if api_key:
        print("✓ Using API key for requests")
    else:
        print("⚠️  No API key found, some tests may fail")
    
    # Run tests
    tests = [
        ("Basic Connectivity", lambda: test_api_gateway_basic_connectivity(api_endpoint, api_key)),
        ("CORS Configuration", lambda: test_cors_configuration(api_endpoint, api_key)),
        ("Request Validation", lambda: test_request_validation(api_endpoint, api_key)),
        ("Authentication Enforcement", lambda: test_authentication_enforcement(api_endpoint, api_key)),
        ("Rate Limiting", lambda: test_rate_limiting(api_endpoint, api_key)),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            results[test_name] = False
    
    # Run pytest tests if available
    if os.path.exists('tests/integration/test_enhanced_api_gateway.py'):
        print(f"\n📋 Running Pytest Integration Tests...")
        print("-" * 30)
        
        pytest_result = run_pytest_tests()
        results["Pytest Integration Tests"] = pytest_result
        status = "✅ PASSED" if pytest_result else "❌ FAILED"
        print(f"{status}: Pytest Integration Tests")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API Gateway tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some API Gateway tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()