# Common functions and variables for all scripts

# Get repository root, with fallback for non-git repositories
function Get-RepoRoot {
    $gitRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitRoot) {
        return $gitRoot.Trim()
    }
    
    # Fall back to checking parent directories for .git or .agents
    $current = $PSScriptRoot
    while ($current) {
        if (Test-Path (Join-Path $current ".git") -PathType Container) {
            return $current
        }
        if (Test-Path (Join-Path $current ".agents") -PathType Container) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current -or !$parent) { break }
        $current = $parent
    }
    
    # Final fallback: go up 4 levels
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..") -ErrorAction SilentlyContinue).Path
}

# Get current branch, with fallback for non-git repositories
function Get-CurrentBranch {
    # First check if SPECIFY_FEATURE environment variable is set
    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }

    # Then check git if available
    $gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitBranch) {
        return $gitBranch.Trim()
    }

    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"

    if (Test-Path $specsDir -PathType Container) {
        $latestFeature = ""
        $highest = 0

        $dirs = Get-ChildItem -Path $specsDir -Directory
        foreach ($dir in $dirs) {
            if ($dir.Name -match "^([0-9]{3})-") {
                [int]$number = $Matches[1]
                if ($number -gt $highest) {
                    $highest = $number
                    $latestFeature = $dir.Name
                }
            }
        }

        if ($latestFeature) {
            return $latestFeature
        }
    }

    return "main" # Final fallback
}

# Check if we have git available
function Has-Git {
    git rev-parse --show-toplevel >$null 2>&1
    return ($LASTEXITCODE -eq 0)
}

function Check-FeatureBranch {
    param(
        [string]$Branch,
        [string]$HasGitRepo
    )

    # For non-git repos, we can't enforce branch naming but still provide output
    if ($HasGitRepo -ne "true") {
        [Console]::Error.WriteLine("[specify] Warning: Git repository not detected; skipped branch validation")
        return $true
    }

    if ($Branch -notmatch "^[0-9]{3}-") {
        [Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $Branch")
        [Console]::Error.WriteLine("Feature branches should be named like: 001-feature-name")
        return $false
    }

    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    return Join-Path $RepoRoot "specs/$Branch"
}

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
function Find-FeatureDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )
    $specsDir = Join-Path $RepoRoot "specs"

    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if ($BranchName -notmatch "^([0-9]{3})-") {
        # If branch doesn't have numeric prefix, fall back to exact match
        return Join-Path $specsDir $BranchName
    }

    $prefix = $Matches[1]

    # Search for directories in specs/ that start with this prefix
    $matchesList = @()
    if (Test-Path $specsDir -PathType Container) {
        $dirs = Get-ChildItem -Path $specsDir -Directory
        foreach ($dir in $dirs) {
            if ($dir.Name -match "^$prefix-") {
                $matchesList += $dir.Name
            }
        }
    }

    # Handle results
    if ($matchesList.Count -eq 0) {
        # No match found - return the branch name path (will fail later with clear error)
        return Join-Path $specsDir $BranchName
    } elseif ($matchesList.Count -eq 1) {
        # Exactly one match - perfect!
        return Join-Path $specsDir $matchesList[0]
    } else {
        # Multiple matches - this shouldn't happen with proper naming convention
        [Console]::Error.WriteLine("ERROR: Multiple spec directories found with prefix '$prefix': $($matchesList -join ' ')")
        [Console]::Error.WriteLine("Please ensure only one spec directory exists per numeric prefix.")
        return Join-Path $specsDir $BranchName # Return something to avoid breaking the script
    }
}

function Get-FeaturePaths {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGitRepo = "false"

    if (Has-Git) {
        $hasGitRepo = "true"
    }

    # Use prefix-based lookup to support multiple branches per spec
    $featureDir = Find-FeatureDirByPrefix -RepoRoot $repoRoot -BranchName $currentBranch

    return [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT        = $hasGitRepo
        FEATURE_DIR    = $featureDir
        FEATURE_SPEC   = Join-Path $featureDir "spec.md"
        IMPL_PLAN      = Join-Path $featureDir "plan.md"
        TASKS          = Join-Path $featureDir "tasks.md"
        RESEARCH       = Join-Path $featureDir "research.md"
        DATA_MODEL     = Join-Path $featureDir "data-model.md"
        QUICKSTART     = Join-Path $featureDir "quickstart.md"
        CONTRACTS_DIR  = Join-Path $featureDir "contracts"
    }
}

function Check-File {
    param([string]$Path, [string]$Label)
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        Write-Output "  ✓ $Label"
    } else {
        Write-Output "  ✗ $Label"
    }
}

function Check-Dir {
    param([string]$Path, [string]$Label)
    if ((Test-Path -LiteralPath $Path -PathType Container) -and (Get-ChildItem -LiteralPath $Path -ErrorAction SilentlyContinue)) {
        Write-Output "  ✓ $Label"
    } else {
        Write-Output "  ✗ $Label"
    }
}
