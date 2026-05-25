#!/usr/bin/env python3
"""
Check admin permissions for specific routes
"""
import requests

def check_admin_route_permissions():
    """Check if admin has the right permissions for each route"""
    print("🔍 Checking Admin Route Permissions...")
    
    # Login as admin first
    login_response = requests.post(
        "http://localhost:8000/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print("❌ Admin login failed")
        return
        
    token = login_response.json()['access_token']
    
    # Verify token and get permissions
    verify_response = requests.post(
        "http://localhost:8000/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if verify_response.status_code != 200:
        print("❌ Token verification failed")
        return
        
    data = verify_response.json()
    permissions = data['permissions']
    user_roles = data['user']['roles']
    
    print(f"👤 Admin User:")
    print(f"  - ID: {data['user']['id']}")
    print(f"  - Username: {data['user']['username']}")
    print(f"  - Roles: {user_roles}")
    print(f"  - Total Permissions: {len(permissions)}")
    
    print(f"\n🛡️ All Admin Permissions:")
    for i, perm in enumerate(sorted(permissions), 1):
        print(f"  {i:2d}. {perm}")
    
    # Check specific route permissions
    print(f"\n📍 Route-Specific Permission Checks:")
    
    # Games route permissions
    games_perms = ['view_own_games', 'chess_board', 'play_stockfish']
    print(f"  🎮 Games Route:")
    for perm in games_perms:
        has_perm = perm in permissions
        status = "✅" if has_perm else "❌"
        print(f"    {status} {perm}")
    
    # Import route permissions  
    import_perms = ['bulk_upload', 'import_pgn', 'manage_sources']
    print(f"  📤 Import Route:")
    for perm in import_perms:
        has_perm = perm in permissions
        status = "✅" if has_perm else "❌"
        print(f"    {status} {perm}")
    
    # Reports route permissions
    reports_perms = ['view_stats', 'advanced_stats', 'reports', 'eda_analysis']
    print(f"  📊 Reports Route:")
    for perm in reports_perms:
        has_perm = perm in permissions
        status = "✅" if has_perm else "❌"
        print(f"    {status} {perm}")
        
    # Summary
    all_route_perms = games_perms + import_perms + reports_perms
    has_all = all(perm in permissions for perm in all_route_perms)
    
    print(f"\n🎯 Summary:")
    print(f"  Admin has ALL required route permissions: {'✅ YES' if has_all else '❌ NO'}")

if __name__ == "__main__":
    check_admin_route_permissions()