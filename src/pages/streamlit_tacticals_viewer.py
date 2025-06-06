
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

st.title("Resumen visual del dataset táctico")

uploaded_file = st.file_uploader("Subí un archivo CSV enriquecido", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Archivo cargado: {uploaded_file.name}")
    st.write("Dimensiones del dataset:", df.shape)

    if "error_label" in df.columns:
        st.subheader("Distribución de etiquetas tácticas")
        st.dataframe(df["error_label"].value_counts())
        sns.countplot(data=df, x="error_label", order=df["error_label"].value_counts().index)
        plt.xticks(rotation=30)
        st.pyplot(plt.gcf())
        plt.clf()

    if "score_diff" in df.columns:
        st.subheader("Distribución de score_diff")
        sns.histplot(data=df, x="score_diff", bins=30, kde=True)
        st.pyplot(plt.gcf())
        plt.clf()

    if "branching_factor" in df.columns and "error_label" in df.columns:
        st.subheader("Boxplot: branching_factor vs error_label")
        sns.boxplot(data=df, x="error_label", y="branching_factor")
        plt.xticks(rotation=30)
        st.pyplot(plt.gcf())
        plt.clf()
else:
    st.info("Esperando archivo CSV...")
