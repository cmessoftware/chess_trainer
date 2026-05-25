"""
Script para crear usuarios de prueba en la base de datos
Ejecutar desde la raíz del proyecto: python -m src.scripts.create_test_users
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))
os.chdir(project_root)

from src.api.database import SessionLocal
from src.api.models.database_models import User
from src.api.services.auth_service import AuthService


def create_test_users():
    """Crear usuarios de prueba con diferentes roles"""
    db = SessionLocal()
    auth_service = AuthService()

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
            password_hash = auth_service.hash_password(user_data["password"])

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
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
