# CHESS TRAINER - Versión: v0.1.51-7633ef4

# Chess Trainer (versión base estable)

Este proyecto permite analizar y entrenar tácticamente partidas de ajedrez utilizando ciencia de datos y visualización interactiva.

## Características

- Generación de datasets a partir de archivos PGN
- Enriquecimiento táctico con Stockfish
- Clasificación de errores con etiquetas automáticas (`error_label`)
- Exploración y visualización con Streamlit y notebooks
- Entrenamiento de modelos supervisados para predicción de errores
- Logging e historial de predicciones

## Requisitos

- Python 3.8+
- streamlit
- pandas, seaborn, matplotlib
- python-chess
- scikit-learn
- Stockfish 

## Estructura

Consulte el archivo [`README_es.md`](./README_es.md) para la documentación completa del proyecto.

## Uso rápido

### Configuración con Docker (Recomendado)

#### Usuarios de Windows - Configuración con Un Solo Comando:
```powershell
.\build_up_clean_all.ps1
```

#### 🎯 Beneficios de la Automatización con PowerShell:
- **Configuración Completa del Entorno**: Construye e inicia todos los contenedores con un comando
- **Compatibilidad Multiplataforma**: Soporte nativo de PowerShell de Windows sin requisitos de permisos Unix
- **Limpieza Automática**: Elimina imágenes Docker no utilizadas para optimizar el uso del disco
- **Integración de Servicios**: Inicia tanto la aplicación principal como los contenedores de Jupyter notebooks
- **Operación en Segundo Plano**: Los contenedores se ejecutan separados para un flujo de trabajo de desarrollo continuo
- **Reducción de Errores**: La secuencia automatizada minimiza errores de configuración manual

#### Configuración Manual de Docker:
```bash
docker-compose build
docker-compose up -d
```

### Desarrollo Local:
```bash
# Ejecutar la interfaz principal
streamlit run app.py (En desarrollo)

# Generar datasets
cd /app/src/pipeline
./run_pipeline.sh interactive
```

## Créditos

Desarrollado por cmessoftware como parte de su trabajo práctico para el Diplomado en Ciencia de Datos.
