import sys
import time
import subprocess
import re
import os
import tempfile
import subprocess
import json
import dotenv
# Cargar variables de entorno desde .env
dotenv.load_dotenv()


TODO_PATTERN = re.compile(r"#\s*TODO\s*[:\-]?\s*(.*)", re.IGNORECASE)
MIGRATED_TAG = "#MIGRATED-TODO"
GITHUB_OWNER = "cmessoftware"
PROJECT_NUMBER = 11  # Número del proyecto
PROJECT_NODE_ID = "PVT_kwHOBgXmV84A8H76"  # ID del proyecto en GitHub
GITHUB_REPO = "chess_trainer"
# IDs de campos y valores ya detectados
STATUS_FIELD_ID = "PVTSSF_lAHOBgXmV84A8H76zgwN2EU"
STATUS_BACKLOG_ID = "f75ad846"
# No tenés Roadmap, podemos dejarlo igual o agregar ese valor en GitHub
STATUS_ROADMAP_ID = "f75ad846"
PRIORITY_FIELD_ID = "PVTSSF_lAHOBgXmV84A8H76zgwN2Kw"
# Debes tener este mapeo en tus constantes al inicio
STATUS_OPTIONS = {
    "Backlog": "f75ad846",
    "Ready": "e18bf179",
    "In progress": "47fc9ee4",
    "In review": "aba860b9",
    "Done": "98236657"
}


def run_gh(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_project_item_id(issue_number, max_retries=5, delay=3):
    issue_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/issues/{issue_number}"

    for attempt in range(max_retries):
        result = run_gh([
            "gh", "project", "item-list",
            str(PROJECT_NUMBER), "--owner", GITHUB_OWNER, "--format", "json"
        ])
        # print(f"DEBUG salida item-list (intento {attempt+1}):\n{result}")

        items_json = json.loads(result)
        items = items_json.get("items", [])

        for item in items:
            content = item.get("content", {})
            if content.get("url") == issue_url:
                print(f"✅ Item encontrado en intento {attempt+1}")
                return item["id"]

        print(
            f"⏳ Item no encontrado aún. Esperando {delay} segundos...", end="", flush=True)

        # Simular progreso visual
        for _ in range(delay * 2):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print()

    raise ValueError(
        f"❌ Item no encontrado en el proyecto para issue_url {issue_url} después de {max_retries} intentos")


def update_issue_status(item_id, status_option_id):
    mutation = f'''
    mutation {{
      updateProjectV2ItemFieldValue(
        input: {{
          projectId: "{PROJECT_NODE_ID}",  # Este es el ID tipo PVT_kwHOBgXmV84A8H76
          itemId: "{item_id}",
          fieldId: "{STATUS_FIELD_ID}",
          value: {{ singleSelectOptionId: "{status_option_id}" }}
        }}
      ) {{
        projectV2Item {{
          id
        }}
      }}
    }}
    '''
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={mutation}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ Status del item {item_id} actualizado correctamente")
    else:
        print(
            f"❌ Error al actualizar status del item {item_id}: {result.stderr}")

# def update_issue_status(issue_id, status_value_name):
#     try:
#         run_gh([
#             "gh", "project", "field-update", str(PROJECT_NUMBER),
#             # "--owner", GITHUB_OWNER,
#             "--field-id", STATUS_FIELD_ID,
#             "--item-id", str(issue_id),
#             "--value", status_value_name
#         ])
#         print(f"✅ Status del issue {issue_id} actualizado")
#     except subprocess.CalledProcessError as e:
#         print(
#             f"❌ Error al actualizar el status del issue {issue_id}: {e.stderr}")
#         if e.__cause__:
#             print(f"🔍 Causa: {e.__cause__}")
#         raise


def add_issue_to_project(issue_number, labels=[]):
    issue_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/issues/{issue_number}"

    run_gh([
        "gh", "project", "item-add", str(PROJECT_NUMBER),
        "--url", issue_url,
        "--owner", GITHUB_OWNER
    ])
    print(f"✅ Issue {issue_number} agregado al proyecto")

    # Definir status según etiquetas
    # status_id = STATUS_ROADMAP_ID if "low-priority" in labels else STATUS_BACKLOG_ID
    item_id = get_project_item_id(issue_number)
    status_id = STATUS_OPTIONS["Backlog"] if "low-priority" in labels else STATUS_OPTIONS["Ready"]
    update_issue_status(item_id, status_id)

    # update_issue_status(item_id, status_id)


# def add_issue_to_project(issue_number, labels=[]):
#     # Agregar issue al proyecto
#     run_gh([
#         "gh", "project", "item-add", str(PROJECT_NUMBER),
#         "--issue", str(issue_number),
#         "--owner", GITHUB_OWNER
#     ])
#     print(f"🔗 Issue {issue_number} agregado al proyecto")

#     # Definir status
#     if "low-priority" in labels:
#         # Si no existe "Roadmap" todavía, lo dejamos como Backlog
#         status_id = STATUS_ROADMAP_ID
#     else:
#         status_id = STATUS_BACKLOG_ID
#     update_issue_status(issue_number, status_id)


def get_issue_id(issue_number):
    result = subprocess.run(
        ["gh", "api",
            f"repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues/{issue_number}"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)["node_id"]

# def get_issue_id(issue_number):
#     cmd = ["gh", "api", f"GITHUB_REPOs/{GITHUB_OWNER}/{GITHUB_REPO}/issues/{issue_number}"]
#     result = subprocess.run(cmd, capture_output=True, text=True, check=True)
#     data = json.loads(result.stdout)
#     return data.get("node_id")


def get_priority_from_issue(issue_number: int) -> str | None:
    """
    Obtiene la prioridad desde las etiquetas del issue usando la GitHub API.
    """
    try:
        result = subprocess.run(
            ["gh", "api", f"GITHUB_REPOs/{GITHUB_REPO}/issues/{issue_number}"],
            capture_output=True,
            check=True,
            text=True
        )
        data = json.loads(result.stdout)
        labels = [label["name"] for label in data.get("labels", [])]

        for p in ["low-priority", "medium-priority", "high-priority"]:
            if p in labels:
                return p
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al obtener labels del issue #{issue_number}: {e}")
        return None


def find_todos(base_path="."):
    todos = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.html', '.css', '.md')):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                modified = False
                for i, line in enumerate(lines):
                    if MIGRATED_TAG in line:
                        continue  # Saltar líneas ya migradas

                    match = TODO_PATTERN.search(line)
                    if match:
                        # Limitar a 40 caracteres
                        title = match.group(1).strip()[:40]
                        print(f"  - Encontrado TODO: {title}")
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

                        modified = True

                if modified:
                    print(
                        f"✏️ Actualizando {full_path} con los TODOs encontrados...")
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

    return todos


def get_GITHUB_REPO():
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"]).decode().strip()
        return re.sub(r'.*github.com[/:](.*)\.git', r'\1', url)
    except Exception:
        print("❌ No se pudo detectar el GITHUB_REPOsitorio GitHub.")
        exit(1)


def label_exists(GITHUB_REPO, label):
    try:
        output = subprocess.check_output(
            ["gh", "label", "list", "--repo", GITHUB_REPO]).decode()
        return any(line.startswith(label) for line in output.splitlines())
    except Exception:
        return False


def ask_with_default(prompt, default="n"):
    value = input(f"{prompt} ({default}/s): ").strip().lower()
    return value == "s" or value == "yes" or value == "y" or value == "" or value == "si" and default.lower() in ["s", "yes", "y", "si"]


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


def ensure_label_exists(GITHUB_REPO, label):
    try:
        output = subprocess.check_output(
            ["gh", "label", "list", "--repo", GITHUB_REPO],
            text=True
        )
        labels = [line.split()[0] for line in output.splitlines()]
        if label not in labels:
            print(f"🏷️ Creando etiqueta '{label}'...")
            subprocess.run(
                ["gh", "label", "create", label,
                    "--repo", GITHUB_REPO, "--color", "BFD4F2"],
                check=True
            )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al validar o crear etiqueta '{label}': {e}")
        raise


def create_issue(GITHUB_REPO, title, body, labels=None, priority=None):
    """
    Crea un issue en el GITHUB_REPOsitorio especificado, con etiquetas y prioridad.

    :param GITHUB_REPO: str - "usuario/GITHUB_REPOsitorio"
    :param title: str - Título del issue
    :param body: str - Descripción del issue
    :param labels: list[str] - Lista de etiquetas (opcional)
    :param priority: str - "low-priority", "medium-priority" o "high-priority"
    """
    try:
        if not title.strip():
            raise ValueError("El título no puede estar vacío.")
        if not body.strip():
            body = "Tarea generada automáticamente."

        cmd = ["gh", "issue", "create", "--repo",
               GITHUB_REPO, "--title", title, "--body", body]

        # Unificar todas las etiquetas
        all_labels = labels or []
        if priority:
            all_labels.append(priority)

        for lbl in all_labels:
            ensure_label_exists(GITHUB_REPO, lbl)

        if all_labels:
            # GitHub CLI espera una sola string con etiquetas separadas por comas
            labels_str = ",".join(all_labels)
            cmd += ["--label", labels_str]

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)

        output = result.stdout.strip()
        print(f"🔗 Salida gh:\n{output}")

        match = re.search(r'/issues/(\d+)', output)
        if not match:
            raise ValueError(
                "No se pudo extraer el número del issue de la salida")

        issue_number = int(match.group(1))
        issue_id = get_issue_id(issue_number)

        return issue_number, issue_id
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear el issue: {e.stderr}")
        if e.__cause__:
            print(f"🔍 Causa: {e.__cause__}")
        raise
    except ValueError as ve:
        print(f"❌ Error de validación: {ve}")
        if ve.__cause__:
            print(f"🔍 Causa: {ve.__cause__}")
        raise


def create_issues(issues, interactive=True):
    gh_login()

    GITHUB_REPO = get_GITHUB_REPO()

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
        body = body.strip()
        if not body:
            body = "Tarea generada automáticamente."

        body += f"\n\n{context}"
        print(f"\n📝 Creando issue: {title}")
        issue_number, issue_id = create_issue(
            GITHUB_REPO,
            title,
            body,
            labels=["low-priority"]
        )
        print(f"Issue creado #{issue_number}:{title} con ID {issue_id}")
        print(f"🔗 Creando backlog: {title}")
        add_issue_to_project(issue_number, labels=["low-priority"])
        print(f"✅ Issue #{issue_number} creado y agregado al proyecto.")

        # ✅ Si todo salió bien, marcamos el TODO como migrado:
        mark_todo_as_migrated(file, line)


def mark_todo_as_migrated(file_path, line_number):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if line_number - 1 >= len(lines):
            print(
                f"⚠️ Línea {line_number} fuera de rango en {file_path}, no se actualiza.")
            return

        timestamp = int(__import__('time').time())
        migrated_tag = f"#MIGRATED-TODO-{timestamp}"

        lines[line_number - 1] = re.sub(r"#\s*TODO", migrated_tag,
                                        lines[line_number - 1], count=1, flags=re.IGNORECASE)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✏️ TODO en {file_path}:{line_number} marcado como migrado.")
    except Exception as e:
        print(
            f"❌ Error al marcar TODO como migrado en {file_path}:{line_number}: {e}")


def gh_login():
    try:
        subprocess.run(["gh", "auth", "status"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ No estás autenticado en GitHub CLI. Por favor, ejecuta 'gh auth login' para autenticarte.")
        exit(1)


# @click.command()
# @click.option('--auto', default=False, is_flag=True, help="Crear los issues automáticamente sin interacción")
def main(auto):
    print("🚀 Buscando TODOs...")
    issues = find_todos(base_path="/app")

    print(f"\n🔍 Se encontraron {len(issues)} TODOs.")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['title']} ({issue['file']}:{issue['line']})")
        if issue['body']:
            print(f"   {issue['body']}")

    if not issues:
        print("❌ No se encontraron TODOs para convertir en issues.")
        exit(1)

    create_issues(issues, interactive=not auto)


if __name__ == "__main__":
    auto = False  # Forzar a no usar auto para pruebas
    main(auto=auto)
