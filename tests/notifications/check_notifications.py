import requests
import json

# Simular autenticación (asumiendo que el token está en algún lugar)
# Para testing, intentaremos con y sin auth

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("VERIFICACIÓN DE NOTIFICACIONES")
print("=" * 60)

# 1. Verificar notificaciones (sin auth)
print("\n1. Estado de notificaciones (sin autenticación):")
try:
    r = requests.get(f"{BASE_URL}/api/features/notifications")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Total notificaciones: {len(data)}")
        if len(data) > 0:
            print(f"   Primera notificación:")
            print(f"      {json.dumps(data[0], indent=6)}")
    else:
        print(f"   Error: {r.json()}")
except Exception as e:
    print(f"   Exception: {e}")

# 2. Verificar jobs de features
print("\n2. Estado de jobs de features:")
try:
    r = requests.get(f"{BASE_URL}/api/features/jobs")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Total jobs: {len(data)}")
        if len(data) > 0:
            print(f"   Último job:")
            print(f"      ID: {data[0].get('id', 'N/A')[:8]}...")
            print(f"      Status: {data[0].get('status', 'N/A')}")
            print(f"      Batch ID: {data[0].get('batch_id', 'N/A')}")
    else:
        print(f"   Error: {r.json()}")
except Exception as e:
    print(f"   Exception: {e}")

# 3. Verificar progreso general
print("\n3. Progreso general de extracción:")
try:
    r = requests.get(f"{BASE_URL}/api/features/progress")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ¿Está procesando?: {data.get('is_processing', False)}")
        print(f"   Progreso: {data.get('progress', 0)}%")
        print(f"   Status: {data.get('status', 'N/A')}")
        print(f"   Total jobs: {data.get('total_jobs', 0)}")
        print(f"   Jobs activos: {data.get('active_jobs', 0)}")
        print(f"   Jobs completados: {data.get('completed_jobs', 0)}")
    else:
        print(f"   Error: {r.json()}")
except Exception as e:
    print(f"   Exception: {e}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO:")
print("=" * 60)
print("Si no hay notificaciones:")
print("- El backend puede haberse reiniciado (notifications_store está en memoria)")
print("- Las notificaciones solo se crean durante extracción de features")
print("- Necesitas hacer una nueva extracción para generar notificaciones")
print("\nSolución: Sube un PGN y presiona 'Extraer Features' para generar notificación")
print("=" * 60)
