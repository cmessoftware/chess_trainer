"""Script rápido para crear usuarios de prueba"""

import sys

sys.path.insert(0, "src")

from api.database import SessionLocal
from api.models.database_models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

# Eliminar usuarios existentes si hay
db.query(User).filter(User.username.in_(["admin", "analyst", "user"])).delete(
    synchronize_session=False
)
db.commit()

# Crear usuarios
users = [
    User(
        username="admin",
        hashed_password=pwd_context.hash("admin123"),
        email="admin@chess-trainer.com",
        roles=["admin"],
        is_active=True,
    ),
    User(
        username="analyst",
        hashed_password=pwd_context.hash("analyst123"),
        email="analyst@chess-trainer.com",
        roles=["basic_gamer", "analysis_board", "stats_viewer"],
        is_active=True,
    ),
    User(
        username="user",
        hashed_password=pwd_context.hash("user123"),
        email="user@chess-trainer.com",
        roles=["basic_gamer", "tactics_trainer"],
        is_active=True,
    ),
]

for user in users:
    db.add(user)
    print(f"✓ Creado: {user.username} con roles {user.roles}")

db.commit()
db.close()
print("\n✅ Usuarios creados exitosamente")
