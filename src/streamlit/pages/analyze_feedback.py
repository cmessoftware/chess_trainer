from sklearn.calibration import LabelEncoder
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

def show():
    st.title("Análisis de feedback de entrenamiento")
    
    folder = Path("data/feedback_logs")
    feedback_files = list(folder.glob("*.json"))

    if not feedback_files:
        st.warning("No hay archivos de feedback registrados.")
        return

    file_names = [f.name for f in feedback_files]
    selected_file = st.selectbox("Seleccioná una sesión", file_names)
    
    with open(folder / selected_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    feedback = data.get("feedback_log", [])
    if not feedback:
        st.info("Este archivo no contiene jugadas evaluadas.")
        return

    df = pd.DataFrame(feedback)

    # Mostrar tabla
    st.subheader("Tabla de jugadas evaluadas")
    st.dataframe(df)

    # Conteo de clasificaciones
    st.subheader("Distribución de feedback")
    counts = df["classification"].value_counts()

    fig, ax = plt.subplots()
    sns.barplot(x=counts.index, y=counts.values, ax=ax)
    ax.set_ylabel("Cantidad de jugadas")
    ax.set_xlabel("Clasificación")
    st.pyplot(fig)

    # Mostrar top jugadas con mayor pérdida de score
    st.subheader("Top 5 jugadas con mayor pérdida de evaluación")
    df["score_diff"] = df["score_after"] - df["score_before"]
    worst = df.sort_values(by="score_diff").head(5)
    st.table(worst[["index", "move", "classification", "score_before", "score_after", "score_diff"]])


    st.subheader("Exportar todo el feedback como dataset")

    if st.button("Exportar todos los logs a CSV"):
        merged = []
        for file in feedback_files:
            with open(folder / file, "r", encoding="utf-8") as f:
                content = json.load(f)
                for entry in content.get("feedback_log", []):
                    entry["exercise_id"] = content.get("exercise_id", file.stem)
                    entry["line_index"] = content.get("line_index", 0)
                    entry["timestamp"] = content.get("timestamp", "")
                    merged.append(entry)

        if not merged:
            st.warning("No se encontraron datos válidos.")
        else:
            df_merged = pd.DataFrame(merged)
            output_path = folder / "all_feedback.csv"
            df_merged.to_csv(output_path, index=False)
            st.success(f"Archivo exportado: {output_path}")
            st.dataframe(df_merged.head(10))

    st.subheader("Exportar dataset ML-ready")

    if st.button("Generar dataset para entrenamiento ML"):
        merged = []

        for file in feedback_files:
            with open(folder / file, "r", encoding="utf-8") as f:
                content = json.load(f)
                for entry in content.get("feedback_log", []):
                    entry["exercise_id"] = content.get("exercise_id", file.stem)
                    entry["timestamp"] = content.get("timestamp", "")
                    merged.append(entry)

        if not merged:
            st.warning("No se encontraron datos válidos.")
        else:
            df = pd.DataFrame(merged)
            df["score_diff"] = df["score_after"] - df["score_before"]
            df["is_capture"] = df["move"].str.contains("x").astype(int)
            df["is_check"] = df["move"].str.contains(r"\+|#").astype(int)
            df["is_promotion"] = df["move"].str.contains("=").astype(int)
            df["same_as_best"] = (df["move"] == df["best_move"]).astype(int)

            def extract_piece(san):
                if not san or not isinstance(san, str):
                    return "U"
                if san[0] in "KQRNB":
                    return san[0]
                return "P"

            df["piece"] = df["move"].apply(extract_piece)
            df["piece_code"] = LabelEncoder().fit_transform(df["piece"])
            df["classification_code"] = LabelEncoder().fit_transform(df["classification"])

            output = folder / "training_dataset.csv"
            df.to_csv(output, index=False)
            st.success(f"Archivo ML exportado: {output}")
            st.dataframe(df[["move", "classification", "score_diff", "piece", "is_capture", "same_as_best"]].head())
