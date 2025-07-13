#!/bin/bash
# 🚀 Script de inicio para MLflow + Jupyter Lab
# Ejecuta ambos servicios en el mismo contenedor

echo "🔄 Iniciando servicios integrados..."

# Crear directorio para MLflow runs si no existe
mkdir -p /notebooks/mlruns

# Iniciar MLflow server en background con SQLite (más simple y confiable)
echo "🚀 Iniciando MLflow server con SQLite..."
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///notebooks/mlruns/mlflow.db \
  --default-artifact-root /notebooks/mlruns \
  --serve-artifacts &

# Esperar a que MLflow esté disponible
echo "⏳ Esperando MLflow server..."
sleep 5

# Verificar que MLflow esté corriendo
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ MLflow server iniciado correctamente"
else
    echo "⚠️ MLflow server tardando en iniciar, continuando..."
fi

# Iniciar Jupyter Lab
echo "📓 Iniciando Jupyter Lab..."
exec jupyter lab --ip=0.0.0.0 --allow-root --no-browser --port=8888
