#!/usr/bin/env python3
"""
Test script for API endpoints
"""
import requests
import json

def test_login_endpoint():
    """Test the login endpoint"""
    
    print("🧪 Testing Login Endpoint...")
    
    # Test data
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    url = "http://localhost:8000/auth/login"
    
    try:
        print(f"\n📡 Making request to: {url}")
        print(f"📦 Payload: {json.dumps(login_data, indent=2)}")
        
        response = requests.post(
            url,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            response_data = response.json()
            print(f"🎫 Token: {response_data.get('access_token', 'N/A')[:50]}...")
            print(f"👤 User: {response_data.get('user', 'N/A')}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚨 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🚨 Raw error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on localhost:8000?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_login_endpoint()