#!/bin/bash

# Tamaño límite sugerido en MB
LIMIT_MB=10

echo "🔎 Buscando archivos mayores a $LIMIT_MB MB en el proyecto..."

# Convertir MB a bloques de 1k para 'find'
LIMIT_KB=$((LIMIT_MB * 1024))

find . -type f -size +"${LIMIT_KB}k" ! -path "./.git/*" -exec ls -lh {} \; | awk '{ printf "%-10s %s\n", $5, $9 }'

echo ""
echo "✅ Recomendación: Archivos listados conviene subir con Git LFS."

