import sys
sys.path.insert(0, 'src')

from db.session import SessionLocal
from db.models.notifications import Notification

db = SessionLocal()

try:
    # Obtener notificaciones
    notifications = db.query(Notification).all()
    
    print(f"📋 Total notificaciones: {len(notifications)}")
    
    if len(notifications) > 0:
        n = notifications[0]
        print(f"\n🔍 Primera notificación:")
        print(f"   ID: {n.id}")
        print(f"   User: {n.user_id}")
        print(f"   Type meta_data: {type(n.meta_data)}")
        print(f"   Meta_data valor: {n.meta_data}")
        print()
        
        # Verificar si tiene método to_dict
        if hasattr(n, 'to_dict'):
            print("✅ Método to_dict() EXISTE")
            try:
                result = n.to_dict()
                print(f"✅ to_dict() ejecutado correctamente")
                print(f"📝 Resultado:")
                import json
                print(json.dumps(result, indent=2))
            except Exception as e:
                print(f"❌ Error al ejecutar to_dict(): {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Método to_dict() NO EXISTE")
            print(f"   Métodos disponibles: {[m for m in dir(n) if not m.startswith('_')]}")

finally:
    db.close()
