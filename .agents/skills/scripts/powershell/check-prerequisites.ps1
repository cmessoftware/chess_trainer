#!/usr/bin/env pwsh

# Consolidated prerequisite checking script (PowerShell)
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: .\check-prerequisites.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -RequireTasks       Require tasks.md to exist (for implementation phase)
#   -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  .\check-prerequisites.ps1 -Json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly
"@
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get feature paths
$paths = Get-FeaturePaths
$CURRENT_BRANCH = $paths.CURRENT_BRANCH
$HAS_GIT = $paths.HAS_GIT
$FEATURE_DIR = $paths.FEATURE_DIR
$FEATURE_SPEC = $paths.FEATURE_SPEC
$IMPL_PLAN = $paths.IMPL_PLAN
$TASKS = $paths.TASKS
$RESEARCH = $paths.RESEARCH
$DATA_MODEL = $paths.DATA_MODEL
$QUICKSTART = $paths.QUICKSTART
$CONTRACTS_DIR = $paths.CONTRACTS_DIR
$REPO_ROOT = $paths.REPO_ROOT

# Validate branch name
if (-not (Check-FeatureBranch -Branch $CURRENT_BRANCH -HasGitRepo $HAS_GIT)) {
    exit 1
}

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if ($PathsOnly) {
    if ($Json) {
        $pathsObj = [PSCustomObject]@{
            REPO_ROOT    = $REPO_ROOT
            BRANCH       = $CURRENT_BRANCH
            FEATURE_DIR  = $FEATURE_DIR
            FEATURE_SPEC = $FEATURE_SPEC
            IMPL_PLAN    = $IMPL_PLAN
            TASKS        = $TASKS
        }
        $pathsObj | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $REPO_ROOT"
        Write-Output "BRANCH: $CURRENT_BRANCH"
        Write-Output "FEATURE_DIR: $FEATURE_DIR"
        Write-Output "FEATURE_SPEC: $FEATURE_SPEC"
        Write-Output "IMPL_PLAN: $IMPL_PLAN"
        Write-Output "TASKS: $TASKS"
    }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $FEATURE_DIR -PathType Container)) {
    [Console]::Error.WriteLine("ERROR: Feature directory not found: $FEATURE_DIR")
    [Console]::Error.WriteLine("Run /speckit.specify first to create the feature structure.")
    exit 1
}

if (-not (Test-Path $IMPL_PLAN -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: plan.md not found in $FEATURE_DIR")
    [Console]::Error.WriteLine("Run /speckit.plan first to create the implementation plan.")
    exit 1
}

# Check for tasks.md if required
if ($RequireTasks -and -not (Test-Path $TASKS -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: tasks.md not found in $FEATURE_DIR")
    [Console]::Error.WriteLine("Run /speckit.tasks first to create the task list.")
    exit 1
}

# Build list of available documents
$docs = @()

# Always check these optional docs
if (Test-Path $RESEARCH -PathType Leaf) { $docs += "research.md" }
if (Test-Path $DATA_MODEL -PathType Leaf) { $docs += "data-model.md" }

# Check contracts directory (only if it exists and has files)
if ((Test-Path $CONTRACTS_DIR -PathType Container) -and (Get-ChildItem -Path $CONTRACTS_DIR -ErrorAction SilentlyContinue)) {
    $docs += "contracts/"
}

if (Test-Path $QUICKSTART -PathType Leaf) { $docs += "quickstart.md" }

# Include tasks.md if requested and it exists
if ($IncludeTasks -and (Test-Path $TASKS -PathType Leaf)) {
    $docs += "tasks.md"
}

# Output results
if ($Json) {
    $resObj = [PSCustomObject]@{
        FEATURE_DIR    = $FEATURE_DIR
        AVAILABLE_DOCS = $docs
    }
    $resObj | ConvertTo-Json -Compress
} else {
    # Text output
    Write-Output "FEATURE_DIR:$FEATURE_DIR"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    Check-File -Path $RESEARCH -Label "research.md"
    Check-File -Path $DATA_MODEL -Label "data-model.md"
    Check-Dir -Path $CONTRACTS_DIR -Label "contracts/"
    Check-File -Path $QUICKSTART -Label "quickstart.md"
    
    if ($IncludeTasks) {
        Check-File -Path $TASKS -Label "tasks.md"
    }
}
