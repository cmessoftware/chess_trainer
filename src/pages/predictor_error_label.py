import pandas as pd
from datetime import datetime
from pathlib import Path

if st.button("Guardar predicción"):
    pred = predict_error_label(features)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "timestamp": timestamp,
        "score_diff": score_diff,
        "branching_factor": branching_factor,
        "self_mobility": self_mobility,
        "opponent_mobility": opponent_mobility,
        "material_balance": material_balance,
        "is_low_mobility": int(is_low_mobility),
        "is_equal_material": int(is_equal_material),
        "phase": phase,
        "player_color": player_color,
        "predicted_label": pred
    }

    output_path = Path("data/predicciones.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        df = pd.read_csv(output_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])

    df.to_csv(output_path, index=False)
    st.success(f"Predicción guardada en {output_path}")
