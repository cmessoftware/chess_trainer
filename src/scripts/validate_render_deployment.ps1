#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validación pre-deployment para Render
.DESCRIPTION
    Verifica que todos los archivos necesarios estén listos antes del deployment
.EXAMPLE
    .\validate_render_deployment.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "🔍 VALIDACIÓN PRE-DEPLOYMENT - RENDER" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

$errors = @()
$warnings = @()

# ============================================================================
# STEP 1: Check Required Files
# ============================================================================

Write-Host "`n📁 Verificando archivos requeridos..." -ForegroundColor Yellow

$requiredFiles = @(
    @{Path = "dockerfile.render"; Description = "Dockerfile para Render" },
    @{Path = "render.yaml"; Description = "Blueprint de configuración" },
    @{Path = "deployment\render_startup.sh"; Description = "Script de inicio" },
    @{Path = "requirements.txt"; Description = "Dependencias Python base" },
    @{Path = "requirements_ai_coach.txt"; Description = "Dependencias AI Coach" },
    @{Path = "src\api\main.py"; Description = "API principal" },
    @{Path = "alembic.ini"; Description = "Configuración Alembic (migrations)" }
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file.Path) {
        Write-Host "   ✅ $($file.Description): $($file.Path)" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ FALTA: $($file.Description): $($file.Path)" -ForegroundColor Red
        $errors += "Archivo faltante: $($file.Path)"
    }
}

# ============================================================================
# STEP 2: Check Docker Configuration
# ============================================================================

Write-Host "`n🐳 Verificando configuración Docker..." -ForegroundColor Yellow

# Check dockerfile.render
if (Test-Path "dockerfile.render") {
    $dockerContent = Get-Content "dockerfile.render" -Raw
    
    # Check critical lines
    $checks = @(
        @{Pattern = "FROM python:3.11"; Name = "Base image" },
        @{Pattern = "ollama"; Name = "Ollama installation" },
        @{Pattern = "requirements_ai_coach.txt"; Name = "AI Coach dependencies" },
        @{Pattern = "EXPOSE.*11434"; Name = "Ollama port" }
    )
    
    foreach ($check in $checks) {
        if ($dockerContent -match $check.Pattern) {
            Write-Host "   ✅ $($check.Name)" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  $($check.Name) no encontrado" -ForegroundColor Yellow
            $warnings += "Dockerfile: $($check.Name) no encontrado"
        }
    }
}

# ============================================================================
# STEP 3: Check render.yaml
# ============================================================================

Write-Host "`n⚙️  Verificando render.yaml..." -ForegroundColor Yellow

if (Test-Path "render.yaml") {
    $renderContent = Get-Content "render.yaml" -Raw
    
    $renderChecks = @(
        @{Pattern = "type: web"; Name = "Web service definido" },
        @{Pattern = "type: pserv|databases:"; Name = "PostgreSQL definido" },
        @{Pattern = "plan: pro"; Name = "Plan Pro (8GB RAM)" },
        @{Pattern = "disk:"; Name = "Persistent disk configurado" },
        @{Pattern = "OLLAMA_MODEL"; Name = "Variable de modelo LLM" }
    )
    
    foreach ($check in $renderChecks) {
        if ($renderContent -match $check.Pattern) {
            Write-Host "   ✅ $($check.Name)" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  $($check.Name) no encontrado" -ForegroundColor Yellow
            $warnings += "render.yaml: $($check.Name) no encontrado"
        }
    }
    
    # Check model configuration
    if ($renderContent -match "llama3.1:8b") {
        Write-Host "   ✅ Modelo de producción: llama3.1:8b" -ForegroundColor Green
    }
    elseif ($renderContent -match "llama3.2:3b") {
        Write-Host "   ⚠️  Modelo de desarrollo: llama3.2:3b (menor calidad)" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 4: Check API Health Endpoint
# ============================================================================

Write-Host "`n🏥 Verificando endpoint /health..." -ForegroundColor Yellow

if (Test-Path "src\api\main.py") {
    $apiContent = Get-Content "src\api\main.py" -Raw
    
    if ($apiContent -match '@app.get\("/health"\)') {
        Write-Host "   ✅ Endpoint /health definido" -ForegroundColor Green
        
        # Check if it's the enhanced version
        if ($apiContent -match "ollama.*check" -or $apiContent -match "database.*check") {
            Write-Host "   ✅ Health check completo (API + DB + Ollama)" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Health check básico (considera mejorar)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   ❌ Endpoint /health NO encontrado" -ForegroundColor Red
        $errors += "/health endpoint faltante en main.py"
    }
}

# ============================================================================
# STEP 5: Check Git Status
# ============================================================================

Write-Host "`n📦 Verificando estado Git..." -ForegroundColor Yellow

try {
    $gitStatus = git status --porcelain 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        if ([string]::IsNullOrWhiteSpace($gitStatus)) {
            Write-Host "   ✅ Todo commiteado" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Hay archivos sin commitear:" -ForegroundColor Yellow
            $uncommitted = ($gitStatus -split "`n") | Select-Object -First 5
            foreach ($file in $uncommitted) {
                Write-Host "      $file" -ForegroundColor Gray
            }
            $warnings += "Archivos sin commitear encontrados"
        }
        
        # Check remote
        $remote = git remote -v 2>&1
        if ($remote -match "github|gitlab|bitbucket") {
            Write-Host "   ✅ Remote configurado" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Remote no configurado o no es GitHub/GitLab" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   ⚠️  No es un repositorio Git" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ⚠️  Git no disponible o error: $_" -ForegroundColor Yellow
}

# ============================================================================
# STEP 6: Estimate Costs
# ============================================================================

Write-Host "`n💰 Estimación de costos mensuales..." -ForegroundColor Yellow

# Check plan in render.yaml
$plan = "pro"  # default
if (Test-Path "render.yaml") {
    $renderContent = Get-Content "render.yaml" -Raw
    if ($renderContent -match "plan:\s*(starter|standard|pro|pro-plus)") {
        $plan = $matches[1]
    }
}

$costs = @{
    "starter"  = @{App = 7; DB = 7; Total = 14; RAM = "512MB"; Model = "No LLM" }
    "standard" = @{App = 25; DB = 7; Total = 32; RAM = "4GB"; Model = "llama3.2:3b" }
    "pro"      = @{App = 85; DB = 7; Total = 92; RAM = "8GB"; Model = "llama3.1:8b" }
    "pro-plus" = @{App = 150; DB = 7; Total = 157; RAM = "16GB"; Model = "llama3.1:70b" }
}

if ($costs.ContainsKey($plan)) {
    $cost = $costs[$plan]
    Write-Host "   📊 Plan: $plan" -ForegroundColor Cyan
    Write-Host "      - App: `$$($cost.App)/mes" -ForegroundColor White
    Write-Host "      - PostgreSQL: `$$($cost.DB)/mes" -ForegroundColor White
    Write-Host "      - RAM: $($cost.RAM)" -ForegroundColor White
    Write-Host "      - Modelo: $($cost.Model)" -ForegroundColor White
    Write-Host "      ━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "      💵 TOTAL: `$$($cost.Total)/mes" -ForegroundColor Green
}

# ============================================================================
# STEP 7: Final Summary
# ============================================================================

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "📊 RESUMEN DE VALIDACIÓN" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "`n✅ ¡TODO PERFECTO! Listo para deployment." -ForegroundColor Green
    Write-Host "`n📚 Próximos pasos:" -ForegroundColor Yellow
    Write-Host "   1. git add ." -ForegroundColor White
    Write-Host "   2. git commit -m 'Ready for Render deployment'" -ForegroundColor White
    Write-Host "   3. git push origin main" -ForegroundColor White
    Write-Host "   4. Ir a Render Dashboard → New + → Blueprint" -ForegroundColor White
    Write-Host "`n📖 Guía completa: deployment\RENDER_QUICK_START.md" -ForegroundColor Cyan
}
else {
    if ($errors.Count -gt 0) {
        Write-Host "`n❌ ERRORES ENCONTRADOS ($($errors.Count)):" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "   • $error" -ForegroundColor Red
        }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️  ADVERTENCIAS ($($warnings.Count)):" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   • $warning" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n💡 Recomendación:" -ForegroundColor Cyan
    if ($errors.Count -gt 0) {
        Write-Host "   Corrige los errores antes de hacer deployment." -ForegroundColor White
    }
    else {
        Write-Host "   Puedes proceder, pero revisa las advertencias." -ForegroundColor White
    }
}

Write-Host "`n"

# Exit code
if ($errors.Count -gt 0) {
    exit 1
}
else {
    exit 0
}
