# Funcionalidad de Ejercicios Personalizados

## 🎯 Descripción General

La funcionalidad de **Ejercicios Personalizados** permite a los usuarios cargar sus partidas PGN y recibir ejercicios específicamente diseñados para mejorar sus debilidades identificadas mediante análisis de Machine Learning.

## 🏗️ Arquitectura

```
Frontend (React + Vite)
    ↓ 
API Flask (/api/exercises)
    ↓
ML Analysis (Python + Stockfish)
    ↓
PostgreSQL Database
    ↓
Export to Lichess Studies
```

## 📋 Funcionalidades Principales

### 1. **Carga de PGN**
- **Endpoint:** `POST /api/exercises/upload-pgn`
- **Descripción:** Permite subir archivos PGN para análisis
- **Formatos soportados:** `.pgn`
- **Proceso:**
  1. Validación del formato PGN
  2. Importación a base de datos PostgreSQL
  3. Generación de features con Stockfish

### 2. **Análisis de Jugador**
- **Endpoint:** `POST /api/exercises/analyze-player`
- **Descripción:** Ejecuta análisis ML completo del jugador
- **Análisis incluidos:**
  - **error_label:** Clasificación de movimientos (good, inaccuracy, mistake, blunder)
  - **streaks:** Detección de rachas de errores consecutivos
  - **player_type:** Clasificación de nivel de jugador basado en ELO

### 3. **Generación de Ejercicios**
- **Basados en debilidades específicas** identificadas por ML
- **Tipos de ejercicios:**
  - Táctica (pins, forks, skewer, etc.)
  - Finales (pawn endgame, rook endgame, etc.)
  - Estrategia (weak squares, pawn breaks, etc.)
  - Prevención de blunders

### 4. **Plan de Estudio Personalizado**
- **Horario diario sugerido** (táctica, análisis, patrones)
- **Metas semanales** específicas
- **Secuencia de prioridades** basada en urgencia de mejora

### 5. **Exportación a Lichess**
- **Endpoint:** `GET /api/exercises/export-lichess/{player_name}`
- **Genera PGN** compatible con Lichess Studies
- **Incluye instrucciones** para importación manual
- **Formato:** Estudio privado con ejercicios organizados

## 🔧 Implementación Técnica

### Backend (Flask API)

#### Estructura de archivos:
```
src/api/routers/exercises.py     # Endpoints principales
src/ml/analyze_th3hound.py       # Análisis específico ML
```

#### Endpoints disponibles:
```python
POST /api/exercises/analyze-player
POST /api/exercises/upload-pgn
GET  /api/exercises/patterns
GET  /api/exercises/export-lichess/{player_name}
POST /api/exercises/create
GET  /api/exercises/player/{player_name}
```

### Frontend (React + Vite)

#### Componentes principales:
```
src/frontend/src/pages/PersonalizedExercisesPage.jsx
src/frontend/src/services/exercisesService.js
```

#### Flujo de usuario:
1. **Subir PGN** → Validación y carga
2. **Analizar** → Ejecutar ML pipeline
3. **Resultados** → Mostrar métricas y ejercicios
4. **Exportar** → Descargar para Lichess

## 📊 Análisis ML Detallado

### Modelos Entrenados:
1. **Clasificador de Errores** (Random Forest)
   - Features: material_balance, mobility, king_safety, etc.
   - Output: good/inaccuracy/mistake/blunder
   - Métrica: F1-Score

2. **Detector de Rachas** (Pattern Recognition)
   - Identifica secuencias de errores consecutivos
   - Genera alertas para rachas >3 errores

3. **Clasificador de Nivel** (Multi-class)
   - Compara con different niveles ELO
   - Identifica fortalezas/debilidades relativas

### Features Utilizadas:
```python
feature_columns = [
    'material_balance',     # Balance material
    'material_total',       # Material total
    'num_pieces',          # Número de piezas
    'branching_factor',    # Factor de ramificación
    'self_mobility',       # Movilidad propia
    'opponent_mobility',   # Movilidad del oponente
    'has_castling_rights', # Derechos de enroque
    'is_repetition',       # Repetición de posición
    'is_low_mobility',     # Baja movilidad
    'is_center_controlled',# Control del centro
    'is_pawn_endgame',     # Final de peones
    'score_diff',          # Diferencia de evaluación
    'player_color',        # Color del jugador
    'move_number'          # Número de movimiento
]
```

## 🎯 Caso de Uso: Th3Hound

### Análisis Específico:
```bash
# Ejecutar análisis para Th3Hound
python src/ml/analyze_th3hound.py
```

### Resultados Esperados:
- **Perfil de juego:** Distribución de calidad de movimientos
- **Rachas de errores:** Patrones de errores consecutivos  
- **Modelos ML:** F1-Score de predicción de errores
- **Recomendaciones:** Ejercicios específicos basados en debilidades

### Ejercicios Personalizados Generados:
1. **Prevención de Blunders** (si blunder_rate > 2%)
2. **Control de Rachas** (si max_error_streak > 3)
3. **Táctica Diaria** (pins, forks, etc.)
4. **Patrones Específicos** (basado en ML feature importance)

## 📋 Formato de Datos

### Request de Análisis:
```json
{
  "player_name": "Th3Hound",
  "pgn_content": "1.e4 e5 2.Nf3...", 
  "analysis_type": ["error_label", "streaks", "player_type"]
}
```

### Response de Análisis:
```json
{
  "player_name": "Th3Hound",
  "analysis_summary": {
    "total_moves": 1500,
    "good_rate": 0.78,
    "error_rate": 0.22,
    "max_error_streak": 4,
    "model_accuracy": 0.85
  },
  "recommended_exercises": [...],
  "priority_areas": ["blunder_prevention", "concentration"],
  "study_plan": {...},
  "lichess_export": {...}
}
```

### Ejercicio Individual:
```json
{
  "id": 1,
  "title": "Prevención de Blunders - Verificación",
  "description": "Ejercicios para verificar amenazas antes de mover",
  "difficulty": "intermediate",
  "pattern_type": "blunder_prevention", 
  "fen_position": "r1bqkbnr/pppp1ppp/2n5/4p3/...",
  "target_moves": ["Bxf7+", "Qh5"],
  "explanation": "Verifica siempre las amenazas del oponente",
  "lichess_study_url": "https://lichess.org/study/..."
}
```

## 🚀 Integración con Lichess

### Proceso de Exportación:
1. **Generar PGN** con formato Lichess Studies
2. **Incluir comentarios** con explicaciones
3. **Organizar por dificultad** y tipo
4. **Proporcionar instrucciones** de importación

### Formato PGN de Salida:
```pgn
[Event "Ejercicio 1: Prevención de Blunders"]
[Site "Chess Trainer - Th3Hound"]  
[Date "2025.02.08"]
[White "Training"]
[Black "Exercise"]
[Result "*"]
[FEN "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4"]
[SetUp "1"]

{Verifica siempre las amenazas del oponente antes de atacar}

Bxf7+ Qh5 *
```

## 📈 Métricas y KPIs

### Métricas de Análisis:
- **Precisión del Modelo:** F1-Score de clasificación de errores
- **Cobertura de Datos:** Número de movimientos analizados
- **Distribución de Errores:** % de good/inaccuracy/mistake/blunder
- **Consistencia:** Varianza en rachas de errores

### Métricas de Usuario:
- **Tiempo de Análisis:** < 2 minutos típico
- **Ejercicios Generados:** 3-8 por análisis
- **Éxito de Exportación:** Compatibilidad con Lichess
- **Satisfacción:** Relevancia de ejercicios generados

## 🔄 Workflow Completo

```mermaid
graph TD
    A[Usuario sube PGN] --> B[Validar formato]
    B --> C[Importar a PostgreSQL]
    C --> D[Generar features con Stockfish]
    D --> E[Ejecutar modelos ML]
    E --> F[Identificar debilidades] 
    F --> G[Generar ejercicios específicos]
    G --> H[Crear plan de estudio]
    H --> I[Exportar a Lichess]
    I --> J[Descargar PGN]
```

## 🎮 Casos de Uso por Tipo de Usuario

### **Jugador Principiante (ELO 800-1200):**
- **Enfoque:** Táctica básica y prevención de blunders
- **Ejercicios:** Pins, forks, capturas simples
- **Tiempo:** 15-20 min diarios

### **Jugador Intermedio (ELO 1200-1800):**
- **Enfoque:** Patrones tácticos avanzados y estrategia
- **Ejercicios:** Combinaciones, finales básicos
- **Tiempo:** 20-30 min diarios

### **Jugador Avanzado (ELO 1800+):**
- **Enfoque:** Precisión posicional y cálculo profundo
- **Ejercicios:** Análisis complejo, finales avanzados  
- **Tiempo:** 30+ min diarios

## 🔧 Configuración y Despliegue

### Requisitos del Sistema:
```bash
# Backend
Python 3.8+
PostgreSQL 12+
Stockfish 15+
scikit-learn, pandas, sqlalchemy

# Frontend  
Node.js 16+
React 18+
Vite 4+
```

### Variables de Entorno:
```bash
CHESS_TRAINER_DB_URL=postgresql://chess:chess_pass@localhost:5432/chess_trainer_db
STOCKFISH_PATH=/usr/local/bin/stockfish
VITE_API_BASE_URL=http://localhost:8000
```

### Comandos de Inicio:
```bash
# Backend
cd src/api
uvicorn main:app --reload --port 8000

# Frontend
cd src/frontend  
npm run dev
```

## 📝 Roadmap Futuro

### Fase 1 (Actual): ✅
- [x] Análisis básico ML
- [x] Generación de ejercicios
- [x] Exportación a Lichess

### Fase 2 (Próxima):
- [ ] **Análisis de Aperturas:** Repertorio personalizado
- [ ] **Seguimiento de Progreso:** Comparación temporal
- [ ] **Ejercicios Adaptativos:** Difficulty ajustada automáticamente

### Fase 3 (Futuro):
- [ ] **Integración Direct con Lichess API**
- [ ] **Análisis en Tiempo Real** durante partidas
- [ ] **Recomendaciones de Oponentes** basadas en debilidades

## 🐛 Troubleshooting

### Problemas Comunes:

#### Error: "Datos insuficientes"
**Causa:** Menos de 10 movimientos en base de datos  
**Solución:** Verificar importación de PGN o usar más partidas

#### Error: "Stockfish no encontrado"  
**Causa:** Motor de ajedrez no instalado  
**Solución:** `apt install stockfish` o configurar STOCKFISH_PATH

#### Error: "Error en análisis ML"
**Causa:** Features insuficientes o datos corruptos  
**Solución:** Re-generar features o verificar calidad de datos

#### Error: "Exportación a Lichess falló"
**Causa:** Formato PGN inválido  
**Solución:** Validar movimientos objetivo y FEN positions

## 📞 Soporte

Para reportar issues o solicitar nuevas funcionalidades:
- **GitHub Issues:** chess_trainer/issues
- **Documentación:** docs/EJERCICIOS_PERSONALIZADOS.md  
- **Análisis ML:** docs/ML_THEORETICAL_FRAMEWORK.md

---

*Última actualización: 2025-02-08*  
*Versión: 1.0.0*  
*Autor: Chess Trainer ML Team*