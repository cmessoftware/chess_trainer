#!/bin/bash
# Script para configurar Git LFS en el container de notebooks

echo "🔧 Configurando Git LFS para Chess Trainer..."

# Instalar y configurar Git LFS
git lfs install --system

# Configurar tracking de archivos grandes
git lfs track "*.zip"
git lfs track "*.pgn"
git lfs track "*.ipynb"
git lfs track "*.parquet"
git lfs track "*.h5"
git lfs track "*.hdf5"
git lfs track "*.pkl"
git lfs track "*.pickle"
git lfs track "*.model"

# Verificar configuración
echo "📋 Archivos tracked por Git LFS:"
git lfs ls-files

echo "✅ Git LFS configurado correctamente!"
echo "📁 Directorio de trabajo: $(pwd)"
echo "🌐 Git remotes:"
git remote -v

echo ""
echo "💡 Para descargar archivos LFS existentes, ejecuta:"
echo "   git lfs pull"
