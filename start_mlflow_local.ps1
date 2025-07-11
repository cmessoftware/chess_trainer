# Script para iniciar MLflow localmente sin Docker con entorno virtual
# start_mlflow_local.ps1

param(
    [switch]$Install,
    [switch]$Help,
    [string]$Port = "5000",
    [string]$HostAddress = "127.0.0.1",
    [switch]$CreateVenv,
    [switch]$UsePostgres = $true
)

function Show-Help {
    Write-Host @"
🚀 MLflow Local Starter para Chess Trainer

USO:
    .\start_mlflow_local.ps1 [opciones]

OPCIONES:
    -Install       Instalar dependencias de MLflow antes de iniciar
    -Port          Puerto para MLflow (default: 5000)
    -HostAddress   Host para MLflow (default: 127.0.0.1)
    -UsePostgres   Usar PostgreSQL como backend (default: true)
    -Help          Mostrar esta ayuda

EJEMPLOS:
    .\start_mlflow_local.ps1                    # Iniciar MLflow con PostgreSQL
    .\start_mlflow_local.ps1 -Install           # Instalar e iniciar
    .\start_mlflow_local.ps1 -Port 5001         # Usar puerto 5001
    .\start_mlflow_local.ps1 -UsePostgres:$false # Usar SQLite en lugar de PostgreSQL

"@ -ForegroundColor Cyan
}

function Test-PythonInstalled {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge [version]"3.8") {
                Write-Host "✅ Python $($matches[1]) encontrado" -ForegroundColor Green
                return $true
            }
            else {
                Write-Host "⚠️ Python $($matches[1]) encontrado, pero se requiere 3.8+" -ForegroundColor Yellow
                return $false
            }
        }
    }
    catch {
        Write-Host "❌ Python no encontrado" -ForegroundColor Red
        return $false
    }
}

function Test-VenvExists {
    return (Test-Path "venv_mlflow\Scripts\activate.ps1") -or (Test-Path "venv_mlflow\bin\activate")
}

function Create-VirtualEnvironment {
    Write-Host "🔨 Creando entorno virtual para MLflow..." -ForegroundColor Yellow
    
    if (-not (Test-PythonInstalled)) {
        Write-Host "❌ Python 3.8+ es requerido para crear el entorno virtual" -ForegroundColor Red
        Write-Host "💡 Instala Python desde: https://python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
    
    # Crear entorno virtual
    try {
        python -m venv venv_mlflow
        Write-Host "✅ Entorno virtual creado en: .\venv_mlflow\" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Error creando entorno virtual: $_" -ForegroundColor Red
        return $false
    }
}

function Activate-VirtualEnvironment {
    $activateScript = if (Test-Path "venv_mlflow\Scripts\activate.ps1") {
        "venv_mlflow\Scripts\activate.ps1"
    }
    elseif (Test-Path "venv_mlflow\bin\activate") {
        "venv_mlflow\bin\activate"
    }
    else {
        $null
    }
    
    if (-not $activateScript) {
        Write-Host "❌ No se encontró script de activación del entorno virtual" -ForegroundColor Red
        return $false
    }
    
    try {
        if ($activateScript.EndsWith(".ps1")) {
            & $activateScript
        }
        else {
            # Para sistemas Unix-like (si ejecutamos desde WSL)
            bash -c "source $activateScript"
        }
        Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "⚠️ No se pudo activar automáticamente. Activando manualmente..." -ForegroundColor Yellow
        # Cambiar al PATH del entorno virtual
        $env:PATH = "$(Resolve-Path 'venv_mlflow\Scripts');$env:PATH"
        return $true
    }
}

function Test-MLflowInstalled {
    try {
        # Verificar en el entorno virtual actual
        $mlflowPath = if (Test-Path "venv_mlflow\Scripts\mlflow.exe") {
            "venv_mlflow\Scripts\mlflow.exe"
        }
        elseif (Test-Path "venv_mlflow\bin\mlflow") {
            "venv_mlflow\bin\mlflow"
        }
        else {
            "mlflow"  # Fallback al global
        }
        
        $version = & $mlflowPath --version 2>&1
        if ($version -match "mlflow") {
            Write-Host "✅ MLflow encontrado: $version" -ForegroundColor Green
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

function Install-MLflowDependencies {
    Write-Host "📦 Instalando dependencias de MLflow en entorno virtual..." -ForegroundColor Yellow
    
    # Determinar el ejecutable pip correcto
    $pipPath = if (Test-Path "venv_mlflow\Scripts\pip.exe") {
        "venv_mlflow\Scripts\pip.exe"
    }
    elseif (Test-Path "venv_mlflow\bin\pip") {
        "venv_mlflow\bin\pip"
    }
    else {
        "pip"  # Fallback
    }
    
    $packages = @(
        "mlflow",
        "pandas", 
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "numpy"
    )
    
    # En Windows necesitamos psycopg2 (no -binary)
    if ($IsWindows -or $PSVersionTable.Platform -eq "Win32NT") {
        $packages += "psycopg2"
    }
    else {
        $packages += "psycopg2-binary"
    }
    
    foreach ($package in $packages) {
        Write-Host "   • Instalando $package..." -ForegroundColor Gray
        try {
            & $pipPath install $package --quiet
            Write-Host "     ✅ $package instalado" -ForegroundColor Green
        }
        catch {
            Write-Host "     ⚠️ Error instalando $package`: $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
}

function New-VirtualEnvironment {
    Write-Host "🔨 Creando entorno virtual para MLflow..." -ForegroundColor Yellow
    
    if (-not (Test-PythonInstalled)) {
        Write-Host "❌ Python 3.8+ es requerido para crear el entorno virtual" -ForegroundColor Red
        Write-Host "💡 Instala Python desde: https://python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
    
    # Crear entorno virtual
    try {
        python -m venv venv_mlflow
        Write-Host "✅ Entorno virtual creado en: .\venv_mlflow\" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Error creando entorno virtual: $_" -ForegroundColor Red
        return $false
    }
}

function Enable-VirtualEnvironment {
    $activateScript = if (Test-Path "venv_mlflow\Scripts\activate.ps1") {
        "venv_mlflow\Scripts\activate.ps1"
    }
    elseif (Test-Path "venv_mlflow\bin\activate") {
        "venv_mlflow\bin\activate"
    }
    else {
        $null
    }
    
    if (-not $activateScript) {
        Write-Host "❌ No se encontró script de activación del entorno virtual" -ForegroundColor Red
        return $false
    }
    
    try {
        if ($activateScript.EndsWith(".ps1")) {
            & $activateScript
        }
        else {
            # Para sistemas Unix-like (si ejecutamos desde WSL)
            bash -c "source $activateScript"
        }
        Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "⚠️ No se pudo activar automáticamente. Configurando PATH..." -ForegroundColor Yellow
        # Cambiar al PATH del entorno virtual
        $venvScripts = Resolve-Path 'venv_mlflow\Scripts' -ErrorAction SilentlyContinue
        if ($venvScripts) {
            $env:PATH = "$venvScripts;$env:PATH"
            Write-Host "✅ PATH configurado para entorno virtual" -ForegroundColor Green
        }
        return $true
    }
}

function Initialize-MLflowDirectories {
    $directories = @("mlruns", "data", "models")
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Name $dir -Force | Out-Null
            Write-Host "📁 Directorio '$dir' creado" -ForegroundColor Yellow
        }
    }
}

function Test-PortAvailable {
    param([int]$Port)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect($HostAddress, $Port)
        $connection.Close()
        return $false  # Puerto ocupado
    }
    catch {
        return $true   # Puerto disponible
    }
}

function Start-MLflowServer {
    param(
        [string]$HostAddress, 
        [string]$Port,
        [bool]$UsePostgres = $true
    )
    
    Write-Host "🔍 Verificando puerto $Port..." -ForegroundColor Gray
    
    if (-not (Test-PortAvailable -Port $Port)) {
        Write-Host "⚠️ Puerto $Port está ocupado. Probando puerto alternativo..." -ForegroundColor Yellow
        $Port = [int]$Port + 1
        if (-not (Test-PortAvailable -Port $Port)) {
            Write-Host "❌ No se pudo encontrar un puerto disponible" -ForegroundColor Red
            return $false
        }
        Write-Host "✅ Usando puerto alternativo: $Port" -ForegroundColor Green
    }
    
    # Determinar el backend basado en el parámetro
    if ($UsePostgres) {
        # Configuración PostgreSQL (docker-compose)
        $pgUser = "chess"
        $pgPassword = "chess_pass"
        $pgHost = "localhost"
        $pgPort = "5432"
        $pgDb = "chess_trainer_db"
        $backendUri = "postgresql://${pgUser}:${pgPassword}@${pgHost}:${pgPort}/${pgDb}"
        $backendType = "PostgreSQL"
    }
    else {
        # SQLite fallback
        $backendUri = "sqlite:///mlflow.db"
        $backendType = "SQLite (mlflow.db)"
    }
    
    $mlflowArgs = @(
        "server",
        "--host", $HostAddress,
        "--port", $Port,
        "--backend-store-uri", $backendUri,
        "--default-artifact-root", "./mlruns"
    )
    
    Write-Host "🌐 Iniciando MLflow en http://$HostAddress`:$Port..." -ForegroundColor Cyan
    Write-Host "📊 Backend: $backendType" -ForegroundColor Gray
    Write-Host "📁 Artifacts: ./mlruns" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⏹️ Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
    Write-Host "🌐 Abriendo navegador..." -ForegroundColor Green
    
    # Abrir navegador después de 3 segundos
    Start-Job -ScriptBlock {
        Start-Sleep 3
        Start-Process "http://$using:HostAddress`:$using:Port"
    } | Out-Null
    
    # Iniciar MLflow server
    try {
        mlflow @mlflowArgs
    }
    catch {
        Write-Host "❌ Error iniciando MLflow: $_" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Función principal
function Main {
    Write-Host @"
🚀 MLflow Local Starter - Chess Trainer
═══════════════════════════════════════
"@ -ForegroundColor Cyan

    if ($Help) {
        Show-Help
        return
    }
    
    # Verificar si estamos en el directorio correcto
    if (-not (Test-Path "src") -or -not (Test-Path ".vscode")) {
        Write-Host "❌ Por favor ejecuta este script desde el directorio raíz de chess_trainer" -ForegroundColor Red
        Write-Host "   Directorio actual: $PWD" -ForegroundColor Gray
        return
    }
    
    # Instalar dependencias si se solicita
    if ($Install -or -not (Test-MLflowInstalled)) {
        if (-not (Test-MLflowInstalled)) {
            Write-Host "⚠️ MLflow no está instalado" -ForegroundColor Yellow
        }
        Install-MLflowDependencies
    }
    
    # Verificar instalación
    if (-not (Test-MLflowInstalled)) {
        Write-Host "❌ MLflow no está disponible. Instala con: .\start_mlflow_local.ps1 -Install" -ForegroundColor Red
        return
    }
    
    Write-Host "✅ MLflow está instalado" -ForegroundColor Green
    
    # Inicializar directorios
    Initialize-MLflowDirectories
    
    # Mostrar información del proyecto
    Write-Host "📋 Información del proyecto:" -ForegroundColor Cyan
    Write-Host "   • Directorio: $PWD" -ForegroundColor Gray
    
    # Determinar tipo de backend
    if ($UsePostgres) {
        Write-Host "   • Backend: PostgreSQL" -ForegroundColor Gray
    }
    else {
        Write-Host "   • Backend: SQLite local" -ForegroundColor Gray
    }
    
    Write-Host "   • Artifacts: ./mlruns" -ForegroundColor Gray
    Write-Host ""
    
    # Iniciar servidor MLflow
    if (Start-MLflowServer -HostAddress $HostAddress -Port $Port -UsePostgres $UsePostgres) {
        Write-Host "✅ MLflow iniciado correctamente" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Error iniciando MLflow" -ForegroundColor Red
        Write-Host "💡 Sugerencias:" -ForegroundColor Yellow
        Write-Host "   • Verificar que no hay otro MLflow corriendo" -ForegroundColor Gray
        Write-Host "   • Probar con otro puerto: .\start_mlflow_local.ps1 -Port 5001" -ForegroundColor Gray
        Write-Host "   • Reinstalar dependencias: .\start_mlflow_local.ps1 -Install" -ForegroundColor Gray
    }
}

# Ejecutar función principal
Main
