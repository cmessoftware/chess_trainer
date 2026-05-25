#!/bin/bash
# Render Build Script - Chess Trainer AI Coach
# This script runs during the build phase on Render

set -e

echo "🔨 Building Chess Trainer AI Coach for Render..."

# Install system dependencies (if needed)
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    postgresql-client

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir -r requirements_ai_coach.txt

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p \
    data/chess_books/raw \
    data/chess_books/processed \
    data/vectorstore \
    logs \
    mlruns \
    mlartifacts \
    models

# Set permissions
chmod -R 755 data logs models

echo "✅ Build completed successfully!"
