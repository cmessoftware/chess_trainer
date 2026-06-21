#!/usr/bin/env pwsh

# Setup plan script (PowerShell)

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: .\setup-plan.ps1 [--json]
  -Json    Output results in JSON format
  -Help    Show this help message
"@
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get all paths
$paths = Get-FeaturePaths
$CURRENT_BRANCH = $paths.CURRENT_BRANCH
$HAS_GIT = $paths.HAS_GIT
$FEATURE_DIR = $paths.FEATURE_DIR
$FEATURE_SPEC = $paths.FEATURE_SPEC
$IMPL_PLAN = $paths.IMPL_PLAN
$REPO_ROOT = $paths.REPO_ROOT

# Check feature branch
if (-not (Check-FeatureBranch -Branch $CURRENT_BRANCH -HasGitRepo $HAS_GIT)) {
    exit 1
}

# Ensure directory exists
if (-not (Test-Path $FEATURE_DIR -PathType Container)) {
    New-Item -ItemType Directory -Path $FEATURE_DIR -Force | Out-Null
}

# Copy plan template
$TEMPLATE = Join-Path $REPO_ROOT ".specify/templates/plan-template.md"
if (Test-Path $TEMPLATE -PathType Leaf) {
    Copy-Item -Path $TEMPLATE -Destination $IMPL_PLAN -Force
    if (-not $Json) {
        Write-Output "Copied plan template to $IMPL_PLAN"
    }
} else {
    if (-not $Json) {
        Write-Warning "Plan template not found at $TEMPLATE"
    }
    # Create empty plan file
    New-Item -ItemType File -Path $IMPL_PLAN -Force | Out-Null
}

# Output results
if ($Json) {
    $outObj = [PSCustomObject]@{
        FEATURE_SPEC = $FEATURE_SPEC
        IMPL_PLAN    = $IMPL_PLAN
        SPECS_DIR    = $FEATURE_DIR
        BRANCH       = $CURRENT_BRANCH
        HAS_GIT      = $HAS_GIT
    }
    $outObj | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $FEATURE_SPEC"
    Write-Output "IMPL_PLAN: $IMPL_PLAN"
    Write-Output "SPECS_DIR: $FEATURE_DIR"
    Write-Output "BRANCH: $CURRENT_BRANCH"
    Write-Output "HAS_GIT: $HAS_GIT"
}
