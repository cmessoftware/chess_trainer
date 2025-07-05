import json
from pathlib import Path
from db.repository.study_repository import StudyRepository

STUDY_JSON_DIR = Path("/app/src/data/studies")
repo = StudyRepository()

json_files = list(STUDY_JSON_DIR.glob("*.json"))
print(f"📁 Archivos encontrados: {len(json_files)}")

for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = {"study_id", "title", "description", "tags", "position_sequence"}
        if not required_keys.issubset(data):
            print(f"⚠️ Archivo omitido por campos faltantes: {file.name}")
            continue

        repo.save_study(data)
        print(f"✅ Estudio migrado: {data['study_id']}")

    except Exception as e:
        print(f"❌ Error procesando {file.name}: {e}")

print("✔️ Migración finalizada.")
