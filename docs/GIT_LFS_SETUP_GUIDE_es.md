# Guía de Configuración Git LFS para Chess Trainer

## Visión General

Este pro### � Trabajando con Archivos Grandes

### **Verificar E## 💡 Mejores Prácticas para Datasetstado de LFS**
```bash
# Ver qué archivos son rastreados por LFS
git lfs track

# Verificar estado de archivos LFS
git lfs status

# Listar todos los archivos LFS
git lfs ls-files
```

### **Agregando Nuevos Archivos Grandes**
```bash
# Rastrear nuevos tipos de archivo
git lfs track "*.nueva_extension"

# Agregar y hacer commit
git add .gitattributes
git add tu_archivo_grande.extension
git commit -m "Agregar archivo grande con LFS"
```

### **Descargar Archivos LFS Específicos**
```bash
# Descargar solo archivos específicos
git lfs pull --include="*.ipynb"

# Descargar excluyendo ciertos archivos
git lfs pull --exclude="*.zip"
```

## 🐳 Entorno Docker

El entorno Docker maneja automáticamente Git LFS:📊 Mejores Prácticas para Datasets

### **Archivos que NO deben estar en el repositorio:**
- **Archivos comprimidos grandes** (*.zip, *.gz, *.tar): Usar servicios de almacenamiento externo o APIs
- **Datasets crudos masivos** (*.pgn): Usar APIs de Lichess/Chess.com para descargar bajo demanda
- **Archivos temporales**: Generar localmente según sea necesario

### **Cuándo usar LFS para notebooks:**
- **Notebooks >1MB**: Especialmente aquellos con outputs extensos
- **Notebooks EDA**: Con visualizaciones grandes y resultados de análisis
- **Notebooks de análisis ML**: Con outputs de modelos y métricas de rendimiento
- **Notebooks de investigación**: Con análisis estadístico comprehensivo

### **Uso recomendado de fuentes externas:**
```bash
# Descargar datasets de Lichess
curl "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.bz2"

# Usar API de Chess.com
curl "https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"
``` **Git Large File Storage (LFS)** para gestionar eficientemente grandes datasets, notebooks y archivos de modelos. Git LFS reemplaza archivos grandes con punteros de texto dentro de Git, mientras almacena el contenido de los archivos en un servidor remoto.

## 📋 Archivos Rastreados por Git LFS

Los siguientes tipos de archivo son automáticamente rastreados por Git LFS:

### **Modelos de Machine Learning**
- `*.pkl` - Modelos de machine learning entrenados
- `*.h5` - Archivos de modelos Keras/TensorFlow
- `*.joblib` - Modelos serializados de Scikit-learn
- `*.model` - Archivos de modelos genéricos

### **Datasets Procesados**
- `*.parquet` - Datasets de características procesadas
- `*.csv` - Datasets CSV grandes

### **Notebooks con Outputs Grandes**
- `*.ipynb` - Notebooks de Jupyter con análisis y modelos
  - **Especialmente importante para**: Notebooks EDA, análisis ML, visualizaciones grandes
  - **Umbral**: Notebooks >1MB deben usar LFS

### **Archivos NO Rastreados por LFS** (Excluidos por Eficiencia)
- `*.zip`, `*.gz`, `*.tar` - Archivos comprimidos (usar fuentes externas)
- `*.pgn` - Archivos de partidas crudos (usar APIs de lichess/chess.com)
- `*.png`, `*.jpg` - Imágenes (mantenidas pequeñas y manejables)

## 🚀 Configuración Rápida

### 1. Instalar Git LFS
```bash
# En Ubuntu/Debian
apt-get install git-lfs

# En macOS
brew install git-lfs

# En Windows
# Descargar desde: https://git-lfs.github.io/
```

### 2. Inicializar Git LFS
```bash
git lfs install
```

### 3. Clonar Repositorio
```bash
git clone https://github.com/cmessoftware/chess_trainer.git
cd chess_trainer
```

### 4. Descargar Archivos LFS
```bash
git lfs pull
```

## � Trabajando con Archivos Grandes

El entorno Docker maneja automáticamente Git LFS:

### **Construir y Ejecutar Contenedor de Notebooks**
```bash
# Construir el contenedor de notebooks
docker-compose build notebooks

# Ejecutar con acceso completo al repositorio
docker-compose up notebooks
```

El `dockerfile.notebooks` incluye:
- ✅ Instalación y configuración de Git LFS
- ✅ Acceso completo al repositorio en `/chess_trainer`
- ✅ Descarga automática de archivos LFS
- ✅ JupyterLab con acceso completo a datasets

## � Mejores Prácticas para Datasets

### **Archivos que NO deben estar en el repositorio:**
- **Archivos comprimidos grandes** (*.zip, *.gz, *.tar): Usar servicios de almacenamiento externo o APIs
- **Datasets crudos masivos** (*.pgn): Usar APIs de Lichess/Chess.com para descargar bajo demanda
- **Archivos temporales**: Generar localmente según sea necesario

### **Uso recomendado de fuentes externas:**
```bash
# Descargar datasets de Lichess
curl "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.bz2"

# Usar API de Chess.com
curl "https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"
```

### **Estructura recomendada:**
```
datasets/
├── export/           # Datasets procesados (parquet, csv) → LFS
├── models/           # Modelos entrenados (pkl, h5) → LFS  
├── notebooks/        # Análisis (ipynb) → LFS (opcional)
└── scripts/          # Scripts de descarga → Git normal
```

## �📊 Trabajando con Archivos Grandes

### **Verificar Estado de LFS**
```bash
# Ver qué archivos son rastreados por LFS
git lfs track

# Verificar estado de archivos LFS
git lfs status

# Listar todos los archivos LFS
git lfs ls-files
```

### **Agregando Nuevos Archivos Grandes**
```bash
# Rastrear nuevos tipos de archivo
git lfs track "*.nueva_extension"

# Agregar y hacer commit
git add .gitattributes
git add tu_archivo_grande.extension
git commit -m "Agregar archivo grande con LFS"
```

### **Descargar Archivos LFS Específicos**
```bash
# Descargar solo archivos específicos
git lfs pull --include="*.ipynb"

# Descargar excluyendo ciertos archivos
git lfs pull --exclude="*.zip"
```

## 🔧 Detalles de Configuración

### **Configuración Actual de .gitattributes**
```
# Modelos de Machine Learning
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.joblib filter=lfs diff=lfs merge=lfs -text
*.model filter=lfs diff=lfs merge=lfs -text

# Datasets procesados
*.parquet filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text

# Notebooks con outputs grandes
*.ipynb filter=lfs diff=lfs merge=lfs -text
```

### **Configuración de Docker**
El `dockerfile.notebooks` está optimizado para LFS:
- **WORKDIR**: `/chess_trainer` (acceso completo al repositorio)
- **Git LFS**: Pre-instalado y configurado
- **Auto-descarga**: Archivos LFS descargados al iniciar contenedor
- **GitHub CLI**: Disponible para autenticación

## 🚨 Solución de Problemas

### **Archivos LFS No se Descargan**
```bash
# Forzar descarga de todos los archivos LFS
git lfs pull --all

# Verificar remoto LFS
git lfs env
```

### **Problemas de Autenticación**
```bash
# Configurar credenciales de Git
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"

# Usar GitHub CLI para autenticación
gh auth login
```

### **Problemas del Contenedor**
```bash
# Reconstruir contenedor con configuración LFS más reciente
docker-compose build --no-cache notebooks

# Verificar estado LFS del contenedor
docker-compose exec notebooks git lfs status
```

## 📈 Beneficios de Rendimiento

- **Tamaño del Repositorio**: ~10MB (vs ~70MB sin LFS)
- **Velocidad de Clonado**: 5x más rápido en clones iniciales
- **Ancho de Banda**: Solo descarga archivos necesarios
- **Historial**: Historial Git limpio sin diffs binarios

## 🔗 Documentación Relacionada

- [Configuración de Volúmenes de Datasets](./DATASETS_VOLUMES_CONFIG_es.md)
- [Configuración de Desarrollo](./README_es.md#configuración-docker-recomendado)
- [Configuración de Docker](./README_es.md#configuración-manual-de-docker)

---

*Para más información sobre Git LFS, visita: https://git-lfs.github.io/*
