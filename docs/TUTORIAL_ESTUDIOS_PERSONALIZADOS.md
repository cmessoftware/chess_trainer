# 📚 Tutorial: Estudios Personalizados con Chess Trainer ML

## Guía Completa para Generar Estudios de Ajedrez Personalizados

---

### 📋 **ÍNDICE**
1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)  
3. [Usuarios con Datos en Chess Trainer](#usuarios-con-datos-en-chess-trainer)
4. [Usuarios Externos (Chess.com/Lichess)](#usuarios-externos-chesscomlichess)
5. [Proceso de Análisis ML](#proceso-de-análisis-ml)
6. [Generación de Estudios](#generación-de-estudios)
7. [Importación a Lichess](#importación-a-lichess)
8. [Seguimiento y Mejora](#seguimiento-y-mejora)
9. [Resolución de Problemas](#resolución-de-problemas)

---

## **Introducción**

Este tutorial te guiará paso a paso para crear estudios de ajedrez personalizados usando el sistema de análisis ML de Chess Trainer. Los estudios se generan automáticamente basándose en:

- ✅ **Análisis ML de partidas reales**
- ✅ **Detección de patrones de error específicos**
- ✅ **Posiciones tácticas personalizadas**
- ✅ **Ejercicios dirigidos a debilidades**
- ✅ **Formato PGN compatible con Lichess**

---

## **Requisitos Previos**

### 🛠️ **Configuración Inicial**

1. **Chess Trainer instalado y configurado**
   ```bash
   cd chess_trainer
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Base de datos PostgreSQL activa** (opcional pero recomendado)
   ```bash
   docker-compose up -d postgres
   ```

3. **Scripts organizados en src/scripts/**
   - ✅ `simple_study_pgn.py` - Generador principal
   - ✅ `auto_study_generator.py` - Generador automático
   - ✅ `lichess_study_manager.py` - Importador a Lichess

---

## **Usuarios con Datos en Chess Trainer**

### 🎯 **Caso 1: Usuario con Análisis ML Completo**

Para usuarios como `cmess4401` y `cmess1315` que ya tienen partidas analizadas:

#### **Paso 1: Generar Estudios Personalizados**

```bash
cd chess_trainer
python src/scripts/simple_study_pgn.py cmess4401
```

**Salida esperada:**
```
📚 SIMPLE STUDY PGN GENERATOR
==================================================
Time: 2026-01-15 13:41:30

INFO: Analyzing user weaknesses for cmess4401...
INFO: Found 5 weakness patterns: pin, fork, back_rank, hanging_piece, skewer
INFO: Generated personalized tactical positions (8/8)
INFO: Exported: tactical_training_cmess4401_20260115_134130.pgn
INFO: Exported: endgame_training_cmess4401_20260115_134130.pgn
✅ Exported 2 personalized study files
```

#### **Paso 2: Revisar Personalización**

Los archivos generados incluirán:

**🎯 Comentarios Personalizados:**
```pgn
{ Exercise 1: Fork ⭐ PERSONALIZED

🎯 This position targets your specific weakness: Fork
📊 You've made errors in similar positions 8 times
📈 Priority: HIGH - Average loss: 245 centipawns

🧠 Focus on:
- Pattern recognition for Fork
- Calculation accuracy  
- Avoiding similar mistakes

Source: Personalized from game abc12345 }
```

#### **Paso 3: Generar Reporte de Análisis**

```bash
python -c "
from src.scripts.simple_study_pgn import SimpleStudyPGNGenerator
generator = SimpleStudyPGNGenerator()
report = generator.generate_personalized_report('cmess4401')
print(report)
"
```

---

## **Usuarios Externos (Chess.com/Lichess)**

### 🌐 **Caso 2: Usuario Nuevo sin Datos**

Para usuarios externos o nuevos en el sistema:

#### **Paso 1: Generar Estudios Generales**

```bash
python src/scripts/simple_study_pgn.py new_user_2026
```

**Resultado:**
```
INFO: No ML data found for new_user_2026
INFO: Using general tactical patterns and fallback positions
INFO: Generated standard training studies
✅ Exported 2 general study files
```

#### **Paso 2: Descargar Partidas de Chess.com**

Para personalización futura, descarga partidas del usuario:

```bash
# Método 1: Usar API de Chess.com
python src/scripts/download_chess_com_games.py username

# Método 2: Importar PGN manualmente
# 1. Ir a chess.com/games/archive
# 2. Descargar PGN del usuario
# 3. Colocar en data/games/personal/
```

#### **Paso 3: Análizar Partidas Descargadas**

```bash
# Importar partidas a la base de datos
python src/scripts/import_pgns_parallel.py data/games/personal/

# Generar análisis ML
python src/scripts/generate_features_with_tactics.py

# Procesar características tácticas
python src/scripts/analyze_games_tactics_parallel.py
```

#### **Paso 4: Regenerar Estudios Personalizados**

Después del análisis ML:

```bash
python src/scripts/simple_study_pgn.py username
# Ahora generará estudios personalizados basados en datos reales
```

---

## **Proceso de Análisis ML**

### 🧠 **Cómo Funciona la Personalización**

#### **1. Análisis de Debilidades**
```sql
-- El sistema ejecuta estas consultas automáticamente:
SELECT 
    f.error_label,
    f.tactical_tags,
    COUNT(*) as frequency,
    AVG(f.score_diff) as avg_loss
FROM features f 
JOIN games g ON f.game_id = g.game_id
WHERE (g.white_player = 'username' OR g.black_player = 'username')
  AND f.error_label IN ('blunder', 'mistake', 'inaccuracy')
GROUP BY f.error_label, f.tactical_tags
ORDER BY frequency DESC;
```

#### **2. Extracción de Posiciones**
```sql
-- Busca posiciones específicas para entrenamiento:
SELECT 
    at.position_fen,
    at.best_move,
    at.tactical_motif,
    at.difficulty_score
FROM analyzed_tacticals at
JOIN features f ON at.game_id = f.game_id
WHERE at.tactical_motif = 'user_weakness_theme'
ORDER BY at.difficulty_score DESC;
```

#### **3. Priorización de Ejercicios**

El sistema prioriza ejercicios según:
- **Frecuencia de error**: Cuántas veces cometió el mismo error
- **Pérdida promedio**: Centipeones perdidos por error
- **Dificultad**: Complejidad de la posición
- **Relevancia**: Similitud con errores pasados

---

## **Generación de Estudios**

### 📝 **Tipos de Estudios Disponibles**

#### **🎯 Entrenamiento Táctico**
```bash
python src/scripts/simple_study_pgn.py username
# Genera: tactical_training_username_TIMESTAMP.pgn
```

**Contenido típico:**
- 5-8 posiciones tácticas personalizadas
- Ejercicios de Fork, Pin, Skewer, etc.
- Comentarios con estadísticas específicas
- Soluciones detalladas

#### **♟️ Entrenamiento de Finales**
```bash
# Incluido automáticamente en la generación
# Genera: endgame_training_username_TIMESTAMP.pgn
```

**Contenido típico:**
- Mates básicos (Q+K vs K, R+K vs K)
- Finales de peones (oposición, peón pasado)
- Técnicas fundamentales
- Conceptos de actividad del rey

#### **📊 Estudios Avanzados (Próximamente)**
```bash
# Funcionalidades en desarrollo:
python src/scripts/generate_advanced_study_pgn.py username --theme=opening
python src/scripts/generate_advanced_study_pgn.py username --theme=middlegame
```

---

## **Importación a Lichess**

### 🚀 **Importación Manual (Recomendado)**

#### **Paso 1: Acceder a Lichess Studies**
1. Ir a https://lichess.org/study
2. Clic en **"New Study"**
3. Seleccionar **"Import PGN"**

#### **Paso 2: Importar Archivo PGN**
```bash
# Copiar contenido del archivo generado
cat training/studies/tactical_training_username_TIMESTAMP.pgn

# Pegar en el campo de texto de Lichess
# Personalizar nombre: "Entrenamiento Táctico - Username"
```

#### **Paso 3: Configurar Estudio**
- ✅ **Visibilidad**: Privado (por defecto)
- ✅ **Permitir clonar**: Sí (para respaldo)
- ✅ **Chat**: Desactivado
- ✅ **Descripción**: "Generado por Chess Trainer ML"

### 🤖 **Importación Automática (Opcional)**

Para usuarios avanzados con API token:

```bash
# Configurar token de Lichess
python src/scripts/setup_lichess_api.py

# Importar automáticamente
python src/scripts/lichess_study_manager.py \
  --study-id YOUR_STUDY_ID \
  --pgn-file training/studies/tactical_training_username.pgn
```

---

## **Seguimiento y Mejora**

### 📈 **Monitoreo de Progreso**

#### **1. Análisis Periódico**
```bash
# Regenerar estudios cada 2-4 semanas
python src/scripts/simple_study_pgn.py username

# Comparar con estudios anteriores
diff training/studies/tactical_training_username_OLD.pgn \
     training/studies/tactical_training_username_NEW.pgn
```

#### **2. Métricas de Mejora**

El sistema rastrea automáticamente:
- **Reducción de errores**: Por patrón táctico
- **Tiempo de resolución**: Mejora en rapidez
- **Accuracy rate**: Porcentaje de aciertos
- **Rating progression**: Evolución ELO

#### **3. Reporte de Progreso**
```bash
python -c "
from src.scripts.generate_real_user_analysis import DataDrivenRecommender
recommender = DataDrivenRecommender()
stats = recommender.get_user_stats(['username'])
print(f'Error rate: {stats.error_rate:.1f}%')
print(f'Improvement: {stats.calculate_improvement()}')
"
```

---

## **Casos de Uso Específicos**

### 💼 **Escenario 1: Entrenador de Ajedrez**

```bash
# Generar estudios para múltiples estudiantes
for student in cmess4401 cmess1315 student01 student02; do
    python src/scripts/simple_study_pgn.py $student
    echo "Estudio generado para $student"
done

# Consolidar reportes
python src/scripts/generate_batch_analysis.py --students=all
```

### 💼 **Escenario 2: Club de Ajedrez**

```bash
# Análisis grupal por rating
python src/scripts/simple_study_pgn.py --rating-range=1200-1400 --theme=tactics
python src/scripts/simple_study_pgn.py --rating-range=1400-1600 --theme=endgames

# Estudios temáticos
python src/scripts/simple_study_pgn.py --theme=sicilian_defense --users=all
```

### 💼 **Escenario 3: Jugador Individual**

```bash
# Rutina semanal personalizada
crontab -e
# 0 9 * * 1 cd /chess_trainer && python src/scripts/simple_study_pgn.py my_username

# Seguimiento mensual
python src/scripts/generate_progress_report.py my_username --period=monthly
```

---

## **Resolución de Problemas**

### 🛠️ **Problemas Comunes**

#### **Error: "Database not available"**
```bash
# Solución 1: Iniciar base de datos
docker-compose up -d postgres

# Solución 2: Verificar conexión
python -c "
from src.repositories.database_manager import DatabaseManager
db = DatabaseManager()
print('DB Status:', db.test_connection())
"

# Solución 3: Usar modo fallback
python src/scripts/simple_study_pgn.py username --fallback-mode
```

#### **Error: "No tactical positions found"**
```bash
# Verificar datos del usuario
python -c "
from src.scripts.simple_study_pgn import SimpleStudyPGNGenerator
gen = SimpleStudyPGNGenerator()
weaknesses = gen.get_user_weaknesses('username')
print('Weaknesses found:', len(weaknesses))
"

# Importar más partidas si es necesario
python src/scripts/import_pgns_parallel.py data/games/personal/
```

#### **Error: "PGN format invalid"**
```bash
# Validar archivo PGN
python -c "
import chess.pgn
with open('training/studies/file.pgn') as f:
    game = chess.pgn.read_game(f)
    print('Valid PGN:', game is not None)
"

# Regenerar con formato corregido
python src/scripts/simple_study_pgn.py username --fix-format
```

### 🔧 **Comandos de Diagnóstico**

```bash
# Estado general del sistema
python src/scripts/diagnose_system.py

# Verificar datos de usuario específico
python src/scripts/diagnose_user_data.py username

# Test de conectividad
python src/scripts/test_connections.py --all

# Limpieza de archivos corruptos
python src/scripts/cleanup_invalid_pgn.py
```

---

## **Configuración Avanzada**

### ⚙️ **Personalización de Parámetros**

#### **Archivo de Configuración** (`config/study_settings.json`)
```json
{
    "tactical_exercises": {
        "count": 8,
        "difficulty_range": [1200, 2000],
        "themes": ["fork", "pin", "skewer", "back_rank", "deflection"],
        "prioritize_user_weaknesses": true
    },
    "endgame_exercises": {
        "count": 6,
        "basic_mates": true,
        "pawn_endings": true,
        "piece_endings": false
    },
    "personalization": {
        "min_games_for_analysis": 10,
        "error_threshold": 5,
        "focus_recent_games": 30
    }
}
```

#### **Personalización de Comentarios**
```python
# src/config/comment_templates.py
PERSONALIZED_COMMENT_TEMPLATE = """
Exercise {exercise_num}: {theme} ⭐ PERSONALIZED

🎯 Target weakness: {weakness_theme}
📊 Error frequency: {error_count} times
📈 Priority: {priority}
💡 Average loss: {avg_score_loss} centipawns

Position: {fen}
Solution: {solution}

🧠 Focus areas:
{focus_areas}

Source: {source}
"""
```

---

## **Roadmap y Futuras Mejoras**

### 🚀 **Próximas Funcionalidades**

1. **✅ Ya Implementado:**
   - Análisis ML personalizado
   - Generación PGN automática
   - Estudios tácticos y de finales
   - Importación a Lichess

2. **🔄 En Desarrollo:**
   - Análisis de aperturas personalizado
   - Estudios de medio juego
   - Integración con Chess.com API
   - Dashboard de progreso

3. **📋 Planificado:**
   - App móvil complementaria
   - Análisis de video automático
   - Competencias entre usuarios
   - IA tutor personalizado

### 📞 **Soporte y Comunidad**

- **📖 Documentación**: `docs/` directory
- **🐛 Issues**: GitHub repository
- **💬 Comunidad**: Discord Chess Trainer
- **📧 Contacto**: chess.trainer.ml@gmail.com

---

## **Ejemplos de Salida**

### 📊 **Reporte de Usuario Típico**

```markdown
# PERSONALIZED CHESS TRAINING REPORT
## User: example_user
## Generated: 2026-01-15 14:00:00

### 🎯 IDENTIFIED WEAKNESSES
1. **FORK - BLUNDER** (12 occurrences, avg loss: 245cp)
2. **PIN - MISTAKE** (8 occurrences, avg loss: 180cp)
3. **BACK_RANK - BLUNDER** (5 occurrences, avg loss: 320cp)

### 📈 IMPROVEMENT PLAN
- Week 1-2: Fork pattern recognition
- Week 3-4: Pin identification drills
- Month 2: Back-rank safety awareness

### 🚀 EXPECTED IMPROVEMENT: +150-200 ELO
```

### 🎯 **Estudio PGN Personalizado**

```pgn
[Event "Chess Trainer: Personalized Tactical Training - Exercise 1"]
[White "Student_example_user"]
[FEN "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5"]

{ Exercise 1: Fork ⭐ PERSONALIZED

🎯 This targets your specific weakness: Fork patterns
📊 You've made similar errors 12 times (avg loss: 245cp)
📈 Priority: HIGH

Solution: Ng5 (attacks f7 and h7)
Focus: Pattern recognition, calculation accuracy }
```

---

**✅ ¡Listo para generar estudios personalizados de ajedrez con IA!**

> **Nota**: Este tutorial cubre tanto casos con datos ML completos como usuarios nuevos. El sistema se adapta automáticamente según la disponibilidad de datos.