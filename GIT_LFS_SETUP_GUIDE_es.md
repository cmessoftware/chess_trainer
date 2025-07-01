# Guía de Configuración Git LFS para Chess Trainer

## Visión General

Este proyecto utiliza **Git Large File Storage (LFS)** para gestionar eficientemente grandes datasets, notebooks y archivos de modelos. Git LFS reemplaza archivos grandes con punteros de texto dentro de Git, mientras almacena el contenido de los archivos en un servidor remoto.

## 📋 Archivos Rastreados por Git LFS

Los siguientes tipos de archivo son automáticamente rastreados por Git LFS:

### **Notebooks y Documentación**
- `*.ipynb` - Notebooks de Jupyter con análisis y modelos
- `*.html` - Reportes generados y documentación

### **Datasets y Partidas**
- `*.zip` - Colecciones de partidas comprimidas
- `*.pgn` - Archivos de notación de partidas de ajedrez
- `*.parquet` - Datasets de características procesadas

### **Modelos y Artefactos**
- `*.pkl` - Modelos de machine learning entrenados
- `*.h5` - Archivos de modelos Keras/TensorFlow
- `*.joblib` - Modelos serializados de Scikit-learn

### **Media y Visualizaciones**
- `*.png` - Gráficos generados y matrices de correlación
- `*.jpg` - Diagramas de posiciones de ajedrez

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

## 🐳 Entorno Docker

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

## 📊 Trabajando con Archivos Grandes

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
*.ipynb filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.pgn filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.joblib filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.html filter=lfs diff=lfs merge=lfs -text
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
