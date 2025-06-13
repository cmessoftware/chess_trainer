# Usar una imagen base de Python
FROM python:3.11-bookworm

# Upgrade all system packages to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*


# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y wget tar && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Damos permisos de ejecución al entrypoint
#RUN chmod +x /app/entrypoint.sh

# Establecer directorio de trabajo
WORKDIR /app

# Ejecutar el entrypoint
#RUN /app/entrypoint.sh --> Instala stockfish y las dependencias de Python
# Descargar Stockfish 17.1 AVX2
# Descargar y extraer Stockfish
RUN wget https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar && \
    mkdir -p /usr/local/bin && \
    tar -xf stockfish-ubuntu-x86-64-avx2.tar -C /usr/local/bin && \
    mv /usr/local/bin/ /usr/local/bin/stockfish2 && \
    mv /usr/local/bin/stockfish2/stockfish/stockfish-ubuntu-x86-64-avx2 /usr/local/bin && \
    rm -rf /usr/local/bin/stockfish2 && \
    chmod +x /usr/local/bin && \
    rm -rf stockfish-ubuntu-x86-64-avx2.tar

# Añadir Stockfish al PATH
ENV PATH="/usr/local/bin/stockfish:${PATH}"

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar debugpy (para debugging remoto)
RUN pip install debugpy

# Exponer puerto para la interfaz web
EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
