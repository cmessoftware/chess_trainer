import os
import sqlite3
from pathlib import Path
import dotenv
dotenv.load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

db_path = DB_PATH
output_dir = Path("models")
output_dir.mkdir(parents=True, exist_ok=True)


def sqlite_type_to_sqlalchemy(sqlite_type: str) -> str:
    t = sqlite_type.upper()
    if "INT" in t:
        return "Integer"
    elif "CHAR" in t or "TEXT" in t or "CLOB" in t:
        return "String"
    elif "BLOB" in t:
        return "LargeBinary"
    elif "REAL" in t or "FLOA" in t or "DOUB" in t:
        return "Float"
    elif "DATE" in t or "TIME" in t:
        return "DateTime"
    else:
        return "String"


def extract_columns(sql: str):
    lines = sql.splitlines()
    column_lines = []
    in_parens = False
    for line in lines:
        line = line.strip().rstrip(",")
        if "(" in line and not in_parens:
            in_parens = True
            continue
        elif ")" in line and in_parens:
            break
        elif in_parens:
            column_lines.append(line)
    return column_lines


def parse_columns(lines):
    columns = []
    primary_found = False
    for i, line in enumerate(lines):
        if not line or line.upper().startswith(("PRIMARY KEY", "UNIQUE", "FOREIGN", "CONSTRAINT", "CHECK")):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0].strip('",')
        col_type = sqlite_type_to_sqlalchemy(parts[1])
        extras = []
        if "PRIMARY KEY" in line.upper():
            extras.append("primary_key=True")
            primary_found = True
        if "NOT NULL" in line.upper():
            extras.append("nullable=False")
        columns.append((name, col_type, extras))

    # If none has primary_key, assume the first column is the PK
    if not primary_found and columns:
        columns[0][2].append("primary_key=True")

    return columns


conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    cursor.execute(
        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
    result = cursor.fetchone()
    if not result:
        continue
    sql = result[0]
    lines = extract_columns(sql)
    columns = parse_columns(lines)

    model_lines = [f"    {name} = Column({col_type}{', ' + ', '.join(extras) if extras else ''})"
                   for name, col_type, extras in columns]

    model_code = f"""from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class {table.capitalize()}(Base):
    __tablename__ = '{table}'

{chr(10).join(model_lines)}
"""

    file_path = output_dir / f"{table}.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(model_code)

print(f"✅ Models regenerated with primary key ensured in {output_dir}")
