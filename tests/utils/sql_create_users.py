"""Script para crear usuarios usando SQL directo"""

import sys

sys.path.insert(0, "src")

from api.database import engine
from sqlalchemy import text

# Contraseñas hasheadas con bcrypt (generadas con bcrypt.hashpw)
# admin123 -> $2b$12$ksiKCA0eXf.1ACClKfNqweENkqAC3cO6yikWzJ02hzGOeoxDF2Hvm
# analyst123 -> $2b$12$MFpNgFR2p6rBXp8hOFM49uYyTksR/BnAPTxl.XCTuf45Ve2XAhOS.
# user123 -> $2b$12$HRHPT8hvJVQGMLxvyX0BCuJYvlocTSK1zweqhAtdePA4BMT.NNDs.

sql_commands = [
    # Eliminar usuarios existentes
    "DELETE FROM users WHERE username IN ('admin', 'analyst', 'user');",
    # Insertar admin
    """
    INSERT INTO users (username, password_hash, email, roles, is_active, created_at)
    VALUES ('admin', '$2b$12$ksiKCA0eXf.1ACClKfNqweENkqAC3cO6yikWzJ02hzGOeoxDF2Hvm', 
            'admin@chess-trainer.com', ARRAY['admin']::varchar[], true, NOW());
    """,
    # Insertar analyst
    """
    INSERT INTO users (username, password_hash, email, roles, is_active, created_at)
    VALUES ('analyst', '$2b$12$MFpNgFR2p6rBXp8hOFM49uYyTksR/BnAPTxl.XCTuf45Ve2XAhOS.', 
            'analyst@chess-trainer.com', ARRAY['basic_gamer', 'analysis_board', 'stats_viewer']::varchar[], true, NOW());
    """,
    # Insertar user
    """
    INSERT INTO users (username, password_hash, email, roles, is_active, created_at)
    VALUES ('user', '$2b$12$HRHPT8hvJVQGMLxvyX0BCuJYvlocTSK1zweqhAtdePA4BMT.NNDs.', 
            'user@chess-trainer.com', ARRAY['basic_gamer', 'tactics_trainer']::varchar[], true, NOW());
    """,
]

with engine.connect() as conn:
    for sql in sql_commands:
        conn.execute(text(sql))
    conn.commit()
    print("✅ Usuarios creados exitosamente!")

    # Verificar
    result = conn.execute(
        text(
            "SELECT username, roles FROM users WHERE username IN ('admin', 'analyst', 'user')"
        )
    )
    for row in result:
        print(f"  ✓ {row[0]}: roles={row[1]}")
