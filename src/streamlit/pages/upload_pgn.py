import os
import streamlit as st
from pathlib import Path

try:
    import dotenv
    dotenv.load_dotenv()  # Carga las variables del archivo .env
except ImportError:
    # dotenv is optional, continue without it
    pass

PGN_PATH = os.environ.get("PGN_PATH", "data/games/personal")
if not Path(PGN_PATH).exists():
    Path(PGN_PATH).mkdir(parents=True, exist_ok=True)

st.title("Cargar archivo PGN")

uploaded_file = st.file_uploader("Subí un archivo PGN", type="pgn")
if uploaded_file:
    Path(PGN_PATH).mkdir(parents=True, exist_ok=True)
    with open(f"{PGN_PATH}/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"Archivo guardado como data/games/{uploaded_file.name}")
