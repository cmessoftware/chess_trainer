#!/usr/bin/env python3
"""
Test the complete end-to-end authentication flow
"""
import requests
import json

def test_complete_auth_flow():
    """Test the complete authentication flow"""
    print("🔐 Testing Complete Authentication Flow...")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Login with admin credentials
    print("\n1. Testing admin login...")
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Admin login successful!")
            login_result = response.json()
            token = login_result.get('access_token')
            user_data = login_result.get('user', {})
            
            print(f"👤 User ID: {user_data.get('id')}")
            print(f"📧 Email: {user_data.get('email')}")
            print(f"🔑 Roles: {user_data.get('roles')}")
            print(f"🎫 Token: {token[:50] if token else 'None'}...")
            
            # Test 2: Verify token
            if token:
                print("\n2. Testing token verification...")
                verify_response = requests.post(
                    f"{base_url}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if verify_response.status_code == 200:
                    print("✅ Token verification successful!")
                    verify_data = verify_response.json()
                    permissions = verify_data.get('permissions', [])
                    print(f"🛡️ Permissions count: {len(permissions)}")
                    print(f"🛡️ First 5 permissions: {permissions[:5]}")
                else:
                    print(f"❌ Token verification failed: {verify_response.status_code}")
                    print(f"Error: {verify_response.text}")
            
            # Test 3: Test roles matrix
            print("\n3. Testing roles matrix...")
            matrix_response = requests.get(f"{base_url}/auth/roles/matrix")
            if matrix_response.status_code == 200:
                print("✅ Roles matrix accessible!")
                matrix_data = matrix_response.json()
                print(f"📊 Available roles: {len(matrix_data.get('available_roles', []))}")
                print(f"📊 Total permissions: {len(matrix_data.get('all_permissions', []))}")
            else:
                print(f"❌ Roles matrix failed: {matrix_response.status_code}")
                
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on localhost:8000?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_complete_auth_flow()