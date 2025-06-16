# CHESS TRAINER - Versión: v0.1.17-d729782

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
│   │   ├── generate_dataset.py
│   │   ├── extractor.py
│   │   └── eda_utils.py
│   ├── scripts/                 # Scripts de ejecución autónomos
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
python src/scripts/import_game.py --input src/data/games/lichess_elite_2020-05.pgn

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
STOCKFISH_PATH=/usr/local/bin/stockfish’
```

Y cargala con:

```python
from dotenv import load_dotenv
load_dotenv()
```

---
## Configurar e implementar migraciona de base de datos usando Alembic y SqlAlchemy 
**Soporta multiples motors como Sqlite, MySql, Postgres , MariaDb etc**

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
from db import models  # asegúrate que __init__.py importe todos los modelos

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
**Nota: el comando alembic se tiene que ejecutar en la misma carpeta donde está alembic.ini (ej: /app)**

---
# Uso de GIT LFS para almecamiento de grandes datasets y modelos ML

**Se elige GTI LFS para reutilizar la infraestructura, esperiencia y credenciales de GitHub**

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

Con `publish_to_lichess.py` podés subir partidas desde la DB como estudios. Necesitás un token Lichess con permisos `study:write`.

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

## Diseño para en analisis de tácticas

| Aspecto                                  | Ventaja                                      |
|------------------------------------------|----------------------------------------------|
| depth por fase                           | Ahorra tiempo sin perder precisión           |
| multipv solo cuando hay muchas opciones  | No desperdicia ciclos de CPU                 |
| compare_to_best evita falsos positivos   | Mejora la calidad de las etiquetas           |
| classify_tactical_pattern sigue funcionando | Etiquetas clásicas como fork, pin, mate   |
| eval_cache                               | Evita evaluaciones repetidas por FEN         |

## Optimizaciones para acelerar el analisis táctico (pasar de dias a horas de analisis) 
**Actualizado: 2025-06-02**

## ✅ Checklist de optimizaciones en `tactical_analysis.py` - `chess_trainer`

| Nº | Optimización                                     | Estado     | Detalles / Comentarios                                                                 |
|----|--------------------------------------------------|------------|-----------------------------------------------------------------------------------------|
| 1️⃣ | 🔻 Reducir profundidad fija                      | ✅ Aplicado | Se usa `depth=6` para jugadas con `pre_tag`; y valores dinámicos según fase para el resto. |
| 2️⃣ | ⏭️ Omitir primeras jugadas                      | ✅ Aplicado | Si `move_number <= 6`, se salta el análisis. Controlado por `opening_move_threshold`.  |
| 3️⃣ | 🧠 Profundidad variable por fase                 | ✅ Aplicado | Usa `PHASE_DEPTHS` basado en la fase del juego (`opening`, `middlegame`, `endgame`).   |
| 4️⃣ | 🧮 Branching factor                              | ✅ Aplicado | Si `branching < 5`, se omite la jugada. Usado como proxy de baja complejidad.          |
| 5️⃣ | 🤖 MultiPV inteligente                           | ✅ Aplicado | Se usa `multipv=3` si `branching > 10`, y se adaptó `get_evaluation` y `parse_info`.    |
| 6️⃣ | 🧷 Análisis condicional por etiquetas previas    | ✅ Aplicado | Si `classify_simple_pattern` devuelve etiqueta, usa `depth=6` y `multipv=1`.           |
| 7️⃣ | ⛓️ Evitar análisis redundante (cache FEN)        | ✅ Aplicado | Usa `eval_cache` para no recalcular evaluaciones por FEN.                              |
| 8️⃣ | ⚡ Evitar jugadas forzadas (`is_forced_move`)     | 🔜 En progreso | Detectado en `evaluate_tactical_features()`, falta usarlo para saltar análisis.         |
| 9️⃣ | 🧪 Score diferencial preciso (`score_diff`)      | ✅ Aplicado | Usa `extract_score()` y ajusta según el color del jugador.                             |

---

## 📌 Otros puntos implementados

| Tema                           | Estado     | Comentarios                                                                 |
|--------------------------------|------------|-----------------------------------------------------------------------------|
| 🧩 `classify_simple_pattern`   | ✅ Reutilizado | Preclasificación táctica rápida (check, fork, pin, etc).                   |
| 🔄 `compare_to_best`           | ✅ Usado     | Compara jugada real con alternativas (`MultiPV`).                          |
| 🧠 `get_game_phase()`          | ✅ Usado     | Determina fase del juego (opening/middlegame/endgame).                     |
| ⏱️ Decorador `@measure_execution_time` | ✅ Aplicado | En funciones clave para medir tiempos.                                     |
| 🧪 Test manual de `multipv`    | ✅ Confirmado | Stockfish devuelve `list[dict]` correctamente al usar `multipv > 1`.       |

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
  - Aplicar los mismos análisis y extracción de features.
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
| **Stockfish vs Stockfish**    | >300k             | Ground truth, partidas perfectas, validación de scoring                      |


  ### 🎯 Proporciones sugeridas en el dataset de entrenamiento

  | Tipo de partida      | % en dataset final | Motivo principal                                 |
  |---------------------|--------------------|--------------------------------------------------|
  | Tus partidas        | 10–20%             | Personalización y evaluación                     |
  | Novatos humanos     | 30–40%             | Entrenamiento base y errores típicos             |
  | Partidas de élite   | 20–30%             | Modelar buen juego, contraste con novatos        |
  | Stockfish test      | 10–20%             | Ground truth y jugadas perfectas                 |



## 🔜 Próximos pasos sugeridos

- [ ] Aplicar `is_forced_move` en `detect_tactics_from_game` para omitir jugadas inevitables.
- [ ] Integrar `depth_score_diff`, `threatens_mate`, `is_forced_move` como columnas adicionales del análisis.
- [ ] Consolidar tags + features tácticas en un solo dataframe.
- [ ] Guardar evaluaciones de Stockfish en base de datos para trazabilidad y debugging.




## 📌 Autor

> Proyecto creado por cmessoftware para la diplomatura de Ciencia de Datos  
> Contacto: [agregá tu correo o GitHub si querés]
