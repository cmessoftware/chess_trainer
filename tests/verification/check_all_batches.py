import sys
sys.path.append('src')
from db.session import get_session
from db.models.games import Games
from db.models.features import Features
from sqlalchemy import desc, func

s = get_session()

# Buscar últimos 10 batches con conteo de partidas
print("Últimos batches importados:\n")

batches = s.query(
    Games.import_batch_id,
    func.count(Games.game_id).label('games_count'),
    func.max(Games.created_at).label('latest_created')
).filter(
    Games.import_batch_id.isnot(None)
).group_by(
    Games.import_batch_id
).order_by(
    desc('latest_created')
).limit(10).all()

for batch_id, games_count, created in batches:
    # Contar features para este batch
    features_count = s.query(Features).join(
        Games, Features.game_id == Games.game_id
    ).filter(Games.import_batch_id == batch_id).count()
    
    status = "✅ COMPLETADO" if features_count > 0 else "⏳ PROCESANDO"
    print(f"{status} | Batch: {str(batch_id)[:8]}... | {games_count} partidas | {features_count} features | {created}")

s.close()
