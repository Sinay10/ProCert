#!/usr/bin/env python3
"""
Test with the real JWT token from the login response.
"""

import requests
import json

# API endpoint from CDK output
API_ENDPOINT = "https://04l6uq5jl4.execute-api.us-east-1.amazonaws.com/prod"

# Real access token from the previous test
ACCESS_TOKEN = "eyJraWQiOiJEdjUrV2FNbXlSeFRLa1dcL21OT0tiK0FCOFwvK2cyQ3MxRmJmRThveUNpMzg9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJhNDM4ZTQ3OC05MDcxLTcwYTEtZjI3ZC02MzM1NmQ1ZmEzMDQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9Qbkx2UDBvN00iLCJjbGllbnRfaWQiOiI1M2ttYThzdWxyaGRsOWtpN2Rib2kwdmoxaiIsIm9yaWdpbl9qdGkiOiI4NzAwZGY4Zi1mOWY3LTQyYjItOTViYS03MDc2NDc2NTlmYjAiLCJldmVudF9pZCI6ImM5ZDliZTEyLTA1ZDYtNGEzZC04MDZkLTdjYmU1NTgyNDZmMiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3NTQ5ODU0OTgsImV4cCI6MTc1NDk4OTA5OCwiaWF0IjoxNzU0OTg1NDk4LCJqdGkiOiJiNGUwYzI5Ny1iOTc3LTQzZGYtYTNiNC00ODUwOTUwOGU2N2YiLCJ1c2VybmFtZSI6ImE0MzhlNDc4LTkwNzEtNzBhMS1mMjdkLTYzMzU2ZDVmYTMwNCJ9.dtHe7MfY6L0801DN_ZhGmVAgeZ1lrraJzuoBn6YbFW6xYFYoEsTfDaDpNeLj9bOspHbodn3r4oOTPTUVFhVyS0-J7i9GjGeP39uefry_O7DchqN7_afHU_lGkmqjFti0yjN__y8yu4R5GBy_DJ8V6-eKFJhVZ1VtifMkOA1073xFpR-5A5o953fNZkSgJVWWIfvtRc00iaCfjFtC158VQlXJwQmED-CVEFtuKxvb6oDrGvAv8exj8cjKu5fqGMzCx0ir1UdIazVmRUk4HrNBYBk5m9uM_N91g0s4uDvYKc3zypwy6Y1CiwaIOg-z68OFR-vKCVCmQeOtKd04N2CZWg"

USER_ID = "a438e478-9071-70a1-f27d-63356d5fa304"

def test_with_real_token():
    """Test with the real JWT token."""
    print("🔐 Testing with real JWT token...")
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}/profile/{USER_ID}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Real token test successful!")
            return json.loads(response.text)
        else:
            print("❌ Real token test failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error with real token: {e}")
        return None

if __name__ == "__main__":
    test_with_real_token()