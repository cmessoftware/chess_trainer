# Validar y crear path si no existe
param(
  [string]$EnvName = "chess_trainer",
  [string]$InfraName = "infra-mlflow",
  [int]$JLabPort = 8800,
  [int]$MLflowPort = 5005,
  [switch]$NoBrowser,               # Jupyter sin abrir navegador
  [switch]$Minimal = $false,    # ds: solo python+jlab+ipykernel
  # MODOS
  [switch]$SetupOnly = $false,    # preparar todo y salir
  [switch]$OnlyLab = $false,    # solo JupyterLab (desde ds)
  [switch]$OnlyMLflow = $false,    # solo MLflow (desde ds o infra)
  [switch]$InfraSplit = $false     # usar entorno separado para MLflow
)

# ───────────── Activar entorno DS ─────────────
function Activate-Environment {
  param(
    [string]$EnvName = "ds",
    [string]$CondaRoot = "$HOME\miniforge3",
    [string]$Channel = "conda-forge"
  )
  if (-Not (Test-Path "$CondaRoot\condabin\conda.bat")) {
    Write-Error "❌ No se encontró conda en $CondaRoot. Verifica la ruta o instala Miniforge/Miniconda."
    exit 1
  }
  & "$CondaRoot\condabin\conda.bat" shell.powershell hook | Out-String | Invoke-Expression
  $envs = conda env list | ForEach-Object { ($_ -split '\s+')[0] } | Where-Object { $_ -and ($_ -ne "Name") }
  if ($EnvName -notin $envs) {
    Write-Host "⚠️ El entorno '$EnvName' no existe. Creándolo..." -ForegroundColor Yellow
    if (Have "mamba") {
      mamba create -n $EnvName -c $Channel python=3.11 jupyterlab ipykernel numpy pandas scikit-learn matplotlib seaborn mlflow -y
    }
    else {
      conda create -n $EnvName -c $Channel python=3.11 jupyterlab ipykernel numpy pandas scikit-learn matplotlib seaborn mlflow -y
    }
    Write-Host "✅ Entorno '$EnvName' creado." -ForegroundColor Green
  }
  conda activate $EnvName
  Write-Host "✅ Entorno '$EnvName' activado." -ForegroundColor Green
}
# ───────────── Inicializar Conda en PowerShell ─────────────
function Init-CondaPowerShell {
  $condaExe = "$env:USERPROFILE\miniforge3\Scripts\conda.exe"
  if (Test-Path $condaExe) {
    & $condaExe init powershell
    Write-Host "✅ Conda inicializado para PowerShell. Cierra y abre una nueva terminal para aplicar los cambios." -ForegroundColor Green
  }
  else {
    Write-Host "❌ No se encontró conda.exe en Miniforge. Verifica la instalación." -ForegroundColor Red
  }
}


# ───────────── PATH Miniforge ─────────────
function Set-MiniforgePath {
  $miniforgePath = "$env:USERPROFILE\miniforge3"
  $paths = @(
    "$miniforgePath",
    "$miniforgePath\Scripts",
    "$miniforgePath\condabin"
  )
  foreach ($p in $paths) {
    if ($env:PATH -notlike "*$p*") {
      [Environment]::SetEnvironmentVariable("PATH", "$($env:PATH);$p", [EnvironmentVariableTarget]::User)
      Write-Host "🔧 PATH actualizado con: $p" -ForegroundColor Green
    }
  }
}


# ───────────── Utils ─────────────
function Have($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
function Find-CondaRoot {
  $c = @("$HOME\miniforge3", "$HOME\mambaforge", "$HOME\miniconda3", "$HOME\anaconda3")
  foreach ($p in $c) { if (Test-Path "$p\condabin\conda.bat") { return $p } }
  if (Have "conda") { return (Split-Path -Parent (Split-Path -Parent (Get-Command conda).Path)) }
  return $null
}
function Use-Conda($root) { & "$root\condabin\conda.bat" shell.powershell hook | Out-String | Invoke-Expression }
function Get-Mamba {
  if (Have "mamba") { return "mamba" }
  conda install -n base -c conda-forge mamba -y | Out-Null
  if (Have "mamba") { return "mamba" }
  conda install -n base -c conda-forge conda-libmamba-solver -y | Out-Null
  conda config --set solver libmamba | Out-Null
  conda config --set channel_priority strict | Out-Null
  return "conda"
}
function Test-EnvExists($n) { (conda env list 2>$null) -match "^\s*$n\s" | Out-Null; return ($? -eq $true) }
function New-Env($tool, $n, $pkgs) {
  & $tool create -n $n -c conda-forge $pkgs -y | Out-Null
  if ($pkgs -match "ipykernel") { conda run -n $n python -m ipykernel install --user --name $n --display-name "Python ($n)" | Out-Null }
}
function Initialize-Env($tool, $n, $pkgs) {
  if (-not (Test-EnvExists $n)) { Write-Host "📦 Creando entorno '$n'…" -ForegroundColor Yellow; New-Env $tool $n $pkgs; Write-Host "✅ '$n' listo." -ForegroundColor Green }
}
function Install-Pkg($tool, $n, $imp, $extra = "") {
  conda run -n $n python -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$imp') else 1)" | Out-Null
  if ($LASTEXITCODE -ne 0) { & $tool install -n $n -c conda-forge ($extra -ne "" ? $extra : $imp) -y | Out-Null }
}
function Test-Port($p) { $x = (Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue); return $null -ne $x }


# ───────────── Activar entorno DS ─────────────
function Ensure-Path {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
    Write-Host "📁 Carpeta creada: $Path" -ForegroundColor Green
  }
  else {
    Write-Host "✔️ Carpeta existe: $Path" -ForegroundColor DarkGray
  }
}

# ───────────── Setup base ─────────────
$root = Find-CondaRoot
if (-not $root) { Write-Error "❌ No se encontró Miniforge/Miniconda/Anaconda."; exit 1 }
Use-Conda $root
$PKG = Get-Mamba
Write-Host "🔧 Gestor: $PKG | Root: $root" -ForegroundColor Cyan

# ds: entorno de trabajo (si Minimal: no instala numpy/pandas/sklearn)
$dsPkgsBase = "python=3.11 jupyterlab ipykernel"
$dsPkgsFull = "$dsPkgsBase numpy pandas scikit-learn matplotlib seaborn"
Initialize-Env $PKG $EnvName ($Minimal ? $dsPkgsBase : $dsPkgsFull)

# Infra MLflow (si InfraSplit)
if ($InfraSplit) {
  # entorno mínimo para servir MLflow
  $infraPkgs = "python=3.11 mlflow"
  Initialize-Env $PKG $InfraName $infraPkgs
}
else {
  # instalar MLflow en ds (si no se usa infra aparte)
  Install-Pkg $PKG $EnvName "mlflow"
}

# JupyterLab siempre en ds
Install-Pkg $PKG $EnvName "jupyterlab" "jupyterlab ipykernel"

if ($SetupOnly) { Write-Host "🧰 Setup listo. (por -SetupOnly)" -ForegroundColor DarkGray; exit 0 }


# ───────────── Lanzar servicios ─────────────
# Crear carpeta de artefactos si no existe antes de lanzar MLflow
Ensure-Path "./artifacts"

# MLflow server
if (-not $OnlyLab) {
  if (-not (Test-Port $MLflowPort)) {
    if ($InfraSplit) {
      $cmd = "conda activate $InfraName; mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --host 127.0.0.1 --port $MLflowPort"
    }
    else {
      $cmd = "conda activate $EnvName; mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --host 127.0.0.1 --port $MLflowPort"
    }
    Start-Process powershell -ArgumentList $cmd | Out-Null
    Write-Host "🚀 MLflow: http://127.0.0.1:$MLflowPort" -ForegroundColor Green
  }
  else { Write-Host "ℹ️  MLflow ya está en :$MLflowPort" -ForegroundColor DarkGray }
  if ($OnlyMLflow) { exit 0 }
}

# JupyterLab (en ds)
if (-not $OnlyMLflow) {
  if (-not (Test-Port $JLabPort)) {
    $token = ($NoBrowser ? "--NotebookApp.token=''" : "")
    $open = ($NoBrowser ? "--no-browser" : "")
    $jcmd = "conda activate $EnvName; jupyter lab $open $token --ip=0.0.0.0 --port $JLabPort"
    Start-Process powershell -ArgumentList $jcmd | Out-Null
    Write-Host "🚀 JupyterLab: http://127.0.0.1:$JLabPort" -ForegroundColor Green
  }
  else { Write-Host "ℹ️  JupyterLab ya está en :$JLabPort" -ForegroundColor DarkGray }
}

Write-Host "`nListo. Kernel: Python ($EnvName)" -ForegroundColor Cyan
if ($InfraSplit) { Write-Host "MLflow corre en entorno: $InfraName" -ForegroundColor DarkGray }

#Ejemplo de uso
# # Solo preparar (no lanza servicios)
# .\ds_tool.ps1 -SetupOnly

# # Activar entorno DS (crea si no existe)
# powershell -ExecutionPolicy Bypass -File .\ds_tools.ps1; Activate-Environment

# # Inicializar conda en PowerShell (solo una vez)
# powershell -ExecutionPolicy Bypass -File .\ds_tools.ps1; Init-CondaPowerShell

# # Agregar Miniforge al PATH de usuario
# powershell -ExecutionPolicy Bypass -File .\ds_tools.ps1; Set-MiniforgePath

# # Lanzar ambos (Jupyter + MLflow) en un entorno
# .\ds_tool.ps1

# # Usar InfraSplit: MLflow en entorno separado
# .\ds_tool.ps1 -InfraSplit

# # Solo JupyterLab (no toca MLflow)
# .\ds_tool.ps1 -OnlyLab

# # Solo MLflow (útil si ya tenés Jupyter abierto)
# .\ds_tool.ps1 -OnlyMLflow

# # Entorno minimal (ds con solo python+jlab+ipykernel)
# .\ds_tool.ps1 -Minimal

# # Puertos personalizados y con navegador abierto
# .\ds_tool.ps1 -JLabPort 8890 -MLflowPort 5050 -NoBrowser:$false
