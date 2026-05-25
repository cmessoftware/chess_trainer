# Chess Error Level Classifier API

API service para clasificar el nivel de errores en partidas de ajedrez usando Machine Learning.

## Estructura del Servicio

```
src/api/
├── chess_error_classifier_api.py    # API principal FastAPI
├── requirements_api.txt             # Dependencias Python
├── start_api.ps1                   # Script inicio Windows
├── start_api.sh                    # Script inicio Linux/Mac
└── README.md                       # Esta documentación
```

## Instalación y Uso

### Windows (PowerShell)
```powershell
cd src/api
./start_api.ps1
```

### Linux/Mac
```bash
cd src/api
chmod +x start_api.sh
./start_api.sh
```

### Manual
```bash
cd src/api
pip install -r requirements_api.txt
uvicorn chess_error_classifier_api:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints Disponibles

### 1. Información del Modelo
```http
GET /model/info
```

### 2. Predicción Individual
```http
POST /predict
Content-Type: application/json

{
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
```

### 3. Predicción Batch
```http
POST /predict/batch
Content-Type: application/json

[
  { /* juego 1 */ },
  { /* juego 2 */ },
  // ...
]
```

## Respuestas

### Predicción Individual
```json
{
  "error_level": 1,
  "error_level_name": "Light Errors",
  "confidence": 0.7234,
  "probabilities": {
    "No Errors": 0.1456,
    "Light Errors": 0.7234,
    "Moderate Errors": 0.1156,
    "Severe Errors": 0.0154
  }
}
```

## Acceso a la Documentación

Una vez iniciado el servicio:
- **API Base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Requisitos

- Python 3.8+
- Modelo entrenado en `../../models/`
- Dependencias listadas en `requirements_api.txt`

## Notas

- El servicio carga automáticamente el mejor modelo disponible
- Incluye feature engineering básico para nuevas predicciones
- Soporta predicciones individuales y en lote
- Documentación interactiva con Swagger UI