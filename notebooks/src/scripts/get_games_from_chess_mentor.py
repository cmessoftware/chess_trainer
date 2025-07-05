import os
import requests
from bs4 import BeautifulSoup

HTML_FILE = "/app/src/data/chess_mentor.html"
LINKS_FILE = "pgn_links.txt"
DEST_FOLDER = "/app/src/data/games/fide"

# 1. Crear la carpeta de destino si no existe
os.makedirs(DEST_FOLDER, exist_ok=True)

# 2. Parsear el HTML y extraer los enlaces .zip
with open(HTML_FILE, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Filtrar solo los .zip que estén bajo /players/
links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.startswith("https://www.pgnmentor.com/players/") and href.endswith(".zip"):
        links.append(href)

# 3. Guardar los enlaces en un archivo de texto
with open(LINKS_FILE, "w", encoding="utf-8") as f:
    for link in links:
        f.write(link + "\n")

print(f"✅ Se guardaron {len(links)} enlaces en {LINKS_FILE}")

# 4. Descargar los archivos ZIP
for link in links:
    filename = os.path.basename(link)
    output_path = os.path.join(DEST_FOLDER, filename)

    if os.path.exists(output_path):
        print(f"🟡 Ya existe: {filename}, se omite.")
        continue

    try:
        print(f"⬇️ Descargando {filename}...")
        response = requests.get(link, timeout=15)
        response.raise_for_status()
        with open(output_path, "wb") as out_file:
            out_file.write(response.content)
        print(f"✅ Guardado en {output_path}")
    except Exception as e:
        print(f"❌ Error al descargar {link}: {e}")
