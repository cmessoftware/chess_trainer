import json
import subprocess
import re
import os
import tempfile
import argparse

from tools import extract_todos

ISSUES_FILE = "issues_todo.json"


def get_repo():
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"]).decode().strip()
        return re.sub(r'.*github.com[/:](.*)\.git', r'\1', url)
    except Exception:
        print("❌ No se pudo detectar el repositorio GitHub.")
        exit(1)


def label_exists(repo, label):
    try:
        output = subprocess.check_output(
            ["gh", "label", "list", "--repo", repo]).decode()
        return any(line.startswith(label) for line in output.splitlines())
    except Exception:
        return False


def ask_with_default(prompt, default="n"):
    value = input(f"{prompt} ({default}/s): ").strip().lower()
    return value == "s"


def edit_with_vim(default_title, default_body):
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write("# Línea 1 = Título del issue (sin '#')\n")
        tmp.write("# Las demás líneas = Cuerpo del issue\n\n")
        tmp.write(f"{default_title}\n\n{default_body}\n")
        tmp_path = tmp.name

    subprocess.call(["vim", tmp_path])

    with open(tmp_path, "r", encoding="utf-8") as f:
        lines = [line for line in f if not line.startswith("#")]
        title = lines[0].strip()
        body = "".join(lines[1:]).strip()

    os.unlink(tmp_path)
    return title, body


def create_issue(repo, title, body, label=None):
    cmd = ["gh", "issue", "create", "--repo",
           repo, "--title", title, "--body", body]
    if label:
        cmd += ["--label", label]
    subprocess.run(cmd, check=True)


def create_issues(interactive=True):
    gh_login()
    with open(ISSUES_FILE, 'r', encoding='utf-8') as f:
        issues = json.load(f)

    repo = get_repo()

    for issue in issues:
        default_title = issue["title"]
        default_body = issue["body"]
        file = issue["file"]
        line = issue["line"]
        context = f"📂 Encontrado en `{file}:{line}`"

        if interactive:
            print(f"\n🔍 Posible issue detectado: {default_title}")
            if not ask_with_default("¿Querés crear este issue?"):
                continue

            if ask_with_default("¿Querés editarlo con vim?"):
                title, body = edit_with_vim(default_title, default_body)
            else:
                prompt = f"Título del issue [por defecto: {default_title}]: "
                user_input = input(prompt).strip()
                title = user_input if user_input else default_title
                print("✍️  Escribí la descripción (Ctrl+D para terminar):")
                try:
                    if default_body:
                        print("✍️ Descripción por defecto detectada:")
                        print(f"\n{default_body}\n")
                        print(
                            "➡️ Presioná Enter para usarla o escribí una nueva (Ctrl+D para terminar):")
                    else:
                        print("✍️ Escribí la descripción (Ctrl+D para terminar):")

                    try:
                        user_input = "".join(iter(input, "")).strip()
                        body = user_input if user_input else default_body
                    except EOFError:
                        body = default_body or ""
                except EOFError:
                    body = ""
        else:
            title = default_title
            body = default_body

        body += f"\n\n{context}"
        create_issue(repo, title, body)
        print("✅ Issue creado.")


def gh_login():
    try:
        subprocess.run(["gh", "auth", "status"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ No estás autenticado en GitHub CLI. Por favor, ejecuta 'gh auth login' para autenticarte.")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crear issues desde un archivo JSON.")
    parser.add_argument("--auto", action="store_true",
                        help="Crear los issues automáticamente sin interacción")

    args = parser.parse_args()
    create_issues(interactive=not args.auto)
