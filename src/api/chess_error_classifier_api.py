from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import List, Dict, Any

# Inicializar FastAPI
app = FastAPI(
    title="Chess Error Level Classifier",
    description="API para clasificar el nivel de errores en partidas de ajedrez",
    version="1.0.0"
)

# Cargar modelo y metadata al iniciar
MODEL_PATH = Path("../../models")
model = None
metadata = None

@app.on_event("startup")
async def load_model():
    global model, metadata
    try:
        # Buscar archivos del modelo
        model_files = list(MODEL_PATH.glob("best_chess_error_classifier_*.pkl"))
        if not model_files:
            raise FileNotFoundError("No se encontró archivo del modelo")
        
        model_file = model_files[0]
        metadata_file = MODEL_PATH / f"metadata_{model_file.stem}.json"
        
        # Cargar modelo
        model = joblib.load(model_file)
        
        # Cargar metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            
        print(f"✅ Modelo cargado: {metadata['model_name']}")
        print(f"✅ Accuracy: {metadata['performance']['test_accuracy']:.4f}")
        
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        raise

# Modelos Pydantic para validación
class ChessGameInput(BaseModel):
    white_elo: float
    black_elo: float
    elo_avg: float
    elo_diff: float
    pgn_length: int
    move_count_estimate: int
    year: int
    month: int
    day: int
    skill_level: str
    source: str
    time_category: str
    
    class Config:
        schema_extra = {
            "example": {
                "white_elo": 1500.0,
                "black_elo": 1450.0,
                "elo_avg": 1475.0,
                "elo_diff": 50.0,
                "pgn_length": 1200,
                "move_count_estimate": 45,
                "year": 2024,
                "month": 6,
                "day": 15,
                "skill_level": "intermediate",
                "source": "personal",
                "time_category": "standard"
            }
        }

class PredictionResponse(BaseModel):
    error_level: int
    error_level_name: str
    confidence: float
    probabilities: Dict[str, float]

class ModelInfo(BaseModel):
    model_name: str
    model_type: str
    classes: List[str]
    feature_count: int
    test_accuracy: float
    training_date: str

# Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "message": "Chess Error Level Classifier API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    if model is None or metadata is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    return ModelInfo(
        model_name=metadata["model_name"],
        model_type=metadata["model_type"],
        classes=metadata["class_names"],
        feature_count=metadata["feature_count"],
        test_accuracy=metadata["performance"]["test_accuracy"],
        training_date=metadata["training_date"]
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_error_level(game: ChessGameInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    try:
        # Convertir input a DataFrame
        input_data = pd.DataFrame([game.dict()])
        
        # Aplicar feature engineering básico
        input_data["elo_ratio"] = np.where(input_data["black_elo"] > 0,
                                          input_data["white_elo"] / input_data["black_elo"], 1)
        input_data["is_weekend"] = False  # Placeholder
        input_data["season"] = "Summer"   # Placeholder
        input_data["game_length_category"] = "Medium"  # Placeholder
        input_data["is_decisive"] = 1
        input_data["white_advantage"] = 0
        input_data["experience_level"] = "Intermediate"
        input_data["elo_gap_percentile"] = 2
        
        # Realizar predicción
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]
        
        # Preparar respuesta
        class_names = ["No Errors", "Light Errors", "Moderate Errors", "Severe Errors"]
        prob_dict = {class_names[i]: float(prob) for i, prob in enumerate(probabilities)}
        
        return PredictionResponse(
            error_level=int(prediction),
            error_level_name=class_names[prediction],
            confidence=float(max(probabilities)),
            probabilities=prob_dict
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en predicción: {str(e)}")

@app.post("/predict/batch")
async def predict_batch(games: List[ChessGameInput]):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    try:
        predictions = []
        for game in games:
            # Convertir cada juego y predecir
            input_data = pd.DataFrame([game.dict()])
            
            # Feature engineering básico
            input_data["elo_ratio"] = np.where(input_data["black_elo"] > 0,
                                              input_data["white_elo"] / input_data["black_elo"], 1)
            input_data["is_weekend"] = False
            input_data["season"] = "Summer"
            input_data["game_length_category"] = "Medium"
            input_data["is_decisive"] = 1
            input_data["white_advantage"] = 0
            input_data["experience_level"] = "Intermediate"
            input_data["elo_gap_percentile"] = 2
            
            prediction = model.predict(input_data)[0]
            probabilities = model.predict_proba(input_data)[0]
            
            class_names = ["No Errors", "Light Errors", "Moderate Errors", "Severe Errors"]
            prob_dict = {class_names[i]: float(prob) for i, prob in enumerate(probabilities)}
            
            predictions.append({
                "error_level": int(prediction),
                "error_level_name": class_names[prediction],
                "confidence": float(max(probabilities)),
                "probabilities": prob_dict
            })
        
        return {"predictions": predictions}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en predicción batch: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)