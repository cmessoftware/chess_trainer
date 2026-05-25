#!/bin/bash
# Script para iniciar el servicio FastAPI

echo "🚀 Iniciando Chess Error Level Classifier API..."

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Instalar dependencias
echo "📋 Instalando dependencias..."
pip install -r requirements_api.txt

# Iniciar el servicio
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "📖 Documentación disponible en http://localhost:8000/docs"

uvicorn chess_error_classifier_api:app --host 0.0.0.0 --port 8000 --reload