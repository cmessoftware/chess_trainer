#!/usr/bin/env pwsh

# Create a new feature (PowerShell)

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number,
    [switch]$Help,
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: .\create-new-feature.ps1 [--json] [--short-name <name>] [--number N] <feature_description>

Options:
  -Json               Output in JSON format
  -ShortName <name>   Provide a custom short name (2-4 words) for the branch
  -Number N           Specify branch number manually (overrides auto-detection)
  -Help, -h           Show this help message

Examples:
  .\create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth'
  .\create-new-feature.ps1 'Implement OAuth2 integration for API' -Number 5
"@
    exit 0
}

if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    [Console]::Error.WriteLine("Usage: .\create-new-feature.ps1 [--json] [--short-name <name>] [--number N] <feature_description>")
    exit 1
}

$FEATURE_DESCRIPTION = ($FeatureDescription -join " ").Trim()
if ([string]::IsNullOrEmpty($FEATURE_DESCRIPTION)) {
    [Console]::Error.WriteLine("Usage: .\create-new-feature.ps1 [--json] [--short-name <name>] [--number N] <feature_description>")
    exit 1
}

# Function to get highest number from specs directory
function Get-HighestFromSpecs {
    param([string]$SpecsDir)
    $highest = 0
    if (Test-Path $SpecsDir -PathType Container) {
        $dirs = Get-ChildItem -Path $SpecsDir -Directory
        foreach ($dir in $dirs) {
            if ($dir.Name -match "^([0-9]+)") {
                [int]$num = $Matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }
    return $highest
}

# Function to get highest number from git branches
function Get-HighestFromBranches {
    $highest = 0
    $branches = git branch -a 2>$null
    if ($LASTEXITCODE -eq 0 -and $branches) {
        foreach ($branch in $branches) {
            # Clean branch name
            $cleanBranch = $branch.Trim().TrimStart('*').Trim()
            $cleanBranch = $cleanBranch -replace '^remotes/[^/]*/', ''
            
            if ($cleanBranch -match "^([0-9]{3})-") {
                [int]$num = $Matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }
    return $highest
}

# Function to check existing branches and return next available number
function Check-ExistingBranches {
    param([string]$SpecsDir)
    # Fetch all remotes
    git fetch --all --prune 2>$null | Out-Null
    
    $highestBranch = Get-HighestFromBranches
    $highestSpec = Get-HighestFromSpecs -SpecsDir $SpecsDir
    
    $maxNum = $highestBranch
    if ($highestSpec -gt $maxNum) {
        $maxNum = $highestSpec
    }
    
    return ($maxNum + 1)
}

# Function to clean and format a branch name
function Clean-BranchName {
    param([string]$Name)
    $clean = $Name.ToLower() -replace '[^a-z0-9]', '-'
    $clean = $clean -replace '-+', '-'
    $clean = $clean -replace '^-', ''
    $clean = $clean -replace '-$', ''
    return $clean
}

# Source common functions
. "$PSScriptRoot\common.ps1"

$REPO_ROOT = Get-RepoRoot
$HAS_GIT = Has-Git

Set-Location $REPO_ROOT

$SPECS_DIR = Join-Path $REPO_ROOT "specs"
if (-not (Test-Path $SPECS_DIR -PathType Container)) {
    New-Item -ItemType Directory -Path $SPECS_DIR -Force | Out-Null
}

# Function to generate branch name with stop word filtering and length filtering
function Generate-BranchName {
    param([string]$Description)
    
    $stopWordsRegex = "^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"
    
    # Convert to lowercase and split into words
    $cleanName = $Description.ToLower() -replace '[^a-z0-9]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }
    
    $meaningfulWords = @()
    foreach ($word in $words) {
        if ($word -notmatch $stopWordsRegex) {
            if ($word.Length -ge 3) {
                $meaningfulWords += $word
            } else {
                # Check if it was uppercase in original (likely acronym)
                $upperWord = $word.ToUpper()
                if ($Description -match "\b$upperWord\b") {
                    $meaningfulWords += $word
                }
            }
        }
    }
    
    if ($meaningfulWords.Count -gt 0) {
        $maxWords = 3
        if ($meaningfulWords.Count -eq 4) { $maxWords = 4 }
        $selectedWords = $meaningfulWords | Select-Object -First $maxWords
        return ($selectedWords -join "-")
    } else {
        $cleaned = Clean-BranchName -Name $Description
        $fallbackWords = ($cleaned -split "-") | Where-Object { $_ } | Select-Object -First 3
        return ($fallbackWords -join "-")
    }
}

# Generate branch name
if ($ShortName) {
    $BRANCH_SUFFIX = Clean-BranchName -Name $ShortName
} else {
    $BRANCH_SUFFIX = Generate-BranchName -Description $FEATURE_DESCRIPTION
}

# Determine branch number
if (-not $Number) {
    if ($HAS_GIT -eq "true") {
        $Number = Check-ExistingBranches -SpecsDir $SPECS_DIR
    } else {
        $highest = Get-HighestFromSpecs -SpecsDir $SPECS_DIR
        $Number = $highest + 1
    }
}

# Format branch name
$FEATURE_NUM = "{0:D3}" -f $Number
$BRANCH_NAME = "${FEATURE_NUM}-${BRANCH_SUFFIX}"

# Validate and truncate if branch name exceeds limit
$MAX_BRANCH_LENGTH = 244
if ($BRANCH_NAME.Length -gt $MAX_BRANCH_LENGTH) {
    $prefixLength = $FEATURE_NUM.Length + 1
    $maxSuffixLength = $MAX_BRANCH_LENGTH - $prefixLength
    
    $truncatedSuffix = $BRANCH_SUFFIX.Substring(0, $maxSuffixLength)
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''
    
    $ORIGINAL_BRANCH_NAME = $BRANCH_NAME
    $BRANCH_NAME = "${FEATURE_NUM}-${truncatedSuffix}"
    
    [Console]::Error.WriteLine("[specify] Warning: Branch name exceeded GitHub's 244-byte limit")
    [Console]::Error.WriteLine("[specify] Original: $ORIGINAL_BRANCH_NAME ($($ORIGINAL_BRANCH_NAME.Length) bytes)")
    [Console]::Error.WriteLine("[specify] Truncated to: $BRANCH_NAME ($($BRANCH_NAME.Length) bytes)")
}

if ($HAS_GIT -eq "true") {
    git checkout -b "$BRANCH_NAME"
} else {
    [Console]::Error.WriteLine("[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME")
}

$FEATURE_DIR = Join-Path $SPECS_DIR $BRANCH_NAME
if (-not (Test-Path $FEATURE_DIR -PathType Container)) {
    New-Item -ItemType Directory -Path $FEATURE_DIR -Force | Out-Null
}

$TEMPLATE = Join-Path $REPO_ROOT ".specify/templates/spec-template.md"
$SPEC_FILE = Join-Path $FEATURE_DIR "spec.md"

if (Test-Path $TEMPLATE -PathType Leaf) {
    Copy-Item -Path $TEMPLATE -Destination $SPEC_FILE -Force
} else {
    New-Item -ItemType File -Path $SPEC_FILE -Force | Out-Null
}

$env:SPECIFY_FEATURE = $BRANCH_NAME

if ($Json) {
    $outObj = [PSCustomObject]@{
        BRANCH_NAME = $BRANCH_NAME
        SPEC_FILE   = $SPEC_FILE
        FEATURE_NUM = $FEATURE_NUM
    }
    $outObj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $BRANCH_NAME"
    Write-Output "SPEC_FILE: $SPEC_FILE"
    Write-Output "FEATURE_NUM: $FEATURE_NUM"
    Write-Output "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
}
