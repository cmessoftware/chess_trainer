# CHESS TRAINER - Versión: v0.1.51-7633ef4

# ♟ chess_trainer – Análisis y entrenamiento con partidas de élite

Este proyecto automatiza la importación, análisis, etiquetado y entrenamiento a partir de miles de partidas de jugadores de élite (ELO >2300), combinando análisis táctico con exploración visual y generación de ejercicios.

---

## 📚 Índice de Documentación

### Documentación Principal
- **[README Principal](./README.md)** - Documentación completa del proyecto en inglés
- **[README (Español)](./README_es.md)** - Documentación completa del proyecto (este archivo)
- **[Version Base (English)](./VERSION_BASE.md)** - Guía rápida y descripción del proyecto en inglés
- **[Version Base (Español)](./VERSION_BASE_es.md)** - Guía rápida y descripción del proyecto en español

### Configuración e Instalación
- **[Configuración de Volúmenes de Datasets](./DATASETS_VOLUMES_CONFIG_es.md)** - Configuración de volúmenes Docker para compartir datasets
- **[Datasets Volumes Configuration](./DATASETS_VOLUMES_CONFIG.md)** - Docker volumes setup for dataset sharing

### Arquitectura y Desarrollo
- **[Arquitectura del Sistema](./src/architecture_es.md)** - Diagrama de arquitectura y descripción de componentes
- **[System Architecture](./src/architecture.md)** - System architecture diagram and component overview
- **[Mejoras en Generación de Características](./src/scripts/GENERATE_FEATURES_ENHANCEMENT.md)** - Documentación de mejoras en generación de características

### Pruebas
- **[Documentación de Pruebas](./tests/README_es.md)** - Guía completa de pruebas y documentación del ejecutor
- **[Tests Documentation](./tests/README.md)** - Comprehensive testing guide and runner documentation
- **[Migración PostgreSQL](./tests/POSTGRESQL_MIGRATION_COMPLETE.md)** - Documentación de migración de base de datos
- **[Unificación Completa](./tests/UNIFICATION_COMPLETE.md)** - Documentación de unificación del proyecto

### Reportes
- **[Reportes de Pruebas](./test_reports/)** - Reportes automatizados de ejecución de pruebas
- **[Reportes de Análisis](./test_reports/analyze_tactics_parallel_20250629_035806_summary.md)** - Resúmenes de ejecución de análisis táctico

### 📦 Instalación y Requisitos

**Todas las dependencias se instalan automáticamente vía contenedores Docker:**
- **[Dockerfile](./dockerfile)** - Contenedor principal de la aplicación con Python 3.11+ y todos los paquetes requeridos
- **[Dockerfile.notebooks](./dockerfile.notebooks)** - Entorno Jupyter con Keras, TensorFlow y librerías de ciencia de datos
- **[requirements.txt](./requirements.txt)** - Lista completa de dependencias de Python
- **[docker-compose.yml](./docker-compose.yml)** - Orquestación de contenedores con configuración automática

**Instalación manual (si no usas Docker):**
```bash
pip install -r requirements.txt  # Paquetes de Python
apt install stockfish           # Motor de ajedrez (Linux)
```

---

## 🚀 Gestión Unificada de Docker para Windows

Este proyecto proporciona un script PowerShell integral para la gestión completa del entorno Docker en Windows.

### 🔧 Script Principal: `build_up_clean_all.ps1`

| Uso                                   | Descripción                                    | Imágenes Generadas                              |
| ------------------------------------- | ---------------------------------------------- | ----------------------------------------------- |
| `.\build_up_clean_all.ps1`            | **Por defecto**: Construir + Iniciar + Limpiar | `chess_trainer_app` + `chess_trainer_notebooks` |
| `.\build_up_clean_all.ps1 -BuildOnly` | Solo construir contenedores                    | Ambas imágenes                                  |
| `.\build_up_clean_all.ps1 -StartOnly` | Solo iniciar contenedores existentes           | N/A                                             |
| `.\build_up_clean_all.ps1 -Backup`    | Respaldar imágenes Docker                      | N/A                                             |
| `.\build_up_clean_all.ps1 -Clean`     | Limpiar imágenes/volúmenes no utilizados       | N/A                                             |
| `.\build_up_clean_all.ps1 -Stop`      | Detener todos los contenedores                 | N/A                                             |
| `.\build_up_clean_all.ps1 -Status`    | Mostrar estado de contenedores                 | N/A                                             |
| `.\build_up_clean_all.ps1 -Help`      | Mostrar ayuda de uso                           | N/A                                             |

---

### 🛠️ Requisitos

- Docker versión **24.x** o superior
- PowerShell 5.1+ (incluido en Windows)

**Para usuarios de Windows**, el script de PowerShell `build_up_clean_all.ps1` proporciona configuración automatizada sin requerir cambios de permisos.

---

## 🚀 Cómo construir los contenedores

### Usuarios de Windows:
**Configuración con un solo comando (construye, inicia y limpia):**
```powershell
.\build_up_clean_all.ps1
```

Este script de PowerShell:
- 🚀 Construye las imágenes chess_trainer y notebooks
- ✅ Inicia todos los contenedores en modo separado
- 🧹 Limpia automáticamente las imágenes Docker no utilizadas
- 🏁 Muestra el estado de los contenedores activos

### 🎯 Beneficios de la Automatización con PowerShell de Windows:
- **Configuración con Un Solo Comando**: Configuración completa del entorno con un comando
- **Sin Gestión de Permisos**: Evita los requisitos de permisos `chmod` estilo Unix
- **Limpieza Automática**: Elimina imágenes Docker no utilizadas para ahorrar espacio en disco
- **Ejecución en Segundo Plano**: Los contenedores se ejecutan en modo separado para operación continua
- **Retroalimentación Instantánea**: Muestra el estado de los contenedores en ejecución después de completarse
- **Prevención de Errores**: La secuencia automatizada reduce errores de configuración manual
- **Ahorro de Tiempo**: Elimina la necesidad de múltiples comandos docker individuales

## 📂 Estructura del proyecto

```
chess_trainer/
├── alembic/                     # Gestión de migraciones de base de datos
│   ├── env.py
│   ├── versions/
│   └── README
├── data/                        # Datos de partidas y bases de datos
│   ├── chess_trainer.db
│   └── Undestanding ML/
├── img/                         # Imágenes y diagramas del proyecto
│   ├── architecture.png
│   └── chessboard.png
├── logs/                        # Logs de la aplicación
├── notebooks/                   # Notebooks de Jupyter para análisis
│   ├── chess_evaluation.ipynb
│   ├── eda_advanced.ipynb
│   ├── eda_analysis.ipynb
│   ├── ml_analize_tacticals_embedings.ipynb
│   └── data/
├── src/                         # Código fuente principal
│   ├── config/                  # Archivos de configuración
│   ├── data/                    # Utilidades de procesamiento de datos
│   ├── db/                      # Utilidades y modelos de base de datos
│   │   ├── postgres_utils.py
│   │   └── repository/
│   ├── decorators/              # Decoradores de Python
│   ├── modules/                 # Módulos de lógica de negocio central
│   │   ├── generate_dataset.py
│   │   ├── extractor.py
│   │   ├── tactics_generator.py
│   │   └── eda_utils.py
│   ├── pages/                   # Páginas de interfaz Streamlit
│   │   ├── elite_explorer.py
│   │   ├── elite_stats.py
│   │   ├── elite_training.py
│   │   ├── export_exercises.py
│   │   ├── tag_games_ui.py
│   │   └── streamlit_eda.py
│   ├── pipeline/                # Pipelines de procesamiento de datos
│   ├── scripts/                 # Scripts de ejecución autónoma
│   │   ├── analyze_games_tactics_parallel.py
│   │   ├── generate_features_parallel.py
│   │   ├── generate_pgn_from_chess_server.py
│   │   ├── generate_exercises_from_elite.py
│   │   ├── inspect_db.py
│   │   └── run_pipeline.sh
│   ├── services/                # Componentes de capa de servicio
│   │   ├── features_export_service.py
│   │   ├── get_lichess_studies.py
│   │   └── study_importer_service.py
│   ├── tools/                   # Herramientas utilitarias
│   │   ├── elite_explorer.py
│   │   └── create_issues_from_json.py
│   ├── validators/              # Utilidades de validación de datos
│   └── app.py                   # Aplicación principal de Streamlit
├── tests/                       # Suite de pruebas unificada
│   ├── test_elite_pipeline.py
│   ├── test_db_integrity.py
│   ├── test_analyze_games_tactics_parallel.py
│   └── run_tests.sh
├── test_reports/                # Reportes de ejecución de pruebas
├── docker-compose.yml           # Orquestación de contenedores
├── dockerfile                   # Contenedor de aplicación principal
├── dockerfile.notebooks         # Contenedor de Jupyter
├── build_up_clean_all.ps1       # Windows PowerShell: Script unificado de gestión Docker
├── alembic.ini                  # Configuración de migración de base de datos
├── requirements.txt             # Dependencias de Python
├── .env                         # Variables de entorno
└── README.md                    # Documentación del proyecto
```

---

## 🚀 Flujo recomendado

```bash
# Guardar partidas en la base
python src/scripts/import_game.py --input src/data/games/lichess_elite_2020-05.pgn

# Análisis táctico paralelo 
python src/scripts/analyze_games_tactics_parallel.py --concurrent_workers 4 --batch_size 100

# Generar features enriquecidos
python src/scripts/generate_features_parallel.py --workers 8

# EDA y entrenamiento
cd notebooks
jupyter lab eda_analysis.ipynb
```

---

## 🎯 **Módulos principales**

### **Interfaz de Usuario (Streamlit)**
```bash
streamlit run src/app.py
```

La aplicación incluye las siguientes páginas:
- **Elite Explorer**: Navegación de partidas de élite con filtros avanzados
- **Elite Stats**: Estadísticas detalladas de jugadores y partidas
- **Elite Training**: Generación de ejercicios tácticos personalizados
- **Export Exercises**: Exportación de ejercicios en diferentes formatos
- **Tag Games UI**: Etiquetado manual de partidas
- **Streamlit EDA**: Análisis exploratorio de datos interactivo

### **Scripts de Análisis**
- `analyze_games_tactics_parallel.py`: Análisis táctico distribuido con Stockfish
- `generate_features_parallel.py`: Generación paralela de características
- `generate_pgn_from_chess_server.py`: Descarga automática de partidas
- `generate_exercises_from_elite.py`: Creación de ejercicios desde partidas de élite

### **Pipeline de Datos**
El pipeline automatizado procesa:
1. **Importación**: Lectura de archivos PGN
2. **Análisis**: Evaluación táctica con Stockfish
3. **Etiquetado**: Clasificación automática de errores
4. **Características**: Extracción de features para ML
5. **Entrenamiento**: Modelos supervisados para predicción

---

## 🧪 Suite de Pruebas Unificada

### Ejecutar Todas las Pruebas
```powershell
# Windows
python -m pytest tests/ -v --html=test_reports/test_report.html

# Linux/macOS
./tests/run_tests.sh
```

### Pruebas Específicas
```bash
# Integridad de base de datos
python -m pytest tests/test_db_integrity.py -v

# Pipeline de élite
python -m pytest tests/test_elite_pipeline.py -v

# Análisis táctico paralelo
python -m pytest tests/test_analyze_games_tactics_parallel.py -v
```

### Reportes de Pruebas
Los reportes se generan automáticamente en `/test_reports/` con:
- Reporte HTML detallado
- Resumen de cobertura
- Logs de errores
- Métricas de rendimiento

---

## 🔧 Configuración

### Variables de Entorno
Crea un archivo `.env` con:
```bash
DATABASE_URL=sqlite:///data/chess_trainer.db
STOCKFISH_PATH=/usr/local/bin/stockfish
LOG_LEVEL=INFO
```

### Configuración de Docker
- **docker-compose.yml**: Orquestación de servicios
- **dockerfile**: Contenedor principal con Python 3.11+
- **dockerfile.notebooks**: Entorno Jupyter con TensorFlow/Keras

### Configuración de Base de Datos
```bash
# Inicializar migraciones
alembic init alembic

# Generar migración
alembic revision --autogenerate -m "Initial migration"

# Aplicar migraciones
alembic upgrade head
```

---

## 📊 Análisis Exploratorio de Datos (EDA)

### Notebooks Disponibles
1. **`eda_analysis.ipynb`**: Análisis básico de distribuciones
2. **`eda_advanced.ipynb`**: Correlaciones y análisis multivariado
3. **`chess_evaluation.ipynb`**: Evaluación de modelos de predicción
4. **`ml_analize_tacticals_embedings.ipynb`**: Embeddings y análisis de similitud

### Métricas y Visualizaciones
- Distribuciones de ELO y ratings
- Análisis temporal de partidas
- Matrices de correlación
- Evaluaciones tácticas por posición
- Mapas de calor de errores

---

## 🚀 Despliegue en Producción

### Docker Compose (Recomendado)
```bash
# Construcción e inicio completo
docker-compose up -d --build

# Solo servicios específicos
docker-compose up -d app notebooks
```

### Configuración Manual
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
alembic upgrade head

# Iniciar aplicación
streamlit run src/app.py --server.port 8501
```

---

## 🤝 Contribuciones

### Estructura de Commits
```bash
feat: nueva funcionalidad
fix: corrección de errores
docs: actualización de documentación
test: adición de pruebas
refactor: mejoras de código
```

### Desarrollo Local
1. Clona el repositorio
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno: `source venv/bin/activate` (Linux/macOS) o `venv\Scripts\activate` (Windows)
4. Instala dependencias: `pip install -r requirements.txt`
5. Ejecuta pruebas: `python -m pytest tests/`

---

## 🐛 Resolución de Problemas

### Problemas Comunes

**Error de Stockfish:**
```bash
# Instalar Stockfish
sudo apt install stockfish  # Linux
brew install stockfish      # macOS
# Windows: Descargar desde https://stockfishchess.org/
```

**Error de Dependencias:**
```bash
# Reinstalar requirements
pip install -r requirements.txt --upgrade --force-reinstall
```

**Error de Base de Datos:**
```bash
# Resetear base de datos
rm data/chess_trainer.db
alembic upgrade head
```

### Logs y Debugging
```bash
# Ver logs de aplicación
tail -f logs/app.log

# Logs de Docker
docker-compose logs -f app

# Modo debug de Streamlit
streamlit run src/app.py --logger.level=debug
```

---

## 📝 Roadmap y TODOs

### Funcionalidades Pendientes
- [ ] Integración con Lichess API
- [ ] Análisis de partidas en tiempo real
- [ ] Predicción de resultados de partidas
- [ ] Sistema de recomendaciones tácticas
- [ ] API REST para integración externa
- [ ] Soporte para formatos FEN y EPD
- [ ] Análisis de patrones de apertura
- [ ] Sistema de puntuación de jugadores

### Mejoras Técnicas
- [ ] Optimización de consultas SQL
- [ ] Cache distribuido con Redis
- [ ] Implementación de tests de carga
- [ ] Monitoreo y alertas
- [ ] Documentación API con Swagger
- [ ] Integración continua con GitHub Actions
- [ ] Containerización con Kubernetes
- [ ] Análisis de seguridad de código

---

## 📞 Soporte y Contacto

### Documentación Adicional
- **[Configuración de Volúmenes](./DATASETS_VOLUMES_CONFIG_es.md)**: Configuración avanzada de Docker
- **[Arquitectura del Sistema](./src/architecture_es.md)**: Diagramas y documentación técnica
- **[Guía de Pruebas](./tests/README_es.md)**: Documentación completa de testing

### Reporte de Issues
1. Describe el problema en detalle
2. Incluye steps para reproducir
3. Adjunta logs relevantes
4. Especifica tu entorno (OS, Python version, etc.)

---

## 📌 Créditos y Licencia

**Autor**: cmessoftware  
**Proyecto**: Parte del trabajo práctico para la Diplomatura en Ciencia de Datos  
**Licencia**: MIT License  

---

**🔗 Enlaces Útiles:**
- [Stockfish Engine](https://stockfishchess.org/)
- [Python Chess Library](https://python-chess.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Lichess API](https://lichess.org/api)

---

*Última actualización: Versión v0.1.51-7633ef4*
