#!/bin/sh

# Esperamos a que VSCode se conecte antes de correr streamlit
echo "Esperando conexión de depurador en 0.0.0.0:5678 ..."
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0
