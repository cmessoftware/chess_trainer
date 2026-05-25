param(
  [string]$EnvName = "chess_ trainer",
  [switch]$UpgradeMamba = $false
)

# 1) Opcional: instalar/actualizar mamba si solo tenés conda
if ($UpgradeMamba) {
  conda install -n base -c conda-forge mamba -y
}

# 2) Crear entorno (canal conda-forge y solver rápido)
mamba create -y -n $EnvName -c conda-forge python=3.11

# 3) Instalar paquetes base de DS + JupyterLab + MLflow
mamba install -y -n $EnvName -c conda-forge `
  jupyterlab ipykernel mlflow numpy pandas scikit-learn lightgbm xgboost `
  pyarrow polars matplotlib jupytext

# 4) Registrar kernel para que aparezca en Jupyter
mamba run -n $EnvName python -m ipykernel install --user --name $EnvName --display-name "Python ($EnvName)"

# 5) Crear carpetas útiles
New-Item -ItemType Directory -Force -Path .\notebooks | Out-Null
New-Item -ItemType Directory -Force -Path .\artifacts | Out-Null

# 6) Lanzar JupyterLab y MLflow en terminales separadas
Start-Process powershell -ArgumentList "mamba run -n $EnvName jupyter lab"
Start-Process powershell -ArgumentList "mamba run -n $EnvName mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --host 127.0.0.1 --port 5000"

Write-Host "`nListo. JupyterLab arriba y MLflow en http://127.0.0.1:5000"
Write-Host "Elegí el kernel: Python ($EnvName) dentro de JupyterLab."
