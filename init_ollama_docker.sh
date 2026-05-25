#!/bin/bash
# Script para inicializar Ollama en Docker con modelos pre-descargados

echo "🚀 Iniciando Ollama en Docker..."

# 1. Levantar servicio Ollama
docker-compose up -d ollama

echo "⏳ Esperando que Ollama esté listo..."
sleep 10

# 2. Verificar que Ollama está corriendo
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo "❌ Error: Ollama no está respondiendo"
    exit 1
fi

echo "✅ Ollama está corriendo"

# 3. Descargar modelo de desarrollo
echo "📥 Descargando modelo llama3.2:3b (desarrollo)..."
docker exec chess_trainer_ollama ollama pull llama3.2:3b

# 4. Descargar modelo de producción (opcional, comentar si no se necesita)
echo "📥 Descargando modelo llama3.1:8b (producción)..."
docker exec chess_trainer_ollama ollama pull llama3.1:8b

# 5. Listar modelos instalados
echo ""
echo "📋 Modelos instalados:"
docker exec chess_trainer_ollama ollama list

echo ""
echo "✅ Ollama configurado correctamente en Docker"
echo "🔗 Acceso: http://localhost:11434"
echo ""
echo "💡 Para usar desde Python/API: OLLAMA_BASE_URL=http://localhost:11434"
