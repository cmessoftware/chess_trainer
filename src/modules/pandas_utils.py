import pandas as pd


def get_feature_from_df(df_or_list,feature_name: str) -> int:
    """
    Extrae move_number desde un DataFrame o lista de dicts.
    """
    if type(feature_name) is str:
        default = ""
    elif type(feature_name) is int:
        default = 0
    
    try:
        if isinstance(df_or_list, list) and df_or_list:
            return int(df_or_list[0].get(feature_name, default))
        elif isinstance(df_or_list, pd.DataFrame) and not df_or_list.empty:
            return int(df_or_list.iloc[0][feature_name])
    except Exception as e:
        print(f"⚠️ Error extrayendo {feature_name}: {e}")
    return default
