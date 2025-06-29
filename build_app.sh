#!/bin/bash
echo "Construyendo contenedor de Streamlit..."
docker build -t chess_trainer_app -f Dockerfile . --ignore-file .dockerignore.app
echo "Contenedor Streamlit listo."
