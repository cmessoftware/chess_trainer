"""
Script para crear usuarios de prueba en la base de datos
Ejecutar desde la raíz: python create_test_users.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.database import SessionLocal
from api.models.database_models import User
from passlib.context import CryptContext


def create_test_users():
    """Crear usuarios de prueba con diferentes roles"""
    db = SessionLocal()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Usuarios de prueba
    test_users = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@chess-trainer.com",
            "roles": ["admin"],
            "is_active": True,
        },
        {
            "username": "analyst",
            "password": "analyst123",
            "email": "analyst@chess-trainer.com",
            "roles": ["basic_gamer", "analysis_board", "stats_viewer"],
            "is_active": True,
        },
        {
            "username": "user",
            "password": "user123",
            "email": "user@chess-trainer.com",
            "roles": ["basic_gamer", "tactics_trainer"],
            "is_active": True,
        },
    ]

    try:
        for user_data in test_users:
            # Verificar si el usuario ya existe
            existing_user = (
                db.query(User).filter(User.username == user_data["username"]).first()
            )

            if existing_user:
                print(f"❌ Usuario '{user_data['username']}' ya existe")
                continue

            # Hash de contraseña
            password_hash = pwd_context.hash(user_data["password"])

            # Crear usuario
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                roles=user_data["roles"],
                is_active=user_data["is_active"],
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            print(f"✅ Usuario creado: {user_data['username']} (ID: {new_user.id})")
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Roles: {', '.join(user_data['roles'])}")
            print()

        print("✅ Usuarios de prueba creados exitosamente!")
        print("\n📝 Credenciales de acceso:")
        print("-" * 50)
        for user_data in test_users:
            print(
                f"Usuario: {user_data['username']} | Password: {user_data['password']}"
            )
        print("-" * 50)

    except Exception as e:
        print(f"❌ Error creando usuarios: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
