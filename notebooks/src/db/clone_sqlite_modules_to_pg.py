import os
import re
from pathlib import Path
from sql_migrator import migrate_sqlite_to_postgres

SQL_KEYWORDS = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')

def is_sql_line(line: str) -> bool:
    """Detecta si una línea probablemente contiene SQL SQLite"""
    return any(k in line.upper() for k in SQL_KEYWORDS) and ('execute' in line or line.strip().startswith(('"""', "'")))

def convert_sql_strings(code: str) -> str:
    """Detecta y convierte sentencias SQL SQLite en el contenido del código"""
    # Regex para strings multilínea y en una línea
    string_pattern = r"(\"\"\".*?\"\"\"|'''.*?'''|\".*?\"|'.*?')"

    def replacer(match):
        s = match.group(0)
        if any(k in s.upper() for k in SQL_KEYWORDS):
            # Intenta migrar el contenido si parece SQL
            try:
                unquoted = s.strip("\"'")  # quita comillas
                converted = migrate_sqlite_to_postgres(unquoted)
                return s[0] + converted + s[-1]  # conserva comillas originales
            except Exception:
                return s
        return s

    return re.sub(string_pattern, replacer, code, flags=re.DOTALL)

def clone_and_convert_py_files(folder: str):
    folder_path = Path(folder)
    for file_path in folder_path.glob("*.py"):
        if file_path.name.endswith("_pg.py"):
            continue  # evita archivos ya migrados

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        if any(is_sql_line(line) for line in code.splitlines()):
            print(f"🎯 Detectando SQL en: {file_path.name}")
            converted_code = convert_sql_strings(code)
            target_path = file_path.with_name(file_path.stem + "_pg.py")
            with open(target_path, "w", encoding="utf-8") as f_out:
                f_out.write(converted_code)
            print(f"✅ Módulo clonado como: {target_path.name}")

if __name__ == "__main__":
    # Usar como: python clone_sqlite_modules_to_pg.py src/modules/
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    clone_and_convert_py_files(folder)

# # Ejemplo de uso:

# clone_and_convert_py_files("src/modules/")