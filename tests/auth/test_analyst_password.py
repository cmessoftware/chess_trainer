"""Test para verificar password de analyst"""

import sys

sys.path.insert(0, "src")

from api.database import engine
from sqlalchemy import text
import bcrypt

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT username, password_hash FROM users WHERE username = 'analyst'")
    )
    row = result.fetchone()

    if row:
        username = row[0]
        stored_hash = row[1]

        print(f"Usuario: {username}")
        print(f"Hash en BD: {stored_hash}")

        # Test con analyst123
        test_password = "analyst123"
        matches = bcrypt.checkpw(
            test_password.encode("utf-8"), stored_hash.encode("utf-8")
        )

        print(f"\nPassword '{test_password}' matches: {matches}")

        if not matches:
            print("\n❌ La contraseña NO coincide con el hash en BD")
            print("Regenerando hash correcto...")
            correct_hash = bcrypt.hashpw(
                test_password.encode("utf-8"), bcrypt.gensalt()
            )
            print(
                f"Hash correcto para '{test_password}': {correct_hash.decode('utf-8')}"
            )
        else:
            print("\n✅ La contraseña coincide correctamente")
    else:
        print("❌ Usuario 'analyst' no encontrado")
