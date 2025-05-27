
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sweetviz
from ydata_profiling import ProfileReport
from autoviz.AutoViz_Class import AutoViz_Class
import dtale

def run_autoviz(df, target="error_label"):
    AV = AutoViz_Class()
    return AV.AutoViz(
        filename="", sep=",", depVar=target, dfte=df,
        header=0, verbose=1, chart_format="bokeh"
    )

def run_profiling(df, output_file="eda_report.html"):
    profile = ProfileReport(df, title="EDA Chess Trainer", explorative=True)
    profile.to_file(output_file)
    return profile

def run_sweetviz(df, output_file="sweetviz_report.html"):
    report = sweetviz.analyze(df)
    report.show_html(output_file)
    return report

def show_correlation_matrix(df):
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Matriz de Correlación Numérica")
    plt.tight_layout()
    plt.show()

def group_summary(df):
    print("\nDistribución de errores por fase del juego:")
    print(df.groupby("move_phase")["error_label"].value_counts(normalize=True).unstack().round(2))

    print("\nEstadísticas de movilidad por color:")
    print(df.groupby("player_color")[["self_mobility", "opponent_mobility"]].describe())

    print("\nPromedio de branching factor por tipo de error:")
    print(df.groupby("error_label")["branching_factor"].mean())

    print("\nErrores según control del centro:")
    print(df.pivot_table(values="error_label", index="is_center_controlled", aggfunc="count"))

def run_dtale(df):
    dtale.show(df).open_browser()
