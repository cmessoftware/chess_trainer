import pandas as pd


def get_move_number_from_df(df_or_list, default: int = 0) -> int:
    """
    Extrae move_number desde un DataFrame o lista de dicts.
    """
    try:
        if isinstance(df_or_list, list) and df_or_list:
            return int(df_or_list[0].get("move_number", default))
        elif isinstance(df_or_list, pd.DataFrame) and not df_or_list.empty:
            return int(df_or_list.iloc[0]["move_number"])
    except Exception as e:
        print(f"⚠️ Error extrayendo move_number: {e}")
    return default
