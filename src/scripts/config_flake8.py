import os

flake8_config = """[flake8]
max-line-length = 120
exclude = .git,__pycache__,env,venv,.venv,build,dist
"""

project_root = os.getcwd()
config_path = os.path.join(project_root, ".flake8")

if not os.path.exists(config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(flake8_config)
    print(f"✅ Archivo .flake8 creado en: {config_path}")
else:
    print(f"⚠️ Ya existe .flake8 en: {config_path}")
