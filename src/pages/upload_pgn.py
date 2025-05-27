import streamlit as st
from pathlib import Path

st.title("Cargar archivo PGN")

uploaded_file = st.file_uploader("Subí un archivo PGN", type="pgn")
if uploaded_file:
    Path("data/games").mkdir(parents=True, exist_ok=True)
    with open(f"data/games/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"Archivo guardado como data/games/{uploaded_file.name}")
