# CHESS TRAINER - Versión: v0.1.20-f9d0260

# ♟ chess_trainer – Análisis y entrenamiento con partidas de élite

Este proyecto automatiza la importación, análisis, etiquetado y entrenamiento a partir de miles de partidas de jugadores de élite (ELO >2300), combinando análisis táctico con exploración visual y generación de ejercicios.

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

## 🚀 Construcción de contenedores con scripts automáticos

Este proyecto incluye scripts para construir los contenedores de forma sencilla, sin necesidad de pasar parámetros manualmente.

Los contenedores disponibles son:

| Script               | Descripción                                | Imagen generada           |
|----------------------|--------------------------------------------|----------------------------|
| `build_app.sh`       | Construye el contenedor de la aplicación Streamlit | `chess_trainer_app`       |
| `build_notebooks.sh` | Construye el contenedor de JupyterLab con Keras y TensorFlow | `chess_trainer_notebooks` |

---

### 🛠️ Requisitos

- Docker versión **24.x** o superior (requerido para `--ignore-file`)
- Scripts con permisos de ejecución

Para dar permisos:

```bash
chmod +x build_app.sh build_notebooks.sh
```
---

## 🚀 Cómo construir los contenedores
**Para la aplicación Streamlit:**

```bash
./build_app.sh
```
**Para el entorno de JupyterLab:**

```bash
./build_notebooks.sh
```

## 📂 Estructura del proyecto

```
chess_trainer/
├── notebooks/                   # Exploración, agrupamiento, predicciones
│   ├── eda_analysis.ipynb
│   ├── pca_clustering_chess.ipynb
│   └── analyze_predictions.ipynb
├── src/
│   ├── data/                    # Base y PGNs de Lichess Elite
│   │   ├── chess_trainer.db
│   │   └── games/*.pgn
│   ├── models/                  # Modelos entrenados
│   │   └── error_label_model.pkl
│   ├── modules/                 # Funcionalidad central (reutilizable)
│   │   ├── generate_dataset.py
│   │   ├── extractor.py
│   │   └── eda_utils.py
│   ├── scripts/                 # Scripts de ejecución autónoma
│   │   ├── run_pipeline.sh
│   │   ├── auto_tag_games.py
│   │   ├── analyze_errors_from_games.py
│   │   ├── generate_exercises_from_elite.py
│   │   ├── save_games_to_db.py
|   |   |__ analize_games_tactics_paralell  
|   |   |__ generate_features_paralell
|   |   |__ generate_pgn_from_chess_server
│   │   └── inspect_db.py
|   |__ services/
│   │   ├── features_export_service.py
│   │   ├── get_lichess_studies.py
│   │   ├── study_importer_service.py
|   |__ tools/ 
│   │   ├── elite_explorer.py
|   |   |__create_issues_from_json
|   ├── pages/                   # Páginas de Streamlit
│   │   ├── elite_explorer.py
│   │   ├── elite_training.py
│   │   ├── elite_stats.py
│   │   └── streamlit_eda.py
│   └── tests/                   # Pruebas automatizadas con pytest
│       ├── test_elite_pipeline.py
│       └── test_tag_games.py
├── .env                         # Ruta configurada a la base
├── requirements.txt             # Dependencias
└── README.md
```

---

## 🚀 Flujo recomendado

```bash
# Guardar partidas en la base
python src/scripts/import_game.py --input src/data/games/lichess_elite_2020-05.pgn

# Etiquetar, analizar, generar ejercicios y dataset acumulativo
bash src/scripts/run_pipeline.sh

# Ejecutar explorador visual
streamlit run src/pages/elite_explorer.py
```

---

## 🧪 Pruebas automatizadas

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
STOCKFISH_PATH=/usr/games/stockfish’
```

Y cargala con:

```python
from dotenv import load_dotenv
load_dotenv()
```

---
## Configurar e implementar migraciones de base de datos usando Alembic y SqlAlchemy 
**Soporta múltiples motores como Sqlite, MySql, Postgres, MariaDb, etc.**

## 📦 Paso 1: Instalá Alembic si aún no lo hiciste
```bash
pip install alembic
```
## 📁 Paso 2: Inicializá Alembic en la raíz del proyecto (por ejemplo en /app)
```bash
cd /app
alembic init alembic
```
#### Esto crea una carpeta alembic/ y un archivo alembic.ini.

## 🛠️ Paso 3: Configurá alembic/env.py
#### Reemplazá el contenido de target_metadata y agregá tu engine.

#### En alembic/env.py
```python
from db.database import Base
from db import models  # asegurate que __init__.py importe todos los modelos

target_metadata = Base.metadata
```
## 🧩 Paso 4: Configurá la conexión a la base de datos
#### Editá alembic.ini y cambiá la línea sqlalchemy.url
```python
sqlalchemy.url = postgresql+psycopg2://usuario:password@localhost:5432/tu_base
```
#### O podés usar una variable de entorno si ya usás dotenv
#### sqlalchemy.url = env:CHESS_TRAINER_DB_URL

## 🧱 Paso 5: Generá el script de migración
```bash
alembic revision --autogenerate -m "Agregar columnas a Games"
```

## 🚀 Paso 6: Aplicá la migración a la base de datos
```bash
alembic upgrade head
```
## 🧽 Paso 7 (opcional): Revertí una migración
```bash
alembic downgrade -1
```
**Nota: el comando alembic se debe ejecutar en la misma carpeta donde está alembic.ini (ej: /app)**

---
# Uso de GIT LFS para almacenamiento de grandes datasets y modelos de ML

**Se elige GIT LFS para reutilizar la infraestructura, experiencia y credenciales de GitHub**

```bash
git lfs install
git lfs track "*.csv"
git add .gitattributes
git add /app/src/data/features_dataset_*.csv #O el path elegido para el dataset.
git commit -m "Agrego dataset al repo con Git LFS"
git push
```

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

Con `publish_to_lichess.py` podés subir partidas desde la base de datos como estudios. Necesitás un token de Lichess con permisos `study:write`.

---
### 🧠 Arquitectura del proyecto

![Arquitectura chess_trainer](../img/architecture.png)

---

## Estructura de training_dataset.csv

### 📊 Campos generados por `generate_features_from_game`

| Campo                | Origen / lógica                                                                 |
|----------------------|----------------------------------------------------------------------------------|
| `fen`                | `board.fen()` antes de la jugada                                                |
| `move_san`           | `board.san(move)`                                                               |
| `move_uci`           | `move.uci()`                                                                    |
| `material_balance`   | Diferencia de material (blancas - negras), usando valores `{P:1, N:3, B:3.25...}` |
| `material_total`     | Suma de material total en el tablero                                            |
| `num_pieces`         | Cantidad de piezas (excluye peones y reyes)                                     |
| `branching_factor`   | `len(legal_moves)` antes **+** después de la jugada                             |
| `self_mobility`      | `len(legal_moves)` del jugador **antes** del movimiento                         |
| `opponent_mobility`  | `len(legal_moves)` del oponente **después** de simular la jugada                |
| `phase`              | `"opening"` (≥24 piezas), `"middlegame"` (12–23), `"endgame"` (<12)             |
| `player_color`       | `"white"` o `"black"` según `board.turn`                                        |
| `has_castling_rights`| `int(board.has_castling_rights())` (0 o 1)                                      |
| `move_number`        | `board.fullmove_number`                                                         |
| `is_repetition`      | `int(board.is_repetition())` (1 si es repetición)                               |
| `is_low_mobility`    | `int(self_mobility <= 5)`                                                        |
| `is_center_controlled`| 1 si el jugador controla d4/e4/d5/e5 con alguna pieza                           |
| `is_pawn_endgame`    | 1 si solo hay reyes y peones en el tablero                                      |

## Diseño para el análisis de tácticas

| Aspecto                                  | Ventaja                                      |
|------------------------------------------|----------------------------------------------|
| profundidad por fase                     | Ahorra tiempo sin perder precisión           |
| multipv solo cuando hay muchas opciones  | No desperdicia recursos de CPU               |
| compare_to_best evita falsos positivos   | Mejora la calidad de las etiquetas           |
| classify_tactical_pattern sigue funcionando | Etiquetas clásicas como fork, pin, mate   |
| eval_cache                               | Evita evaluaciones repetidas por FEN         |

## Optimizaciones para acelerar el análisis táctico (reducir de días a horas de análisis) 
**Actualizado: 2025-06-02**

## ✅ Lista de optimizaciones en `tactical_analysis.py` - `chess_trainer`

| Nº | Optimización                                     | Estado     | Detalles / Comentarios                                                                 |
|----|--------------------------------------------------|------------|-----------------------------------------------------------------------------------------|
| 1️⃣ | 🔻 Reducir profundidad fija                      | ✅ Aplicado | Se usa `depth=6` para jugadas con `pre_tag`; y valores dinámicos según fase para el resto. |
| 2️⃣ | ⏭️ Omitir primeras jugadas                      | ✅ Aplicado | Si `move_number <= 6`, se salta el análisis. Controlado por `opening_move_threshold`.  |
| 3️⃣ | 🧠 Profundidad variable por fase                 | ✅ Aplicado | Usa `PHASE_DEPTHS` basado en la fase del juego (`opening`, `middlegame`, `endgame`).   |
| 4️⃣ | 🧮 Branching factor                              | ✅ Aplicado | Si `branching < 5`, se omite la jugada. Usado como indicador de baja complejidad.      |
| 5️⃣ | 🤖 MultiPV inteligente                           | ✅ Aplicado | Se usa `multipv=3` si `branching > 10`, y se adaptó `get_evaluation` y `parse_info`.    |
| 6️⃣ | 🧷 Análisis condicional por etiquetas previas    | ✅ Aplicado | Si `classify_simple_pattern` devuelve etiqueta, usa `depth=6` y `multipv=1`.           |
| 7️⃣ | ⛓️ Evitar análisis redundante (cache FEN)        | ✅ Aplicado | Usa `eval_cache` para no recalcular evaluaciones por FEN.                              |
| 8️⃣ | ⚡ Evitar jugadas forzadas (`is_forced_move`)     | 🔜 En progreso | Detectado en `evaluate_tactical_features()`, falta usarlo para saltar análisis.         |
| 9️⃣ | 🧪 Score diferencial preciso (`score_diff`)      | ✅ Aplicado | Usa `extract_score()` y ajusta según el color del jugador.                             |

---

## 📌 Otros puntos implementados

| Tema                           | Estado     | Comentarios                                                                 |
|--------------------------------|------------|-----------------------------------------------------------------------------|
| 🧩 `classify_simple_pattern`   | ✅ Reutilizado | Preclasificación táctica rápida (jaque, tenedor, clavada, etc).             |
| 🔄 `compare_to_best`           | ✅ Usado     | Compara jugada real con alternativas (`MultiPV`).                          |
| 🧠 `get_game_phase()`          | ✅ Usado     | Determina fase del juego (apertura, medio juego, final).                   |
| ⏱️ Decorador `@measure_execution_time` | ✅ Aplicado | En funciones clave para medir tiempos.                                     |
| 🧪 Prueba manual de `multipv`  | ✅ Confirmado | Stockfish devuelve `list[dict]` correctamente al usar `multipv > 1`.       |

---

## Separación de dataset según fuente.

```
/data/games/
    ├── personal/
    │   └── cmess1315_games_2020_2024.pgn
    ├── novice/
    │   └── lichess_novice_2023.pgn
    ├── elite/
    │   └── lichess_elite_2023.pgn
    └── stockfish/
        └── stockfish_vs_stockfish_tests.pgn

/data/processed/
    ├── personal_games.parquet
    ├── novice_games.parquet
    ├── elite_games.parquet
    ├── stockfish_games.parquet
    └── training_dataset.parquet  ← dataset combinado final
```

### ✅ ¿Por qué tener múltiples datasets?

Separar los datasets por origen (personal, novato, élite, stockfish) ofrece ventajas clave:

1. **Control y trazabilidad**
  - Permite saber cuántas partidas hay de cada tipo.
  - Facilita el análisis de errores según la fuente.
  - Evita mezclar datos que podrían sesgar el modelo (por ejemplo, humanos vs Stockfish).

2. **Entrenamiento dirigido**
  - Posibilita entrenar modelos específicos:
    - Personal: para recomendaciones personalizadas.
    - Novato: para detectar errores frecuentes en principiantes.
    - Élite/Stockfish: para generar datasets de jugadas correctas o perfectas.

3. **Balance y mezcla estratégica**
  - Permite decidir la proporción de cada tipo de partida en el dataset final.
  - Facilita técnicas como undersampling/oversampling según el objetivo.

🧩 **¿Por qué unificar los datasets?**
- Tras procesar cada dataset por separado, se pueden:
  - Aplicar los mismos análisis y extracción de características.
  - Añadir un campo `source` para identificar el origen.
  - Combinar todos en un dataset final para entrenamiento general, evaluación o análisis cruzado.

El script `generate_combined_dataset.py` automatiza este proceso.

---

## 🧩 Resumen óptimo de datasets por tipo de partida

| Tipo de partida                | Cantidad estimada | Uso principal                                                                 |
|-------------------------------|-------------------|------------------------------------------------------------------------------|
| **Tus propias partidas**      | ~12.000           | Entrenamiento personalizado, detección de patrones de error, evaluación real |
| **Novatos (ELO < 1500)**      | 50k–200k          | Entrenamiento base, comparación de estilos, generalización                   |
| **Élite (ELO > 2200)**        | >300k             | Modelar buen juego, etiquetar jugadas correctas, referencia                  |
| **Stockfish vs Stockfish**    | >300k             | Referencia perfecta, partidas ideales, validación de puntuaciones            |


  ### 🎯 Proporciones sugeridas en el dataset de entrenamiento

  | Tipo de partida      | % en dataset final | Motivo principal                                 |
  |---------------------|--------------------|--------------------------------------------------|
  | Tus partidas        | 10–20%             | Personalización y evaluación                     |
  | Novatos humanos     | 30–40%             | Entrenamiento base y errores típicos             |
  | Partidas de élite   | 20–30%             | Modelar buen juego, contraste con novatos        |
  | Stockfish test      | 10–20%             | Referencia perfecta y jugadas ideales            |

## 🧠 Entrenamiento de modelos con DVC

Este proyecto utiliza [DVC](https://dvc.org/es/) para versionar datasets, modelos entrenados y predicciones. El pipeline automatiza las etapas del proceso y asegura la reproducibilidad de los resultados.

### 📦 Estructura básica del pipeline

```text
export_features_by_source.py  ➜  genera datasets por fuente (source)
merge_datasets.py             ➜  unifica los datasets en uno general
train_model.py                ➜  entrena el modelo de aprendizaje automático
predict_and_eval.py           ➜  genera predicciones y métricas de evaluación
```

## 🧠 Tactics Generator Module (`tactics_generator.py`)

Este módulo forma parte del sistema de generación automática de ejercicios tácticos para el proyecto `chess_trainer`. Su objetivo es analizar partidas previamente procesadas, detectar jugadas con valor instructivo, y almacenarlas como ejercicios tácticos reutilizables.

### ✅ Funcionalidades implementadas

- Crea automáticamente la tabla `tactics` si no existe.
- Extrae posiciones con etiquetas tácticas (`tactical_tags`) desde la tabla `features`.
- Filtra jugadas candidatas según criterios como:
  - Pérdida o ganancia significativa de material (`score_diff`)
  - Presencia de patrones como clavadas, dobles ataques, sacrificios, etc.
- Genera un `tactic_id` único por jugada.
- Inserta ejercicios en la base de datos con la siguiente estructura:
  - `tactic_id`
  - `fen`
  - `move_uci`
  - `error_label`
  - `tags`
  - `game_id`
  - `ply`
  - `mate_in`
  - `depth_score_diff`
  - Timestamps y status

### 🔄 Uso típico

El módulo se invoca como parte del pipeline con:

```bash
python -m app.src.modules.tactics_generator

```

## 🧠Próximos pasos (Roadmap)
 - Conectar los ejercicios generados con estudios existentes o nuevos en la tabla studies.
 - Agregar campo source (e.g. auto, manual, lichess_import) para distinguir su origen.
 - Integrar interfaz en Streamlit para visualizarlos e interactuar con ellos.
 - Sugerir ejercicios similares según el error táctico más frecuente (error_label).
 - Exportar ejercicios seleccionados como PGN, JSON o PDF.

## 🧩 Estado Actual de Funcionalidades Predictivas en `chess_trainer`

| Aspecto                                    | Estado           | Descripción                                                                                                 |
|---------------------------------------------|------------------|-------------------------------------------------------------------------------------------------------------|
| Análisis de partidas y aperturas            | ✅ Implementado   | Evaluación detallada de jugadas y aperturas usando Stockfish.                                               |
| Evaluación de posiciones                    | ✅ Implementado   | Función heurística tradicional para valorar posiciones.                                                     |
| Entrenamiento personalizado basado en errores| ✅ Implementado   | Adaptación de sesiones según errores frecuentes del usuario.                                                |
| Integración de bases de datos de partidas   | ✅ Implementado   | Análisis de tendencias y patrones a partir de una base de datos de partidas.                                |
| Análisis de estilo de juego del usuario     | ⚠️ Parcial        | Análisis básico del estilo, falta caracterización profunda (velocidad, riesgo, patrones estratégicos).      |
| #MIGRATED-TODO-1750642686 Uso de redes neuronales para evaluación     | ❌ No implementado| No se usan redes neuronales para evaluar posiciones o jugadas.                                              |
|#MIGRATED-TODO-1750642906 Entrenamiento mediante autoaprendizaje      | ❌ No implementado| Falta módulo de self-play para autoaprendizaje.                                                             |
|#MIGRATED-TODO-1750643754 Bases de datos de finales (tablebases)      | ❌ No implementado| No se usan tablebases para finales perfectos.                                                               |
|#MIGRATED-TODO-1750645297 Análisis de estilo de juego del oponente    | ❌ No implementado| No se analiza el estilo de los oponentes.                                                                   |
|#MIGRATED-TODO-1750645646 Visualización de progresos y métricas       | ❌ No implementado| Falta interfaz para mostrar progreso y métricas del usuario.                                                |


### 💡 Ideas a Considerar

- **Redes neuronales para evaluación:** Integrar modelos tipo NNUE para mejorar la valoración posicional.
- **Autoaprendizaje (self-play):** Permitir que el motor juegue contra sí mismo para descubrir nuevas estrategias.
- **Análisis avanzado del estilo de juego:** Caracterizar el estilo del usuario (agresivo, defensivo, etc.) usando análisis de datos.
- **Integración de tablebases:** Usar bases como Syzygy para precisión en finales.
- **Análisis de oponentes:** Analizar partidas previas de rivales para adaptar estrategias.
- **Visualización de progreso:** Desarrollar dashboards con métricas y evolución del usuario.

---

## ✅ Próximos Pasos Recomendados

1. **Implementar redes neuronales para evaluación:** Explorar integración de NNUE o similares.
2. **Desarrollar sistema de autoaprendizaje:** Crear módulo de self-play para entrenamiento autónomo.
3. **Ampliar análisis de estilo de juego:** Profundizar en la caracterización del usuario y oponentes.
4. **Integrar bases de datos de finales:** Incorporar Syzygy para mejorar el juego en finales.
5. **Desarrollar interfaz de visualización de progreso:** Dashboard en Streamlit o panel propio.

---

## 🛠️ Roadmap de Implementación

### Etapa 1: Diagnóstico y Personalización (Prioridad Alta)

| Tarea                                 | Objetivo                                               | Técnica / Herramienta                        | Tiempo Estimado |
|---------------------------------------|--------------------------------------------------------|----------------------------------------------|-----------------|
| 🔍 Análisis avanzado del estilo       | Identificar perfil del usuario                         | Clustering + métricas (score_diff, risk, etc)| 3 días          |
| 📊 Visualización de progresos         | Mostrar evolución y errores frecuentes                 | Dashboard en Streamlit                       | 2 días          |
| ⚙️ Análisis de oponentes              | Detectar patrones en rivales frecuentes                | Filtrado y clustering simplificado           | 2 días          |

**Resultado:** Chess_trainer se adapta al usuario, mostrando perfil, errores y rivales clave.

---

### Etapa 2: Potenciación con AI (Media Prioridad)

| Tarea                                 | Objetivo                                               | Técnica / Herramienta                        | Tiempo Estimado |
|---------------------------------------|--------------------------------------------------------|----------------------------------------------|-----------------|
| 🧠 Evaluador basado en NNUE           | Evaluaciones más contextuales y posicionales           | Modelos open source NNUE                     | 4-6 días        |
| ♟️ Integración de Tablebases          | Juego perfecto en finales                              | Syzygy + python-chess                        | 2 días          |
| 🔁 Autoaprendizaje (Self-Play)        | Entrenamiento autónomo del sistema                     | Simulación de partidas y refuerzo            | 5 días          |

---

### Etapa 3: Estudios y Flujo Táctico Dinámico

| Tarea                                 | Objetivo                                               | Técnica / Herramienta                        | Tiempo Estimado |
|---------------------------------------|--------------------------------------------------------|----------------------------------------------|-----------------|
| 🧩 Generador automático de estudios   | Crear estudios interactivos tipo Lichess               | Extracción de segmentos con score_diff alto  | 2 días          |
| 🧠 Sugeridor de entrenamiento táctico | Recomendar ejercicios según fallas frecuentes           | tactical_recommender.py                      | 2 días          |

---

### Etapa 4: Extras Opcionales e I+D

| Tarea                                 | Objetivo                                               | Técnica / Herramienta                        | Estado          |
|---------------------------------------|--------------------------------------------------------|----------------------------------------------|-----------------|
| 🧮 Predicción de rendimiento futuro    | Predecir resultado según apertura y jugadas            | Logistic Regression / RandomForest           | Idea nueva      |
| 🎮 Interfaz tipo videojuego            | Gamificación y logros por niveles                      | Sistema de badges + tracking en SQLite       | Idea nueva      |

---

## ✅ Pros y Contras de las Funcionalidades

| Aspecto                   | Ventajas                                 | Desventajas                                  |
|---------------------------|------------------------------------------|----------------------------------------------|
| Personalización táctica   | Entrenamiento enfocado y motivante       | Requiere buen etiquetado y clustering        |
| Evaluación NNUE           | Más precisión posicional                 | Complejidad técnica moderada                 |
| Autoaprendizaje           | Sistema autónomo y replicable            | Puede consumir CPU si no se optimiza         |
| Visualización de progreso | Clara percepción de mejora               | Puede generar frustración si no hay avances  |
| Tablebases                | Juego perfecto en finales                | Sólo aplica a casos concretos                |
| Análisis de oponentes     | Mejor preparación ante rivales           | Depende de partidas previas disponibles      |


## 🧠 Resumen de Machine Learning en `chess_trainer`

### ✅ Módulos implementados / bosquejados

| Módulo / Archivo                | Descripción                                                                  | Estado                  |
|---------------------------------|------------------------------------------------------------------------------|-------------------------|
| `tactical_evaluator.py`         | Evalúa jugadas con Stockfish y etiqueta errores tácticos                     | ✅ Implementado         |
| `training_dataset.parquet`      | Dataset generado con múltiples features por jugada (tácticos, posicionales)  | ✅ Generado             |
| `eda_feedback.ipynb`            | Análisis exploratorio del dataset táctico con gráficos y boxplots            | ✅ En uso               |
| `feedback_analysis.ipynb`       | Analiza errores frecuentes, aperturas problemáticas, patrones de blunder     | ✅ Base implementada    |
| `error_label_model.ipynb`       | Entrena un modelo supervisado para predecir el tipo de error (`error_label`) | ⚠️ Parcialmente hecho   |
| `predicciones.parquet`          | Guarda predicciones del modelo ML por jugada                                 | ✅ Implementado         |
| `tactical_recommender.py`       | Recomienda ejercicios tácticos según debilidades detectadas                  | ✅ Implementado (base)  |

---

### 📊 Técnicas de ML aplicadas o preparadas

| Técnica                | Uso                                                        | Estado                  |
|------------------------|------------------------------------------------------------|-------------------------|
| Aprendizaje supervisado| Clasificación de errores (`error_label`) por jugada        | ⚠️ Parcial (modelo inicial) |
| Clustering (K-Means)   | Agrupación de jugadas por tipo de error, fase, etc.        | ⚠️ En notebooks         |
| PCA                    | Reducción de dimensionalidad para visualización            | ✅ Aplicado en EDA      |
| Feature Engineering    | Construcción de métricas como `score_diff`, `mobility`, etc.| ✅ Hecho                |
| Árboles de decisión / Random Forest | Modelo candidato para clasificar errores tácticos | 💡 Idea sugerida        |
| Regresión logística    | Predicción binaria de blunder / no blunder                 | 💡 Idea sugerida        |

---

### 📁 Features extraídas por jugada

**Ya implementados en el dataset:**

- `score_diff` (evaluación del motor)
- `material_total`, `material_balance`
- `num_pieces`, `phase`
- `branching_factor`, `self_mobility`, `opponent_mobility`
- `is_low_mobility`, `is_center_controlled`, `is_pawn_endgame`
- `move_number`, `player_color`, `has_castling_rights`
- `is_repetition`, `threatens_mate`, `is_forced_move`, `depth_score_diff`
- `tactical_tags` (clavada, doble ataque, etc.)

**Pendientes de implementar**
- mate_int
- standarized_elo

---

### ❌ Faltantes en el pipeline ML

| Faltante                        | Descripción                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| Entrenamiento formal del modelo  | Definir y entrenar modelo final (ej: RandomForest, Logistic Regression)     |
| Evaluación del modelo            | Validación cruzada, matriz de confusión, métricas tipo F1 o accuracy        |
| Exportación del modelo           | Serializar como `.pkl` o `.joblib` para uso en producción                   |
| Inferencia en producción         | Cargar modelo desde Python y etiquetar nuevas jugadas al vuelo              |
| Visualización de predicciones    | Mostrar `predicciones.csv` en la interfaz para feedback al usuario          |

---

### 🗂️ Próximos pasos sugeridos para completar ML

| Paso | Acción                                                                 | Módulo/Notebook                |
|------|------------------------------------------------------------------------|--------------------------------|
| 1️⃣  | Terminar `error_label_model.ipynb` entrenando modelo completo           | Jupyter                        |
| 2️⃣  | Evaluar modelo y guardar como `trained_model.pkl`                       | Jupyter + joblib               |
| 3️⃣  | Crear módulo `ml_predictor.py` para cargar modelo y etiquetar jugadas   | Python                         |
| 4️⃣  | Integrar a `full_pipeline.py` o `tactical_analysis.py`                  | Python                         |
| 5️⃣  | Visualizar las predicciones en Streamlit con ejemplos y feedback        | Streamlit                      |


## 🔜 Vista general de próximos pasos sugeridos

**Nota: Los MIGRATED-TODO fueron migrado con issues del repositorio github del proyecto**

- [#MIGRATED-TODO-1750286988] Aplicar `is_forced_move` en `detect_tactics_from_game` para omitir jugadas inevitables.
- [#MIGRATED-TODO-1750287009] Integrar `depth_score_diff`, `threatens_mate`, `is_forced_move` como columnas adicionales del análisis.
- [#MIGRATED-TODO-1750287014] Consolidar etiquetas + características tácticas en un solo dataframe.
- [#MIGRATED-TODO-1750287017] Guardar evaluaciones de Stockfish en base de datos para trazabilidad y depuración.
- [#MIGRATED-TODO-1750288408] Implementar pruebas unitarias para init_db.
- [#MIGRATED-TODO-1750288409] Implementar pruebas unitarias para get_games.
- [#MIGRATED-TODO-1750288409] Implementar pruebas unitarias para import_games.P
- [#MIGRATED-TODO-1750288409] Implementar pruebas unitarias para generate_features.
- [#MIGRATED-TODO-1750288410] Implementar pruebas unitarias para analyze_tactics.
- [#MIGRATED-TODO-1750288410] Implementar pruebas unitarias para export_dataset.
- [#MIGRATED-TODO-1750288411] Implementar pruebas unitarias para generate_exercises.
- [#MIGRATED-TODO-1750288411] Consolidar scripts para implementar lógica de generación/visualización/navegación/edición de estudio tipo Lichess.
- [#MIGRATED-TODO-1750288412] Analizar notebooks de análisis EDA, agrupamiento, aprendizaje automático en base a los datasets generados.
- #MIGRATED-TODO-1750618157 Aplicar estandarización de elo (campo standarized_elo)
- #MIGRATED-TODO-1750618158 Agregar campos mate_in y depth_score_diff para enriquecer modelo ML 
- #MIGRATED-TODO-1750618158 Implementación SHAP en Chess para descripcion de predicciones ML.

## Pendientes Vista UI (streamlit)
**La aplicación tiene vistas UI básicas usandoo streamlit.
## 📝 Validación de funcionalidades por vista (v0.1.20-f9d0260)

| Vista                        | Estado de validación | Notas / Comentarios |
|------------------------------|---------------------|---------------------|
| app                          | #TODO               |                     |
| analyze feedback             | #TODO               |                     |
| create exercise              | #TODO               |                     |
| elite explorer               | #TODO               |                     |
| elite stats                  | #TODO               |                     |
| elite training               | #TODO               |                     |
| export exercises             | #TODO               |                     |
| log viewer                   | #TODO               |                     |
| prediction history           | #TODO               |                     |
| predictor error label        | #TODO               |                     |
| streamlit eda                | #TODO               |                     |
| streamlit study viewer       | #TODO               |                     |
| streamlit tacticals viewer   | #TODO               |                     |
| summary viewer               | #TODO               |                     |
| tactics                      | #TODO               |                     |
| tactics viewer               | #TODO               |                     |
| tag games ui                 | #TODO               |                     |
| upload pgn                   | #TODO               |                     |

## 📌 Autor


> Proyecto creado por cmessoftware para la diplomatura de Ciencia de Datos  
> Contacto: [agregá tu correo o GitHub si querés]

