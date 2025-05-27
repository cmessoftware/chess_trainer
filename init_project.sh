#!/bin/bash

# Crear carpetas necesarias
mkdir -p .github/workflows
mkdir -p data/tactics/elite
mkdir -p tests

# Crear requirements.txt básico
echo "streamlit
python-chess
berserk
matplotlib
pandas
plotly
pytest" > requirements.txt

# Crear test.yml para GitHub Actions
cat <<EOF > .github/workflows/test.yml
name: chess_trainer_tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest tests/
EOF

# Crear alias run_pipeline (solo visible al ejecutar este script)
cat <<EOL > run_pipeline.sh
#!/bin/bash

# Ejecutar el pipeline completo
python tag_games.py
python analyze_errors_from_db.py
python generate_exercises_from_elite.py
pytest tests/
EOL
chmod +x run_pipeline.sh

# Confirmación
echo "✅ Estructura base creada. Ejecutá './run_pipeline.sh' para correr todo el flujo."
echo "✅ Ejecutá 'pip install -r requirements.txt' si no lo hiciste aún."
echo "✅ Agregá tus tests en la carpeta 'tests/'."
echo "✅ Agregá tus tácticas en la carpeta 'data/tactics/elite/'."
