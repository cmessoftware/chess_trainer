from __future__ import annotations

import pandas as pd


def summarize_error_distribution(df: pd.DataFrame) -> dict[str, int]:
    if "error_label" not in df.columns:
        return {}
    return df["error_label"].astype(str).str.lower().value_counts().to_dict()
