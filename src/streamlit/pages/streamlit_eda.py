
import streamlit as st
import pandas as pd
import eda_utils as eda
import export_utils as ex

st.set_page_config(page_title="EDA Chess Trainer", layout="wide")

st.title("📊 Análisis Exploratorio de Datos - Chess Trainer")

# Cargar el dataset
st.sidebar.header("Configuración")
uploaded_file = st.sidebar.file_uploader("Cargar archivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Dataset cargado correctamente")

    st.subheader("🔍 Vista previa del dataset")
    st.dataframe(df.head())

    # Secciones disponibles
    st.subheader("🧠 Matriz de correlación")
    if st.button("Mostrar correlación"):
        eda.show_correlation_matrix(df)

    st.subheader("📚 Resumen por categorías")
    if st.button("Mostrar agrupamientos"):
        eda.group_summary(df)

    st.subheader("📄 Exportar resumen a PDF")
    if st.button("Exportar PDF"):
        ex.export_summary_to_pdf(df, filename="eda_chess_summary.pdf")
        st.success("📁 PDF generado como 'eda_chess_summary.pdf'")

    st.subheader("🧪 Lanzar D-Tale")
    if st.button("Abrir D-Tale"):
        eda.run_dtale(df)
        st.info("🌐 D-Tale se abrirá en tu navegador.")
else:
    st.warning("📂 Cargá un archivo CSV desde la barra lateral para comenzar.")
