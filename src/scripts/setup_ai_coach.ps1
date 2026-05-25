#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Instalador y configurador del sistema AI Chess Coach
.DESCRIPTION
    Script de instalación automatizada para el sistema completo de AI Chess Coach
    según el roadmap definido en docs/0-ai_chess_coach_roadmap.md
.EXAMPLE
    .\setup_ai_coach.ps1 -InstallAll
    .\setup_ai_coach.ps1 -CheckDependencies
#>

param(
    [switch]$InstallDependencies,
    [switch]$CreateStructure,
    [switch]$DownloadModels,
    [switch]$InstallAll,
    [switch]$CheckDependencies,
    [switch]$TestInstallation
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔹 $Message" -ForegroundColor $InfoColor
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $WarningColor
}

# ============================================================================
# STEP 1: Check Prerequisites
# ============================================================================

function Test-Prerequisites {
    Write-Step "Verificando prerequisitos..."
    
    $allGood = $true
    
    # Check conda activation
    $condaEnv = $env:CONDA_DEFAULT_ENV
    if ($condaEnv -ne "chess_trainer") {
        Write-Error-Custom "Ambiente conda 'chess_trainer' NO está activado"
        Write-Host "   Ejecuta: conda activate chess_trainer" -ForegroundColor Yellow
        $allGood = $false
    }
    else {
        Write-Success "Ambiente conda 'chess_trainer' activado"
    }
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python encontrado: $pythonVersion"
    }
    catch {
        Write-Error-Custom "Python no encontrado"
        $allGood = $false
    }
    
    # Check pip
    try {
        $pipVersion = pip --version 2>&1
        Write-Success "pip encontrado: $pipVersion"
    }
    catch {
        Write-Error-Custom "pip no encontrado"
        $allGood = $false
    }
    
    return $allGood
}

# ============================================================================
# STEP 2: Install Python Dependencies
# ============================================================================

function Install-PythonDependencies {
    Write-Step "Instalando dependencias Python..."
    
    $requirementsFile = "requirements_ai_coach.txt"
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Error-Custom "Archivo $requirementsFile no encontrado"
        return $false
    }
    
    try {
        Write-Host "   Instalando desde $requirementsFile..." -ForegroundColor Gray
        pip install -r $requirementsFile --upgrade
        
        Write-Success "Dependencias Python instaladas correctamente"
        return $true
    }
    catch {
        Write-Error-Custom "Error instalando dependencias: $_"
        return $false
    }
}

# ============================================================================
# STEP 3: Check Ollama Installation
# ============================================================================

function Test-OllamaInstallation {
    Write-Step "Verificando instalación de Ollama..."
    
    try {
        $ollamaVersion = ollama --version 2>&1
        Write-Success "Ollama instalado: $ollamaVersion"
        
        # Check if Ollama is running
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434" -Method GET -TimeoutSec 5 -ErrorAction Stop
            Write-Success "Ollama está ejecutándose en localhost:11434"
            return $true
        }
        catch {
            Write-Warning-Custom "Ollama instalado pero NO está ejecutándose"
            Write-Host "   Ejecuta: ollama serve" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Warning-Custom "Ollama NO instalado"
        Write-Host "   Descarga desde: https://ollama.ai/download" -ForegroundColor Yellow
        Write-Host "   O ejecuta: winget install Ollama.Ollama" -ForegroundColor Yellow
        return $false
    }
}

# ============================================================================
# STEP 4: Download LLM Models
# ============================================================================

function Install-OllamaModels {
    Write-Step "Descargando modelos LLM..."
    
    $models = @(
        @{Name = "llama3.2:3b"; Size = "3GB"; Priority = "Development"; Description = "Rápido para desarrollo" },
        @{Name = "llama3.1:8b"; Size = "4.7GB"; Priority = "Production"; Description = "Mejor calidad para producción" }
    )
    
    foreach ($model in $models) {
        Write-Host "`n   📥 Descargando $($model.Name) ($($model.Size)) - $($model.Description)..." -ForegroundColor Gray
        
        try {
            ollama pull $model.Name
            Write-Success "$($model.Name) descargado exitosamente"
        }
        catch {
            Write-Error-Custom "Error descargando $($model.Name): $_"
        }
    }
}

# ============================================================================
# STEP 5: Create Directory Structure
# ============================================================================

function New-ProjectStructure {
    Write-Step "Creando estructura de directorios..."
    
    $directories = @(
        "src/ai_coach",
        "src/ai_coach/rag",
        "src/ai_coach/llm",
        "src/ai_coach/prompts",
        "data/chess_books",
        "data/chess_books/raw",
        "data/chess_books/processed",
        "data/vectorstore",
        "tests/ai_coach"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            Write-Host "   ✓ Creado: $dir" -ForegroundColor Green
        }
        else {
            Write-Host "   ✓ Ya existe: $dir" -ForegroundColor Gray
        }
    }
    
    # Create __init__.py files
    $initFiles = @(
        "src/ai_coach/__init__.py",
        "src/ai_coach/rag/__init__.py",
        "src/ai_coach/llm/__init__.py",
        "tests/ai_coach/__init__.py"
    )
    
    foreach ($file in $initFiles) {
        if (-not (Test-Path $file)) {
            New-Item -ItemType File -Force -Path $file | Out-Null
            Write-Host "   ✓ Creado: $file" -ForegroundColor Green
        }
    }
    
    Write-Success "Estructura de directorios creada"
}

# ============================================================================
# STEP 6: Test Installation
# ============================================================================

function Test-Installation {
    Write-Step "Probando instalación..."
    
    $testScript = @"
import sys

def test_imports():
    """Test critical imports."""
    print('🧪 Testing imports...')
    
    errors = []
    
    # Test sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        print('✅ sentence-transformers OK')
    except ImportError as e:
        errors.append(f'sentence-transformers: {e}')
        print(f'❌ sentence-transformers FAILED: {e}')
    
    # Test chromadb
    try:
        import chromadb
        print('✅ chromadb OK')
    except ImportError as e:
        errors.append(f'chromadb: {e}')
        print(f'❌ chromadb FAILED: {e}')
    
    # Test langchain
    try:
        from langchain_ollama import OllamaLLM
        print('✅ langchain-ollama OK')
    except ImportError as e:
        errors.append(f'langchain-ollama: {e}')
        print(f'❌ langchain-ollama FAILED: {e}')
    
    # Test pypdf2
    try:
        import PyPDF2
        print('✅ PyPDF2 OK')
    except ImportError as e:
        errors.append(f'PyPDF2: {e}')
        print(f'❌ PyPDF2 FAILED: {e}')
    
    if errors:
        print(f'\n❌ {len(errors)} errors found')
        return False
    else:
        print('\n✅ All imports successful!')
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
"@
    
    $testScript | python -
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Instalación verificada correctamente"
        return $true
    }
    else {
        Write-Error-Custom "La instalación tiene errores"
        return $false
    }
}

# ============================================================================
# STEP 7: Display Summary
# ============================================================================

function Show-Summary {
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "📊 RESUMEN DE INSTALACIÓN" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    
    Write-Host "`n✅ Instalación completada con éxito!" -ForegroundColor Green
    
    Write-Host "`n📚 Próximos pasos:" -ForegroundColor Yellow
    Write-Host "   1. Implementar feature_summarizer.py" -ForegroundColor White
    Write-Host "   2. Implementar chess_rag.py" -ForegroundColor White
    Write-Host "   3. Implementar coaching_llm.py" -ForegroundColor White
    Write-Host "   4. Ejecutar tests: pytest tests/ai_coach/ -v" -ForegroundColor White
    
    Write-Host "`n📖 Documentación:" -ForegroundColor Yellow
    Write-Host "   docs/AI_COACH_IMPLEMENTATION_GUIDE.md" -ForegroundColor White
    Write-Host "   docs/0-ai_chess_coach_roadmap.md" -ForegroundColor White
    
    Write-Host "`n🚀 Comandos útiles:" -ForegroundColor Yellow
    Write-Host "   ollama serve                    # Iniciar servidor Ollama" -ForegroundColor White
    Write-Host "   ollama list                     # Ver modelos instalados" -ForegroundColor White
    Write-Host "   python src/scripts/test_ai_coach_pipeline.py  # Probar pipeline" -ForegroundColor White
    
    Write-Host "`n"
}

# ============================================================================
# Main Execution Flow
# ============================================================================

function Start-Installation {
    Write-Host "`n"
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "🤖 AI CHESS COACH - INSTALADOR AUTOMATIZADO" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    
    # Step 1: Prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error-Custom "Prerequisitos no cumplidos. Abortando."
        exit 1
    }
    
    # Step 2: Install Python dependencies
    if ($InstallDependencies -or $InstallAll) {
        if (-not (Install-PythonDependencies)) {
            Write-Error-Custom "Error instalando dependencias Python"
            exit 1
        }
    }
    
    # Step 3: Check Ollama
    $ollamaInstalled = Test-OllamaInstallation
    
    # Step 4: Download models
    if (($DownloadModels -or $InstallAll) -and $ollamaInstalled) {
        Install-OllamaModels
    }
    
    # Step 5: Create structure
    if ($CreateStructure -or $InstallAll) {
        New-ProjectStructure
    }
    
    # Step 6: Test installation
    if ($TestInstallation -or $InstallAll) {
        Test-Installation
    }
    
    # Step 7: Summary
    Show-Summary
}

# ============================================================================
# Execute based on parameters
# ============================================================================

if ($CheckDependencies) {
    Test-Prerequisites
    Test-OllamaInstallation
    Test-Installation
}
elseif ($InstallAll -or $InstallDependencies -or $CreateStructure -or $DownloadModels -or $TestInstallation) {
    Start-Installation
}
else {
    Write-Host "AI Chess Coach - Setup Script" -ForegroundColor Cyan
    Write-Host "`nUso:" -ForegroundColor Yellow
    Write-Host "   .\setup_ai_coach.ps1 -InstallAll         # Instalar todo" -ForegroundColor White
    Write-Host "   .\setup_ai_coach.ps1 -CheckDependencies  # Verificar instalación" -ForegroundColor White
    Write-Host "   .\setup_ai_coach.ps1 -InstallDependencies  # Solo instalar Python deps" -ForegroundColor White
    Write-Host "   .\setup_ai_coach.ps1 -CreateStructure      # Solo crear directorios" -ForegroundColor White
    Write-Host "   .\setup_ai_coach.ps1 -DownloadModels       # Solo descargar modelos LLM" -ForegroundColor White
    Write-Host "   .\setup_ai_coach.ps1 -TestInstallation     # Solo probar instalación" -ForegroundColor White
}
