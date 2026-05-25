# CHESS TRAINER - Versión: v0.1.107-d679114

# ♟ chess_trainer – Análisis y entrenamiento para todos los jugadores de ajedrez

Este proyecto automatiza la importación, análisis, etiquetado y entrenamiento a partir de miles de partidas de ajedrez de todos los niveles de habilidad (desde principiantes hasta maestros), combinando análisis táctico con exploración visual y generación de ejercicios personalizados usando un stack tecnológico moderno con frontend **React + Vite** y backend **FastAPI**.

## 🚀 Stack Tecnológico

### Frontend
- **React 19** + **TypeScript** - Framework de UI moderno basado en componentes
- **Vite** - Herramienta de construcción rápida y servidor de desarrollo
- **Material-UI (MUI)** - Librería de componentes React profesional
- **React Query (@tanstack/react-query)** - Gestión de estado del servidor
- **Chess.js** + **React-Chessboard** - Lógica de ajedrez y tablero interactivo
- **React Router Dom** - Enrutamiento del lado del cliente

### Backend  
- **FastAPI** - Framework web Python de alto rendimiento
- **PostgreSQL** - Base de datos relacional lista para producción
- **MLflow** - Seguimiento de experimentos de machine learning
- **Stockfish** - Motor de ajedrez para análisis de movimientos
- **Docker + Docker Compose** - Entorno de desarrollo containerizado

### Ciencia de Datos y ML
- **Ecosistema Python**: pandas, numpy, scikit-learn, tensorflow
- **Jupyter Notebooks** - Análisis interactivo de datos y experimentación ML
- **Alembic** - Migraciones de base de datos
- **Procesamiento PGN** - Procesamiento de formato de juegos de ajedrez

### Herramientas de Desarrollo
- **Scripts PowerShell** - Flujos de trabajo de desarrollo automatizados
- **Git LFS** - Almacenamiento de archivos grandes para datasets
- **PyTest** - Framework de testing Python
- **ESLint** - Linting JavaScript/TypeScript

---

## 📚 Índice de Documentación

### Documentación Principal
- **[Changelog](./CHANGELOG.md)** - Historial completo de cambios del proyecto con historial de versiones
- **[README Principal](../README.md)** - Documentación completa del proyecto en inglés
- **[README (Español)](./README_es.md)** - Documentación completa del proyecto (este archivo)
- **[Version Base (English)](./VERSION_BASE.md)** - Descripción del proyecto y guía rápida en inglés
- **[Version Base (Español)](./VERSION_BASE_es.md)** - Descripción del proyecto y guía rápida en español
- **[Roadmap Técnico](./ROADMAP_TECHNICAL.md)** - Hoja de ruta de desarrollo de 6 fases con estado actual
- **[Roadmap Frontend](./ROADMAP_FRONT_CHESS_TRAINER.md)** - Hoja de ruta de desarrollo frontend React

### Documentación Técnica
- **[Integración MLflow PostgreSQL](./MLFLOW_POSTGRES_INTEGRATION.md)** - Guía para la integración del backend MLflow PostgreSQL
- **[Predicciones Confiables con MLflow](./PREDICCIONES_FIABLES_MLFLOW.md)** - Guía completa para hacer predicciones confiables de movimientos de ajedrez
- **[Guía de Estandarización ELO](./ELO_STANDARDIZATION_GUIDE.md)** - Guía técnica para el sistema de estandarización ELO
- **[Reporte de Finalización Issue #21](./ISSUE_21_COMPLETION_REPORT.md)** - Reporte completo sobre implementación de estandarización ELO
- **[Estrategia de Desarrollo Docker](./DOCKER_DEVELOPMENT_STRATEGY.md)** - Guía de flujo de trabajo de desarrollo Docker
- **[Configuración de Volúmenes de Datasets](./DATASETS_VOLUMES_CONFIG.md)** - Configuración de volúmenes para datasets
- **[Guía de Configuración Git LFS](./GIT_LFS_SETUP_GUIDE.md)** - Guía de configuración de Git Large File Storage

### Guías de Desarrollo y Configuración
- **[Ejecutar Entorno DEV](./EJECUTAR_ENTORNO_DEV.md)** - Guía completa para configurar entorno de desarrollo
- **[Guía de Mejora de Características](./GENERATE_FEATURES_ENHANCEMENT.md)** - Guía para mejoras en generación de características de ajedrez
- **[Actualización de Mejora de Arquitectura](./ARCHITECTURE_IMPROVEMENT_UPDATE.md)** - Últimas mejoras y actualizaciones de arquitectura
- **[Guía del Runner Postman](./POSTMAN_RUNNER_GUIDE.md)** - Testing de API con automatización Postman
- **[Resumen de Finalización de Tareas](./TASK_COMPLETION_SUMMARY.md)** - Milestones del proyecto y estado de finalización

### Sistema de Entrenamiento y Estudios
- **[Sistema Completo de Estudios PGN](./ESTUDIOS_PGN_SISTEMA_COMPLETO.md)** - Sistema completo de estudios PGN y análisis
- **[Sistema de Entrenamiento Completo](./TRAINING_SYSTEM_COMPLETE.md)** - Sistema completo de gestión de recursos de entrenamiento
- **[Tutorial de Estudios Personalizados](./TUTORIAL_ESTUDIOS_PERSONALIZADOS.md)** - Tutorial para crear estudios de ajedrez personalizados
- **[Reporte de Datasets](./DATASETS_REPORT.md)** - Análisis completo de datasets de ajedrez disponibles

## 🚀 Inicio Rápido

### Opción 1: Configuración Completa del Entorno (Recomendado)

#### Usuarios de Windows - Configuración con Un Comando:
```powershell
# Configuración completa: Backend + Frontend + Base de datos
.\build_up_clean_all.ps1
```

#### Configuración Manual:
```bash
# Iniciar todos los servicios con Docker Compose
docker-compose up -d

# Instalar dependencias del frontend e iniciar servidor de desarrollo
cd src/frontend
npm install
npm run dev

# Iniciar backend FastAPI (en otra terminal)
cd src/api
python -m uvicorn main:app --reload --port 8000
```

### Opción 2: Modo de Desarrollo

#### Iniciar API Backend:
```powershell
# Usando tareas PowerShell (recomendado)
.\ds_tools.ps1 -Action StartAPI

# O manualmente
cd src/api
python -m uvicorn main:app --reload --port 8000
```

#### Iniciar Frontend:
```bash
cd src/frontend
npm run dev
```

### 🌐 Puntos de Acceso:
- **Frontend (React)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000
- **Base de Datos**: PostgreSQL en localhost:5432

### 🎯 Beneficios de la Arquitectura Actual:
- **UI/UX Moderna**: React + Material-UI para interfaz profesional
- **Seguridad de Tipos**: TypeScript para confiabilidad del frontend  
- **Alto Rendimiento**: Vite para desarrollo rápido y FastAPI para velocidad del backend
- **Actualizaciones en Tiempo Real**: React Query para gestión eficiente del estado del servidor
- **Escalable**: Containerización Docker para entornos consistentes
- **Integración ML**: MLflow para seguimiento de experimentos y gestión de modelos

# chess_trainer
Plataforma moderna de entrenamiento de ajedrez usando frontend React + TypeScript, backend FastAPI, y pipeline ML avanzado con integración MLflow para análisis de ajedrez y mejora de jugadores.

## 🏢 Descripción General de la Arquitectura

### Arquitectura Frontend (React + Vite)
```
src/frontend/
├── src/
│   ├── components/     # Componentes UI reutilizables
│   ├── pages/         # Componentes de páginas basados en rutas  
│   ├── hooks/         # Hooks personalizados de React
│   ├── services/      # Servicios cliente API
│   ├── utils/         # Funciones auxiliares
│   └── types/         # Definiciones de tipos TypeScript
├── public/            # Assets estáticos
└── package.json       # Dependencias y scripts
```

### Arquitectura Backend (FastAPI)
```
src/api/
├── routers/           # Manejadores de rutas API
│   ├── auth.py       # Endpoints de autenticación
│   ├── chess.py      # Endpoints específicos de ajedrez
│   └── logs.py       # Endpoints de logging
├── models/           # Modelos de datos Pydantic
├── services/         # Servicios de lógica de negocio
├── middleware/       # Middleware personalizado
└── main.py          # Punto de entrada de la aplicación FastAPI
```

### 🔄 Flujo de Datos:
1. **Frontend React** hace llamadas API al backend FastAPI
2. **FastAPI** procesa requests, interactúa con PostgreSQL
3. **MLflow** rastrea experimentos y rendimiento de modelos
4. **Stockfish** proporciona análisis de motor de ajedrez
5. **Actualizaciones en tiempo real** vía gestión de estado React Query

## 📅 Estado de Implementación

| Componente                                                   | Estado        | Stack Tecnológico     | Prioridad |
| ------------------------------------------------------------ | ------------- | --------------------- | --------- |
| Frontend React + TypeScript                                  | ✅ Completado  | React 19 + Vite       | ✅         |
| Backend FastAPI con Autenticación                            | ✅ Completado  | FastAPI + JWT         | ✅         |
| Base de Datos PostgreSQL con Migraciones                     | ✅ Completado  | PostgreSQL + Alembic  | ✅         |
| Recolección de Datos de Juegos de Ajedrez (PGN, APIs)        | ✅ Completado  | Python + Chess APIs   | ✅         |
| Ingeniería de Características y Análisis Stockfish           | ✅ Completado  | Stockfish + pandas    | ✅         |
| Pipeline ML con Seguimiento MLflow                           | ✅ Completado  | MLflow + scikit-learn | ALTO      |
| Configuración Entorno Docker                                 | ✅ Completado  | Docker Compose        | ✅         |
| Componente de Tablero de Ajedrez Interactivo                 | ✅ Completado  | React-Chessboard      | MEDIO     |
| Dashboard de Análisis de Juegos                              | ⏳ En Progreso | Material-UI + Charts  | ALTO      |
| Gestión de Usuarios y Perfiles                               | ⏳ En Progreso | FastAPI + React       | MEDIO     |
| Importación de Juegos en Tiempo Real desde Chess.com/Lichess | ❌ Pendiente   | Integración API       | MEDIO     |

### 🎯 Prioridades del Próximo Sprint:
1. **Completar Dashboard de Análisis de Juegos** - Gráficos visuales y estadísticas
2. **Gestión de Perfil de Usuario** - Historial de juegos personales y preferencias  
3. **Integración API en Tiempo Real** - Importación de juegos en vivo desde plataformas principales
4. **Responsividad Móvil** - Optimizar para tablets/dispositivos móviles

### 🔧 Flujo de Desarrollo:

#### Desarrollo Frontend:
```bash
cd src/frontend
npm run dev          # Iniciar servidor de desarrollo Vite
npm run build        # Construir para producción
npm run lint         # Ejecutar verificaciones ESLint
```

#### Desarrollo Backend:
```bash
cd src/api
python -m uvicorn main:app --reload  # Iniciar FastAPI con hot reload
python -m pytest tests/              # Ejecutar pruebas API
```

#### Gestión de Base de Datos:
```bash
alembic upgrade head     # Aplicar migraciones de base de datos
alembic revision --autogenerate -m "descripción"  # Crear nueva migración
```

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

## 💻 Stack de Desarrollo Moderno

### 🎨 Frontend (React + Vite)
- **⚛️ React 19**: Último React con características concurrentes
- **🚀 Vite**: Herramienta de construcción ultrarápida y servidor dev  
- **📘 TypeScript**: Seguridad de tipos y mejor experiencia de desarrollador
- **🎁 Material-UI**: Librería de componentes profesional y accesible
- **🔄 React Query**: Potente gestión de estado del servidor
- **♟️ Chess.js**: Librería robusta de lógica de ajedrez
- **🏁 React Router**: Enrutamiento declarativo del lado del cliente

### ⚡ Backend (FastAPI)  
- **🐍 FastAPI**: Framework web moderno de alto rendimiento
- **🔐 Autenticación JWT**: Autenticación segura basada en tokens
- **🗄️ PostgreSQL**: Base de datos relacional de nivel empresarial
- **🔄 Alembic**: Gestión de migraciones de base de datos
- **📊 MLflow**: Seguimiento de experimentos ML y registro de modelos
- **🐳 Docker**: Entorno de desarrollo containerizado

### 🧠 Ciencia de Datos y ML
- **🔬 Jupyter Notebooks**: Análisis interactivo de datos
- **🤖 Stockfish**: Integración de motor de ajedrez de clase mundial
- **📈 scikit-learn**: Algoritmos de machine learning
- **🐼 pandas**: Manipulación y análisis de datos
- **📊 numpy**: Base de computación numérica

---

## 🏆 Créditos

**Chess Trainer** - Plataforma moderna de análisis de ajedrez combinando React + FastAPI con capacidades ML avanzadas.

Desarrollado por **cmessoftware** como parte de su trabajo práctico para la Diplomatura en Ciencia de Datos.

### 🤝 Contribuyendo
¡Este proyecto acepta contribuciones! Por favor revisa nuestra documentación para configuración de desarrollo y guías de contribución.

### 📄 Licencia
Este proyecto se desarrolla con fines educativos e de investigación.

---

**Última Actualización**: Enero 2026 - Versión v0.1.107  
**Stack Tecnológico**: React 19 + TypeScript + Vite + FastAPI + PostgreSQL + MLflow + Docker
