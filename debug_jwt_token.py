#!/usr/bin/env python3

import base64
import json

# JWT token from the browser (truncated for security)
jwt_token = "eyJraWQiOiJEdjUrV2FNbXlSeFRLa1dcL21OT0tiK0FCOFwvK2cyQ3MxRmJmRThveUNpMzg9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJmNGU4MDQyOC0wMGIxLTcwZTItZjYwMC1jZjIwMjhkNmQyYTQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9Qbkx2UDBvN00iLCJjbGllbnRfaWQiOiI1M2ttYThzdWxyaGRsOWtpN2Rib2kwdmoxaiIsIm9yaWdpbl9qdGkiOiJhOTY4YzFlZi0yZDE1LTRmZDEtYTZhNy1hNzRkYTAzNTU0YTYiLCJldmVudF9pZCI6IjBkYTJiNDEwLWRmZWUtNGU1MS1iNTQxLTEzOGU0OTUyNDU5MiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3NTU0NDk2NDksImV4cCI6MTc1NTQ1MzI0OSwiaWF0IjoxNzU1NDQ5NjQ5LCJqdGkiOiI3ZGIyY2QyMS05YjNmLTRhNGQtODBiZS0xMTdiMGNkNjk2ODYiLCJ1c2VybmFtZSI6ImY0ZTgwNDI4LTAwYjEtNzBlMi1mNjAwLWNmMjAyOGQ2ZDJhNCJ9.R168aJxk7Wq1gtyVyO7QDPIwxvZk4fR3fHulCNViWi_a7oTJM8i6dbcCqwgqXJ98ZbtA3ObIWIE5Hk02qrsZp4Akh2ocIihq3g-ID9M4Gwb2-8FdgDk3wrtCsAqTVVjqseciaof5ilAhYr83ckPv9cmMujS4CmAYaobbvMrxHS1Am80DTeIOO0DjOLz48hzyGr4gN2pl8QGC4uH_JEZ9Fr37EIThe81ERVpy43z_IANN2_G2gyP3lzbjdNQOLE0lgBbBTcVu7yjhUTG5wqprt_UGN7Lj049A6R_uBJdZ1qmbnE_t57uXodHYSs2FDudfV7W0ViKM7C03IcqOGDJDAw"

def decode_jwt_payload(token):
    """Decode JWT payload without verification"""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Invalid JWT format - should have 3 parts")
            return None
        
        header, payload, signature = parts
        
        # Decode header
        header_decoded = base64.urlsafe_b64decode(header + '==')
        header_json = json.loads(header_decoded)
        
        # Decode payload
        payload_decoded = base64.urlsafe_b64decode(payload + '==')
        payload_json = json.loads(payload_decoded)
        
        print("✅ JWT Token Analysis:")
        print(f"Header: {json.dumps(header_json, indent=2)}")
        print(f"Payload: {json.dumps(payload_json, indent=2)}")
        
        # Check expiration
        import time
        current_time = int(time.time())
        exp_time = payload_json.get('exp', 0)
        
        if exp_time < current_time:
            print(f"❌ Token is EXPIRED! Expired at: {exp_time}, Current: {current_time}")
        else:
            print(f"✅ Token is valid until: {exp_time} (Current: {current_time})")
        
        return payload_json
        
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return None

if __name__ == "__main__":
    decode_jwt_payload(jwt_token)