#!/bin/bash
echo "Construyendo contenedor de JupyterLab..."
docker build -t chess_trainer_notebooks -f Dockerfile.notebooks . --ignore-file .dockerignore.notebooks
echo "Contenedor JupyterLab listo."
