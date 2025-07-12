#!/bin/bash
export PYTHONPATH=src
cd /app/src || exit 1
echo "🏁 Ejecutando pruebas unitarias..."
pytest /app/src/tests

