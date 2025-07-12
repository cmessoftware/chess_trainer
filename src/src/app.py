import streamlit as st
from pathlib import Path
import base64

from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env


st.set_page_config(page_title="Chess Trainer", layout="wide")

st.markdown("<h1 style='text-align: center;'>♞ Chess Trainer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Entrená, analizá y mejorá tus decisiones tácticas.</p>", unsafe_allow_html=True)
st.markdown("---")

# 📦 Tarjetas de navegación
col1, col2, col3 = st.columns(3)

with col1:
    st.header("🧠 Entrenamiento táctico")
    st.markdown("Revisá ejercicios tácticos y entrená con feedback inteligente.")
    if st.button("Ir a entrenamiento"):
        st.switch_page("pages/tactics.py")

    st.header("🛠️ Crear ejercicios")
    st.markdown("Diseñá tus propios ejercicios tácticos desde el tablero.")
    if st.button("Ir a creador"):
        st.switch_page("pages/create_exercise.py")

with col2:
    st.header("📊 Analizar dataset")
    st.markdown("Explorá visualmente tu dataset enriquecido con tácticas.")
    if st.button("Ver resumen"):
        st.switch_page("pages/summary_viewer.py")

    st.header("⏱️ Subir PGN")
    st.markdown("Subí archivos PGN desde múltiples fuentes para generar datasets.")
    if st.button("Ir a subida"):
        st.switch_page("pages/upload_pgn.py")

with col3:
    st.header("🤖 Predecir errores")
    st.markdown("Probá el modelo y predecí etiquetas tácticas desde valores.")
    if st.button("Ir al predictor"):
        st.switch_page("pages/predictor_error_label.py")

    st.header("📝 Historial de predicciones")
    st.markdown("Revisá las predicciones realizadas con el modelo.")
    if st.button("Ver historial"):
        st.switch_page("pages/prediction_history.py")

st.markdown("---")
st.caption("Creado por Sergio – Proyecto Chess Trainer (versión base estable)")
