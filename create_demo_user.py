#!/usr/bin/env python3
"""
Create a demo user for testing the chat interface
"""

import json
import requests
import time

API_BASE_URL = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

def create_demo_user():
    """Create a demo user for testing."""
    print("👤 Creating demo user...")
    
    # Use a consistent demo email
    demo_email = "demo@procert.com"
    demo_password = "DemoPass123!"
    
    try:
        # Register user
        register_data = {
            "email": demo_email,
            "password": demo_password,
            "name": "Demo User",
            "given_name": "Demo",
            "family_name": "User"
        }
        
        print(f"Registering demo user: {demo_email}")
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data,
            timeout=30
        )
        
        print(f"Registration status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✅ Demo user registered: {demo_email}")
        elif response.status_code == 409:
            print(f"ℹ️  Demo user already exists: {demo_email}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
        
        # Login to verify
        login_data = {
            "email": demo_email,
            "password": demo_password
        }
        
        print("Verifying login...")
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json=login_data,
            timeout=30
        )
        
        print(f"Login status: {login_response.status_code}")
        if login_response.status_code == 200:
            login_result = login_response.json()
            tokens = login_result.get('tokens', {})
            jwt_token = tokens.get('access_token') or login_result.get('access_token')
            user_id = login_result.get('user_id', login_result.get('sub'))
            
            print(f"✅ Demo user login successful!")
            print(f"✅ User ID: {user_id}")
            print(f"✅ Email: {demo_email}")
            print(f"✅ Password: {demo_password}")
            
            return demo_email, demo_password
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
    
    except Exception as e:
        print(f"❌ Demo user creation failed: {str(e)}")
    
    return None, None

if __name__ == "__main__":
    print("🚀 Creating Demo User for Frontend Testing\n")
    
    email, password = create_demo_user()
    
    if email and password:
        print(f"\n✅ Demo user ready!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"\n🌐 You can now sign in to the frontend at http://localhost:3000")
        print(f"   Use these credentials to test the chat interface.")
    else:
        print("\n❌ Failed to create demo user")