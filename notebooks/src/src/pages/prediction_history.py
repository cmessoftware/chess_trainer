import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

st.title("Historial de predicciones tácticas")

csv_path = Path("data/predicciones.csv")

if not csv_path.exists():
    st.info("Todavía no hay predicciones registradas.")
else:
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    st.subheader("Vista previa")
    st.dataframe(df.tail(20))

    st.subheader("Distribución global de etiquetas")
    sns.countplot(data=df, x="predicted_label", order=df["predicted_label"].value_counts().index)
    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("Evolución diaria")
    etiquetas_por_fecha = df.groupby(df["timestamp"].dt.date)["predicted_label"].value_counts().unstack().fillna(0)
    etiquetas_por_fecha.plot(kind="bar", stacked=True, figsize=(10, 5))
    st.pyplot(plt.gcf())
    plt.clf()
