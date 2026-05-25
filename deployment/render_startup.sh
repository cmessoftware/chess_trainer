#!/bin/bash
# Render Startup Script - Chess Trainer AI Coach

set -e

echo "🚀 Chess Trainer AI Coach - Starting on Render..."

# Start Ollama in background
echo "📦 Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo "❌ Ollama failed to start"
    exit 1
fi
echo "✅ Ollama is running"

# Download production model if not already present
MODEL_NAME="${OLLAMA_MODEL:-llama3.1:8b}"
echo "📥 Checking for model: $MODEL_NAME"

if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "📥 Downloading model: $MODEL_NAME (this may take a while on first deploy)..."
    ollama pull "$MODEL_NAME"
    echo "✅ Model downloaded successfully"
else
    echo "✅ Model already available"
fi

# Run database migrations
echo "🗄️ Running database migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "⚠️ Migration failed or not needed"
fi

# Start FastAPI application
echo "🌐 Starting Chess Trainer API..."
cd /app/src/api
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}
