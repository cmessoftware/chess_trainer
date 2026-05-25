#!/usr/bin/env python3
"""
Test script para debugging del sistema de autenticación
"""
import asyncio
import sys
import os

# Add the src/api directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api'))

from services.auth_service import AuthService
from database import get_db

async def test_auth():
    """Test authentication functionality"""
    auth_service = AuthService()
    
    print("🧪 Testing Auth Service...")
    
    # Test legacy authentication first
    print("\n1. Testing legacy authentication:")
    legacy_result = await auth_service.authenticate_user_legacy("admin", "admin123")
    print(f"Legacy auth result: {legacy_result}")
    
    # Test database connection
    print("\n2. Testing database connection:")
    try:
        db_gen = get_db()
        db = next(db_gen)
        print("✅ Database connection successful")
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test full authentication (with database fallback)
    print("\n3. Testing full authentication:")
    try:
        full_result = await auth_service.authenticate_user("admin", "admin123", None)
        print(f"Full auth result: {full_result}")
    except Exception as e:
        print(f"❌ Full auth failed: {e}")
    
    # Test token creation
    print("\n4. Testing token creation:")
    try:
        if legacy_result:
            token_data = {
                "sub": legacy_result["username"],
                "user_id": legacy_result["user_id"],
                "roles": ",".join([role.value for role in legacy_result["roles"]])
            }
            token = auth_service.create_access_token(token_data)
            print(f"✅ Token created: {token[:50]}...")
        else:
            print("❌ No user data to create token")
    except Exception as e:
        print(f"❌ Token creation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())