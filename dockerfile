# Dockerfile for a Streamlit application with minimal dependencies
# Excludes heavy libraries like TensorFlow, JupyterLab, and TensorBoard

FROM python:3.11-slim

WORKDIR /app

# Instala paquetes esenciales, GitHub CLI y limpieza en un solo RUN para menor tamaño final
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y vim git git-lfs stockfish ca-certificates curl gnupg && \
    git lfs install && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Filtra los requirements para excluir librerías pesadas
COPY requirements.txt .
RUN grep -vE "tensorflow|jupyterlab|notebook|tensorflow-io-gcs-filesystem|tensorboard" requirements.txt > requirements_min.txt

# Instalación de dependencias
RUN pip install --no-cache-dir -r requirements_min.txt && pip install --upgrade pip

# Configuración del path
ENV PYTHONPATH=/app/src

# Copia el resto del proyecto
COPY . .

# Comando por defecto: levanta Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
