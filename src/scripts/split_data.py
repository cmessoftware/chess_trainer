import pandas as pd
import mlflow
from mlflow_config import init_mlflow
from sklearn.model_selection import train_test_split

# Inicia MLFlow
init_mlflow()

df = pd.read_parquet("data/training_dataset.parquet")
X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)

# Guarda datasets
X_train.to_csv("data/splits/training.parquet", index=False)
X_test.to_csv("data/splits/test.parquet", index=False)

# Log en MLFlow
with mlflow.start_run(run_name="Dataset Split"):
    mlflow.log_artifact("data/splits/train.parquet", artifact_path="datasets")
    mlflow.log_artifact("data/splits/test.parquet", artifact_path="datasets")
