#!/bin/bash

PAGE="$1"

if [ -z "$PAGE" ]; then
    echo "❌ Debes pasar el archivo .py a ejecutar como parámetro."
    echo "Uso: ./run_streamlit.sh ../pages/export_exercises.py"
    exit 1
fi

# Mata procesos previos en el puerto 8501 si existen (requiere pkill)
echo "🧼 Verificando si el puerto 8501 está en uso..."
PID=$(lsof -ti:8501)
if [ -n "$PID" ]; then
    echo "🛑 Matando proceso anterior en puerto 8501 (PID $PID)..."
    kill -9 $PID
fi

echo "🚀 Ejecutando Streamlit en http://localhost:8501 (archivo: $PAGE)"
streamlit run "$PAGE" \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.runOnSave true
