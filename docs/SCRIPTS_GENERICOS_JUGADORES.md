# 📋 Scripts Genéricos de Análisis de Jugadores

Guía completa de scripts reutilizables para análisis de cualquier jugador de ajedrez.

## 🎯 Scripts Disponibles

### 1. **import_player_pgns.py** - Importación de PGNs
Importa archivos PGN de cualquier jugador a PostgreSQL.

```bash
# Uso básico
python src/scripts/import_player_pgns.py <player_name>

# Con opciones avanzadas  
python src/scripts/import_player_pgns.py Magnus --source elite --data-dir data/games

# Ejemplos
python src/scripts/import_player_pgns.py Th3Hound                    # personal/
python src/scripts/import_player_pgns.py Carlsen --source elite     # elite/
python src/scripts/import_player_pgns.py novice_player --source novice  # novice/
```

**Parámetros:**
- `player_name`: Nombre del jugador (busca patrones case-insensitive)
- `--source`: Fuente de PGNs (`personal`, `elite`, `novice`, `stockfish`, `fide`)
- `--data-dir`: Directorio base de datos (default: `data/games`)

### 2. **check_player_data.py** - Verificación de Datos
Verifica qué datos están disponibles para un jugador.

```bash
# Verificación básica
python src/scripts/check_player_data.py <player_name>

# Con detalles completos
python src/scripts/check_player_data.py Th3Hound --details

# Verificar múltiples jugadores
python src/scripts/check_player_data.py Magnus
python src/scripts/check_player_data.py hikaru --details
```

**Información mostrada:**
- ✅ Número total de juegos
- ⚪⚫ Distribución por color (Blanco/Negro)  
- 🤖 Features disponibles para ML
- 📊 Estado de preparación para análisis
- 📋 Detalles por fuente (con `--details`)

### 3. **analyze_player.py** - Análisis Completo
Genera análisis completo con recomendaciones personalizadas.

```bash
# Análisis estándar (mínimo 50 juegos)
python src/scripts/analyze_player.py <player_name>

# Análisis con parámetros personalizados
python src/scripts/analyze_player.py Magnus --min-games 100 --output-dir my_reports

# Ejemplos por nivel
python src/scripts/analyze_player.py Th3Hound                    # Maestro (2400+)
python src/scripts/analyze_player.py intermediate_player        # Intermedio (<2000)
```

**Parámetros:**
- `player_name`: Nombre del jugador a analizar
- `--min-games`: Mínimo juegos requeridos (default: 50)
- `--output-dir`: Directorio de reportes (default: `reports`)

### 4. **player_analysis_pipeline.py** - Pipeline Completo
Script maestro que automatiza todo el proceso.

```bash
# Pipeline completo automático
python src/scripts/player_analysis_pipeline.py <player_name>

# Pipeline con opciones específicas
python src/scripts/player_analysis_pipeline.py Magnus --source elite --min-games 100

# Pipeline con control de pasos
python src/scripts/player_analysis_pipeline.py hikaru --skip-features --force-reimport
```

**Pasos del Pipeline:**
1. 🔍 Verificación de datos existentes
2. 📥 Importación de PGNs (si necesario)  
3. 🤖 Generación de features (en background)
4. 📊 Verificación final
5. 📋 Análisis completo y reporte

**Opciones avanzadas:**
- `--skip-import`: Saltar importación
- `--skip-features`: Saltar generación de features  
- `--force-reimport`: Forzar re-importación
- `--dry-run`: Solo mostrar qué se ejecutaría

## 🚀 Ejemplos de Uso Completo

### Ejemplo 1: Análisis de Jugador Nuevo
```bash
# 1. Verificar si existe
python src/scripts/check_player_data.py NuevoJugador

# 2. Importar sus PGNs
python src/scripts/import_player_pgns.py NuevoJugador --source personal

# 3. Generar análisis
python src/scripts/analyze_player.py NuevoJugador --min-games 20
```

### Ejemplo 2: Pipeline Automático
```bash
# Todo en un comando
python src/scripts/player_analysis_pipeline.py NuevoJugador --source personal --min-games 20
```

### Ejemplo 3: Análisis de Maestro Elite
```bash
# Con datos de elite y análisis profundo
python src/scripts/player_analysis_pipeline.py Magnus --source elite --min-games 200
```

### Ejemplo 4: Re-análisis con Nuevos Datos
```bash
# Forzar re-importación y nuevo análisis
python src/scripts/player_analysis_pipeline.py Th3Hound --force-reimport --min-games 100
```

## 📊 Tipos de Análisis Generado

### Análisis Básico (Siempre Disponible)
- 📈 Estadísticas de juego por color
- 🏆 Tasas de victoria/empate/derrota
- ⏰ Controles de tiempo preferidos  
- 🎼 Aperturas más jugadas
- 📊 Distribución de resultados

### Análisis ML (Con Features Disponibles)
- 🎯 Clasificación de errores (good/inaccuracy/mistake/blunder)
- 🔥 Análisis de rachas de errores
- 📊 Distribución detallada de precisión
- 🤖 Patrones tácticos identificados

### Recomendaciones Personalizadas por Nivel

#### 🏆 Maestro (2400+ ELO)
- Perfeccionamiento en finales complejos
- Optimización de apertura según oponente
- Preparación específica anti-sistema

#### 🎯 Experto (2200-2400 ELO)  
- Precisión táctica avanzada
- Planificación estratégica a largo plazo
- Cálculo profundo sin mover piezas

#### 📈 Avanzado (2000-2200 ELO)
- Mejora en middlegame
- Estructuras de peones típicas
- Coordinación de ataques

#### 📚 Intermedio (<2000 ELO)
- Fundamentos tácticos
- Motivos básicos (clavada, horqueta)
- Reconocimiento de amenazas

## 🔧 Configuración y Prerequisitos

### Variables de Entorno (.env)
```bash
CHESS_TRAINER_DB_URL=postgresql://usuario:password@localhost/chess_trainer
PGN_PATH=data/games
```

### Estructura de Directorios
```
chess_trainer/
├── data/games/
│   ├── personal/     # PGNs personales
│   ├── elite/        # Maestros y GMs
│   ├── novice/       # Principiantes
│   └── ...
├── reports/          # Reportes generados
└── src/scripts/      # Scripts genéricos
```

### Dependencias
- PostgreSQL con base de datos configurada
- Python 3.8+ con dependencias del proyecto
- Stockfish (para generación de features)

## 🐛 Troubleshooting

### Error: "No module named 'db'"
```bash
# Ejecutar desde directorio correcto
cd chess_trainer/src
python scripts/analyze_player.py Th3Hound
```

### Error: "No se encontraron archivos PGN"
```bash
# Verificar patrones de archivo
ls data/games/personal/*jugador*
python src/scripts/check_player_data.py jugador --details
```

### Error: "Datos insuficientes"
```bash
# Reducir mínimo de juegos requeridos
python src/scripts/analyze_player.py jugador --min-games 10
```

### Features no disponibles
```bash
# Generar features manualmente
python src/scripts/generate_features_with_tactics.py

# O usar pipeline sin features
python src/scripts/player_analysis_pipeline.py jugador --skip-features
```

## 🎯 Mejores Prácticas

### Para Análisis de Producción
1. **Usar pipeline completo** para nuevos jugadores
2. **Verificar datos primero** con `check_player_data.py`
3. **Generar features en background** para no bloquear análisis
4. **Usar mínimos apropiados** según disponibilidad de datos

### Para Desarrollo/Testing  
1. **Dry-run primero** para verificar pasos
2. **Usar --skip-features** para análisis rápido
3. **Probar con jugadores de diferentes niveles**

### Para Análisis Masivo
```bash
# Script para multiple jugadores
for player in Magnus hikaru Th3Hound; do
    python src/scripts/player_analysis_pipeline.py $player --source elite
done
```

## 📄 Formato de Reportes

Todos los reportes se generan en **Markdown** con estructura estándar:

```markdown
# 📊 Análisis Completo: [Jugador]

## 🎯 Resumen Ejecutivo  
- **Nivel**: Maestro/Experto/Avanzado/Intermedio
- **ELO Promedio**: XXXX
- **Tasa de Victoria**: XX.X%

## 📈 Estadísticas de Juego
## 🎯 Análisis de Errores  
## 🎯 Recomendaciones Personalizadas
```

**Ubicación**: `reports/[jugador]_analysis_[timestamp].md`

---

## 🚀 Inicio Rápido

```bash
# 1. Análisis completo automático
python src/scripts/player_analysis_pipeline.py TuJugador

# 2. Buscar el reporte generado
ls reports/tujugador_analysis_*.md
```

¡Listo para analizar cualquier jugador! 🎯