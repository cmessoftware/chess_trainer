#!/usr/bin/env pwsh

# Update agent context files with information from plan.md (PowerShell)

[CmdletBinding()]
param(
    [string]$AgentType
)

$ErrorActionPreference = 'Stop'

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

$NEW_PLAN = $IMPL_PLAN

# Agent-specific file paths  
$CLAUDE_FILE = Join-Path $REPO_ROOT "CLAUDE.md"
$GEMINI_FILE = Join-Path $REPO_ROOT "GEMINI.md"
$COPILOT_FILE = Join-Path $REPO_ROOT ".github/agents/copilot-instructions.md"
$CURSOR_FILE = Join-Path $REPO_ROOT ".cursor/rules/specify-rules.mdc"
$QWEN_FILE = Join-Path $REPO_ROOT "QWEN.md"
$AGENTS_FILE = Join-Path $REPO_ROOT "AGENTS.md"
$WINDSURF_FILE = Join-Path $REPO_ROOT ".windsurf/rules/specify-rules.md"
$KILOCODE_FILE = Join-Path $REPO_ROOT ".kilocode/rules/specify-rules.md"
$AUGGIE_FILE = Join-Path $REPO_ROOT ".augment/rules/specify-rules.md"
$ROO_FILE = Join-Path $REPO_ROOT ".roo/rules/specify-rules.md"
$CODEBUDDY_FILE = Join-Path $REPO_ROOT "CODEBUDDY.md"
$QODER_FILE = Join-Path $REPO_ROOT "QODER.md"
$AMP_FILE = Join-Path $REPO_ROOT "AGENTS.md"
$SHAI_FILE = Join-Path $REPO_ROOT "SHAI.md"
$Q_FILE = Join-Path $REPO_ROOT "AGENTS.md"
$BOB_FILE = Join-Path $REPO_ROOT "AGENTS.md"

# Template file
$TEMPLATE_FILE = Join-Path $REPO_ROOT ".specify/templates/agent-file-template.md"

# Global variables for parsed plan data
$script:NEW_LANG = ""
$script:NEW_FRAMEWORK = ""
$script:NEW_DB = ""
$script:NEW_PROJECT_TYPE = ""

#==============================================================================
# Logging Functions
#==============================================================================

function Log-Info { param([string]$Message) Write-Output "INFO: $Message" }
function Log-Success { param([string]$Message) Write-Output "✓ $Message" }
function Log-Error { param([string]$Message) [Console]::Error.WriteLine("ERROR: $Message") }
function Log-Warning { param([string]$Message) [Console]::Error.WriteLine("WARNING: $Message") }

#==============================================================================
# Validation Functions
#==============================================================================

function Validate-Environment {
    if (-not $CURRENT_BRANCH) {
        Log-Error "Unable to determine current feature"
        if ($HAS_GIT -eq "true") {
            Log-Info "Make sure you're on a feature branch"
        } else {
            Log-Info "Set SPECIFY_FEATURE environment variable or create a feature first"
        }
        exit 1
    }
    
    if (-not (Test-Path $NEW_PLAN -PathType Leaf)) {
        Log-Error "No plan.md found at $NEW_PLAN"
        Log-Info "Make sure you're working on a feature with a corresponding spec directory"
        if ($HAS_GIT -ne "true") {
            Log-Info "Use: export SPECIFY_FEATURE=your-feature-name or create a new feature first"
        }
        exit 1
    }
    
    if (-not (Test-Path $TEMPLATE_FILE -PathType Leaf)) {
        Log-Warning "Template file not found at $TEMPLATE_FILE"
        Log-Warning "Creating new agent files will fail"
    }
}

#==============================================================================
# Plan Parsing Functions
#==============================================================================

function Extract-PlanField {
    param(
        [string]$FieldPattern,
        [string]$PlanFile
    )
    if (-not (Test-Path $PlanFile -PathType Leaf)) { return "" }
    
    $lines = Get-Content -Path $PlanFile -ErrorAction SilentlyContinue
    if (-not $lines) { return "" }
    
    $escapedPattern = [regex]::Escape($FieldPattern)
    
    foreach ($line in $lines) {
        if ($line -match "^\*\*$escapedPattern\*\*:\s*(.*)") {
            $val = $Matches[1].Trim()
            if ($val -and $val -ne "NEEDS CLARIFICATION" -and $val -ne "N/A") {
                return $val
            }
        }
    }
    return ""
}

function Parse-PlanData {
    param([string]$PlanFile)
    
    if (-not (Test-Path $PlanFile -PathType Leaf)) {
        Log-Error "Plan file not found: $PlanFile"
        return $false
    }
    
    Log-Info "Parsing plan data from $PlanFile"
    
    $script:NEW_LANG = Extract-PlanField -FieldPattern "Language/Version" -PlanFile $PlanFile
    $script:NEW_FRAMEWORK = Extract-PlanField -FieldPattern "Primary Dependencies" -PlanFile $PlanFile
    $script:NEW_DB = Extract-PlanField -FieldPattern "Storage" -PlanFile $PlanFile
    $script:NEW_PROJECT_TYPE = Extract-PlanField -FieldPattern "Project Type" -PlanFile $PlanFile
    
    if ($script:NEW_LANG) {
        Log-Info "Found language: $script:NEW_LANG"
    } else {
        Log-Warning "No language information found in plan"
    }
    
    if ($script:NEW_FRAMEWORK) {
        Log-Info "Found framework: $script:NEW_FRAMEWORK"
    }
    
    if ($script:NEW_DB -and $script:NEW_DB -ne "N/A") {
        Log-Info "Found database: $script:NEW_DB"
    }
    
    if ($script:NEW_PROJECT_TYPE) {
        Log-Info "Found project type: $script:NEW_PROJECT_TYPE"
    }
    
    return $true
}

function Format-TechnologyStack {
    param(
        [string]$Lang,
        [string]$Framework
    )
    $parts = @()
    if ($Lang -and $Lang -ne "NEEDS CLARIFICATION") { $parts += $Lang }
    if ($Framework -and $Framework -ne "NEEDS CLARIFICATION" -and $Framework -ne "N/A") { $parts += $Framework }
    
    if ($parts.Count -eq 0) {
        return ""
    } elseif ($parts.Count -eq 1) {
        return $parts[0]
    } else {
        return ($parts -join " + ")
    }
}

#==============================================================================
# Template and Content Generation Functions
#==============================================================================

function Get-ProjectStructure {
    param([string]$ProjectType)
    if ($ProjectType -like "*web*") {
        return "backend/`nfrontend/`ntests/"
    } else {
        return "src/`ntests/"
    }
}

function Get-CommandsForLanguage {
    param([string]$Lang)
    if ($Lang -like "*Python*") {
        return "cd src && pytest && ruff check ."
    } elseif ($Lang -like "*Rust*") {
        return "cargo test && cargo clippy"
    } elseif ($Lang -like "*JavaScript*" -or $Lang -like "*TypeScript*") {
        return "npm test && npm run lint"
    } else {
        return "# Add commands for $Lang"
    }
}

function Get-LanguageConventions {
    param([string]$Lang)
    return "$Lang: Follow standard conventions"
}

function Create-NewAgentFile {
    param(
        [string]$TargetFile,
        [string]$TempFile,
        [string]$ProjectName,
        [string]$CurrentDate
    )
    
    if (-not (Test-Path $TEMPLATE_FILE -PathType Leaf)) {
        Log-Error "Template not found at $TEMPLATE_FILE"
        return $false
    }
    
    Log-Info "Creating new agent context file from template..."
    
    try {
        $content = [System.IO.File]::ReadAllText($TEMPLATE_FILE)
    } catch {
        Log-Error "Failed to read template file: $_"
        return $false
    }
    
    $projectStructure = Get-ProjectStructure -ProjectType $script:NEW_PROJECT_TYPE
    $commands = Get-CommandsForLanguage -Lang $script:NEW_LANG
    $languageConventions = Get-LanguageConventions -Lang $script:NEW_LANG
    
    # Build tech stack and recent changes strings
    $techStack = ""
    if ($script:NEW_LANG -and $script:NEW_FRAMEWORK) {
        $techStack = "- $script:NEW_LANG + $script:NEW_FRAMEWORK ($CURRENT_BRANCH)"
    } elseif ($script:NEW_LANG) {
        $techStack = "- $script:NEW_LANG ($CURRENT_BRANCH)"
    } elseif ($script:NEW_FRAMEWORK) {
        $techStack = "- $script:NEW_FRAMEWORK ($CURRENT_BRANCH)"
    } else {
        $techStack = "- ($CURRENT_BRANCH)"
    }
    
    $recentChange = ""
    if ($script:NEW_LANG -and $script:NEW_FRAMEWORK) {
        $recentChange = "- $CURRENT_BRANCH: Added $script:NEW_LANG + $script:NEW_FRAMEWORK"
    } elseif ($script:NEW_LANG) {
        $recentChange = "- $CURRENT_BRANCH: Added $script:NEW_LANG"
    } elseif ($script:NEW_FRAMEWORK) {
        $recentChange = "- $CURRENT_BRANCH: Added $script:NEW_FRAMEWORK"
    } else {
        $recentChange = "- $CURRENT_BRANCH: Added"
    }
    
    # Perform substitutions
    $content = $content.Replace("[PROJECT NAME]", $ProjectName)
    $content = $content.Replace("[DATE]", $CurrentDate)
    $content = $content.Replace("[EXTRACTED FROM ALL PLAN.MD FILES]", $techStack)
    $content = $content.Replace("[ACTUAL STRUCTURE FROM PLANS]", $projectStructure)
    $content = $content.Replace("[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]", $commands)
    $content = $content.Replace("[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]", $languageConventions)
    $content = $content.Replace("[LAST 3 FEATURES AND WHAT THEY ADDED]", $recentChange)
    
    try {
        [System.IO.File]::WriteAllText($TempFile, $content)
        return $true
    } catch {
        Log-Error "Failed to write temporary file: $_"
        return $false
    }
}

function Update-ExistingAgentFile {
    param(
        [string]$TargetFile,
        [string]$CurrentDate
    )
    
    Log-Info "Updating existing agent context file..."
    
    $tempFile = [System.IO.Path]::GetTempFileName()
    
    $techStack = Format-TechnologyStack -Lang $script:NEW_LANG -Framework $script:NEW_FRAMEWORK
    $newTechEntries = @()
    $newChangeEntry = ""
    
    $existingContent = Get-Content -Path $TargetFile
    
    # Check if tech stack is already in target file
    $hasTechStack = $false
    $hasDb = $false
    foreach ($line in $existingContent) {
        if ($techStack -and $line -like "*$techStack*") { $hasTechStack = $true }
        if ($script:NEW_DB -and $line -like "*$script:NEW_DB*") { $hasDb = $true }
    }
    
    if ($techStack -and -not $hasTechStack) {
        $newTechEntries += "- $techStack ($CURRENT_BRANCH)"
    }
    
    if ($script:NEW_DB -and $script:NEW_DB -ne "N/A" -and $script:NEW_DB -ne "NEEDS CLARIFICATION" -and -not $hasDb) {
        $newTechEntries += "- $script:NEW_DB ($CURRENT_BRANCH)"
    }
    
    # Prepare new change entry
    if ($techStack) {
        $newChangeEntry = "- $CURRENT_BRANCH: Added $techStack"
    } elseif ($script:NEW_DB -and $script:NEW_DB -ne "N/A" -and $script:NEW_DB -ne "NEEDS CLARIFICATION") {
        $newChangeEntry = "- $CURRENT_BRANCH: Added $script:NEW_DB"
    }
    
    # Check if sections exist in the file
    $hasActiveTechnologies = $false
    $hasRecentChanges = $false
    foreach ($line in $existingContent) {
        if ($line -eq "## Active Technologies") { $hasActiveTechnologies = $true }
        if ($line -eq "## Recent Changes") { $hasRecentChanges = $true }
    }
    
    $newLines = @()
    
    # Process file line by line
    $inTechSection = $false
    $inChangesSection = $false
    $techEntriesAdded = $false
    $existingChangesCount = 0
    
    foreach ($line in $existingContent) {
        # Handle Active Technologies section
        if ($line -eq "## Active Technologies") {
            $newLines += $line
            $inTechSection = $true
            continue
        } elseif ($inTechSection -and ($line -match "^##\s")) {
            if (-not $techEntriesAdded -and $newTechEntries.Count -gt 0) {
                $newLines += $newTechEntries
                $techEntriesAdded = $true
            }
            $newLines += $line
            $inTechSection = $false
            continue
        } elseif ($inTechSection -and [string]::IsNullOrEmpty($line)) {
            if (-not $techEntriesAdded -and $newTechEntries.Count -gt 0) {
                $newLines += $newTechEntries
                $techEntriesAdded = $true
            }
            $newLines += $line
            continue
        }
        
        # Handle Recent Changes section
        if ($line -eq "## Recent Changes") {
            $newLines += $line
            if ($newChangeEntry) {
                $newLines += $newChangeEntry
            }
            $inChangesSection = $true
            continue
        } elseif ($inChangesSection -and ($line -match "^##\s")) {
            $newLines += $line
            $inChangesSection = $false
            continue
        } elseif ($inChangesSection -and ($line -like "- *")) {
            if ($existingChangesCount -lt 2) {
                $newLines += $line
                $existingChangesCount++
            }
            continue
        }
        
        # Update timestamp
        if ($line -match "\*\*Last\s+updated\*\*:\s*.*[0-9]{4}-[0-9]{2}-[0-9]{2}") {
            $updatedLine = $line -replace "[0-9]{4}-[0-9]{2}-[0-9]{2}", $CurrentDate
            $newLines += $updatedLine
        } else {
            $newLines += $line
        }
    }
    
    # Post-loop check
    if ($inTechSection -and -not $techEntriesAdded -and $newTechEntries.Count -gt 0) {
        $newLines += $newTechEntries
        $techEntriesAdded = $true
    }
    
    # If sections don't exist, add them at the end
    if (-not $hasActiveTechnologies -and $newTechEntries.Count -gt 0) {
        $newLines += ""
        $newLines += "## Active Technologies"
        $newLines += $newTechEntries
    }
    
    if (-not $hasRecentChanges -and $newChangeEntry) {
        $newLines += ""
        $newLines += "## Recent Changes"
        $newLines += $newChangeEntry
    }
    
    try {
        [System.IO.File]::WriteAllLines($tempFile, $newLines)
        Move-Item -Path $tempFile -Destination $TargetFile -Force
        return $true
    } catch {
        Log-Error "Failed to update target file: $_"
        Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
        return $false
    }
}

#==============================================================================
# Main Agent File Update Function
#==============================================================================

function Update-AgentFile {
    param(
        [string]$TargetFile,
        [string]$AgentName
    )
    
    if (-not $TargetFile -or -not $AgentName) {
        Log-Error "Update-AgentFile requires TargetFile and AgentName parameters"
        return $false
    }
    
    Log-Info "Updating $AgentName context file: $TargetFile"
    
    $projectName = Split-Path $REPO_ROOT -Leaf
    $currentDate = Get-Date -Format "yyyy-MM-dd"
    
    # Create directory if it doesn't exist
    $targetDir = Split-Path $TargetFile -Parent
    if (-not (Test-Path $targetDir -PathType Container)) {
        try {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        } catch {
            Log-Error "Failed to create directory: $targetDir"
            return $false
        }
    }
    
    if (-not (Test-Path $TargetFile -PathType Leaf)) {
        # Create new file from template
        $tempFile = [System.IO.Path]::GetTempFileName()
        
        if (Create-NewAgentFile -TargetFile $TargetFile -TempFile $tempFile -ProjectName $projectName -CurrentDate $currentDate) {
            try {
                Move-Item -Path $tempFile -Destination $TargetFile -Force
                Log-Success "Created new $AgentName context file"
                return $true
            } catch {
                Log-Error "Failed to move temporary file to $TargetFile: $_"
                Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
                return $false
            }
        } else {
            Log-Error "Failed to create new agent file"
            Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
            return $false
        }
    } else {
        # Update existing file
        if (Update-ExistingAgentFile -TargetFile $TargetFile -CurrentDate $currentDate) {
            Log-Success "Updated existing $AgentName context file"
            return $true
        } else {
            Log-Error "Failed to update existing agent file"
            return $false
        }
    }
}

#==============================================================================
# Agent Selection and Processing
#==============================================================================

function Update-SpecificAgent {
    param([string]$AgentType)
    
    switch ($AgentType) {
        "claude" {
            Update-AgentFile -TargetFile $CLAUDE_FILE -AgentName "Claude Code"
        }
        "gemini" {
            Update-AgentFile -TargetFile $GEMINI_FILE -AgentName "Gemini CLI"
        }
        "copilot" {
            Update-AgentFile -TargetFile $COPILOT_FILE -AgentName "GitHub Copilot"
        }
        "cursor-agent" {
            Update-AgentFile -TargetFile $CURSOR_FILE -AgentName "Cursor IDE"
        }
        "qwen" {
            Update-AgentFile -TargetFile $QWEN_FILE -AgentName "Qwen Code"
        }
        "opencode" {
            Update-AgentFile -TargetFile $AGENTS_FILE -AgentName "opencode"
        }
        "codex" {
            Update-AgentFile -TargetFile $AGENTS_FILE -AgentName "Codex CLI"
        }
        "windsurf" {
            Update-AgentFile -TargetFile $WINDSURF_FILE -AgentName "Windsurf"
        }
        "kilocode" {
            Update-AgentFile -TargetFile $KILOCODE_FILE -AgentName "Kilo Code"
        }
        "auggie" {
            Update-AgentFile -TargetFile $AUGGIE_FILE -AgentName "Auggie CLI"
        }
        "roo" {
            Update-AgentFile -TargetFile $ROO_FILE -AgentName "Roo Code"
        }
        "codebuddy" {
            Update-AgentFile -TargetFile $CODEBUDDY_FILE -AgentName "CodeBuddy CLI"
        }
        "qoder" {
            Update-AgentFile -TargetFile $QODER_FILE -AgentName "Qoder CLI"
        }
        "amp" {
            Update-AgentFile -TargetFile $AMP_FILE -AgentName "Amp"
        }
        "shai" {
            Update-AgentFile -TargetFile $SHAI_FILE -AgentName "SHAI"
        }
        "q" {
            Update-AgentFile -TargetFile $Q_FILE -AgentName "Amazon Q Developer CLI"
        }
        "bob" {
            Update-AgentFile -TargetFile $BOB_FILE -AgentName "IBM Bob"
        }
        default {
            Log-Error "Unknown agent type '$AgentType'"
            Log-Error "Expected: claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|codebuddy|shai|q|bob|qoder"
            exit 1
        }
    }
}

function Update-AllExistingAgents {
    $foundAgent = $false
    
    if (Test-Path $CLAUDE_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $CLAUDE_FILE -AgentName "Claude Code" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $GEMINI_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $GEMINI_FILE -AgentName "Gemini CLI" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $COPILOT_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $COPILOT_FILE -AgentName "GitHub Copilot" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $CURSOR_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $CURSOR_FILE -AgentName "Cursor IDE" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $QWEN_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $QWEN_FILE -AgentName "Qwen Code" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $AGENTS_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $AGENTS_FILE -AgentName "Codex/opencode" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $WINDSURF_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $WINDSURF_FILE -AgentName "Windsurf" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $KILOCODE_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $KILOCODE_FILE -AgentName "Kilo Code" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $AUGGIE_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $AUGGIE_FILE -AgentName "Auggie CLI" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $ROO_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $ROO_FILE -AgentName "Roo Code" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $CODEBUDDY_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $CODEBUDDY_FILE -AgentName "CodeBuddy CLI" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $SHAI_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $SHAI_FILE -AgentName "SHAI" | Out-Null
        $foundAgent = $true
    }
    
    if (Test-Path $QODER_FILE -PathType Leaf) {
        Update-AgentFile -TargetFile $QODER_FILE -AgentName "Qoder CLI" | Out-Null
        $foundAgent = $true
    }
    
    # If no agent files exist, create a default Claude file
    if (-not $foundAgent) {
        Log-Info "No existing agent files found, creating default Claude file..."
        Update-AgentFile -TargetFile $CLAUDE_FILE -AgentName "Claude Code" | Out-Null
    }
}

function Print-Summary {
    Write-Output ""
    Log-Info "Summary of changes:"
    
    if ($script:NEW_LANG) {
        Write-Output "  - Added language: $script:NEW_LANG"
    }
    
    if ($script:NEW_FRAMEWORK) {
        Write-Output "  - Added framework: $script:NEW_FRAMEWORK"
    }
    
    if ($script:NEW_DB -and $script:NEW_DB -ne "N/A") {
        Write-Output "  - Added database: $script:NEW_DB"
    }
    
    Write-Output ""
    Log-Info "Usage: .\update-agent-context.ps1 [claude|gemini|copilot|cursor-agent|qwen|opencode|codex|windsurf|kilocode|auggie|roo|codebuddy|shai|q|bob|qoder]"
}

#==============================================================================
# Main Execution
#==============================================================================

function Main {
    Validate-Environment
    
    Log-Info "=== Updating agent context files for feature $CURRENT_BRANCH ==="
    
    if (-not (Parse-PlanData -PlanFile $NEW_PLAN)) {
        Log-Error "Failed to parse plan data"
        exit 1
    }
    
    $success = $true
    if (-not $AgentType) {
        Log-Info "No agent specified, updating all existing agent files..."
        try {
            Update-AllExistingAgents
        } catch {
            $success = $false
        }
    } else {
        Log-Info "Updating specific agent: $AgentType"
        try {
            Update-SpecificAgent -AgentType $AgentType
        } catch {
            $success = $false
        }
    }
    
    Print-Summary
    
    if ($success) {
        Log-Success "Agent context update completed successfully"
        exit 0
    } else {
        Log-Error "Agent context update completed with errors"
        exit 1
    }
}

Main
