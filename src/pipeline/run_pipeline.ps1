#!/usr/bin/env pwsh
# Usage: run_pipeline.ps1 {all | from <step> | auto_tag | analyze_tactics | generate_exercises | generate_features [args]}
# Examples:
# .\run_pipeline.ps1 all
# .\run_pipeline.ps1 generate_exercises
# .\run_pipeline.ps1 from analyze_tactics
# .\run_pipeline.ps1 analyze_tactics --source lichess --max-games 1000
# .\run_pipeline.ps1 generate_features --max-games 5

param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

$ErrorActionPreference = "Stop"

# Save the initial directory to restore it at the end
$InitialDirectory = Get-Location

# Colors
$Colors = @{
    Green  = "`e[0;32m"
    Red    = "`e[0;31m"
    Cyan   = "`e[0;36m"
    Yellow = "`e[1;33m"
    Blue   = "`e[0;34m"
    Reset  = "`e[0m"
}

# Paths
$env:PYTHONPATH = "src"
$env:STOCKFISH_PATH = "bin\stockfish.exe"  # Use local stockfish binary
$env:PGN_PATH = "src\data\games"

$LogDir = "src\logs"
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Validations
if ([string]::IsNullOrEmpty($env:STOCKFISH_PATH)) {
    Write-Host "$($Colors.Red)[ERROR] STOCKFISH_PATH not defined$($Colors.Reset)"
    Set-Location $InitialDirectory
    exit 1
}
if ([string]::IsNullOrEmpty($env:PGN_PATH)) {
    Write-Host "$($Colors.Red)[ERROR] PGN_PATH not defined$($Colors.Reset)"
    Set-Location $InitialDirectory
    exit 1
}

# Check if we can access the source directory
try {
    Set-Location "..\.."  # Go to project root
}
catch {
    Write-Host "$($Colors.Red)[ERROR] Cannot access project root directory$($Colors.Reset)"
    Set-Location $InitialDirectory
    exit 1
}

# Step runner function
function Invoke-Step {
    param(
        [string]$StepName,
        [scriptblock]$StepFunction,
        [string[]]$StepArgs = @()
    )
    
    $LogFile = "$LogDir/$StepName.log"
    
    $confirm = Read-Host "$($Colors.Yellow)[PROMPT] Do you want to execute the step: $($Colors.Cyan)$StepName$($Colors.Reset)? (y/n)"
    if ($confirm -notmatch "^[Yy]$") {
        Write-Host "$($Colors.Yellow)[SKIP] Step '$StepName' skipped by user.$($Colors.Reset)"
        return 0
    }
    
    Write-Host "$($Colors.Cyan)[RUN] Executing $StepName...$($Colors.Reset)"
    $StartTime = Get-Date
    
    try {
        "[START] $(Get-Date) - Starting step: $StepName" | Tee-Object -FilePath $LogFile
        
        & $StepFunction @StepArgs
        $Status = $LASTEXITCODE
        
        if ($Status -eq 0) {
            "[SUCCESS] Finished successfully" | Tee-Object -FilePath $LogFile -Append
        }
        else {
            "[FAILED] Step failed with exit code $Status" | Tee-Object -FilePath $LogFile -Append
            throw "Step failed with exit code $Status"
        }
    }
    catch {
        Write-Host "$($Colors.Red)[ERROR] $StepName failed. Check log: $LogFile$($Colors.Reset)"
        return $Status
    }
    
    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds
    Write-Host "$($Colors.Green)[OK] $StepName completed in $([int]$Duration) seconds.$($Colors.Reset)"
    return 0
}

# Helper function to run steps interactively
function Invoke-StepsInteractive {
    param([string[]]$Steps)
    
    foreach ($step in $Steps) {
        $status = Invoke-Step $step (Get-Command "Step-$step").ScriptBlock
        if ($status -ne 0 -and $status -ne 2) {
            Write-Host "$($Colors.Red)[ERROR] Error executing step '$step'. Aborting.$($Colors.Reset)"
            exit $status
        }
    }
}

# Step implementations
function Step-clean_analysis_data {
    Write-Host "$($Colors.Cyan)[CLEAN] Cleaning analysis-related tables...$($Colors.Reset)"
    python db/truncate_analysis_data.py
    Write-Host "$($Colors.Green)[OK] Analysis tables cleaned (features, processed_features, tactics).$($Colors.Reset)"
}

function Step-check_db {
    Write-Host "$($Colors.Cyan)[CHECK] Checking database connection...$($Colors.Reset)"
    Write-Host "$($Colors.Cyan)[CHECK] Checking database schema...$($Colors.Reset)"
    python src\scripts\init_db.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$($Colors.Green)[OK] Database connection is OK.$($Colors.Reset)"
    }
    else {
        Write-Host "$($Colors.Red)[ERROR] Database connection failed.$($Colors.Reset)"
        exit 1
    }
}

function Step-create_issues {
    Write-Host "$($Colors.Cyan)[CREATE] Creating GitHub issues from TODOs...$($Colors.Reset)"
    python src\tools\create_issues.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Issues created correctly."
    }
    else {
        Write-Host "[ERROR] Error extracting TODOs."
        exit 1
    }
}

function Step-import_pgns {
    Write-Host "$($Colors.Cyan)[CHECK] Checking if there are new games to import...$($Colors.Reset)"
    python src\scripts\import_pgns_parallel.py --input $env:PGN_PATH
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$($Colors.Green)[OK] New games imported successfully.$($Colors.Reset)"
    }
    else {
        Write-Host "$($Colors.Red)[ERROR] Error importing new games.$($Colors.Reset)"
        exit 1
    }
}

function Step-auto_tag {
    python src\scripts\auto_tag_games.py
}

function Step-analyze_tactics {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[ANALYZE] Analyzing tactics in games...$($Colors.Reset)"
    Write-Host "$($Colors.Yellow)This step can take a long time depending on the number of games.$($Colors.Reset)"
    
    # Parse additional arguments
    $PassThroughArgs = @()
    $UseSourceBatching = $true
    
    for ($i = 0; $i -lt $Args.Count; $i++) {
        switch ($Args[$i]) {
            "--source" {
                $UseSourceBatching = $false
                $PassThroughArgs += "--source", $Args[$i + 1]
                $i++
            }
            "--max-games" {
                if (-not $UseSourceBatching) {
                    $PassThroughArgs += "--max-games", $Args[$i + 1]
                }
                $i++
            }
            default {
                $PassThroughArgs += $Args[$i]
            }
        }
    }
    
    # If source batching is disabled, use direct processing
    if (-not $UseSourceBatching) {
        Write-Host "$($Colors.Cyan)[TARGET] Processing with provided parameters...$($Colors.Reset)"
        python src\scripts\analyze_games_tactics_parallel.py @PassThroughArgs
        return
    }
    
    # Source batching mode
    Write-Host "$($Colors.Cyan)[LOOP] Running analyze_tactics sequentially by source with batches of 10,000 games...$($Colors.Reset)"
    
    # Get list of available sources
    Write-Host "$($Colors.Cyan)[DATA] Getting available sources from database...$($Colors.Reset)"
    $SourcesOutput = python pipeline/pipeline_helper.py --operation get-sources --format space-separated 2>$null
    $Sources = if ($SourcesOutput) { $SourcesOutput -split '\s+' } else { @() }
    
    if ($Sources.Count -eq 0) {
        Write-Host "$($Colors.Yellow)[WARN] No sources found in database, running without source filter...$($Colors.Reset)"
        python src\scripts\analyze_games_tactics_parallel.py --max-games 10000 @PassThroughArgs
        return
    }
    
    Write-Host "$($Colors.Green)[LIST] Found sources: $($Sources -join ' ')$($Colors.Reset)"
    
    # Process each source sequentially
    foreach ($source in $Sources) {
        Write-Host "$($Colors.Cyan)[TARGET] Processing source: $source$($Colors.Reset)"
        
        $TotalGames = [int](python pipeline/pipeline_helper.py --operation count-unanalyzed --source $source)
        Write-Host "$($Colors.Cyan)[STAT] Total unanalyzed games for source '$source': $TotalGames$($Colors.Reset)"
        
        if ($TotalGames -eq 0) {
            Write-Host "$($Colors.Yellow)[SKIP] No unanalyzed games found for source '$source', skipping...$($Colors.Reset)"
            continue
        }
        
        # Calculate batches
        $BatchSize = 10000
        $Batches = [Math]::Ceiling($TotalGames / $BatchSize)
        
        Write-Host "$($Colors.Cyan)[LOOP] Will process $Batches batch(es) of $BatchSize games each for source '$source'$($Colors.Reset)"
        
        # Process batches
        for ($batch = 1; $batch -le $Batches; $batch++) {
            Write-Host "$($Colors.Cyan)[WORK] Processing batch $batch/$Batches for source '$source'...$($Colors.Reset)"
            
            $StartTime = Get-Date
            $Offset = ($batch - 1) * $BatchSize
            
            python src\scripts\analyze_games_tactics_parallel.py --source $source --max-games $BatchSize --offset $Offset @PassThroughArgs
            
            $ExitCode = $LASTEXITCODE
            $EndTime = Get-Date
            $Duration = [int]($EndTime - $StartTime).TotalSeconds
            
            if ($ExitCode -eq 0) {
                Write-Host "$($Colors.Green)[SUCCESS] Batch $batch/$Batches completed successfully for source '$source' in ${Duration}s$($Colors.Reset)"
            }
            else {
                Write-Host "$($Colors.Red)[ERROR] Batch $batch/$Batches failed for source '$source' (exit code: $ExitCode)$($Colors.Reset)"
                return $ExitCode
            }
            
            Start-Sleep -Seconds 2
        }
        
        Write-Host "$($Colors.Green)[COMPLETE] Completed processing all batches for source '$source'$($Colors.Reset)"
    }
    
    Write-Host "$($Colors.Green)[FINISH] Tactical analysis completed for all sources!$($Colors.Reset)"
}

function Step-generate_exercises {
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing generate_exercises logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\generate_features*" -Force -ErrorAction SilentlyContinue
    python src\scripts\generate_exercises_from_elite.py
}

function Step-generate_features {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing generate_features logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\generate_features*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "$($Colors.Cyan)[LOOP] Running generate_features sequentially by source with batches of 10,000 games...$($Colors.Reset)"
    
    # Get available sources
    Write-Host "$($Colors.Cyan)[DATA] Getting available sources from database...$($Colors.Reset)"
    $SourcesOutput = python pipeline/pipeline_helper.py --operation get-sources --format space-separated
    $Sources = if ($SourcesOutput) { $SourcesOutput -split '\s+' } else { @() }
    
    if ($Sources.Count -eq 0) {
        Write-Host "$($Colors.Yellow)[WARN] No sources found in database, running without source filter...$($Colors.Reset)"
        python src\scripts\generate_features_parallel.py --max-games 10000 @Args
        return
    }
    
    Write-Host "$($Colors.Green)[LIST] Found sources: $($Sources -join ' ')$($Colors.Reset)"
    
    # Process each source
    foreach ($source in $Sources) {
        Write-Host "$($Colors.Cyan)[TARGET] Processing source: $source$($Colors.Reset)"
        
        $TotalGames = [int](python pipeline/pipeline_helper.py --operation count-games --source $source)
        Write-Host "$($Colors.Cyan)[STAT] Total games for source '$source': $TotalGames$($Colors.Reset)"
        
        if ($TotalGames -eq 0) {
            Write-Host "$($Colors.Yellow)[SKIP] No games found for source '$source', skipping...$($Colors.Reset)"
            continue
        }
        
        $BatchSize = 10000
        $Batches = [Math]::Ceiling($TotalGames / $BatchSize)
        
        Write-Host "$($Colors.Cyan)[LOOP] Will process $Batches batch(es) of $BatchSize games each for source '$source'$($Colors.Reset)"
        
        for ($batch = 1; $batch -le $Batches; $batch++) {
            Write-Host "$($Colors.Cyan)[WORK] Processing batch $batch/$Batches for source '$source'...$($Colors.Reset)"
            
            $StartTime = Get-Date
            $Offset = ($batch - 1) * $BatchSize
            
            python src\scripts\generate_features_parallel.py --source $source --max-games $BatchSize --offset $Offset @Args
            
            $ExitCode = $LASTEXITCODE
            $EndTime = Get-Date
            $Duration = [int]($EndTime - $StartTime).TotalSeconds
            
            if ($ExitCode -eq 0) {
                Write-Host "$($Colors.Green)[SUCCESS] Batch $batch/$Batches completed successfully for source '$source' in ${Duration}s$($Colors.Reset)"
            }
            else {
                Write-Host "$($Colors.Red)[ERROR] Batch $batch/$Batches failed for source '$source' (exit code: $ExitCode)$($Colors.Reset)"
                return $ExitCode
            }
            
            Start-Sleep -Seconds 2
        }
        
        Write-Host "$($Colors.Green)[COMPLETE] Completed processing all batches for source '$source'$($Colors.Reset)"
    }
    
    Write-Host "$($Colors.Green)[FINISH] Feature generation completed for all sources!$($Colors.Reset)"
}

function Step-generate_features_with_tactics {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing generate_features_with_tactics logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\generate_features_with_tactics*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "$($Colors.Cyan)[LOOP] Running integrated feature generation + tactical analysis...$($Colors.Reset)"
    python src\scripts\generate_features_with_tactics.py @Args
}

function Step-estimate_tactical_features {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing estimate_tactical_features logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\estimate_tactical_features*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "$($Colors.Cyan)[FAST] Running fast lightweight tactical feature estimation...$($Colors.Reset)"
    python src\scripts\estimate_tactical_features.py @Args
}

function Step-test_tactical_analysis {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing test_tactical_analysis logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\test_tactical_analysis*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "$($Colors.Cyan)[TEST] Testing and reporting tactical analysis coverage...$($Colors.Reset)"
    python src\scripts\test_tactical_analysis.py @Args
}

function Step-clean_db {
    python db/truncate_postgres_tables.py
}

function Step-export_dataset {
    python src\scripts\export_features_dataset_parallel.py
}

function Step-generate_combined_dataset {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing generate_combined_dataset logs$($Colors.Reset)"
    Remove-Item -Path "src\logs\generate_combined_dataset*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "$($Colors.Cyan)[TARGET] Generating optimally balanced dataset (150k games)...$($Colors.Reset)"
    Write-Host "$($Colors.Cyan)   - Elite: 50k games$($Colors.Reset)"
    Write-Host "$($Colors.Cyan)   - Fide: 50k games$($Colors.Reset)"
    Write-Host "$($Colors.Cyan)   - Novice: 25k games$($Colors.Reset)"
    Write-Host "$($Colors.Cyan)   - Personal: 25k games$($Colors.Reset)"
    
    python src\scripts\generate_combined_dataset.py @Args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$($Colors.Green)[SUCCESS] Balanced dataset generated successfully$($Colors.Reset)"
    }
    else {
        Write-Host "$($Colors.Red)[ERROR] Failed to generate balanced dataset$($Colors.Reset)"
        return 1
    }
}

function Step-get_random_games {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[FETCH] Fetching random games using smart discovery algorithms...$($Colors.Reset)"
    
    # Default parameters
    $Platform = "lichess"
    $SkillLevel = "intermediate"
    $MaxGames = "100"
    $GameTypes = "all"
    $SinceDate = ""
    $OutputFile = ""
    $IncludeMetadata = $false
    
    # Parse arguments
    for ($i = 0; $i -lt $Args.Count; $i++) {
        switch ($Args[$i]) {
            "--platform" { $Platform = $Args[$i + 1]; $i++ }
            "--skill-level" { $SkillLevel = $Args[$i + 1]; $i++ }
            "--max-games" { $MaxGames = $Args[$i + 1]; $i++ }
            "--game-types" { $GameTypes = $Args[$i + 1]; $i++ }
            "--since" { $SinceDate = $Args[$i + 1]; $i++ }
            "--output" { $OutputFile = $Args[$i + 1]; $i++ }
            "--include-metadata" { $IncludeMetadata = $true }
            default { Write-Host "$($Colors.Yellow)Unknown parameter: $($Args[$i])$($Colors.Reset)" }
        }
    }
    
    # Build command
    $CmdArgs = @(
        "src\scripts\smart_random_games_fetcher.py",
        "--platform", $Platform,
        "--skill-level", $SkillLevel,
        "--max-games", $MaxGames,
        "--game-types", $GameTypes
    )
    
    if ($SinceDate) { $CmdArgs += "--since", $SinceDate }
    if ($OutputFile) { $CmdArgs += "--output", $OutputFile }
    if ($IncludeMetadata) { $CmdArgs += "--include-metadata" }
    
    Write-Host "$($Colors.Blue)[EXEC] Executing: python $($CmdArgs -join ' ')$($Colors.Reset)"
    python @CmdArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$($Colors.Green)[OK] Random games fetched successfully using smart discovery.$($Colors.Reset)"
    }
    else {
        Write-Host "$($Colors.Red)[ERROR] Failed to fetch random games.$($Colors.Reset)"
        return 1
    }
}

function Step-get_games {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[FETCH] Importing games from remote servers...$($Colors.Reset)"
    
    # Parse arguments
    $UseSmartMode = $true
    $Platform = "both"
    $MaxGames = "500"
    $SinceDate = ""
    $UsersList = ""
    
    for ($i = 0; $i -lt $Args.Count; $i++) {
        switch ($Args[$i]) {
            "--legacy" { $UseSmartMode = $false }
            "--platform" { $Platform = $Args[$i + 1]; $i++ }
            "--max-games" { $MaxGames = $Args[$i + 1]; $i++ }
            "--since" { $SinceDate = $Args[$i + 1]; $i++ }
            "--users" { $UsersList = $Args[$i + 1]; $i++ }
            "--server" { $UseSmartMode = $false; break }
        }
    }
    
    if ($UseSmartMode) {
        Write-Host "$($Colors.Blue)[SMART] Using smart games fetching with heuristic user discovery...$($Colors.Reset)"
        
        $CmdArgs = @(
            "src\scripts\smart_random_games_fetcher.py",
            "--platform", $Platform,
            "--skill-level", "all",
            "--max-games", $MaxGames,
            "--game-types", "all",
            "--include-metadata"
        )
        
        if ($SinceDate) { $CmdArgs += "--since", $SinceDate }
        
        Write-Host "$($Colors.Blue)[EXEC] Executing smart fetch: python $($CmdArgs -join ' ')$($Colors.Reset)"
        python @CmdArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$($Colors.Green)[OK] Games imported successfully using smart discovery.$($Colors.Reset)"
        }
        else {
            Write-Host "$($Colors.Red)[ERROR] Smart fetch failed, falling back to legacy mode...$($Colors.Reset)"
            $UseSmartMode = $false
        }
    }
    
    if (-not $UseSmartMode) {
        Write-Host "$($Colors.Blue)[LEGACY] Using legacy games download (predefined users)...$($Colors.Reset)"
        
        $LegacyCmdArgs = @("src\scripts\download_games_parallel.py")
        
        if ($UsersList) { $LegacyCmdArgs += "--users", $UsersList }
        if ($SinceDate) { $LegacyCmdArgs += "--since", $SinceDate } else { $LegacyCmdArgs += "--since", "2024-01-01" }
        
        # Add default servers if not specified
        if ($Args -notcontains "--server") {
            $LegacyCmdArgs += "--server", "lichess.org", "chess.com"
        }
        else {
            $LegacyCmdArgs += $Args
        }
        
        Write-Host "$($Colors.Blue)[EXEC] Executing legacy fetch: python $($LegacyCmdArgs -join ' ')$($Colors.Reset)"
        python @LegacyCmdArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$($Colors.Green)[OK] Games imported successfully using legacy method.$($Colors.Reset)"
        }
        else {
            Write-Host "$($Colors.Red)[ERROR] Failed to import games.$($Colors.Reset)"
            return 1
        }
    }
}

function Step-inspect_pgn {
    Write-Host "$($Colors.Cyan)[CHECK] Inspecting PGN files...$($Colors.Reset)"
    python src\scripts\inspect_pgn.py --output $env:PGN_PATH
    Write-Host "$($Colors.Green)[OK] PGN inspection completed.$($Colors.Reset)"
}

function Step-inspect_pgn_zip {
    param([string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[CHECK] Inspecting PGN files...$($Colors.Reset)"
    python src\scripts\inspect_pgn_cli.py @Args
    Write-Host "$($Colors.Green)[OK] PGN inspection completed.$($Colors.Reset)"
}

function Step-clean_games {
    Write-Host "$($Colors.Cyan)[CLEAN] Cleaning PGN files...$($Colors.Reset)"
    $confirm = Read-Host "$($Colors.Yellow)[PROMPT] Do you want to clean ALL pgn files? If yes, you must import games again (get_games command) (y/n)$($Colors.Reset)"
    if ($confirm -notmatch "^[Yy]$") {
        Write-Host "$($Colors.Red)[STOP] Pipeline execution stopped by user.$($Colors.Reset)"
        exit 0
    }
    Remove-Item -Path $env:PGN_PATH -Recurse -Force
    Write-Host "$($Colors.Green)[OK] PGN files cleaned.$($Colors.Reset)"
}

function Step-init_db {
    Write-Host "$($Colors.Cyan)[INIT] Initializing database schema...$($Colors.Reset)"
    python src\scripts\init_db.py
    Write-Host "$($Colors.Green)[OK] Database schema initialized.$($Colors.Reset)"
}

function Step-clean_cache {
    Write-Host "$($Colors.Cyan)[CLEAN] Clearing Python cache...$($Colors.Reset)"
    Set-Location ".."  # Go to project root
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path . -Recurse -File -Name "*.pyc" | Remove-Item -Force
    Write-Host "$($Colors.Green)[OK] Cache cleared.$($Colors.Reset)"
    Set-Location "src\pipeline"
}

function Invoke-UpTo {
    param([string]$UpToStep, [string[]]$Args = @())
    
    Write-Host "$($Colors.Cyan)[RUN] Running pipeline up to and including step: $UpToStep...$($Colors.Reset)"
    
    $Steps = @("init_db", "import_pgns", "generate_features", "analyze_tactics", "export_dataset", "generate_exercises", "get_random_games")
    $UpToIndex = $Steps.IndexOf($UpToStep)
    
    if ($UpToIndex -eq -1) {
        Write-Host "$($Colors.Red)[ERROR] Step '$UpToStep' not found in pipeline.$($Colors.Reset)"
        return 1
    }
    
    $SelectedSteps = $Steps[0..$UpToIndex]
    Invoke-StepsInteractive $SelectedSteps
}

function Invoke-All {
    $steps = @("init_db", "clean_cache", "get_games", "import_pgns", "inspect_pgn", "generate_features_with_tactics", "export_dataset", "generate_combined_dataset", "generate_exercises")
    
    foreach ($step in $steps) {
        $status = Invoke-Step $step (Get-Command "Step-$step").ScriptBlock
        if ($status -ne 0) {
            Write-Host "$($Colors.Red)[ERROR] Step '$step' failed. Stopping pipeline.$($Colors.Reset)"
            exit 1
        }
    }
    
    Write-Host "$($Colors.Green)[COMPLETE] Pipeline executed successfully.$($Colors.Reset)"
}

function Invoke-FromStep {
    param([string]$StartStep, [string[]]$Args = @())
    
    $AllSteps = @("auto_tag", "analyze_tactics", "generate_exercises", "generate_features", "export_dataset", "clean_db", "import_pgns", "init_db", "clean_cache", "clean_games", "inspect_pgn_zip", "check_db", "clean_analysis_data", "get_random_games")
    $StartIndex = $AllSteps.IndexOf($StartStep)
    
    if ($StartIndex -eq -1) {
        Write-Host "$($Colors.Red)[ERROR] Step '$StartStep' not found.$($Colors.Reset)"
        return 1
    }
    
    $StepsToRun = $AllSteps[$StartIndex..($AllSteps.Count - 1)]
    foreach ($step in $StepsToRun) {
        $status = Invoke-Step $step (Get-Command "Step-$step").ScriptBlock $Args
        if ($status -ne 0) {
            Write-Host "$($Colors.Red)[ERROR] Step '$step' failed. Stopping pipeline.$($Colors.Reset)"
            exit $status
        }
    }
}

function Invoke-InteractivePipeline {
    $Steps = @("init_db", "clean_cache", "get_games", "import_pgns", "inspect_pgn", "generate_features", "analyze_tactics", "export_dataset", "generate_exercises", "clean_analysis_data", "clean_games", "inspect_pgn_zip", "check_db", "create_issues")
    
    Write-Host "$($Colors.Cyan)[INTERACTIVE] Interactive mode: Execute pipeline steps one by one$($Colors.Reset)"
    Invoke-StepsInteractive $Steps
}

# Main dispatcher
switch ($Command) {
    "all" {
        Invoke-All
    }
    "from" {
        if ($Arguments.Count -eq 0) {
            Write-Host "$($Colors.Red)[ERROR] 'from' command requires a step name$($Colors.Reset)"
            exit 1
        }
        Invoke-FromStep $Arguments[0] $Arguments[1..($Arguments.Count - 1)]
    }
    "interactive" {
        Invoke-InteractivePipeline
    }
    { $_ -in @("auto_tag", "analyze_tactics", "generate_exercises", "generate_features", "generate_features_with_tactics", "estimate_tactical_features", "test_tactical_analysis", "clean_db", "export_dataset", "import_pgns", "init_db", "clean_cache", "get_games", "inspect_pgn", "clean_games", "inspect_pgn_zip", "check_db", "clean_analysis_data", "create_issues", "get_random_games", "generate_combined_dataset") } {
        $status = Invoke-Step $Command (Get-Command "Step-$Command").ScriptBlock $Arguments
        exit $status
    }
    default {
        Write-Host "$($Colors.Yellow)Usage:$($Colors.Reset) $($MyInvocation.MyCommand.Name) {all | from <step> | auto_tag | analyze_tactics [--method enhanced|lightweight] | generate_exercises | generate_features [args] | generate_features_with_tactics [args] | estimate_tactical_features [args] | test_tactical_analysis | clean_db | export_dataset | import_pgns | init_db | clean_cache | get_games | inspect_pgn | clean_games| inspect_pgn_zip| check_db| clean_analysis_data|create_issues| get_random_games}"
        Write-Host "$($Colors.Cyan)[SMART] Smart Game Fetching Commands:$($Colors.Reset)"
        Write-Host "  $($Colors.Yellow)get_games$($Colors.Reset)                             - Smart games import with heuristic user discovery"
        Write-Host "  $($Colors.Yellow)get_games --platform lichess$($Colors.Reset)          - Fetch from Lichess only using smart discovery"
        Write-Host "  $($Colors.Yellow)get_games --platform both$($Colors.Reset)             - Fetch from both Lichess and Chess.com"
        Write-Host "  $($Colors.Yellow)get_games --max-games 1000$($Colors.Reset)            - Limit total games to fetch"
        Write-Host "  $($Colors.Yellow)get_games --since 2024-01-01$($Colors.Reset)          - Fetch games since specific date"
        Write-Host "  $($Colors.Yellow)get_games --legacy$($Colors.Reset)                    - Use legacy method with predefined users"
        Write-Host "  $($Colors.Yellow)get_random_games$($Colors.Reset)                      - Fetch random games using smart discovery"
        Write-Host "  $($Colors.Yellow)get_random_games --skill-level intermediate$($Colors.Reset) - Target specific skill level"
        Write-Host "  $($Colors.Yellow)get_random_games --game-types rapid blitz$($Colors.Reset) - Target specific game types"
        Write-Host "  $($Colors.Yellow)get_random_games --include-metadata$($Colors.Reset)   - Include JSON metadata file"
        Write-Host "$($Colors.Cyan)[TACTICAL] New Tactical Analysis Commands:$($Colors.Reset)"
        Write-Host "  $($Colors.Yellow)analyze_tactics --method enhanced$($Colors.Reset)     - Enhanced batch tactical analysis with tracking"
        Write-Host "  $($Colors.Yellow)analyze_tactics --method lightweight$($Colors.Reset)  - Use lightweight estimation within analyze_tactics"
        Write-Host "  $($Colors.Yellow)generate_features_with_tactics$($Colors.Reset)        - Integrated feature generation + tactical analysis"
        Write-Host "  $($Colors.Yellow)estimate_tactical_features$($Colors.Reset)            - Fast lightweight tactical feature estimation"
        Write-Host "  $($Colors.Yellow)test_tactical_analysis$($Colors.Reset)                - Test and report tactical analysis coverage"
        Write-Host "$($Colors.Cyan)[DATASET] Dataset Export Commands:$($Colors.Reset)"
        Write-Host "  $($Colors.Yellow)export_dataset$($Colors.Reset)                        - Export each source to separate parquet files"
        Write-Host "$($Colors.Cyan)[EXAMPLES] Examples:$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) get_games --platform both --max-games 1000 --since 2024-01-01$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) get_random_games --platform lichess --skill-level advanced --max-games 200$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) get_random_games --game-types rapid --include-metadata$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) analyze_tactics --method enhanced --source personal --max-games 1000$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) generate_features_with_tactics --source elite --max-games 500$($Colors.Reset)"
        Write-Host "  $($Colors.Green).\$($MyInvocation.MyCommand.Name) estimate_tactical_features --source personal --max-games 10000$($Colors.Reset)"
        Set-Location $InitialDirectory
        exit 1
    }
}

# Cleanup function to restore the initial directory
finally {
    Set-Location $InitialDirectory
}
