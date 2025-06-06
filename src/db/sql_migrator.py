import re

def migrate_sqlite_to_postgres(sql: str) -> str:
    """
    Transforma una sentencia SQL de SQLite a PostgreSQL compatible
    """
    sql = sql.strip()

    # AUTOINCREMENT → SERIAL PRIMARY KEY
    sql = re.sub(r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)

    # Solo PRIMARY KEY → SERIAL si es INTEGER
    sql = re.sub(r'\bINTEGER\s+PRIMARY\s+KEY\b', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)

    # TEXT → TEXT (ok), opcionalmente podrías convertir a VARCHAR
    # REAL → DOUBLE PRECISION
    sql = re.sub(r'\bREAL\b', 'DOUBLE PRECISION', sql, flags=re.IGNORECASE)

    # DATETIME → TIMESTAMP
    sql = re.sub(r'\bDATETIME\b', 'TIMESTAMP', sql, flags=re.IGNORECASE)

    # BOOLEAN → BOOLEAN (Postgres lo soporta, pero SQLite no: se usaban INTEGER)
    sql = re.sub(r'\bBOOLEAN\b', 'BOOLEAN', sql, flags=re.IGNORECASE)

    # Remove SQLite-only pragmas or unsupported clauses
    sql = re.sub(r'WITHOUT ROWID\b', '', sql, flags=re.IGNORECASE)

    # Replace double quotes around identifiers with nothing (Postgres uses double quotes optionally)
    sql = sql.replace('"', '')

    return sql
