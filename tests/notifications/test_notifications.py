import requests
import json

# Login para obtener token
login_url = "http://localhost:8000/auth/login"
login_data = {"username": "admin", "password": "admin123"}

try:
    print("🔑 Obteniendo token...")
    login_response = requests.post(login_url, json=login_data)
    login_response.raise_for_status()
    token = login_response.json()["access_token"]
    print(f"✅ Token obtenido: {token[:50]}...")
    print()
    
    # Decodificar payload
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    # Probar endpoint de notificaciones
    print("🔔 Probando endpoint de notificaciones...")
    notifications_url = "http://localhost:8000/api/features/notifications"
    headers = {"Authorization": f"Bearer {token}"}
    
    notifications_response = requests.get(notifications_url, headers=headers)
    
    print(f"📡 Status Code: {notifications_response.status_code}")
    
    if notifications_response.ok:
        data = notifications_response.json()
        print(f"✅ Notificaciones obtenidas: {len(data)}")
        if len(data) > 0:
            print(f"📝 Primera notificación:")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"❌ Error: {notifications_response.status_code}")
        print(f"   Response: {notifications_response.text}")
        
except Exception as e:
    print(f"💥 Exception: {e}")
    import traceback
    traceback.print_exc()
