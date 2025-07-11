#!/bin/bash

Write-Output "🔧 Instalando Stockfish 17.1 (AVX2)..."

Set-Variable -e  # Detenerse ante cualquier error

# Descargar y extraer
wget https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar
tar -xf stockfish-ubuntu-x86-64-avx2.tar

# Mover el ejecutable
mkdir -p /usr/local/bin
Move-Item stockfish-ubuntu-x86-64-avx2/stockfish /usr/games/stockfish
chmod +x /usr/games/stockfish

# Limpiar
Remove-Item -rf stockfish-ubuntu-x86-64-avx2*
Write-Output "✅ Stockfish instalado en /usr/games/stockfish"
