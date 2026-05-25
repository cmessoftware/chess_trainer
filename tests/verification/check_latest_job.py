import sys
sys.path.append('src')
from db.session import get_session
from db.models.games import Games
from db.models.features import Features
from sqlalchemy import desc
from datetime import datetime

s = get_session()

# Buscar último batch
latest_batch = s.query(Games.import_batch_id, Games.created_at).filter(
    Games.import_batch_id.isnot(None)
).order_by(desc(Games.created_at)).first()

if latest_batch:
    batch_id, created = latest_batch
    
    # Contar partidas y features
    games = s.query(Games).filter(Games.import_batch_id == batch_id).count()
    features = s.query(Features).join(
        Games, Features.game_id == Games.game_id
    ).filter(Games.import_batch_id == batch_id).count()
    
    print(f"Último batch: {str(batch_id)[:8]}...")
    print(f"Creado: {created}")
    print(f"Partidas: {games}")
    print(f"Features: {features}")
    
    if games > 0 and features == 0:
        print("⏳ PROCESANDO - Features aún no generadas")
    elif games > 0 and features > 0:
        print(f"✅ COMPLETADO - {features/games:.1f} features por partida en promedio")
else:
    print("No hay batches en la base de datos")

s.close()
