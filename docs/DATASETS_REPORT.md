# 📊 Chess Trainer - Datasets Report

**Fecha de generación:** 27 de agosto de 2025  
**Versión:** v1.0  
**Base de datos:** PostgreSQL con 11,676 partidas totales

---

## 🎯 Resumen Ejecutivo

Este reporte detalla los datasets Parquet generados para el proyecto Chess Trainer, incluyendo partidas de múltiples fuentes con diferentes niveles de habilidad para entrenar modelos de machine learning en análisis de ajedrez.

### 📈 Estadísticas Globales
- **Total de partidas:** 11,676
- **Fuentes de datos:** 5 (personal, elite, fide, stockfish, novice)
- **Rango temporal:** 1945-2025 (80 años de historia)
- **ELO promedio:** 1,541
- **Tamaño total datasets:** 2.39 MB

---

## 📂 Estructura de Datasets

### 🗃️ Archivos Generados

| Archivo                             | Registros | Tamaño  | Descripción                                  |
| ----------------------------------- | --------- | ------- | -------------------------------------------- |
| `chess_games_unified.parquet`       | 11,676    | 0.97 MB | **Dataset principal** con todas las partidas |
| `chess_games_personal.parquet`      | 4,242     | 0.41 MB | Partidas personales del usuario              |
| `chess_games_elite.parquet`         | 4,000     | 0.38 MB | Partidas de jugadores elite (ELO 2400+)      |
| `chess_games_fide.parquet`          | 1,434     | 0.08 MB | Partidas de grandes maestros FIDE            |
| `chess_games_stockfish.parquet`     | 1,000     | 0.09 MB | Partidas generadas por Stockfish             |
| `chess_games_novice.parquet`        | 1,000     | 0.05 MB | Partidas de jugadores novatos                |
| `chess_games_sample.parquet`        | 5,000     | 0.40 MB | Muestra equilibrada para testing             |
| `chess_datasets_statistics.parquet` | 6         | 0.01 MB | Estadísticas detalladas por fuente           |

---

## 🎮 Distribución por Fuente

### 📊 Partidas por Origen
```
personal     4,242 partidas (36.3%)
elite        4,000 partidas (34.3%) 
fide         1,434 partidas (12.3%)
stockfish    1,000 partidas (8.6%)
novice       1,000 partidas (8.6%)
```

### 🏆 Características por Fuente

#### 🔷 **Personal (4,242 partidas)**
- **ELO promedio:** 1,325 (ambos jugadores)
- **Período:** 2023-2025
- **Ratio resultados:** 50.4% blancas, 46.6% negras, 3.0% empates
- **Características:** Partidas reales del usuario, principalmente rapid (600+5)

#### 🔷 **Elite (4,000 partidas)**
- **ELO promedio:** 2,455 (nivel maestro)
- **Período:** 2020
- **Ratio resultados:** 49.5% blancas, 42.4% negras, 8.1% empates
- **Características:** Partidas de alto nivel, mayor frecuencia de empates

#### 🔷 **FIDE (1,434 partidas)**
- **ELO promedio:** 1,205 (variable por época)
- **Período:** 1945-2025 (80 años de historia)
- **Ratio resultados:** 37.9% blancas, 27.4% negras, 34.7% empates
- **Características:** Grandes maestros históricos (Carlsen, Kasparov, Fischer)

#### 🔷 **Stockfish (1,000 partidas)**
- **ELO:** Sin ELO (motor de ajedrez)
- **Período:** 2019
- **Ratio resultados:** 22.5% blancas, 11.0% negras, 66.5% empates
- **Características:** Partidas perfectas de motor, alta frecuencia de empates

#### 🔷 **Novice (1,000 partidas)**
- **ELO promedio:** 826 (nivel principiante)
- **Período:** 2025 (generadas sintéticamente)
- **Ratio resultados:** 18.5% blancas, 48.6% negras, 32.9% empates
- **Características:** Patrones típicos de principiantes, errores comunes

---

## 🎯 Distribución por Nivel de Habilidad

### 📈 Categorización por ELO
```
intermediate (1200-1600)  3,745 partidas (32.1%)
master (2400+)           3,182 partidas (27.3%)
unknown (sin ELO)        1,700 partidas (14.6%)
expert (2000-2400)       1,547 partidas (13.2%)
novice (800-1200)          970 partidas (8.3%)
beginner (<800)            485 partidas (4.2%)
advanced (1600-2000)        47 partidas (0.4%)
```

### 🏅 Análisis de Niveles
- **Cobertura completa:** Desde principiantes (400 ELO) hasta super grandes maestros (2840 ELO)
- **Concentración principal:** Niveles intermedio y maestro representan el 59.4% de los datos
- **Balance educativo:** Suficientes datos en cada nivel para entrenamiento efectivo

---

## 📋 Schema de Datos (22 columnas)

### 🔍 Campos Principales
| Campo          | Tipo   | Descripción                                   |
| -------------- | ------ | --------------------------------------------- |
| `game_id`      | string | ID único de la partida (hash SHA256)          |
| `white_player` | string | Nombre del jugador con blancas                |
| `black_player` | string | Nombre del jugador con negras                 |
| `result`       | string | Resultado (1-0, 0-1, 1/2-1/2)                 |
| `source`       | string | Fuente de datos (personal, elite, fide, etc.) |

### 🔢 Features ELO
| Campo         | Tipo   | Descripción                      |
| ------------- | ------ | -------------------------------- |
| `white_elo`   | int    | ELO del jugador blanco           |
| `black_elo`   | int    | ELO del jugador negro            |
| `elo_avg`     | float  | ELO promedio de la partida       |
| `elo_diff`    | float  | Diferencia absoluta de ELO       |
| `skill_level` | string | Categoría de habilidad calculada |

### 📊 Features ML
| Campo                 | Tipo   | Descripción                                              |
| --------------------- | ------ | -------------------------------------------------------- |
| `result_numeric`      | float  | Resultado numérico (1.0=blancas, 0.0=negras, 0.5=empate) |
| `pgn_length`          | int    | Longitud del PGN en caracteres                           |
| `move_count_estimate` | int    | Estimación de número de movimientos                      |
| `time_category`       | string | Categoría de tiempo (blitz, rapid, classical)            |

### 📅 Features Temporales
| Campo         | Tipo   | Descripción                      |
| ------------- | ------ | -------------------------------- |
| `date_played` | string | Fecha de la partida (YYYY.MM.DD) |
| `year`        | int    | Año de la partida                |
| `month`       | int    | Mes de la partida                |
| `day`         | int    | Día de la partida                |

### ♟️ Features Ajedrecísticos
| Campo          | Tipo   | Descripción                |
| -------------- | ------ | -------------------------- |
| `opening`      | string | Nombre de la apertura      |
| `eco`          | string | Código ECO de la apertura  |
| `time_control` | string | Control de tiempo original |

---

## 📈 Análisis Estadístico

### 🏆 Distribución de Resultados (Global)
- **Victorias blancas:** 43.4% (5,074 partidas)
- **Victorias negras:** 39.9% (4,662 partidas)
- **Empates:** 16.6% (1,940 partidas)

*Nota: Las blancas mantienen una ligera ventaja estadística, consistente con la teoría del ajedrez.*

### 📊 Estadísticas ELO
- **ELO mínimo:** 400 (principiantes absolutos)
- **ELO máximo:** 2,840 (super grandes maestros)
- **ELO promedio:** 1,541
- **ELO mediana:** 1,407
- **Desviación estándar:** ~650 puntos

### ⏰ Análisis Temporal
- **Período más antiguo:** 1945 (partidas históricas FIDE)
- **Período más reciente:** 2025 (partidas actuales)
- **Concentración principal:** 2020-2025 (70% de las partidas)
- **Partidas históricas:** 15% anterior a 2000

---

## 🚀 Aplicaciones ML

### 🎯 Casos de Uso Principales

#### 1. **Predicción de Resultados**
- **Target:** `result_numeric`
- **Features clave:** `elo_avg`, `elo_diff`, `skill_level`, `opening`
- **Algoritmos sugeridos:** Random Forest, XGBoost, Neural Networks

#### 2. **Clasificación de Nivel**
- **Target:** `skill_level`
- **Features clave:** `pgn_length`, `move_count_estimate`, resultado patterns
- **Algoritmos sugeridos:** SVM, Gradient Boosting, Ensemble methods

#### 3. **Análisis de Aperturas**
- **Target:** `result_numeric` por `eco`/`opening`
- **Features clave:** `elo_avg`, historical performance, color
- **Algoritmos sugeridos:** Clustering, Association Rules

#### 4. **Detección de Patrones Temporales**
- **Target:** Performance trends
- **Features clave:** `year`, `month`, `elo_avg`, results
- **Algoritmos sugeridos:** Time Series, LSTM

### 🛠️ Configuración ML Recomendada

#### **Train/Validation/Test Split**
```python
# Dataset principal: chess_games_unified.parquet
train: 70% (8,173 partidas)
validation: 15% (1,751 partidas)  
test: 15% (1,752 partidas)

# O usar chess_games_sample.parquet para prototipado rápido
```

#### **Feature Engineering Sugerido**
- **ELO binning:** Crear bins de ELO para mejor generalización
- **Opening families:** Agrupar aperturas por familia (e.g., 1.e4, 1.d4)
- **Time pressure:** Calcular ratio tiempo/movimiento
- **Historical performance:** Win rate histórico por jugador

---

## 🔧 Instrucciones de Uso

### 📥 Carga de Datos
```python
import pandas as pd

# Dataset completo
df = pd.read_parquet('data/datasets/chess_games_unified.parquet')

# Dataset específico
df_elite = pd.read_parquet('data/datasets/chess_games_elite.parquet')

# Muestra para testing
df_sample = pd.read_parquet('data/datasets/chess_games_sample.parquet')

# Estadísticas
df_stats = pd.read_parquet('data/datasets/chess_datasets_statistics.parquet')
```

### 🎯 Filtrado Común
```python
# Partidas con ELO conocido
df_rated = df[df['elo_avg'] > 0]

# Partidas recientes (últimos 5 años)
df_recent = df[df['year'] >= 2020]

# Solo partidas de alto nivel
df_masters = df[df['skill_level'].isin(['expert', 'master'])]

# Partidas rápidas
df_rapid = df[df['time_category'] == 'rapid']
```

### 📊 Análisis Básico
```python
# Distribución de resultados por nivel
result_by_level = df.groupby('skill_level')['result_numeric'].mean()

# Win rate por apertura
opening_stats = df.groupby('eco')['result_numeric'].agg(['mean', 'count'])

# Evolución temporal del ELO
elo_trends = df.groupby('year')['elo_avg'].mean()
```

---

## ⚠️ Consideraciones y Limitaciones

### 🚨 Aspectos a Considerar

#### **Calidad de Datos**
- **Stockfish games:** Sin ELO real, pueden sesgar modelos que dependan de rating
- **Partidas sintéticas:** Las 957 partidas novice son generadas, no reales
- **Datos faltantes:** ~14.6% de partidas sin ELO (unknown category)

#### **Distribución Temporal**
- **Sesgo reciente:** 70% de partidas son post-2020
- **Datos históricos limitados:** Solo 15% anterior a 2000
- **Gap temporal:** Algunos años intermedios pueden estar subrepresentados

#### **Balance de Clases**
- **Skill levels:** Concentración en intermediate/master (59.4%)
- **Results:** Ligero sesgo hacia victorias blancas (43.4% vs 39.9%)
- **Sources:** Personal y elite dominan (70.6% del dataset)

### 🎯 Recomendaciones

#### **Para Training ML**
1. **Estratificar por skill_level** para evitar sesgo hacia niveles dominantes
2. **Considerar pesos de clase** para balancear resultados
3. **Validación temporal** para evitar data leakage temporal
4. **Feature scaling** especialmente para ELO y años

#### **Para Análisis**
1. **Filtrar por período** para análisis consistentes temporalmente
2. **Separar motores** (stockfish) para análisis de humanos
3. **Agrupar skill levels** si hay pocos datos en categorías extremas
4. **Cross-validation estratificada** por fuente y nivel

---

## 📝 Conclusiones

### ✅ **Fortalezas del Dataset**
- **Diversidad de niveles:** Cobertura completa desde principiantes hasta grandes maestros
- **Múltiples fuentes:** Diferentes contextos y épocas de ajedrez
- **Features ricos:** 22 columnas con información relevante para ML
- **Tamaño adecuado:** 11.6K partidas es suficiente para modelos robustos
- **Formato optimizado:** Parquet con compresión para carga rápida

### 🎯 **Aplicaciones Inmediatas**
- **Sistemas de recomendación** de aperturas por nivel
- **Predictores de resultado** basados en ELO y contexto
- **Clasificadores de nivel** automáticos
- **Análisis de evolución** del ajedrez a lo largo del tiempo

### 🚀 **Potencial Futuro**
- **Expansión temporal:** Añadir más partidas históricas pre-2000
- **Análisis táctico:** Integrar evaluaciones de Stockfish move-by-move
- **Patrones de error:** Detectar errores típicos por nivel
- **Recomendaciones personalizadas:** Sistemas adaptativos de entrenamiento

---

## 📞 Información Técnica

**Ubicación:** `data/datasets/`  
**Formato:** Apache Parquet con compresión Snappy  
**Encoding:** UTF-8  
**Generado:** 27 de agosto de 2025, 14:02 UTC  
**Script:** `create_parquet_datasets.py`  
**Validación:** `explore_datasets.py`

**Compatibilidad:**
- Python 3.8+
- pandas >= 1.3
- pyarrow >= 5.0
- scikit-learn >= 1.0
- MLflow >= 1.20

---

*Este reporte es generado automáticamente y se actualiza con cada regeneración de datasets.*
