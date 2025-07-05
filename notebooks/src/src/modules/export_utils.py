import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns


def export_summary_to_pdf(df, filename="eda_summary.pdf"):
    with PdfPages(filename) as pdf:
        # 1. Matriz de correlación
        plt.figure(figsize=(10, 8))
        corr = df.corr(numeric_only=True)
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Matriz de Correlación")
        pdf.savefig()
        plt.close()

        # 2. Branching factor por tipo de error
        plt.figure(figsize=(8, 5))
        df.groupby("error_label")["branching_factor"].mean().plot(
            kind="bar", color="skyblue")
        plt.title("Branching Factor Promedio por Tipo de Error")
        plt.ylabel("Branching Factor")
        pdf.savefig()
        plt.close()

        # 3. Errores por fase de juego
        plt.figure(figsize=(8, 5))
        df.groupby("phase")["error_label"].value_counts(
        ).unstack().plot(kind="bar", stacked=True)
        plt.title("Distribución de Errores por Fase de Juego")
        plt.ylabel("Cantidad")
        pdf.savefig()
        plt.close()

        # 4. Movilidad promedio
        plt.figure(figsize=(8, 5))
        df.groupby("player_color")[
            ["self_mobility", "opponent_mobility"]].mean().plot(kind="bar")
        plt.title("Movilidad Promedio por Color")
        plt.ylabel("Cantidad de Jugadas")
        pdf.savefig()
        plt.close()


if __name__ == "__main__":
    # Example usage: replace 'your_data.csv' with your actual CSV file
    df = pd.read_csv("your_data.csv")
    export_summary_to_pdf(df)
