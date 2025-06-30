# Configuración de Volúmenes Compartidos para Datasets

## Descripción

Se ha configurado un volumen compartido (`chess_datasets`) para compartir los datasets Parquet generados por el contenedor de la aplicación principal con el contenedor de notebooks.

## Estructura de Volúmenes

```
docker-compose.yml
├── chess_trainer (app container)
│   └── /app/src/data -> chess_datasets volume
└── notebooks container  
    └── /notebooks/datasets -> chess_datasets volume
```

## Ubicación de los Datasets

### En el contenedor de la aplicación (`chess_trainer`):
- **Ruta**: `/app/src/data/`
- **Subdirectorios importantes**:
  - `/app/src/data/processed/` - Datasets combinados finales
  - `/app/src/data/export/` - Datasets por fuente (personal, novice, elite, etc.)

### En el contenedor de notebooks:
- **Ruta**: `/notebooks/datasets/`
- **Acceso desde notebooks**:
  ```python
  import pandas as pd
  
  # Leer dataset combinado
  df = pd.read_parquet("/notebooks/datasets/processed/training_dataset.parquet")
  
  # Leer datasets por fuente
  df_elite = pd.read_parquet("/notebooks/datasets/export/elite/features.parquet")
  df_personal = pd.read_parquet("/notebooks/datasets/export/personal/features.parquet")
  ```

## Scripts que Generan Datasets

### 1. `export_features_dataset_parallel.py`
- **Función**: Exporta features filtrados por fuente, jugador, apertura, ELO
- **Salida**: `/app/src/data/export/{source}/features.parquet`
- **Uso**:
  ```bash
  python src/scripts/export_features_dataset_parallel.py --source elite --limit 10000
  ```

### 2. `generate_combined_dataset.py`
- **Función**: Combina datasets de múltiples fuentes en uno solo
- **Entrada**: `/app/src/data/processed/{source}_games.parquet`
- **Salida**: `/app/src/data/processed/training_dataset.parquet`
- **Uso**:
  ```bash
  python src/scripts/generate_combined_dataset.py
  ```

### 3. `generate_features_parallel.py`
- **Función**: Genera features desde los juegos almacenados en PostgreSQL
- **Almacena**: Features en la base de datos, exportables con scripts anteriores

## Comandos Docker

### Iniciar los contenedores:
```bash
docker-compose up -d
```

### Ver el volumen compartido:
```bash
docker volume inspect chess_trainer_chess_datasets
```

### Acceder al contenedor de la app para generar datasets:
```bash
docker exec -it chess_trainer_chess_trainer_1 bash
cd /app
python src/scripts/export_features_dataset_parallel.py --source elite
```

### Acceder al contenedor de notebooks:
```bash
docker exec -it chess_trainer_notebooks_1 bash
ls -la /notebooks/datasets/
```

## Ejemplo de Uso en Notebook

```python
import pandas as pd
import os

# Verificar archivos disponibles
datasets_path = "/notebooks/datasets"
print("Datasets disponibles:")
for root, dirs, files in os.walk(datasets_path):
    for file in files:
        if file.endswith('.parquet'):
            print(f"  {os.path.join(root, file)}")

# Cargar dataset principal
df_training = pd.read_parquet(f"{datasets_path}/processed/training_dataset.parquet")
print(f"Dataset de entrenamiento: {len(df_training)} filas")

# Cargar dataset específico por fuente
df_elite = pd.read_parquet(f"{datasets_path}/export/elite/features.parquet")
print(f"Dataset elite: {len(df_elite)} filas")
```

## Flujo de Trabajo Recomendado

1. **Generación de Features** (en app container):
   ```bash
   python src/scripts/generate_features_parallel.py --source elite --max-games 1000
   ```

2. **Exportación a Parquet** (en app container):
   ```bash
   python src/scripts/export_features_dataset_parallel.py --source elite
   ```

3. **Generación de Dataset Combinado** (en app container):
   ```bash
   python src/scripts/generate_combined_dataset.py
   ```

4. **Análisis en Notebooks** (en notebooks container):
   - Abrir Jupyter en http://localhost:8888
   - Crear nuevo notebook
   - Cargar datos desde `/notebooks/datasets/`

## Ventajas de esta Configuración

- ✅ **Persistencia**: Los datasets persisten entre reinicios de contenedores
- ✅ **Compartición**: Ambos contenedores acceden a los mismos datos
- ✅ **Sincronización**: Los datasets generados en app están inmediatamente disponibles en notebooks
- ✅ **Separación**: Los datasets no se mezclan con el código fuente
- ✅ **Escalabilidad**: Fácil agregar más contenedores que necesiten acceso a los datasets
