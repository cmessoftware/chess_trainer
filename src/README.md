# ♟ chess_trainer – Análisis y entrenamiento con partidas de élite

Este proyecto automatiza la importación, análisis, etiquetado y entrenamiento a partir de miles de partidas de jugadores de élite (ELO >2500), combinando análisis táctico con exploración visual y generación de ejercicios.

---

## 📦 Requisitos

- Python 3.10+
- Paquetes:
  ```bash
  pip install -r requirements.txt
  ```
- Stockfish instalado (Linux):
  ```bash
  sudo apt install stockfish
  ```

---

## 📂 Estructura del proyecto

```
chess_trainer/
├── notebooks/                   # Exploración, clustering, predicciones
│   ├── eda_analysis.ipynb
│   ├── pca_clustering_chess.ipynb
│   └── analyze_predictions.ipynb
├── src/
│   ├── data/                    # Base y PGNs de Lichess Elite
│   │   ├── chess_trainer.db
│   │   └── games/*.pgn
│   ├── models/                  # Modelos entrenados
│   │   └── error_label_model.pkl
│   ├── modules/                 # Funcionalidad central (reusable)
│   │   ├── generate_full_report.py
│   │   ├── extractor.py
│   │   └── eda_utils.py
│   ├── scripts/                 # Scripts de ejecución autónomos
│   │   ├── run_pipeline.sh
│   │   ├── auto_tag_games.py
│   │   ├── analyze_errors_from_db.py
│   │   ├── generate_exercises_from_elite.py
│   │   ├── save_games_to_db.py
│   │   └── inspect_db.py
│   ├── pages/                   # Páginas de Streamlit
│   │   ├── elite_explorer.py
│   │   ├── elite_training.py
│   │   ├── elite_stats.py
│   │   └── streamlit_eda.py
│   └── tests/                   # Tests automatizados con pytest
│       ├── test_elite_pipeline.py
│       └── test_tag_games.py
├── .env                         # Ruta configurada a la base
├── requirements.txt             # Dependencias
└── README.md
```

---

## 🚀 Flujo recomendado

```bash
# Guardar partidas en base
python src/scripts/save_games_to_db.py --input src/data/games/lichess_elite_2020-05.pgn

# Etiquetar, analizar, generar ejercicios y dataset acumulativo
bash src/scripts/run_pipeline.sh

# Ejecutar explorador visual
streamlit run src/pages/elite_explorer.py
```

---

## 🧪 Tests automatizados

Este proyecto usa `pytest` para verificar:
- Estructura de la base
- Existencia de etiquetas
- Validez de ejercicios JSON

```bash
pytest src/tests/
```

---

## 🧠 Variables de entorno

Definí la ruta a la base SQLite en un `.env`:

```env
CHESS_TRAINER_DB=src/data/chess_trainer.db
STOCKFISH_PATH=/usr/games/stockfish
```

Y cargala con:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 Análisis exploratorio (EDA)

Explorá y visualizá el dataset con:

📄 `notebooks/eda_analysis.ipynb`

Incluye:
- Distribución de errores
- Correlaciones
- Movilidad vs score
- Aperturas frecuentes

---

## 📤 Publicar partidas en Lichess

Con `publish_to_lichess.py` podés subir partidas desde la DB como estudios. Necesitás un token Lichess con permisos `study:write`.

---

## 📌 Autor

> Proyecto creado por Sergio para la diplomatura de Ciencia de Datos  
> Contacto: [agregá tu correo o GitHub si querés]
