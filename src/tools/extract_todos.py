import os
import json
import re
import argparse

ISSUES_FILE = "issues_todo.json"
TODO_PATTERN = re.compile(r"#\s*TODO\s*[:\-]?\s*(.*)", re.IGNORECASE)
MIGRATED_TAG = "#MIGRATED-TODO"


def find_todos(base_path="."):
    todos = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.cs', '.cpp', '.java', '.go', '.rb', '.html', '.css', '.md')):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                modified = False
                for i, line in enumerate(lines):
                    if MIGRATED_TAG in line:
                        continue  # Saltar líneas ya migradas

                    match = TODO_PATTERN.search(line)
                    if match:
                        title = match.group(1).strip()
                        if not title:
                            continue

                        print(f"\n🔎 {full_path}:{i+1} → {title}")
                        body = input("📝 Descripción opcional: ")

                        todos.append({
                            "title": title,
                            "body": body,
                            "file": full_path,
                            "line": i + 1
                        })

                        # Marcar como migrado con timestamp
                        timestamp = int(__import__('time').time())
                        migrated_tag = f"#MIGRATED-TODO-{timestamp}"
                        lines[i] = re.sub(
                            r"#\s*TODO", migrated_tag, line, count=1, flags=re.IGNORECASE)
                        modified = True

                if modified:
                    print(
                        f"✏️ Actualizando {full_path} con los TODOs encontrados...")
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

    return todos


def save_issues(issues):
    with open(ISSUES_FILE, 'w', encoding='utf-8') as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)
    print(f"\n✅ {len(issues)} issues guardados en '{ISSUES_FILE}'")


def main():
    parser = argparse.ArgumentParser(
        description="Extraer TODOs del código fuente.")
    parser.add_argument("--path", type=str, default=".",
                        help="Ruta base donde buscar TODOs (por defecto '.')")
    args = parser.parse_args()

    print("🚀 Buscando TODOs...")
    issues = find_todos(args.path)

    print(f"\n🔍 Se encontraron {len(issues)} TODOs.")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['title']} ({issue['file']}:{issue['line']})")
        if issue['body']:
            print(f"   {issue['body']}")

    if not issues:
        print("❌ No se encontraron TODOs.")
        exit(1)

    save_issues(issues)


if __name__ == "__main__":
    main()
