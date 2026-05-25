import os
from pathlib import Path
import streamlit as st
import dotenv

dotenv.load_dotenv()
PGN_PATH = os.environ.get("PGN_PATH")

def upload_file(label: str = "📂 Subí un archivo", type = "pgn",file_path=PGN_PATH , content: bool = False):
    uploaded_file = st.file_uploader(label, type=type)
    if uploaded_file:
        Path(file_path).mkdir(parents=True, exist_ok=True)
        save_path = Path(file_path) / uploaded_file.name

        if save_path.exists():
            st.warning(f"⚠️ Ya existe un archivo llamado {uploaded_file.name}. Se sobrescribirá.")

        file_bytes = uploaded_file.read()
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        st.success(f"✅ Archivo guardado: {save_path}")

        if content:
            try:
                decoded = file_bytes.decode("utf-8")
                return decoded
            except UnicodeDecodeError:
                st.error("❌ Error al decodificar el contenido del archivo como UTF-8.")
                return None
        return file_bytes.decode("utf-8")