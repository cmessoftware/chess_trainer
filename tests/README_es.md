# Directorio de Pruebas

Este directorio contiene todos los scripts de prueba y utilidades para el proyecto chess_trainer. Todas las pruebas han sido centralizadas aquí para una mejor organización y gestión.

## Prerrequisitos

### Configuración del Entorno Docker
Las pruebas requieren un entorno Docker configurado adecuadamente con base de datos PostgreSQL y motor Stockfish.

**Para usuarios de Windows (Recomendado):**
```powershell
.\build_up_clean_all.ps1
```
Esto asegura que todos los servicios requeridos (PostgreSQL, Stockfish) estén ejecutándose antes de ejecutar las pruebas.

**Configuración manual de Docker:**
```bash
docker-compose up -d
```

## Ejecutor de Pruebas

El script ejecutor de pruebas completo está ubicado en `/app/tests/run_tests.sh` y puede usarse para ejecutar cualquier prueba en el proyecto.

### Uso

#### Desde el directorio de pruebas:
```bash
cd /app/tests
./run_tests.sh [OPCIONES] [PATRÓN_DE_PRUEBA]
```

#### Desde la raíz del proyecto:
```bash
./tests/run_tests.sh [OPCIONES] [PATRÓN_DE_PRUEBA]
```

### Opciones Disponibles

#### Opciones de Entorno:
- `--use-venv`: Usa entorno virtual
- `--conda-env ENV_NAME`: Usa entorno conda específico
- `--python-path PATH`: Especifica ejecutable de Python personalizado

#### Opciones de Configuración de Pruebas:
- `-v`, `--verbose`: Salida detallada
- `-s`, `--capture=no`: No capturar salida (útil para debugging)
- `-x`, `--exitfirst`: Parar en la primera falla
- `--maxfail=N`: Parar después de N fallas
- `--tb=style`: Estilo de traceback (short/line/long/no)

#### Opciones de Reporte:
- `--html`: Generar reporte HTML
- `--junit`: Generar reporte XML JUnit
- `--summary`: Generar resumen en markdown
- `--detailed`: Incluir detalles adicionales en reportes

#### Opciones de Selección:
- `--quick`: Solo pruebas rápidas (omite las marcadas como slow)
- `--integration`: Solo pruebas de integración
- `--unit`: Solo pruebas unitarias
- `--db`: Solo pruebas de base de datos

### Ejemplos de Uso

#### Ejecutar todas las pruebas:
```bash
./run_tests.sh
```

#### Ejecutar pruebas específicas:
```bash
./run_tests.sh test_db_integrity.py
./run_tests.sh test_analyze_*
./run_tests.sh -k "test_parallel"
```

#### Generar reportes:
```bash
./run_tests.sh --html --junit --summary
```

#### Debugging:
```bash
./run_tests.sh -v -s -x test_specific.py
```

#### Solo pruebas rápidas:
```bash
./run_tests.sh --quick
```

## Archivos de Prueba

### Pruebas de Base de Datos
- `test_db_integrity.py`: Verificación de integridad de base de datos
- `test_postgresql_migration.py`: Pruebas de migración a PostgreSQL

### Pruebas de Análisis
- `test_analyze_games_tactics_parallel.py`: Análisis táctico en paralelo
- `test_analyze_games_tactics_parallel_simple.py`: Versión simplificada
- `test_analyze_errors.py`: Análisis de errores
- `test_batch_processing_analyze_tactics.py`: Procesamiento por lotes

### Pruebas de Generación
- `test_generate_exercises.py`: Generación de ejercicios
- `test_exercise_generation.py`: Pruebas adicionales de ejercicios
- `test_generate_features_pipeline.py`: Pipeline de características

### Pruebas de Integración
- `test_chesscom_download.py`: Descarga desde Chess.com
- `test_elite_pipeline.py`: Pipeline completo de élite
- `test_classify_error_label.py`: Clasificación de etiquetas de error

## Configuración

### pytest.ini
La configuración de pytest está en el archivo raíz `pytest.ini` del proyecto.

### Marcadores Personalizados
- `@pytest.mark.slow`: Para pruebas que toman mucho tiempo
- `@pytest.mark.integration`: Para pruebas de integración
- `@pytest.mark.db`: Para pruebas que requieren base de datos

### Variables de Entorno
Las pruebas pueden requerir las siguientes variables de entorno:
- `CHESS_TRAINER_DB_URL`: URL de la base de datos de prueba
- `STOCKFISH_PATH`: Ruta al ejecutable de Stockfish
- `TEST_DATA_PATH`: Ruta a datos de prueba

## Reportes

Los reportes se generan en el directorio `test_reports/` con timestamps únicos:
- HTML: Reporte detallado con gráficos y estadísticas
- JUnit XML: Para integración con CI/CD
- Markdown: Resumen ejecutivo legible

## Mejores Prácticas

1. **Ejecutar pruebas antes de commits importantes**
2. **Usar `--quick` para verificaciones rápidas durante desarrollo**
3. **Generar reportes para análisis detallado de fallos**
4. **Usar marcadores para categorizar pruebas**
5. **Mantener datos de prueba separados de datos de producción**

## Troubleshooting

### Problemas Comunes

#### Error de base de datos:
```bash
# Reiniciar base de datos de prueba
rm test_database.db
pytest --tb=short
```

#### Problemas de entorno:
```bash
# Verificar dependencias
pip install -r requirements_test.txt
```

#### Stockfish no encontrado:
```bash
# En Ubuntu/Debian
sudo apt install stockfish

# Verificar instalación
which stockfish
```

Para más información sobre pruebas específicas, consulta los docstrings en cada archivo de prueba.
