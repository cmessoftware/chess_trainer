
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sweetviz
from ydata_profiling import ProfileReport
from autoviz.AutoViz_Class import AutoViz_Class
import dtale


import pandas as pd

def coerce_schema_types(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura los tipos correctos antes de validar con Pandera."""
    
    int_columns = [
        "move_number", "num_pieces", "branching_factor", "self_mobility", "opponent_mobility",
        "has_castling_rights", "move_number_global", "is_repetition", "is_low_mobility",
        "is_center_controlled", "is_pawn_endgame"
    ]
    
    float_columns = [
        "material_balance", "material_total", "score_diff"
    ]
    
    string_columns = [
        "game_id", "fen", "move_san", "move_uci", "phase", "player_color",
        "tags", "site", "event", "date", "white_player", "black_player", "result"
    ]
    
    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df


def clean_and_prepare_dataset(df):
    # Asegurar que 'num_pieces' sea int para cumplir el esquema de validación
    if 'num_pieces' in df.columns:
        df['num_pieces'] = df['num_pieces'].astype('int64')
    # df.dropna(subset=["game_id", "move_number", "fen", "move_uci"], inplace=True)
    # Limpiar espacios en valores de columnas string
    df["phase"] = df["phase"].str.strip()
    
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df.columns = [col.strip() for col in df.columns]
    df["player_color"] = df["player_color"].replace({1: "white", 0: "black"})

    # Drop rows where essential fields are missing
    df.dropna(subset=["game_id", "move_number", "fen", "move_uci"], inplace=True)

    # Fill nulls in non-critical fields
    df["score_diff"] = df["score_diff"].fillna(0)
    df["tags"] = df["tags"].fillna("")
    df["event"] = df["event"].fillna("unknown")
    df["site"] = df["site"].fillna("unknown")
    df["date"] = df["date"].fillna("unknown")
    df["white_player"] = df["white_player"].fillna("unknown")
    df["black_player"] = df["black_player"].fillna("unknown")
    df["result"] = df["result"].fillna("unknown")

    # Convert binary/boolean flags
    bool_fields = [
        "has_castling_rights", "is_repetition", "is_low_mobility",
        "is_center_controlled", "is_pawn_endgame"
    ]
    for col in bool_fields:
        df[col] = df[col].fillna(0).astype(int)

    return df


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
