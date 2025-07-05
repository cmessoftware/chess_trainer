import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
import joblib
import mlflow
import mlflow.sklearn
from mlflow_config import init_mlflow

# Inicia MLFlow
init_mlflow()

# Carga dataset
df = pd.read_csv("data/training_dataset.csv")
X = df.drop(columns=["error_label"])
y = df["error_label"]

# Entrenamiento con tracking
with mlflow.start_run():
    
    # Hiperparámetros (podés variar estos)
    n_estimators = 100
    max_depth = 5
    
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X, y)
    
    # Guardá el modelo
    joblib.dump(model, "models/error_predictor.pkl")
    mlflow.sklearn.log_model(model, "model")

    # Métricas simples (ejemplo)
    y_pred = model.predict(X)
    f1 = f1_score(y, y_pred, average='weighted')
    mlflow.log_metric("f1_train", f1)
    
    print(f"F1 score (train): {f1}")
