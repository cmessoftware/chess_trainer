# tools/create_issues_from_json.py
import json
import subprocess
import re

ISSUES_FILE = "issues_todo.json"


def get_repo():
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"]).decode().strip()
        return re.sub(r'.*github.com[/:](.*)\.git', r'\1', url)
    except Exception:
        print("❌ No se pudo detectar el repositorio GitHub.")
        exit(1)


def create_issues():
    with open(ISSUES_FILE, 'r', encoding='utf-8') as + p f:
        issues = json.load(f)

    repo = get_repo()

    for issue in issues:
        title = issue['title']
        body = issue['body']
        file = issue['file']
        line = issue['line']
        print(f"\n📌 Creando issue: {title}")
        body_full = f"{body}\n\n📂 Encontrado originalmente en: `{file}:{line}`" if body else f"📂 Encontrado en: `{file}:{line}`"

        subprocess.run([
            "gh", "issue", "create",
            "--repo", repo,
            "--title", title,
            "--body", body_full
        ], check=True)


if __name__ == "__main__":
    create_issues()
