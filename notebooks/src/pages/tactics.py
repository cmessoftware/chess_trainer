import streamlit as st
from tactical_analysis import load_all_tactics
from pages.tactics_viewer import show_interactive_line_viewer

st.title("Entrenamiento táctico")

tactics = load_all_tactics()
if not tactics:
    st.warning("No hay ejercicios tácticos cargados.")
else:
    selected = st.selectbox("Elegí ejercicio", tactics,
                            format_func=lambda x: x["title"])
    show_interactive_line_viewer(
        selected["fen"],
        selected["lines"],
        tactic_id=selected.get("id", selected["title"]),
        feedback_mode=True
    )
