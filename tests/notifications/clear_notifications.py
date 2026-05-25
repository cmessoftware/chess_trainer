import sys
sys.path.insert(0, 'src')

from db.session import SessionLocal
from db.models.notifications import Notification

db = SessionLocal()

try:
    # Eliminar todas las notificaciones existentes
    count = db.query(Notification).count()
    print(f"📋 Encontradas {count} notificaciones antiguas")
    
    db.query(Notification).delete()
    db.commit()
    
    print("✅ Todas las notificaciones eliminadas")
    print("💡 Ahora genera una nueva notificación desde la UI (subir PGN + extraer features)")
    
finally:
    db.close()
